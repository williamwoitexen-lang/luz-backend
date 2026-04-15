"""
Testes para PromptService - CRUD de prompts com LLM Server sync
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from app.services.prompt_service import PromptService


class TestPromptServiceCreate:
    """Testes para PromptService.create_prompt()"""
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_create_prompt_success(self, mock_sql_conn):
        """Teste: Criar prompt com sucesso"""
        # Setup mocks
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        # Mock: agente não existe (None), depois retorna o prompt criado
        mock_row = MagicMock()
        mock_row_dict = {
            'prompt_id': 1, 'agente': 'LUZ', 'system_prompt': 'You are helpful',
            'version': 1, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()
        }
        mock_row.__getitem__ = lambda self, x: mock_row_dict[x]
        mock_row.keys = lambda: mock_row_dict.keys()
        
        mock_sql.execute_single.side_effect = [None, mock_row]  # First: not exists, Second: fetch
        mock_sql.execute.return_value = None
        
        # Create service and patch LLM sync
        service = PromptService()
        with patch.object(service, '_sync_with_llm_server', return_value=True):
            result = service.create_prompt(agente="LUZ", system_prompt="You are helpful")
        
        # Assert
        assert result["agente"] == "LUZ"
        assert result["system_prompt"] == "You are helpful"
        assert result["version"] == 1
        assert mock_sql.execute.called
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_create_prompt_already_exists(self, mock_sql_conn):
        """Teste: Criar prompt que já existe falha"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = (1,)  # Agente já existe
        
        service = PromptService()
        with pytest.raises(ValueError, match="já existe"):
            service.create_prompt(agente="LUZ", system_prompt="...")
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_create_prompt_llm_sync_fails(self, mock_sql_conn):
        """Teste: LLM Server sync falha, não salva no DB"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = None  # Agente não existe
        
        service = PromptService()
        with patch.object(service, '_sync_with_llm_server', side_effect=RuntimeError("LLM failed")):
            with pytest.raises(RuntimeError):
                service.create_prompt(agente="LUZ", system_prompt="...")
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_create_prompt_db_error(self, mock_sql_conn):
        """Teste: Erro no DB ao salvar prompt"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = None  # Agente não existe
        mock_sql.execute.side_effect = Exception("DB error")
        
        service = PromptService()
        with patch.object(service, '_sync_with_llm_server', return_value=True):
            with pytest.raises(Exception):
                service.create_prompt(agente="LUZ", system_prompt="...")


class TestPromptServiceRead:
    """Testes para PromptService.get_prompt_by_agente() e list_prompts()"""
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_get_prompt_by_agente_success(self, mock_sql_conn):
        """Teste: Buscar prompt por agente com sucesso"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        mock_row = MagicMock()
        mock_row_dict = {
            'prompt_id': 1, 'agente': 'LUZ', 'system_prompt': 'You are LUZ',
            'version': 1, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()
        }
        mock_row.__getitem__ = lambda self, x: mock_row_dict[x]
        mock_row.keys = lambda: mock_row_dict.keys()
        
        mock_sql.execute_single.return_value = mock_row
        
        service = PromptService()
        result = service.get_prompt_by_agente("LUZ")
        
        assert result["agente"] == "LUZ"
        assert result["system_prompt"] == "You are LUZ"
        assert result["prompt_id"] == 1
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_get_prompt_by_agente_not_found(self, mock_sql_conn):
        """Teste: Buscar prompt que não existe retorna None"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = None
        
        service = PromptService()
        result = service.get_prompt_by_agente("NONEXISTENT")
        
        assert result is None
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_get_prompt_db_error(self, mock_sql_conn):
        """Teste: Erro no DB ao buscar prompt"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.side_effect = Exception("DB error")
        
        service = PromptService()
        with pytest.raises(Exception):
            service.get_prompt_by_agente("LUZ")
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_list_prompts_success(self, mock_sql_conn):
        """Teste: Listar todos os prompts"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        mock_row1 = MagicMock()
        mock_row1_dict = {
            'prompt_id': 1, 'agente': 'IGP', 'system_prompt': 'You are IGP',
            'version': 1, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()
        }
        mock_row1.__getitem__ = lambda self, x: mock_row1_dict[x]
        mock_row1.keys = lambda: mock_row1_dict.keys()
        
        mock_row2 = MagicMock()
        mock_row2_dict = {
            'prompt_id': 2, 'agente': 'LUZ', 'system_prompt': 'You are LUZ',
            'version': 1, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()
        }
        mock_row2.__getitem__ = lambda self, x: mock_row2_dict[x]
        mock_row2.keys = lambda: mock_row2_dict.keys()
        
        mock_sql.execute.return_value = [mock_row1, mock_row2]
        
        service = PromptService()
        results = service.list_prompts()
        
        assert len(results) == 2
        assert results[0]["agente"] == "IGP"
        assert results[1]["agente"] == "LUZ"
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_list_prompts_empty(self, mock_sql_conn):
        """Teste: Listar prompts quando lista está vazia"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute.return_value = []
        
        service = PromptService()
        results = service.list_prompts()
        
        assert results == []
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_list_prompts_db_error(self, mock_sql_conn):
        """Teste: Erro no DB ao listar prompts"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute.side_effect = Exception("DB error")
        
        service = PromptService()
        with pytest.raises(Exception):
            service.list_prompts()


