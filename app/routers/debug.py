"""
Debug endpoints - diagnostics and testing.
ONLY for development and troubleshooting.
"""
import os
import struct
import socket
import logging
from fastapi import APIRouter
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/env")
def debug_env():
    """Debug endpoint melhorado - testa TODAS as variáveis com diagnóstico completo"""
    
    def mask_secret(value: str, prefix: int = 4) -> str:
        if not value:
            return "NOT SET"
        if len(value) <= prefix:
            return "***"
        return value[:prefix] + "..." + f"(len={len(value)})"
    
    # Categorias de variáveis críticas
    categories = {
        "sqlserver": {
            "vars": ["SQLSERVER_HOST", "SQLSERVER_DATABASE", "SQLSERVER_USERNAME", "", "SQLSERVER_CONNECTION_STRING"],
            "optional_connection_string": True
        },
        "storage": {
            "vars": ["STORAGE_TYPE", "AZURE_STORAGE_ACCOUNT_NAME", "AZURE_STORAGE_CONTAINER_NAME", "AZURE_STORAGE_CONNECTION_STRING"],
            "optional_connection_string": True
        },
        "identity": {
            "vars": ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", ""]
        },
        "openai": {
            "vars": ["AZURE_OPENAI_ENDPOINT", ""]
        },
        "app": {
            "vars": ["LLM_SERVER_URL", "LANGCHAIN_BASE_URL", "CORS_ORIGINS"]
        },
        "infrastructure": {
            "vars": ["KEYVAULT_URL", "KEYVAULT_NAME", "CONTAINERAPPS_RG", "CONTAINERAPPS_NAME", "ACR_NAME", "CONTAINER_NAME", "FALLBACK_TAG", "MIN_REPLICAS"]
        }
    }
    
    # Funções de teste
    def test_sqlserver_connectivity():
        """Testa se SQL Server pode conectar via Managed Identity"""
        try:
            from app.core.sqlserver import get_sqlserver_token, get_sqlserver_connection
            
            host = os.getenv("SQLSERVER_HOST")
            database = os.getenv("SQLSERVER_DATABASE")
            conn_str = os.getenv("SQLSERVER_CONNECTION_STRING")
            
            # Se tem connection string, não precisa de token
            if conn_str:
                return {"auth_method": "connection_string", "status": "configured"}
            
            # Tenta via Managed Identity
            if not host or not database:
                return {"auth_method": "managed_identity", "status": "missing_host_or_database"}
            
            token = get_sqlserver_token()
            if token:
                return {"auth_method": "managed_identity", "status": "token_obtained"}
            return {"auth_method": "managed_identity", "status": "failed_to_obtain_token"}
        except Exception as e:
            return {"status": "error", "error": str(e)[:100]}
    
    def test_blob_connectivity():
        """Testa se Blob Storage pode conectar"""
        try:
            account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
            conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            
            # Se tem connection string, não precisa de Managed Identity
            if conn_str:
                return {"auth_method": "connection_string", "status": "configured"}
            
            # Tenta via Managed Identity
            if not account_name:
                return {"auth_method": "managed_identity", "status": "missing_account_name"}
            
            from azure.identity import DefaultAzureCredential
            cred = DefaultAzureCredential()
            # Tenta obter token para testar
            token = cred.get_token("https://storage.azure.com/.default")
            if token:
                return {"auth_method": "managed_identity", "status": "token_obtained"}
            return {"auth_method": "managed_identity", "status": "failed_to_obtain_token"}
        except Exception as e:
            return {"status": "error", "error": str(e)[:100]}
    
    def test_managed_identity_available():
        """Testa se Managed Identity está disponível (IMDS)"""
        try:
            from azure.identity import DefaultAzureCredential
            cred = DefaultAzureCredential()
            # Tenta qualquer token para verificar se MI está disponível
            token = cred.get_token("https://management.azure.com/.default")
            return True
        except:
            return False
    
    # Coleta informações
    all_vars = {}
    for category, config in categories.items():
        all_vars[category] = {}
        for var in config["vars"]:
            val = os.getenv(var)
            all_vars[category][var] = {
                "is_set": bool(val),
                "length": len(val) if val else 0,
                "preview": val if var in ["STORAGE_TYPE", "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "SQLSERVER_HOST", "SQLSERVER_DATABASE"] else mask_secret(val) if val else "NOT SET"
            }
    
    # Calcula status
    managed_identity_available = test_managed_identity_available()
    sqlserver_test = test_sqlserver_connectivity()
    blob_test = test_blob_connectivity()
    
    # Agrupa por categoria
    result = {}
    for category, config in categories.items():
        result[category] = {
            "variables": all_vars[category],
            "total": len(config["vars"]),
            "set": sum(1 for v in all_vars[category].values() if v["is_set"]),
            "missing": sum(1 for v in all_vars[category].values() if not v["is_set"])
        }
    
    # Adiciona testes de conectividade
    result["connectivity"] = {
        "managed_identity_available": managed_identity_available,
        "sqlserver": sqlserver_test,
        "blob_storage": blob_test
    }
    
    # Resumo geral
    all_vars_flat = [v for cat in all_vars.values() for v in cat.values()]
    total_set = sum(1 for v in all_vars_flat if v["is_set"])
    total_expected = len(all_vars_flat)
    missing = [k for cat, config in categories.items() for k in config["vars"] if not os.getenv(k)]
    
    result["summary"] = {
        "total_expected": total_expected,
        "total_set": total_set,
        "total_missing": len(missing),
        "percentage_set": f"{(total_set/total_expected)*100:.1f}%" if total_expected > 0 else "0%",
        "missing_vars": missing,
        "suggestions": [
            "🔴 SQLSERVER_HOST e SQLSERVER_DATABASE não estão setadas - configure-as na Pipeline" if not os.getenv("SQLSERVER_HOST") else None,
            "🟡 Managed Identity não disponível - verifique se Container App tem identidade atribuída" if not managed_identity_available else None,
            "✅ Managed Identity disponível" if managed_identity_available else None,
        ]
    }
    result["summary"]["suggestions"] = [s for s in result["summary"]["suggestions"] if s]
    
    return result


@router.get("/sqlserver")
def debug_sqlserver():
    """Debug endpoint - testa conexão com SQL Server"""
    import pyodbc
    from importlib.metadata import version as get_package_version
    from app.core.sqlserver import get_sqlserver_connection, get_sqlserver_token
    from app.core.config import KeyVaultConfig
    
    try:
        pyodbc_version = get_package_version("pyodbc")
    except Exception:
        pyodbc_version = "unknown"
    
    result = {
        "pyodbc_version": pyodbc_version,
        "pyodbc_drivers": pyodbc.drivers(),
        "connection_string": KeyVaultConfig.get_sqlserver_connection_string()[:80] + "..." if KeyVaultConfig.get_sqlserver_connection_string() else "NOT SET",
        "managed_identity_token": "checking...",
        "connection_status": "unknown",
        "error": None
    }
    
    try:
        # Tentar obter token
        token = get_sqlserver_token()
        result["managed_identity_token"] = "obtained" if token else "failed_to_obtain"
        
        # Tentar conectar
        sql = get_sqlserver_connection()
        if sql.conn:
            result["connection_status"] = "success"
            # Testar com query simples
            try:
                sql.execute("SELECT 1 as test")
                result["test_query"] = "success"
            except Exception as e:
                result["test_query"] = f"failed: {str(e)}"
                result["error"] = str(e)
        else:
            result["connection_status"] = "failed"
            result["error"] = "Connection object is None"
    except Exception as e:
        result["connection_status"] = "error"
        result["error"] = str(e)
    
    return result


@router.get("/blob-storage")
def debug_blob_storage():
    """Debug endpoint - testa conexão com Azure Blob Storage"""
    from app.providers.storage import get_storage_provider
    
    result = {
        "storage_type": os.getenv("STORAGE_TYPE", "NOT SET"),
        "connection_string_set": bool(os.getenv("AZURE_STORAGE_CONNECTION_STRING")),
        "account_name": os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "NOT SET"),
        "container_name": os.getenv("AZURE_STORAGE_CONTAINER_NAME", "NOT SET"),
        "provider_status": "unknown"
    }
    
    try:
        provider = get_storage_provider()
        result["provider_type"] = type(provider).__name__
        
        # Se for Azure, testa a conexão listando containers
        if hasattr(provider, 'blob_service_client'):
            try:
                containers = list(provider.blob_service_client.list_containers())
                result["provider_status"] = "success"
                result["containers_found"] = len(containers)
                result["container_names"] = [c["name"] for c in containers]
                # Verifica se o container configurado existe
                configured_container = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "documents")
                result["configured_container_exists"] = configured_container in result["container_names"]
            except Exception as e:
                result["provider_status"] = "error"
                result["error"] = str(e)
        else:
            # Local storage
            result["provider_status"] = "success (local)"
            
    except Exception as e:
        result["provider_status"] = "error"
        result["error"] = str(e)
    
    return result


