"""
Testes para AgentService - Validação e guardrail de agentes
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.agent_service import AgentService


class TestAgentServiceValidation:
    """Testes para validação de agentes"""
    
    @patch('app.services.agent_service.get_sqlserver_connection')
    def test_is_agent_valid_by_id_valid(self, mock_sql_conn):
        """Teste: Validar agent_id válido (1=LUZ)"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = {"agent_id": 1}
        
        result = AgentService.is_agent_valid_by_id(1)
        
        assert result == True
    
    @patch('app.services.agent_service.get_sqlserver_connection')
    def test_is_agent_valid_by_id_invalid(self, mock_sql_conn):
        """Teste: Validar agent_id inválido"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = None
        
        result = AgentService.is_agent_valid_by_id(999)
        
        assert result == False
    
    @patch('app.services.agent_service.get_sqlserver_connection')
    def test_is_agent_valid_string_valid(self, mock_sql_conn):
        """Teste: Validar code do agente válido (LUZ)"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = {"agent_id": 1}
        
        result = AgentService.is_agent_valid("LUZ")
        
        assert result == True
    
    @patch('app.services.agent_service.get_sqlserver_connection')
    def test_is_agent_valid_string_invalid(self, mock_sql_conn):
        """Teste: Validar code do agente inválido"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = None
        
        result = AgentService.is_agent_valid("INVALID")
        
        assert result == False


class TestAgentServiceValidateOrRaise:
    """Testes para validação com exceção"""
    
    @patch('app.services.agent_service.AgentService.is_agent_valid')
    @patch('app.services.agent_service.AgentService.get_allowed_agents')
    def test_validate_agent_or_raise_valid(self, mock_get_agents, mock_is_valid):
        """Teste: Validar agente válido (sem exceção)"""
        mock_is_valid.return_value = True
        
        # Não deve lançar exceção
        AgentService.validate_agent_or_raise("LUZ")
    
    @patch('app.services.agent_service.AgentService.is_agent_valid')
    @patch('app.services.agent_service.AgentService.get_allowed_agents')
    def test_validate_agent_or_raise_invalid(self, mock_get_agents, mock_is_valid):
        """Teste: Validar agente inválido (lança exceção)"""
        mock_is_valid.return_value = False
        mock_get_agents.return_value = [
            {"code": "LUZ", "name": "Luz"},
            {"code": "IGP", "name": "IGP"},
            {"code": "SMART", "name": "Smart"}
        ]
        
        with pytest.raises(ValueError, match="não é permitido"):
            AgentService.validate_agent_or_raise("INVALID")


class TestAgentServiceGet:
    """Testes para obter dados de agentes"""
    
    @patch('app.services.agent_service.get_sqlserver_connection')
    def test_get_agent_by_id_success(self, mock_sql_conn):
        """Teste: Obter agente por ID"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = {
            "agent_id": 1,
            "code": "LUZ",
            "name": "Luz - RH",
            "description": "Gerenciador de assuntos de RH",
            "is_active": 1
        }
        
        result = AgentService.get_agent_by_id(1)
        
        assert result["agent_id"] == 1
        assert result["code"] == "LUZ"
        assert result["name"] == "Luz - RH"
    
    @patch('app.services.agent_service.get_sqlserver_connection')
    def test_get_agent_by_id_not_found(self, mock_sql_conn):
        """Teste: Agente não encontrado"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = None
        
        result = AgentService.get_agent_by_id(999)
        
        assert result is None
    
    @patch('app.services.agent_service.get_sqlserver_connection')
    def test_get_allowed_agents_success(self, mock_sql_conn):
        """Teste: Listar agentes permitidos"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute.return_value = [
            {"agent_id": 1, "code": "LUZ", "name": "Luz - RH"},
            {"agent_id": 2, "code": "IGP", "name": "IGP"},
            {"agent_id": 3, "code": "SMART", "name": "Smart"}
        ]
        
        result = AgentService.get_allowed_agents()
        
        assert len(result) == 3
        assert result[0]["code"] == "LUZ"
        assert result[1]["code"] == "IGP"
        assert result[2]["code"] == "SMART"
