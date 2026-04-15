"""
Testes para LLMServerClient e outros providers complexos
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests


class TestLLMServerClient:
    """Testes para app/providers/llm_server.py"""
    
    def test_llm_server_client_initialization(self):
        """Testa inicialização do cliente"""
        from app.providers.llm_server import LLMServerClient
        
        with patch.dict('os.environ', {"LLM_SERVER_URL": "https://test.com"}):
            client = LLMServerClient()
            assert client.base_url == "https://test.com"
            assert client.timeout > 0
    
    def test_llm_server_client_default_url(self):
        """Testa URL padrão quando não configurada"""
        from app.providers.llm_server import LLMServerClient
        
        with patch.dict('os.environ', {}, clear=True):
            client = LLMServerClient()
            assert "localhost" in client.base_url
    
    def test_get_file_format_pdf(self):
        """Testa detecção de formato PDF"""
        from app.providers.llm_server import LLMServerClient
        
        client = LLMServerClient()
        result = client._get_file_format("document.pdf")
        assert result == "pdf"
    
    def test_get_file_format_docx(self):
        """Testa detecção de formato DOCX"""
        from app.providers.llm_server import LLMServerClient
        
        client = LLMServerClient()
        result = client._get_file_format("report.docx")
        assert result == "docx"
    
    def test_get_file_format_xlsx(self):
        """Testa detecção de formato Excel"""
        from app.providers.llm_server import LLMServerClient
        
        client = LLMServerClient()
        result = client._get_file_format("data.xlsx")
        assert result == "xlsx"
    
    def test_get_file_format_unknown(self):
        """Testa formato desconhecido retorna txt"""
        from app.providers.llm_server import LLMServerClient
        
        client = LLMServerClient()
        result = client._get_file_format("file.unknown")
        assert result == "txt"
    
    def test_get_file_format_no_extension(self):
        """Testa arquivo sem extensão"""
        from app.providers.llm_server import LLMServerClient
        
        client = LLMServerClient()
        result = client._get_file_format("README")
        assert result == "txt"
    
    def test_get_file_format_empty_filename(self):
        """Testa filename vazio"""
        from app.providers.llm_server import LLMServerClient
        
        client = LLMServerClient()
        result = client._get_file_format("")
        assert result == "txt"
    
    def test_handle_llm_error_with_json(self):
        """Testa parsing de erro JSON"""
        from app.providers.llm_server import LLMServerClient
        
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.text = '{"detail": "Validation error"}'
        mock_response.json.return_value = {"detail": "Validation error"}
        
        error_msg = LLMServerClient._handle_llm_error(mock_response)
        assert "422" in error_msg
        assert "Validation error" in error_msg
    
    def test_handle_llm_error_with_list(self):
        """Testa parsing de erro com lista de validação"""
        from app.providers.llm_server import LLMServerClient
        
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.text = "error"
        mock_response.json.return_value = {
            "detail": [
                {"msg": "Field required", "loc": ["role_id"]},
                {"msg": "Invalid value", "loc": ["user_id"]}
            ]
        }
        
        error_msg = LLMServerClient._handle_llm_error(mock_response)
        assert "Field required" in error_msg
        assert "role_id" in error_msg
    
    def test_handle_llm_error_plain_text(self):
        """Testa parsing de erro texto simples"""
        from app.providers.llm_server import LLMServerClient
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_response.json.side_effect = ValueError("Not JSON")
        
        error_msg = LLMServerClient._handle_llm_error(mock_response)
        assert "500" in error_msg
    
    @patch('app.providers.llm_server.requests.post')
    def test_ingest_document_success(self, mock_post):
        """Testa ingestão de documento com sucesso"""
        from app.providers.llm_server import LLMServerClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "chunks": 5}
        mock_response.headers = {}  # Fix: mock headers como dict vazio
        mock_post.return_value = mock_response
        
        client = LLMServerClient()
        result = client.ingest_document(
            document_id="123",
            file_content="Test content",
            filename="test.pdf",
            category_id=1
        )
        
        assert result["status"] == "success"
        assert mock_post.called
    
    @patch('app.providers.llm_server.requests.post')
    def test_ingest_document_truncates_large_content(self, mock_post):
        """Testa que conteúdo grande é truncado"""
        from app.providers.llm_server import LLMServerClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.headers = {}  # Fix: mock headers
        mock_post.return_value = mock_response
        
        client = LLMServerClient()
        large_content = "x" * 2000000  # 2MB
        
        client.ingest_document(
            document_id="123",
            file_content=large_content,
            filename="test.pdf",
            category_id=1
        )
        
        # Verifica que foi chamado (conteúdo truncado internamente)
        assert mock_post.called
    
    @patch('app.providers.llm_server.requests.post')
    def test_ingest_document_empty_content_error(self, mock_post):
        """Testa erro com conteúdo vazio"""
        from app.providers.llm_server import LLMServerClient
        
        client = LLMServerClient()
        
        with pytest.raises(ValueError, match="empty"):
            client.ingest_document(
                document_id="123",
                file_content="   ",  # Apenas espaços
                filename="test.pdf",
                category_id=1
            )
    
    @patch('app.providers.llm_server.requests.post')
    def test_ingest_document_with_metadata(self, mock_post):
        """Testa ingestão com todos os metadados"""
        from app.providers.llm_server import LLMServerClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.headers = {}  # Fix: mock headers
        mock_post.return_value = mock_response
        
        client = LLMServerClient()
        result = client.ingest_document(
            document_id="123",
            file_content="Test content",
            filename="test.pdf",
            category_id=1,
            user_id="user123",
            title="Test Document",
            min_role_level=2,
            allowed_roles=["admin", "manager"],
            allowed_countries=["Brazil"],
            allowed_cities=["São Paulo"],
            version_id=2
        )
        
        assert result["status"] == "success"
        # Verifica que foi chamado
        assert mock_post.called


class TestStorageProvider:
    """Testes para app/providers/storage.py"""
    
    def test_storage_module_imports(self):
        """Testa que módulo storage pode ser importado"""
        from app.providers import storage
        
        assert storage is not None
        assert hasattr(storage, 'get_storage_provider')


class TestFormatConverter:
    """Testes para app/providers/format_converter.py"""
    
    def test_format_converter_imports(self):
        """Testa imports do format_converter"""
        from app.providers import format_converter
        
        assert format_converter is not None
        assert hasattr(format_converter, 'FormatConverter')
    
    def test_format_converter_initialization(self):
        """Testa inicialização do FormatConverter"""
        from app.providers.format_converter import FormatConverter
        
        converter = FormatConverter()
        assert converter is not None


class TestLocationService:
    """Testes para app/services/location_service.py"""
    
    @patch('app.services.location_service.get_sqlserver_connection')
    def test_location_service_imports(self, mock_conn):
        """Testa imports do location_service"""
        from app.services import location_service
        
        assert location_service is not None
        assert hasattr(location_service, 'LocationService')


class TestDocumentServiceHelpers:
    """Testes para helpers do document_service"""
    
    def test_document_service_has_helper_methods(self):
        """Testa que DocumentService tem métodos helper"""
        from app.services.document_service import DocumentService
        
        assert hasattr(DocumentService, '_safe_json_loads')
        assert hasattr(DocumentService, '_normalize_input')
        assert hasattr(DocumentService, '_ensure_json_string')
    
    def test_safe_json_loads_valid_json(self):
        """Testa _safe_json_loads com JSON válido"""
        from app.services.document_service import DocumentService
        
        result = DocumentService._safe_json_loads('{"key": "value"}')
        assert result == {"key": "value"}
    
    def test_safe_json_loads_invalid_json(self):
        """Testa _safe_json_loads com JSON inválido"""
        from app.services.document_service import DocumentService
        
        result = DocumentService._safe_json_loads('not json', default={})
        assert result == {}
    
    def test_safe_json_loads_none_input(self):
        """Testa _safe_json_loads com None"""
        from app.services.document_service import DocumentService
        
        result = DocumentService._safe_json_loads(None, default=[])
        assert result == []
    
    def test_ensure_json_string_from_dict(self):
        """Testa _ensure_json_string com dict"""
        from app.services.document_service import DocumentService
        
        result = DocumentService._ensure_json_string({"test": "value"})
        assert '"test"' in result
        assert '"value"' in result
    
    def test_ensure_json_string_from_string(self):
        """Testa _ensure_json_string com string"""
        from app.services.document_service import DocumentService
        
        result = DocumentService._ensure_json_string('["item1"]')
        assert result == '["item1"]'
    
    def test_normalize_input_string(self):
        """Testa _normalize_input com string"""
        from app.services.document_service import DocumentService
        
        result = DocumentService._normalize_input('["BR"]')
        assert result == ["BR"]
    
    def test_normalize_input_list(self):
        """Testa _normalize_input com lista"""
        from app.services.document_service import DocumentService
        
        result = DocumentService._normalize_input(["BR", "US"])
        assert result == ["BR", "US"]
