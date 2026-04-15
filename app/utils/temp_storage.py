import uuid
import time
import shutil
import threading
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# In-memory storage (fallback quando Redis não está disponível)
# Format: { temp_id: { "file_path": Path, "created_at": datetime, "filename": str, "extracted_fields": dict, ... } }
_temp_storage: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()

TEMP_DIR = Path("storage/temp")
TEMP_TTL_SECONDS = 10 * 60  # 10 minutes
REDIS_PREFIX = "temp_session:"

# Redis client (inicializado na primeira use)
_redis_client: Optional[redis.Redis] = None
_redis_enabled = False


def _init_redis():
    """Initialize Redis connection. Returns True if successful, False otherwise."""
    global _redis_client, _redis_enabled
    
    if not REDIS_AVAILABLE:
        return False
    
    try:
        host = os.getenv('REDIS_HOST', 'localhost')
        port = int(os.getenv('REDIS_PORT', 6379))
        
        _redis_client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_keepalive=True,
            health_check_interval=30
        )
        
        # Test connection
        _redis_client.ping()
        _redis_enabled = True
        logger.info(f"✅ Redis connected ({host}:{port})")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️  Redis not available ({e}), using in-memory storage fallback")
        _redis_client = None
        _redis_enabled = False
        return False


def init_temp_dir():
    """Initialize temporary storage directory."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    # Try to init Redis on first temp storage use
    if not _redis_enabled and REDIS_AVAILABLE:
        _init_redis()


def create_temp_session(filename: str, file_bytes: bytes, extracted_fields: dict) -> str:
    """
    Create a temporary ingestion session.
    Returns temp_id for later confirmation.
    Uses Redis if available, falls back to in-memory storage.
    """
    global _redis_enabled, _redis_client
    init_temp_dir()
    
    temp_id = str(uuid.uuid4())
    temp_path = TEMP_DIR / temp_id
    temp_path.mkdir(parents=True, exist_ok=True)
    
    # Save file to disk
    file_path = temp_path / filename
    file_path.write_bytes(file_bytes)
    
    # Prepare session data
    session_data = {
        "file_path": str(file_path),
        "filename": filename,
        "created_at": datetime.now().isoformat(),
        "extracted_fields": extracted_fields,
    }
    
    # Try Redis first
    if _redis_enabled and _redis_client:
        try:
            _redis_client.setex(
                f"{REDIS_PREFIX}{temp_id}",
                TEMP_TTL_SECONDS,
                json.dumps(session_data)
            )
            logger.debug(f"Session {temp_id} stored in Redis")
            return temp_id
        except Exception as e:
            logger.warning(f"Redis write failed ({e}), falling back to memory")
            _redis_enabled = False
    
    # Fallback to in-memory storage
    with _lock:
        _temp_storage[temp_id] = {
            **session_data,
            "created_at": datetime.now(),
        }
    
    logger.debug(f"Session {temp_id} stored in memory")
    # Schedule cleanup in TTL
    _schedule_cleanup(temp_id)
    
    return temp_id


def get_temp_session(temp_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a temporary session by ID.
    Checks Redis first, then falls back to memory.
    """
    global _redis_enabled, _redis_client
    # Try Redis first
    if _redis_enabled and _redis_client:
        try:
            session_json = _redis_client.get(f"{REDIS_PREFIX}{temp_id}")
            if session_json:
                session = json.loads(session_json)
                # Convert created_at back to datetime if needed
                session["created_at"] = datetime.fromisoformat(session["created_at"])
                return session
        except Exception as e:
            logger.warning(f"Redis read failed ({e}), trying memory fallback")
    
    # Fallback to in-memory storage
    with _lock:
        if temp_id not in _temp_storage:
            return None
        
        session = _temp_storage[temp_id]
        # Check if expired
        age = (datetime.now() - session["created_at"]).total_seconds()
        if age > TEMP_TTL_SECONDS:
            # Auto-cleanup
            delete_temp_session(temp_id)
            return None
        
        return session


def delete_temp_session(temp_id: str) -> bool:
    """
    Delete a temporary session and its files.
    Deletes from Redis and memory.
    """
    global _redis_enabled, _redis_client
    # Delete from Redis
    if _redis_enabled and _redis_client:
        try:
            _redis_client.delete(f"{REDIS_PREFIX}{temp_id}")
        except Exception as e:
            logger.warning(f"Redis delete failed ({e})")
    
    # Delete from memory
    with _lock:
        if temp_id not in _temp_storage:
            # Try anyway, in case it's only in Redis
            temp_path = TEMP_DIR / temp_id
            if temp_path.exists():
                shutil.rmtree(temp_path)
                return True
            # Session not found anywhere
            return False
        
        session = _temp_storage.pop(temp_id)
        # Remove files
        temp_path = Path(session["file_path"]).parent
        if temp_path.exists():
            shutil.rmtree(temp_path)
        return True


def _schedule_cleanup(temp_id: str):
    """Schedule automatic cleanup after TTL."""
    def cleanup():
        time.sleep(TEMP_TTL_SECONDS)
        delete_temp_session(temp_id)
    
    thread = threading.Thread(target=cleanup, daemon=True)
    thread.start()


def cleanup_expired():
    """Cleanup all expired sessions (can be called periodically)."""
    # Redis handles this automatically via SETEX TTL, no manual cleanup needed
    
    # Cleanup memory storage
    with _lock:
        expired = []
        for temp_id, session in _temp_storage.items():
            age = (datetime.now() - session["created_at"]).total_seconds()
            if age > TEMP_TTL_SECONDS:
                expired.append(temp_id)
        
        for temp_id in expired:
            session = _temp_storage.pop(temp_id)
            temp_path = Path(session["file_path"]).parent
            if temp_path.exists():
                shutil.rmtree(temp_path)
            logger.debug(f"Cleaned up expired session {temp_id}")