@router.post("/test-config")
def debug_test_config(config: dict):
    """
    Debug endpoint - testa SQL e Blob com variáveis fornecidas via POST.
    
    Body exemplo (opção 1 - connection string):
    {
        "SQLSERVER_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=...",
        "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;..."
    }
    
    Body exemplo (opção 2 - Managed Identity):
    {
        "SQLSERVER_HOST": "myserver.database.windows.net",
        "SQLSERVER_DATABASE": "mydb",
        "AZURE_STORAGE_ACCOUNT_NAME": "myaccount"
    }
    """
    import pyodbc
    from azure.storage.blob import BlobServiceClient
    
    result = {
        "sqlserver": {"status": "not_tested", "error": None},
        "blob_storage": {"status": "not_tested", "error": None}
    }
    
    # Testa SQL Server - tenta com connection string OU host+database (Managed Identity)
    sql_conn_str = config.get("SQLSERVER_CONNECTION_STRING")
    sql_host = config.get("SQLSERVER_HOST")
    sql_database = config.get("SQLSERVER_DATABASE", "master")
    
    if not sql_conn_str and sql_host:
        # Build connection string para Managed Identity
        sql_conn_str = f"Driver={{ODBC Driver 18 for SQL Server}};Server={sql_host};Database={sql_database};Encrypt=yes;TrustServerCertificate=no"
    
    if sql_conn_str:
        try:
            # Tentar conectar com token de Managed Identity
            from app.core.sqlserver import get_sqlserver_token
            token = get_sqlserver_token()
            
            if token:
                token_bytes = token.encode("utf-16-le")
                token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
                conn_attrs = {1256: token_struct}
            else:
                conn_attrs = {}
            conn = pyodbc.connect(sql_conn_str, attrs_before=conn_attrs, timeout=10)
            
            # Testa query simples
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            result["sqlserver"]["status"] = "success"
        except Exception as e:
            result["sqlserver"]["status"] = "error"
            result["sqlserver"]["error"] = str(e)
    else:
        result["sqlserver"]["status"] = "skipped (no connection string or host)"
    
    # Testa Blob Storage - suporta connection string OU account name (Managed Identity)
    blob_conn_str = config.get("AZURE_STORAGE_CONNECTION_STRING")
    account_name = config.get("AZURE_STORAGE_ACCOUNT_NAME")
    container_name = config.get("AZURE_STORAGE_CONTAINER_NAME")
    
    if blob_conn_str:
        try:
            blob_service = BlobServiceClient.from_connection_string(blob_conn_str)
            containers = list(blob_service.list_containers())
            
            result["blob_storage"]["status"] = "success"
            result["blob_storage"]["containers_found"] = len(containers)
            
            # Se container específico foi informado, verifica se existe
            if container_name:
                container_exists = any(c.name == container_name for c in containers)
                result["blob_storage"]["container_exists"] = container_exists
                
        except Exception as e:
            result["blob_storage"]["status"] = "error"
            result["blob_storage"]["error"] = str(e)
    elif account_name:
        # Tentar com Managed Identity
        try:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
            blob_service = BlobServiceClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                credential=credential
            )
            containers = list(blob_service.list_containers())
            
            result["blob_storage"]["status"] = "success (managed identity)"
            result["blob_storage"]["containers_found"] = len(containers)
            
            if container_name:
                container_exists = any(c.name == container_name for c in containers)
                result["blob_storage"]["container_exists"] = container_exists
                
        except Exception as e:
            result["blob_storage"]["status"] = "error (managed identity)"
            result["blob_storage"]["error"] = str(e)
    else:
        result["blob_storage"]["status"] = "skipped (no connection string or account name)"
    
    return result


