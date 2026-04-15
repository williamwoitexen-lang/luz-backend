"""
Configuração global de testes (pytest conftest)

Este arquivo é automaticamente carregado pelo pytest e fornece:
- Fixtures compartilhadas entre todos os testes
- Configuração de ambiente de teste
- Mocks globais
- Configuração de banco de dados de teste
"""

import pytest
import sys
import os
from pathlib import Path

# Add app to path para permitir imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))


@pytest.fixture(scope="session")
def test_env():
    """Setup ambiente de teste"""
    os.environ["ENV"] = "test"
    os.environ["SKIP_LLM_SERVER"] = "true"  # Não chamar LLM em testes
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"  # Use in-memory DB
    return os.environ


@pytest.fixture(scope="function")
def mock_storage(monkeypatch):
    """Mock de storage provider para testes"""
    
    class MockStorage:
        def __init__(self):
            self.files = {}
        
        def save_file(self, doc_id, version, filename, content):
            key = f"{doc_id}/v{version}/{filename}"
            self.files[key] = content
            return f"mock://storage/{key}"
        
        def get_file(self, path):
            return self.files.get(path, b"")
        
        def delete_file(self, path):
            if path in self.files:
                del self.files[path]
    
    return MockStorage()


@pytest.fixture(scope="function")
def mock_llm_client(monkeypatch):
    """Mock de LLM Server client para testes"""
    
    class MockLLMClient:
        def extract_metadata(self, text, filename):
            return {
                "title": filename,
                "description": "Mocked description",
                "language": "pt",
                "category": "general"
            }
        
        def ask_question(self, question, chat_id="test", user_id="test"):
            return {
                "answer": f"Mock response to: {question}",
                "agente": "Mock Agent",
                "total_time_ms": 100,
                "documents_returned": 0
            }
        
        def ingest_document(self, **kwargs):
            return {
                "status": "success",
                "chunks": 1,
                "message": "Document ingested"
            }
    
    return MockLLMClient()


@pytest.fixture(scope="function")
def sample_pdf_text():
    """Amostra de texto extraído de PDF com binários"""
    return """
CLÁUSULA DÉCIMA SEGUNDA
\x00\x01\x02Benefícios de Saúde\x03\x04
Compensações - Ação Judicial
\x80\x81\x82São Carlos\x83\x84
PARÁGRAFO § 1º - Artigo 30°
    """.strip()


@pytest.fixture(scope="function")
def sample_document_metadata():
    """Metadados de documento de exemplo"""
    return {
        "document_id": "test-doc-123",
        "user_id": "test-user-456",
        "title": "Test Document",
        "category_id": 1,
        "min_role_level": 0,
        "is_active": True,
        "version": 1
    }


@pytest.fixture(scope="function", autouse=True)
def mock_database_factory(monkeypatch):
    """
    Fixture GLOBAL para mockar get_sqlserver_connection().
    Isso permite testar serviços @staticmethod sem refatoração!
    
    Qualquer teste que use serviços estáticos que chamem get_sqlserver_connection()
    automaticamente vai receber um mock. Sem precisar refatorar nada.
    """
    from unittest.mock import MagicMock
    
    class MockSQLConnection:
        """Mock simples para testes"""
        def __init__(self):
            self.execute_calls = []
            self.execute_single_calls = []
        
        def execute(self, query, params=None):
            self.execute_calls.append({"query": query, "params": params})
            
            # INSERT
            if "INSERT" in query:
                return None
            
            # UPDATE / DELETE
            elif "UPDATE" in query or "DELETE" in query:
                return None
            
            # COUNT
            elif "SELECT COUNT" in query:
                return [{"count": 0}]
            
            # SELECT for categories
            elif "SELECT" in query and "category" in query.lower():
                return [{
                    "category_id": 1,
                    "category_name": "Test",
                    "description": "Test Desc",
                    "is_active": True
                }]
            
            # SELECT for roles
            elif "SELECT" in query and "role" in query.lower():
                return [{
                    "role_id": 1,
                    "role_name": "Test",
                    "is_active": True
                }]
            
            # SELECT for locations
            elif "SELECT" in query and ("location" in query.lower() or "city" in query.lower() or "country" in query.lower()):
                return [{
                    "location_id": 1,
                    "country_name": "Brazil",
                    "state_name": "São Paulo",
                    "city_name": "São Paulo",
                    "region": "South America",
                    "continent": "South America",
                    "operation_type": "HQ",
                    "is_active": True
                }]
            
            # Generic SELECT
            elif "SELECT" in query:
                return []
            
            return None
        
        def execute_single(self, query, params=None):
            self.execute_single_calls.append({"query": query, "params": params})
            return {"id": 1}
        
        def commit(self):
            pass
        
        def rollback(self):
            pass
        
        def close(self):
            pass
    
    mock_conn = MockSQLConnection()
    
    # Mockar get_sqlserver_connection() em todos os módulos
    def mock_get_sqlserver_connection():
        return mock_conn
    
    # Mockar em app.core.sqlserver
    monkeypatch.setattr(
        "app.core.sqlserver.get_sqlserver_connection",
        mock_get_sqlserver_connection
    )
    
    # Mockar em todos os serviços que importam
    monkeypatch.setattr(
        "app.services.category_service.get_sqlserver_connection",
        mock_get_sqlserver_connection
    )
    monkeypatch.setattr(
        "app.services.role_service.get_sqlserver_connection",
        mock_get_sqlserver_connection
    )
    monkeypatch.setattr(
        "app.services.location_service.get_sqlserver_connection",
        mock_get_sqlserver_connection
    )
    monkeypatch.setattr(
        "app.services.job_title_role_service.get_sqlserver_connection",
        mock_get_sqlserver_connection
    )
    monkeypatch.setattr(
        "app.services.conversation_service.get_sqlserver_connection",
        mock_get_sqlserver_connection
    )
    
    return mock_conn


