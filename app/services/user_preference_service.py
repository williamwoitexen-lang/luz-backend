"""
Serviço para gerenciar preferências de usuário (idioma, etc).

Utiliza cache Redis para performance e sincroniza com SQL Server.
"""

import logging
import os
try:
    import redis
    REDIS_AVAILABLE_IMPORT = True
except ImportError:
    REDIS_AVAILABLE_IMPORT = False

from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Inicializar conexão Redis (com fallback)
redis_client = None
REDIS_AVAILABLE = False

if REDIS_AVAILABLE_IMPORT:
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True,
            socket_connect_timeout=2
        )
        redis_client.ping()
        REDIS_AVAILABLE = True
        logger.info("[UserPreferenceService] ✅ Redis connected (shared cache enabled)")
    except Exception as e:
        logger.warning(f"[UserPreferenceService] ⚠️  Redis unavailable ({e}), queries will not be cached")
        redis_client = None
        REDIS_AVAILABLE = False
else:
    logger.warning("[UserPreferenceService] ⚠️  Redis package not installed, queries will not be cached")


class UserPreference:
    """Modelo SQLAlchemy para preferências de usuário."""
    
    def __init__(self, user_id: str, preferred_language: str = "pt"):
        self.user_id = user_id
        self.preferred_language = preferred_language
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class UserPreferenceService:
    """Serviço para gerenciar preferências de usuário."""
    
    # Constantes
    CACHE_TTL = 86400  # 24 horas em segundos
    CACHE_KEY_PATTERN = "user:{user_id}:language"
    
    @staticmethod
    def _get_cache_key(user_id: str) -> str:
        """Gera chave de cache para usuário."""
        return UserPreferenceService.CACHE_KEY_PATTERN.format(user_id=user_id)
    
    @staticmethod
    def save_user_preference(
        user_id: str,
        preferred_language: str = "pt"
    ) -> dict:
        """
        Salva ou atualiza preferência do usuário.
        
        Primeira vez: INSERT no DB
        Próximas vezes: UPDATE no DB + cache Redis
        
        Args:
            db: Sessão SQLAlchemy
            user_id: ID do usuário (Azure Object ID)
            preferred_language: Código de idioma (pt, en, es, etc)
        
        Returns:
            Dict com status da operação
        """
        try:
            cache_key = UserPreferenceService._get_cache_key(user_id)
            
            # Atualizar cache sempre (rápido)
            if REDIS_AVAILABLE:
                redis_client.setex(
                    cache_key,
                    UserPreferenceService.CACHE_TTL,
                    preferred_language
                )
                logger.info(f"[UserPreference] Cache atualizado: {user_id} → {preferred_language}")
            
            # Buscar preferência existente no DB
            from app.core.sqlserver import get_sqlserver_connection
            conn = get_sqlserver_connection()
            
            # Verificar se já existe
            result_list = conn.execute(
                "SELECT preferred_language FROM user_preferences WHERE user_id = ?",
                [user_id]
            )
            result = result_list[0] if result_list else None
            
            if result:
                # UPDATE
                if result.get('preferred_language') != preferred_language:
                    conn.execute(
                        """
                        UPDATE user_preferences 
                        SET preferred_language = ?, updated_at = GETUTCDATE()
                        WHERE user_id = ?
                        """,
                        [preferred_language, user_id]
                    )
                    logger.info(f"[UserPreference] Preferência atualizada: {user_id}")
                    return {
                        "status": "updated",
                        "user_id": user_id,
                        "preferred_language": preferred_language
                    }
            else:
                # INSERT
                conn.execute(
                    """
                    INSERT INTO user_preferences (user_id, preferred_language, created_at, updated_at)
                    VALUES (?, ?, GETUTCDATE(), GETUTCDATE())
                    """,
                    [user_id, preferred_language]
                )
                logger.info(f"[UserPreference] Nova preferência criada: {user_id}")
                return {
                    "status": "created",
                    "user_id": user_id,
                    "preferred_language": preferred_language
                }
            return {
                "status": "unchanged",
                "user_id": user_id,
                "preferred_language": preferred_language
            }
            
        except Exception as e:
            logger.error(f"[UserPreference] Erro ao salvar preferência: {e}")
            raise
    
    @staticmethod
    def get_user_preferred_language(
        user_id: str,
        default: str = "pt"
    ) -> str:
        """
        Busca preferência de idioma do usuário com cache.
        
        Ordem:
        1. Redis cache (rápido)
        2. SQL Server DB (se expirou cache)
        3. Default (pt) se não encontrar
        
        Args:
            db: Sessão SQLAlchemy
            user_id: ID do usuário
            default: Idioma padrão se não encontrar
        
        Returns:
            Código de idioma (pt, en, es, etc)
        """
        cache_key = UserPreferenceService._get_cache_key(user_id)
        
        # Tentar cache primeiro (muito rápido)
        if REDIS_AVAILABLE:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"[UserPreference] Cache HIT para {user_id}: {cached}")
                    return cached
                logger.debug(f"[UserPreference] Cache MISS para {user_id}")
            except Exception as e:
                logger.warning(f"[UserPreference] Erro ao acessar cache Redis: {e}")
        
        # Buscar do DB se não tem em cache
        try:
            from app.core.sqlserver import get_sqlserver_connection
            conn = get_sqlserver_connection()
            
            result_list = conn.execute(
                "SELECT preferred_language FROM user_preferences WHERE user_id = ?",
                [user_id]
            )
            result = result_list[0] if result_list else None
            
            if result:
                language = result.get('preferred_language')
                logger.debug(f"[UserPreference] Encontrado no DB: {user_id} → {language}")
            else:
                language = default
                logger.debug(f"[UserPreference] Não encontrado, usando default: {default}")
            
            # Atualizar cache
            if REDIS_AVAILABLE:
                redis_client.setex(
                    cache_key,
                    UserPreferenceService.CACHE_TTL,
                    language
                )
            
            return language
            
        except Exception as e:
            logger.error(f"[UserPreference] Erro ao buscar preferência: {e}")
            return default
    
    @staticmethod
    def update_preferred_language(
        user_id: str,
        new_language: str
    ) -> dict:
        """
        Atualiza idioma preferido do usuário.
        
        Chamado quando usuário muda de idioma na interface.
        
        Args:
            user_id: ID do usuário
            new_language: Novo código de idioma
        
        Returns:
            Dict com confirmação da atualização
        """
        logger.info(f"[UserPreference] Atualizando idioma para {user_id}: {new_language}")
        return UserPreferenceService.save_user_preference(user_id, new_language)
    
    @staticmethod
    def invalidate_cache(user_id: str) -> None:
        """
        Invalida cache Redis para um usuário.
        
        Usado quando houver alteração direta no DB.
        
        Args:
            user_id: ID do usuário
        """
        if REDIS_AVAILABLE:
            cache_key = UserPreferenceService._get_cache_key(user_id)
            redis_client.delete(cache_key)
            logger.info(f"[UserPreference] Cache invalidado para {user_id}")


def create_user_preferences_table_if_not_exists():
    """
    Cria tabela user_preferences se não existir.
    
    Chamado na inicialização da aplicação.
    """
    try:
        from app.core.sqlserver import get_sqlserver_connection
        conn = get_sqlserver_connection()
        
        # Verificar se tabela já existe
        conn.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES 
                          WHERE TABLE_NAME = 'user_preferences')
            CREATE TABLE user_preferences (
                user_id NVARCHAR(36) PRIMARY KEY,
                preferred_language NVARCHAR(10) DEFAULT 'pt',
                created_at DATETIME2 DEFAULT GETUTCDATE(),
                updated_at DATETIME2 DEFAULT GETUTCDATE(),
                INDEX idx_language (preferred_language)
            )
        """)
        
        logger.info("[UserPreference] Tabela user_preferences verificada/criada")
        
    except Exception as e:
        logger.error(f"[UserPreference] Erro ao criar tabela: {e}")
        raise