@router.get("/diagnose")
def debug_diagnose():
    """Debug endpoint AVANÇADO - diagnóstico completo com sugestões de correção"""
    
    import sys
    
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "diagnostics": {}
    }
    
    # TODAS as variáveis de ambiente (para debug)
    all_env_vars = dict(os.environ)
    result["all_environment_variables"] = {k: v[:50] + "..." if len(v) > 50 else v for k, v in all_env_vars.items() if not k.startswith("_")}
    
    # 1. Diagnóstico de SQL Server
    sqlserver_host = os.getenv("SQLSERVER_HOST")
    sqlserver_database = os.getenv("SQLSERVER_DATABASE")
    
    sqlserver_diag = {
        "host": sqlserver_host or "NOT SET",
        "database": sqlserver_database or "NOT SET",
        "has_connection_string": bool(os.getenv("SQLSERVER_CONNECTION_STRING")),
        "issues": [],
        "action_items": [],
        "debug_info": {
            "os_getenv_result_host": repr(sqlserver_host),
            "os_getenv_result_database": repr(sqlserver_database),
            "type_host": str(type(sqlserver_host)),
            "type_database": str(type(sqlserver_database))
        }
    }
    
    if not sqlserver_host:
        sqlserver_diag["issues"].append("❌ SQLSERVER_HOST não está definida")
        sqlserver_diag["action_items"].append("1. Ir para Azure DevOps → Pipeline Variables")
        sqlserver_diag["action_items"].append("2. Criar variável: SQLSERVER_HOST = elxa3sql-peoplechatbot-dev-001.database.windows.net")
    else:
        sqlserver_diag["issues"].append(f"✅ SQLSERVER_HOST está definida: {sqlserver_host}")
    
    if not sqlserver_database:
        sqlserver_diag["issues"].append("❌ SQLSERVER_DATABASE não está definida")
        sqlserver_diag["action_items"].append("1. Ir para Azure DevOps → Pipeline Variables")
        sqlserver_diag["action_items"].append("2. Criar variável: SQLSERVER_DATABASE = data")
    else:
        sqlserver_diag["issues"].append(f"✅ SQLSERVER_DATABASE está definida: {sqlserver_database}")
    
    # Tenta conectar
    try:
        from app.core.sqlserver import get_sqlserver_token
        token = get_sqlserver_token()
        if token:
            sqlserver_diag["managed_identity_token"] = "✅ Token obtido com sucesso"
        else:
            sqlserver_diag["managed_identity_token"] = "❌ Falha ao obter token"
            sqlserver_diag["action_items"].append("Verificar se Container App tem Managed Identity configurada")
    except Exception as e:
        sqlserver_diag["managed_identity_token"] = f"❌ Erro: {str(e)[:80]}"
        sqlserver_diag["action_items"].append(f"Erro ao obter token Managed Identity: {str(e)[:100]}")
    
    result["diagnostics"]["sqlserver"] = sqlserver_diag
    
    # 2. Diagnóstico de Blob Storage
    blob_diag = {
        "account_name": os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "NOT SET"),
        "container_name": os.getenv("AZURE_STORAGE_CONTAINER_NAME", "NOT SET"),
        "has_connection_string": bool(os.getenv("AZURE_STORAGE_CONNECTION_STRING")),
        "issues": [],
        "action_items": []
    }
    
    if not os.getenv("AZURE_STORAGE_ACCOUNT_NAME"):
        blob_diag["issues"].append("❌ AZURE_STORAGE_ACCOUNT_NAME não está definida")
        blob_diag["action_items"].append("Verificar valor em Pipeline Variables")
    else:
        blob_diag["issues"].append("✅ AZURE_STORAGE_ACCOUNT_NAME está definida")
    
    if not os.getenv("AZURE_STORAGE_CONTAINER_NAME"):
        blob_diag["issues"].append("❌ AZURE_STORAGE_CONTAINER_NAME não está definida")
        blob_diag["action_items"].append("Verificar valor em Pipeline Variables")
    else:
        blob_diag["issues"].append("✅ AZURE_STORAGE_CONTAINER_NAME está definida")
    
    # Testa acesso
    try:
        from app.providers.storage import get_storage_provider
        provider = get_storage_provider()
        if hasattr(provider, 'blob_service_client'):
            containers = list(provider.blob_service_client.list_containers())
            blob_diag["containers_accessible"] = f"✅ {len(containers)} containers encontrados"
        else:
            blob_diag["containers_accessible"] = "ℹ️ Usando Local Storage (não é Azure)"
    except Exception as e:
        blob_diag["containers_accessible"] = f"❌ Erro: {str(e)[:80]}"
        blob_diag["action_items"].append(f"Erro ao acessar containers: {str(e)[:100]}")
    
    result["diagnostics"]["blob_storage"] = blob_diag
    
    # 3. Diagnóstico de Identidade
    identity_diag = {
        "azure_tenant_id": "✅" if os.getenv("AZURE_TENANT_ID") else "❌",
        "azure_client_id": "✅" if os.getenv("AZURE_CLIENT_ID") else "❌",
        "azure_client_secret": "✅" if os.getenv("") else "❌",
        "issues": [],
        "notes": []
    }
    
    try:
        from azure.identity import DefaultAzureCredential
        cred = DefaultAzureCredential()
        token = cred.get_token("https://management.azure.com/.default")
        identity_diag["managed_identity_working"] = "✅ Managed Identity funcionando"
    except Exception as e:
        identity_diag["managed_identity_working"] = f"❌ {str(e)[:60]}"
        identity_diag["notes"].append("Managed Identity pode não estar configurada no Container App")
    
    result["diagnostics"]["identity"] = identity_diag
    
    # 4. Checklist de próximos passos
    all_issues = [
        issue for cat in result["diagnostics"].values() 
        if isinstance(cat, dict) 
        for issue in cat.get("issues", [])
    ]
    
    result["summary"] = {
        "total_issues": len([i for i in all_issues if i.startswith("❌")]),
        "total_ok": len([i for i in all_issues if i.startswith("✅")]),
        "quick_fix_steps": [
            "1️⃣ Se as variáveis não existem no Azure DevOps: criar SQLSERVER_HOST e SQLSERVER_DATABASE",
            "2️⃣ Depois de criar: clicar em 'Run pipeline' para redeploy",
            "3️⃣ Aguardar pipeline completar (5-10 min)",
            "4️⃣ Chamar /debug/diagnose novamente para verificar"
        ]
    }
    
    return result