@pytest.fixture(scope="function", autouse=True)
def mock_llm_factory(monkeypatch):
    """
    Fixture GLOBAL para mockar get_llm_client().
    Mesma ideia que mock_database_factory - permite testar serviços
    @staticmethod sem refatoração!
    """
    from unittest.mock import MagicMock, AsyncMock
    
    class MockLLMServerClient:
        """Mock para LLMServerClient"""
        def extract_metadata(self, text, filename=None):
            return {
                "title": filename or "Test Doc",
                "summary": "Mock summary",
                "language": "pt",
                "entities": [],
                "keywords": []
            }
        
        async def ask_question(self, question, **kwargs):
            return {
                "answer": f"Mock: {question}",
                "total_time_ms": 100,
                "documents_returned": 0
            }
        
        async def ingest_document(self, **kwargs):
            return {"status": "success", "chunks": 1}
    
    mock_llm = MockLLMServerClient()
    
    def mock_get_llm_client():
        return mock_llm
    
    # Mockar em todos os módulos que usam
    monkeypatch.setattr(
        "app.providers.llm_server.get_llm_client",
        mock_get_llm_client
    )
    
    return mock_llm


# Markers para categorizar testes
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "unit: marca um teste como unitário (rápido, sem dependências)"
    )
    config.addinivalue_line(
        "markers", "integration: marca um teste como integração (pode ser lento)"
    )
    config.addinivalue_line(
        "markers", "slow: marca um teste como lento"
    )
    config.addinivalue_line(
        "markers", "requires_db: marca um teste que precisa de banco de dados"
    )


# Hook para adicionar marcador padrão baseado no path
def pytest_collection_modifyitems(config, items):
    for item in items:
        # Adicionar marker baseado no caminho
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# =============================================================================
# TESTCLIENT FIXTURE - Base para todos os testes HTTP
# =============================================================================

@pytest.fixture(scope="function")
def client():
    """TestClient para testar endpoints FastAPI"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


# =============================================================================
# AUTHENTICATION MOCKS - Para aumentar cobertura de endpoints autenticados
# =============================================================================

@pytest.fixture(scope="function", autouse=False)
def mock_auth_user(monkeypatch):
    """Mock de usuário autenticado para testes"""
    
    class MockUser:
        def __init__(self, user_id="test_user_123", email="test@example.com", 
                     roles=None, is_admin=False):
            self.user_id = user_id
            self.email = email
            self.roles = roles or ["user"]
            self.is_admin = is_admin
            self.name = "Test User"
            self.oid = "oid_" + user_id
        
        def __dict__(self):
            return {
                "user_id": self.user_id,
                "email": self.email,
                "roles": self.roles,
                "is_admin": self.is_admin
            }
    
    mock_user = MockUser()
    
    # Mock da função get_current_user
    async def mock_get_current_user(request=None, token: str = None):
        return mock_user
    
    # Patch em dependencies
    monkeypatch.setattr(
        "app.providers.dependencies.get_current_user",
        mock_get_current_user
    )
    
    return mock_user


@pytest.fixture(scope="function", autouse=False)
def mock_auth_admin(monkeypatch):
    """Mock de usuário admin autenticado"""
    
    class MockAdminUser:
        def __init__(self, user_id="admin_user_123", email="admin@example.com"):
            self.user_id = user_id
            self.email = email
            self.roles = ["admin", "user"]
            self.is_admin = True
            self.name = "Admin User"
            self.oid = "oid_" + user_id
    
    mock_admin = MockAdminUser()
    
    async def mock_get_current_user(request=None, token: str = None):
        return mock_admin
    
    monkeypatch.setattr(
        "app.providers.dependencies.get_current_user",
        mock_get_current_user
    )
    
    return mock_admin


@pytest.fixture(scope="function", autouse=False)
def mock_jwt_validation(monkeypatch):
    """Mock de validação JWT"""
    
    def mock_verify_jwt_token(token: str):
        """Mock verifica qualquer token como válido"""
        if not token:
            raise ValueError("Token inválido")
        return {
            "user_id": "test_user",
            "email": "test@example.com",
            "exp": 9999999999
        }
    
    monkeypatch.setattr(
        "app.providers.auth_msal.verify_jwt_token",
        mock_verify_jwt_token
    )
    
    return mock_verify_jwt_token


@pytest.fixture(scope="function", autouse=False)
def authenticated_client(client, mock_auth_user):
    """TestClient com usuário autenticado"""
    # Adiciona header de autenticação
    client.headers = {
        **client.headers,
        "Authorization": "Bearer test_token_12345"
    }
    return client


@pytest.fixture(scope="function", autouse=False)
def admin_client(client, mock_auth_admin):
    """TestClient com usuário admin"""
    client.headers = {
        **client.headers,
        "Authorization": "Bearer admin_token_12345"
    }
    return client
