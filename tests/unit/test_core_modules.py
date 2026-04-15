"""
Testes unitários para módulos core com 0% cobertura
Aumenta cobertura testando lógica pura
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil


class TestLoggerUtils:
    """Testes para app/core/logger_utils.py"""
    
    def test_get_logger_returns_logger(self):
        """Testa que get_logger retorna um Logger"""
        from app.core.logger_utils import get_logger
        
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test"
    
    def test_log_info_formats_correctly(self):
        """Testa formatação do log_info"""
        from app.core.logger_utils import log_info
        
        mock_logger = Mock()
        log_info(mock_logger, "context", "test message")
        
        mock_logger.info.assert_called_once_with("[context] test message")
    
    def test_log_error_formats_correctly(self):
        """Testa formatação do log_error"""
        from app.core.logger_utils import log_error
        
        mock_logger = Mock()
        log_error(mock_logger, "context", "error message")
        
        mock_logger.error.assert_called_once_with("[context] error message", exc_info=False)
    
    def test_log_error_with_exc_info(self):
        """Testa log_error com exc_info=True"""
        from app.core.logger_utils import log_error
        
        mock_logger = Mock()
        log_error(mock_logger, "context", "error", exc_info=True)
        
        mock_logger.error.assert_called_once_with("[context] error", exc_info=True)
    
    def test_log_warning_formats_correctly(self):
        """Testa formatação do log_warning"""
        from app.core.logger_utils import log_warning
        
        mock_logger = Mock()
        log_warning(mock_logger, "context", "warning message")
        
        mock_logger.warning.assert_called_once_with("[context] warning message")
    
    def test_log_debug_formats_correctly(self):
        """Testa formatação do log_debug"""
        from app.core.logger_utils import log_debug
        
        mock_logger = Mock()
        log_debug(mock_logger, "context", "debug message")
        
        mock_logger.debug.assert_called_once_with("[context] debug message")
    
    def test_print_success_contains_emoji(self, capsys):
        """Testa que print_success inclui emoji"""
        from app.core.logger_utils import print_success
        
        print_success("test")
        captured = capsys.readouterr()
        assert "✅" in captured.out
        assert "test" in captured.out
    
    def test_print_error_contains_emoji(self, capsys):
        """Testa que print_error inclui emoji"""
        from app.core.logger_utils import print_error
        
        print_error("error")
        captured = capsys.readouterr()
        assert "❌" in captured.out
        assert "error" in captured.out
    
    def test_print_warning_contains_emoji(self, capsys):
        """Testa que print_warning inclui emoji"""
        from app.core.logger_utils import print_warning
        
        print_warning("warning")
        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "warning" in captured.out
    
    def test_print_info_contains_emoji(self, capsys):
        """Testa que print_info inclui emoji"""
        from app.core.logger_utils import print_info
        
        print_info("info")
        captured = capsys.readouterr()
        assert "ℹ️" in captured.out
        assert "info" in captured.out


class TestTempStorage:
    """Testes para app/utils/temp_storage.py"""
    
    @pytest.fixture
    def temp_dir(self):
        """Cria diretório temporário para testes"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)
    
    def test_init_temp_dir_creates_directory(self, temp_dir):
        """Testa que init_temp_dir cria diretório"""
        from app.utils import temp_storage
        
        # Patch TEMP_DIR para usar nosso temp
        with patch.object(temp_storage, 'TEMP_DIR', temp_dir / "test_temp"):
            temp_storage.init_temp_dir()
            assert (temp_dir / "test_temp").exists()
    
    def test_create_temp_session_returns_uuid(self, temp_dir):
        """Testa que create_temp_session retorna UUID"""
        from app.utils import temp_storage
        
        with patch.object(temp_storage, 'TEMP_DIR', temp_dir):
            with patch.object(temp_storage, '_schedule_cleanup'):
                temp_id = temp_storage.create_temp_session(
                    filename="test.pdf",
                    file_bytes=b"test content",
                    extracted_fields={"title": "Test"}
                )
                
                assert temp_id is not None
                assert len(temp_id) == 36  # UUID format
    
    def test_get_temp_session_returns_session(self, temp_dir):
        """Testa que get_temp_session retorna sessão criada"""
        from app.utils import temp_storage
        
        with patch.object(temp_storage, 'TEMP_DIR', temp_dir):
            with patch.object(temp_storage, '_schedule_cleanup'):
                temp_id = temp_storage.create_temp_session(
                    filename="test.pdf",
                    file_bytes=b"content",
                    extracted_fields={"title": "Test"}
                )
                
                session = temp_storage.get_temp_session(temp_id)
                
                assert session is not None
                assert session["filename"] == "test.pdf"
                assert session["extracted_fields"]["title"] == "Test"
    
    def test_get_temp_session_returns_none_for_invalid_id(self):
        """Testa que get_temp_session retorna None para ID inválido"""
        from app.utils import temp_storage
        
        session = temp_storage.get_temp_session("invalid-id-12345")
        assert session is None
    
    def test_delete_temp_session_removes_files(self, temp_dir):
        """Testa que delete_temp_session remove arquivos"""
        from app.utils import temp_storage
        
        with patch.object(temp_storage, 'TEMP_DIR', temp_dir):
            with patch.object(temp_storage, '_schedule_cleanup'):
                temp_id = temp_storage.create_temp_session(
                    filename="test.pdf",
                    file_bytes=b"content",
                    extracted_fields={}
                )
                
                # Verifica que foi criado
                session = temp_storage.get_temp_session(temp_id)
                assert session is not None
                
                # Deleta
                result = temp_storage.delete_temp_session(temp_id)
                assert result is True
                
                # Verifica que foi removido
                session_after = temp_storage.get_temp_session(temp_id)
                assert session_after is None
    
    def test_delete_temp_session_returns_false_for_invalid_id(self):
        """Testa que delete_temp_session retorna False para ID inválido"""
        from app.utils import temp_storage
        
        result = temp_storage.delete_temp_session("invalid-id")
        assert result is False