class TestPromptServiceUpdate:
    """Testes para PromptService.update_prompt()"""
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_update_prompt_success(self, mock_sql_conn):
        """Teste: Atualizar prompt com sucesso"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        mock_row = MagicMock()
        mock_row_dict = {
            'prompt_id': 1, 'agente': 'LUZ', 'system_prompt': 'Updated prompt',
            'version': 2, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()
        }
        mock_row.__getitem__ = lambda self, x: mock_row_dict[x]
        mock_row.keys = lambda: mock_row_dict.keys()
        
        mock_sql.execute_single.return_value = mock_row
        mock_sql.execute.return_value = None
        
        service = PromptService()
        with patch.object(service, '_sync_with_llm_server', return_value=True):
            result = service.update_prompt(agente="LUZ", system_prompt="Updated prompt")
        
        assert result["system_prompt"] == "Updated prompt"
        assert result["agente"] == "LUZ"
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_update_prompt_llm_sync_fails(self, mock_sql_conn):
        """Teste: LLM sync falha, não atualiza DB"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        service = PromptService()
        with patch.object(service, '_sync_with_llm_server', side_effect=RuntimeError("LLM failed")):
            with pytest.raises(RuntimeError):
                service.update_prompt(agente="LUZ", system_prompt="New prompt")
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_update_prompt_not_found(self, mock_sql_conn):
        """Teste: Atualizar prompt que não existe falha"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = None  # Prompt não existe
        
        service = PromptService()
        with patch.object(service, '_sync_with_llm_server', return_value=True):
            with pytest.raises(ValueError, match="não encontrado"):
                service.update_prompt(agente="NONEXISTENT", system_prompt="...")


class TestPromptServiceDelete:
    """Testes para PromptService.delete_prompt()"""
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_delete_prompt_success(self, mock_sql_conn):
        """Teste: Deletar prompt com sucesso"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = (1,)  # Prompt existe
        mock_sql.execute.return_value = None
        
        service = PromptService()
        service.delete_prompt("LUZ")
        
        assert mock_sql.execute.called
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_delete_prompt_not_found(self, mock_sql_conn):
        """Teste: Deletar prompt que não existe falha"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = None  # Prompt não existe
        
        service = PromptService()
        with pytest.raises(ValueError, match="não encontrado"):
            service.delete_prompt("NONEXISTENT")
    
    @patch('app.services.prompt_service.get_sqlserver_connection')
    def test_delete_prompt_db_error(self, mock_sql_conn):
        """Teste: Erro no DB ao deletar prompt"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = (1,)  # Existe
        mock_sql.execute.side_effect = Exception("DB error")
        
        service = PromptService()
        with pytest.raises(Exception):
            service.delete_prompt("LUZ")
