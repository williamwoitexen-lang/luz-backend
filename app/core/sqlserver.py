"""
SQL Server connection and utilities with Managed Identity support.
"""
import os
import logging
import threading
import struct
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Importar pyodbc ou mock
import sys

# Estratégia simples:
# 1. Tentar importar pyodbc real (disponível em produção)
# 2. Se falhar, usar mock (disponível em dev/teste)
# Exceto se estiver hardcoded com USE_PYODBC_MOCK=true

_force_mock = os.getenv('USE_PYODBC_MOCK', '').lower() == 'true'

if _force_mock:
    logger.info("📋 USE_PYODBC_MOCK=true, loading MockConnection")
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    import pyodbc_mock as pyodbc
else:
    # Tentar import real pyodbc
    try:
        import pyodbc
        logger.info("✅ Using real pyodbc library")
    except ImportError as e:
        # Fallback para mock em dev/teste
        logger.warning(f"⚠️  Real pyodbc not available, using MockConnection: {e}")
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        import pyodbc_mock as pyodbc

# Importar azure-identity para Managed Identity
try:
    from azure.identity import DefaultAzureCredential
    HAS_AZURE_IDENTITY = True
except ImportError:
    logger.warning("azure-identity not available, will use connection string as-is")
    HAS_AZURE_IDENTITY = False


def get_sqlserver_token() -> Optional[str]:
    """
    Obter token do Managed Identity para SQL Server.
    Retorna None se nao conseguir (fallback para credenciais na connection string).
    """
    if not HAS_AZURE_IDENTITY:
        return None
    
    try:
        credential = DefaultAzureCredential()
        # Token para Azure SQL Database
        token = credential.get_token("https://database.windows.net/.default")
        return token.token
    except Exception as e:
        logger.warning(f"Failed to get Managed Identity token: {e}")
        return None


def build_connection_string(
    host: str,
    database: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    use_managed_identity: bool = False
) -> str:
    """
    Build connection string for SQL Server.
    
    Args:
        host: SQL Server hostname
        database: Database name
        username: SQL Server username (if not using Managed Identity)
        password: SQL Server password (if not using Managed Identity)
        use_managed_identity: Use Managed Identity instead of username/password
    
    Returns:
        Connection string
    """
    base = f"Driver={{ODBC Driver 18 for SQL Server}};Server={host};Database={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=5"
    
    if use_managed_identity:
        logger.info(f"Connection string will use Managed Identity for {host}/{database}")
        return base
    elif username and password:
        # SQL Server authentication
        cs = f"{base};UID={username};PWD={password}"
        logger.info(f"Connection string will use SQL Server authentication for {host}/{database}")
        return cs
    else:
        logger.warning(f"No credentials provided, using Managed Identity for {host}/{database}")
        return base