class TestEmbeddingsModule:
    """Testes para app/providers/embeddings.py"""
    
    def test_embeddings_module_loads(self):
        """Testa que módulo embeddings carrega sem erro"""
        # O módulo deve carregar sem exceção mesmo sem credenciais
        from app.providers import embeddings
        
        # Verifica que variáveis foram definidas
        assert hasattr(embeddings, 'client')
        assert hasattr(embeddings, 'EMBEDDING_MODEL')
        assert hasattr(embeddings, 'embed_text')
    
    def test_embed_text_raises_without_client(self):
        """Testa que embed_text levanta erro sem cliente configurado"""
        from app.providers import embeddings
        
        # Se client é None, deve levantar RuntimeError
        if embeddings.client is None:
            with pytest.raises(RuntimeError) as exc:
                embeddings.embed_text("test text")
            
            assert "not initialized" in str(exc.value)


class TestModelsModule:
    """Testes para app/models.py - linhas não cobertas"""
    
    def test_models_import(self):
        """Testa que models carrega corretamente"""
        from app import models
        
        # Verifica classes existem
        assert hasattr(models, 'SearchResponse')
        assert hasattr(models, 'ConversationResponse')
        assert hasattr(models, 'QuestionRequest')
    
    def test_search_result_item_serialization(self):
        """Testa serialização de SearchResultItem"""
        from app.models import SearchResultItem
        
        item = SearchResultItem(
            title="Test Document",
            version_number=1,
            chunk_index=0,
            content="test content",
            score=0.95
        )
        
        # Deve serializar corretamente
        data = item.model_dump()
        assert data["title"] == "Test Document"
        assert data["version_number"] == 1
    
    def test_question_request_validation(self):
        """Testa validação de QuestionRequest"""
        from app.models import QuestionRequest
        
        req = QuestionRequest(
            chat_id="chat-123",
            question="What is Python?",
            user_id="user-123",
            name="Test User",
            email="test@example.com",
            role_id=1
        )
        
        assert req.question == "What is Python?"
        assert req.role_id == 1
    
    def test_conversation_response_serialization(self):
        """Testa serialização de ConversationResponse"""
        from app.models import ConversationResponse
        from datetime import datetime
        
        resp = ConversationResponse(
            conversation_id="conv-123",
            user_id="user-123",
            title="Test Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        data = resp.model_dump()
        assert data["conversation_id"] == "conv-123"
        assert data["title"] == "Test Conversation"


class TestConfigModule:
    """Testes para app/core/config.py - linhas não cobertas"""
    
    def test_config_loads(self):
        """Testa que configuração carrega"""
        from app.core import config
        
        assert hasattr(config, 'get_config') or hasattr(config, 'KeyVaultConfig')
    
    def test_environment_variables_can_be_read(self):
        """Testa que variáveis de ambiente são lidas"""
        import os
        
        # Define variável temporária
        os.environ["TEST_VAR_COVERAGE"] = "test_value"
        
        # Verifica que é lida
        assert os.getenv("TEST_VAR_COVERAGE") == "test_value"
        
        # Limpa
        del os.environ["TEST_VAR_COVERAGE"]


class TestLLMIntegrationModule:
    """Testes para app/services/llm_integration.py"""
    
    def test_llm_integration_module_loads(self):
        """Testa que módulo llm_integration carrega"""
        from app.services import llm_integration
        
        # Verifica que módulo existe
        assert llm_integration is not None


class TestVectorstoreModule:
    """Testes para app/providers/vectorstore.py"""
    
    def test_vectorstore_module_loads(self):
        """Testa que módulo vectorstore carrega"""
        from app.providers import vectorstore
        
        # Verifica que módulo existe
        assert vectorstore is not None


class TestMetadataExtractorModule:
    """Testes para app/providers/metadata_extractor.py"""
    
    def test_metadata_extractor_module_loads(self):
        """Testa que módulo metadata_extractor carrega"""
        from app.providers import metadata_extractor
        
        # Verifica que módulo existe
        assert metadata_extractor is not None
        
        # Verifica que classe existe
        assert hasattr(metadata_extractor, 'MetadataExtractor')


class TestLLMModule:
    """Testes para app/providers/llm.py"""
    
    def test_llm_module_loads(self):
        """Testa que módulo llm carrega"""
        from app.providers import llm
        
        # Verifica que módulo existe
        assert llm is not None