@router.get("/sqlserver-quick")
def debug_sqlserver_quick():
    """Debug rápido - apenas mostra config sem tentar conectar"""
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "host": os.getenv("SQLSERVER_HOST", "NOT_SET"),
            "database": os.getenv("SQLSERVER_DATABASE", "NOT_SET"),
            "has_connection_string": bool(os.getenv("SQLSERVER_CONNECTION_STRING")),
            "username_raw": repr(os.getenv("SQLSERVER_USERNAME")),
            "password_set": bool(os.getenv("")),
        },
        "managed_identity_check": "will_test_next"
    }


@router.get("/sqlserver-test-connection")
def debug_sqlserver_test_connection():
    """Testa get_sqlserver_connection() exatamente como o ingest faz"""
    
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "env_vars": {
            "host": os.getenv("SQLSERVER_HOST"),
            "database": os.getenv("SQLSERVER_DATABASE"),
            "username": "***SET***" if os.getenv("SQLSERVER_USERNAME") else None,
            "password": "***SET***" if os.getenv("") else None,
            "connection_string": "***SET***" if os.getenv("SQLSERVER_CONNECTION_STRING") else None,
        },
        "connection_test": {}
    }
    
    try:
        from app.core.sqlserver import get_sqlserver_connection
        sql = get_sqlserver_connection()
        result["connection_test"]["status"] = "✅ Connected"
        
        # Test query
        try:
            query_result = sql.execute_single("SELECT 1 as test")
            result["connection_test"]["query_result"] = query_result
        except Exception as e:
            result["connection_test"]["query_error"] = str(e)
            
    except Exception as e:
        result["connection_test"]["status"] = f"❌ Failed: {str(e)}"
        result["connection_test"]["error_type"] = type(e).__name__
    
    return result