class SQLServerConnection:
    """SQL Server connection manager with SQL Server auth and Managed Identity fallback."""
    
    def __init__(self, connection_string: str, use_managed_identity: bool = False):
        self.connection_string = connection_string
        self.use_managed_identity = use_managed_identity
        self.conn = None
        self._lock = threading.Lock()  # Previne race condition
    
    def connect(self):
        """Connect on demand (lazy connection - thread-safe)."""
        if self.conn:
            return
        
        with self._lock:
            # Double-check after acquiring lock
            if self.conn:
                return
            
            logger.info("Iniciando conexão com SQL Server...")
            try:
                if self.use_managed_identity:
                    # Try Managed Identity first
                    token = get_sqlserver_token()
                    if token:
                        logger.info(f"Token obtido (comprimento: {len(token)} chars)")
                        token_bytes = token.encode("utf-16-le")
                        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
                        logger.info("Conectando com token via attrs_before...")
                        self.conn = pyodbc.connect(
                            self.connection_string,
                            attrs_before={1256: token_struct},
                            timeout=5
                        )
                        self.conn.autocommit = False
                        # Desabilitar limite de 8000 caracteres para strings
                        self.conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
                        self.conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
                        logger.info("Conectado com Managed Identity token")
                    else:
                        logger.warning("Token não disponível, tentando com connection string...")
                        self.conn = pyodbc.connect(self.connection_string, timeout=5)
                        self.conn.autocommit = False
                        # Desabilitar limite de 8000 caracteres para strings
                        self.conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
                        self.conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
                        logger.info("Conectado com connection string")
                else:
                    # Use SQL Server authentication from connection string
                    logger.info("Conectando com SQL Server authentication...")
                    self.conn = pyodbc.connect(self.connection_string, timeout=5)
                    self.conn.autocommit = False
                    # Desabilitar limite de 8000 caracteres para strings
                    self.conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
                    self.conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
                    logger.info("Conectado com SQL Server authentication")
                    
            except Exception as e:
                logger.error(f"Erro ao conectar: {e}", exc_info=True)
                self.conn = None
                raise
        
    
    def execute(self, query: str, params: List[Any] = None) -> List[Dict]:
        """Execute query and return results."""
        if not self.conn:
            raise RuntimeError("SQL Server not connected")
        
        cursor = self.conn.cursor()
        try:
            # Force fresh data - disable query cache
            if query.strip().upper().startswith("SELECT"):
                cursor.execute("SET NOCOUNT ON;")
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Se for SELECT, retorna resultados
            if query.strip().upper().startswith("SELECT"):
                columns = [description[0] for description in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            else:
                # Para INSERT/UPDATE/DELETE
                self.conn.commit()
                return []
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Query execution error: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_single(self, query: str, params: List[Any] = None) -> Optional[Dict]:
        """Execute query and return first result."""
        results = self.execute(query, params)
        return results[0] if results else None
    
    def close(self):
        """Close connection."""
        if self.conn:
            self.conn.close()


def get_sqlserver_connection() -> SQLServerConnection:
    """Get SQL Server connection (lazy - connects on first use).
    
    Priority (in order of preference):
    1. SQL Server authentication (UID/PWD from env vars) - PRIMARY (no MFA issues)
    2. Managed Identity (DefaultAzureCredential) - FALLBACK (production)
    3. Connection string from env var - LEGACY (for backwards compatibility)
    
    Environment variables:
    - SQLSERVER_HOST: Server hostname (required)
    - SQLSERVER_DATABASE: Database name (default: master)
    - SQLSERVER_USERNAME: SQL Server username (for SQL auth)
    - : SQL Server password (for SQL auth)
    - SQLSERVER_CONNECTION_STRING: Full connection string (overrides above if set)
    - USE_MANAGED_IDENTITY: Force Managed Identity even if credentials provided
    
    Requires SQLSERVER_HOST and SQLSERVER_DATABASE OR SQLSERVER_CONNECTION_STRING
    """
    use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true"
    
    # Try to build connection string from individual env vars FIRST (new preferred method)
    host = os.getenv("SQLSERVER_HOST")
    database = os.getenv("SQLSERVER_DATABASE", "master")
    username = os.getenv("SQLSERVER_USERNAME")
    password = os.getenv("")
    
    # Priority 1: SQL Server auth with individual env vars (if credentials provided)
    if host and username and password and not use_managed_identity:
        logger.info(f"Using SQL Server authentication for {host}/{database}")
        cs = build_connection_string(host, database, username, password, use_managed_identity=False)
        conn = SQLServerConnection(cs, use_managed_identity=False)
        conn.connect()
        return conn
    
    # Priority 2: Full connection string from env var (backwards compatibility)
    cs = os.getenv("SQLSERVER_CONNECTION_STRING")
    if cs:
        logger.info("Using SQLSERVER_CONNECTION_STRING from env var")
        conn = SQLServerConnection(cs, use_managed_identity=use_managed_identity)
        conn.connect()
        return conn
    
    if not host:
        raise RuntimeError(
            "SQL Server connection not configured. Provide either:\n"
            "1. SQLSERVER_HOST + SQLSERVER_USERNAME + , OR\n"
            "2. SQLSERVER_CONNECTION_STRING env var"
        )
    
    # Priority 3: Managed Identity (fallback)
    logger.info(f"Using Managed Identity for {host}/{database}")
    cs = build_connection_string(host, database, use_managed_identity=True)
    conn = SQLServerConnection(cs, use_managed_identity=True)
    conn.connect()
    return conn