@router.get("/sqlserver-detailed")
def debug_sqlserver_detailed():
    """Debug detalhado do SQL Server - testa conectividade de rede e autenticação"""
    
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "host": os.getenv("SQLSERVER_HOST", "NOT_SET"),
        "database": os.getenv("SQLSERVER_DATABASE", "NOT_SET"),
        "username_set": bool(os.getenv("SQLSERVER_USERNAME")),
        "password_set": bool(os.getenv("")),
        "network": {},
        "token": {},
        "connection": {},
        "summary": {}
    }
    
    logger.info(f"DEBUG endpoint called: username_set={result['username_set']}, password_set={result['password_set']}")
    
    try:
        import pyodbc
        
        host = os.getenv("SQLSERVER_HOST")
        database = os.getenv("SQLSERVER_DATABASE")
        
        # 1. Teste de conectividade de rede (DNS + TCP)
        if not host:
            result["network"]["status"] = "❌ SQLSERVER_HOST não definida"
            return result
        
        try:
            # Resolve DNS
            ip = socket.gethostbyname(host)
            result["network"]["dns_resolution"] = f"✅ {host} → {ip}"
        except socket.gaierror as e:
            result["network"]["dns_resolution"] = f"❌ Falha ao resolver DNS: {str(e)}"
            result["network"]["status"] = "network_error"
            return result
        
        try:
            # Testa TCP na porta 1433 com timeout curto
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 segundos apenas
            result_code = sock.connect_ex((ip, 1433))
            sock.close()
            
            if result_code == 0:
                result["network"]["tcp_port_1433"] = "✅ Porta 1433 está aberta (acessível)"
            else:
                result["network"]["tcp_port_1433"] = f"❌ Porta 1433 fechada/bloqueada (código: {result_code})"
                result["network"]["status"] = "port_blocked"
        except Exception as e:
            result["network"]["tcp_port_1433"] = f"❌ Erro ao testar TCP: {str(e)}"
            result["network"]["status"] = "network_error"
    except Exception as e:
        result["network"]["tcp_port_1433"] = f"❌ Erro ao testar TCP: {str(e)}"
        result["network"]["status"] = "network_error"
    
    # 2. Teste de token Managed Identity
    try:
        from app.core.sqlserver import get_sqlserver_token
        token = get_sqlserver_token()
        if token:
            # Mostra tamanho e primeiros 50 chars
            result["token"]["status"] = "✅ Token obtido com sucesso"
            result["token"]["length"] = len(token)
            result["token"]["preview"] = token[:50] + "..." if len(token) > 50 else token
        else:
            result["token"]["status"] = "❌ Token é None"
    except Exception as e:
        result["token"]["status"] = f"❌ Erro ao obter token: {str(e)}"
        result["token"]["error"] = str(e)
    
    # 3. Teste de conexão pyodbc com timeout curto
    try:
        # Tenta SQL Server auth PRIMEIRO (PRIMARY)
        username = os.getenv("SQLSERVER_USERNAME")
        password = os.getenv("")
        
        if username and password:
            # SQL Server authentication
            conn_str = f"Driver={{ODBC Driver 18 for SQL Server}};Server={host};Database={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=5"
            result["connection"]["auth_method"] = "SQL Server Auth (username/password)"
            result["connection"]["conn_string"] = conn_str[:100] + "..."
            
            try:
                conn = pyodbc.connect(conn_str, timeout=5)
                result["connection"]["status"] = "✅ Conectado com SQL Server Auth!"
                
                # Testa query simples
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT @@VERSION as version")
                    version = cursor.fetchone()
                    result["connection"]["sql_version"] = version[0] if version else "unknown"
                    
                    cursor.execute("SELECT 1 as test_query")
                    result["connection"]["test_query"] = "✅ SELECT 1 executado com sucesso"
                    
                    cursor.close()
                except Exception as e:
                    result["connection"]["query_error"] = str(e)
                finally:
                    conn.close()
                    
            except pyodbc.Error as e:
                result["connection"]["status"] = f"❌ SQL Auth falhou: {str(e)}"
                result["connection"]["error"] = str(e)[:200]
        
        # FALLBACK: Tenta Managed Identity se SQL auth falhou ou não fornecido
        else:
            from app.core.sqlserver import get_sqlserver_token
            token = get_sqlserver_token()
            
            # Build connection string com timeout reduzido
            conn_str = f"Driver={{ODBC Driver 18 for SQL Server}};Server={host};Database={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=5"
            
            result["connection"]["conn_string"] = conn_str[:100] + "..."
            result["connection"]["auth_method"] = "Managed Identity (token)"
            
            if token:
                token_bytes = token.encode("utf-16-le")
                token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
                conn_attrs = {1256: token_struct}
                
                try:
                    conn = pyodbc.connect(conn_str, attrs_before=conn_attrs, timeout=5)
                    result["connection"]["status"] = "✅ Conectado com Managed Identity!"
                    
                    # Testa query simples
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT @@VERSION as version")
                        version = cursor.fetchone()
                        result["connection"]["sql_version"] = version[0] if version else "unknown"
                        
                        # Testa SELECT 1
                        cursor.execute("SELECT 1 as test_query")
                        result["connection"]["test_query"] = "✅ SELECT 1 executado com sucesso"
                        
                        cursor.close()
                    except Exception as e:
                        result["connection"]["query_error"] = str(e)
                    finally:
                        conn.close()
                        
                except pyodbc.Error as e:
                    result["connection"]["status"] = f"❌ Erro pyodbc: {str(e)}"
                    result["connection"]["error_code"] = e.args[0] if e.args else None
                    result["connection"]["error_details"] = str(e)
            else:
                result["connection"]["status"] = "❌ Token não disponível"
            
    except Exception as e:
        result["connection"]["status"] = f"❌ Erro geral: {str(e)}"
        result["connection"]["error"] = str(e)
    
    # 4. Resumo e sugestões
    issues = []
    
    if "❌" in result["network"].get("dns_resolution", ""):
        issues.append("❌ DNS não consegue resolver o host - verificar firewall/DNS")
    
    if "❌" in result["network"].get("tcp_port_1433", ""):
        issues.append("❌ Porta 1433 bloqueada - verificar SQL Server firewall rules (Azure Portal → SQL Server → Firewalls and virtual networks)")
        issues.append("   Adicionar regra: 'Allow Azure services and resources to access this server' = ON")
    
    if "❌" in result["token"].get("status", ""):
        issues.append("❌ Managed Identity não funcionando - verificar se Container App tem identidade atribuída")
    
    if "✅" in result["connection"].get("status", ""):
        issues.append("✅ SQL Server conectado com sucesso!")
    elif "❌" in result["connection"].get("status", ""):
        error = result["connection"].get("status", "")
        if "Login failed" in error or "authentication" in error.lower():
            issues.append("❌ Falha de autenticação - verificar se usuário Managed Identity existe em SQL Server")
            issues.append("   Execute em SQL Server: CREATE USER [ca-peoplechatbot-dev-latam001] FROM EXTERNAL PROVIDER;")
        elif "Connection refused" in error or "timeout" in error.lower():
            issues.append("❌ Conexão recusada - SQL Server indisponível ou bloqueado por firewall")
    
    result["summary"]["issues"] = issues
    result["summary"]["status"] = "success" if "✅ SQL Server conectado" in " ".join(issues) else "failed"
    
    return result
