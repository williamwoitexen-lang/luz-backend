"""
Testes para AdminService - CRUD de admins com agent_id FK
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from app.services.admin_service import AdminService
from app.services.agent_service import AgentService


class TestAdminServiceCreate:
    """Testes para AdminService.create_admin()"""
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    @patch('app.services.admin_service.AgentService.is_agent_valid_by_id')
    @patch('app.services.admin_service.AgentService.get_agent_by_id')
    @patch('app.services.admin_service.AdminService.list_features')
    @patch('app.services.admin_service.AdminService.get_admin_by_email_and_agent')
    def test_create_admin_success(self, mock_get_existing, mock_list_features, mock_get_agent, mock_is_valid, mock_sql_conn):
        """Teste: Criar admin com sucesso"""
        # Setup
        mock_is_valid.return_value = True
        mock_get_agent.return_value = {"name": "LUZ", "agent_id": 1, "code": "LUZ"}
        mock_get_existing.return_value = None  # Admin não existe ainda
        mock_list_features.return_value = [
            {"feature_id": 1, "agente": "LUZ"},
            {"feature_id": 2, "agente": "LUZ"}
        ]
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        # Execute
        result = AdminService.create_admin(
            email="test@example.com",
            agent_id=1,
            feature_ids=[1, 2]
        )
        
        # Assert
        assert result["email"] == "test@example.com"
        assert result["agent_id"] == 1
        assert result["agent_name"] == "LUZ"
        assert result["is_active"] == True
        assert mock_sql.execute.called
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    @patch('app.services.admin_service.AgentService.is_agent_valid_by_id')
    def test_create_admin_invalid_agent_id(self, mock_is_valid, mock_sql_conn):
        """Teste: Criar admin com agent_id inválido"""
        mock_is_valid.return_value = False
        
        with pytest.raises(ValueError, match="Agent ID inválido"):
            AdminService.create_admin(email="test@example.com", agent_id=999)
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    @patch('app.services.admin_service.AgentService.is_agent_valid_by_id')
    @patch('app.services.admin_service.AgentService.get_agent_by_id')
    @patch('app.services.admin_service.AdminService.list_features')
    @patch('app.services.admin_service.AdminService.get_admin_by_email_and_agent')
    def test_create_admin_with_no_features(self, mock_get_existing, mock_list_features, mock_get_agent, mock_is_valid, mock_sql_conn):
        """Teste: Criar admin sem features - deve auto-atribuir todas do agente"""
        mock_is_valid.return_value = True
        mock_get_agent.return_value = {"name": "IGP", "agent_id": 2}
        mock_get_existing.return_value = None  # Admin não existe ainda
        mock_list_features.return_value = [
            {"feature_id": 3, "agente": "IGP"},
            {"feature_id": 4, "agente": "IGP"}
        ]
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        result = AdminService.create_admin(
            email="test2@example.com",
            agent_id=2
        )
        
        assert result["agent_name"] == "IGP"
        assert result["feature_ids"] == [3, 4]


class TestAdminServiceGet:
    """Testes para AdminService GET methods"""
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    def test_parse_admin_row_with_agent(self, mock_sql_conn):
        """Teste: Parse admin row com agent_id válido"""
        row = {
            "admin_id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "test@example.com",
            "agent_id": 1,
            "name": "Lucas Lorensi",
            "job_title": "Engineer",
            "city": "SP",
            "agent_name": "LUZ",
            "is_active": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = AdminService._parse_admin_row(row)
        
        assert result["admin_id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert result["email"] == "test@example.com"
        assert result["agent_id"] == 1
        assert result["agent_name"] == "LUZ"
        assert result["is_active"] == True
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    def test_parse_admin_row_without_agent(self, mock_sql_conn):
        """Teste: Parse admin row com agent_id NULL (LEFT JOIN retornou NULL)"""
        row = {
            "admin_id": "223e4567-e89b-12d3-a456-426614174000",
            "email": "test2@example.com",
            "agent_id": None,
            "name": None,
            "is_active": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = AdminService._parse_admin_row(row)
        
        assert result["agent_id"] is None
        assert result["agent_name"] is None
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    def test_get_admin_by_id_success(self, mock_sql_conn):
        """Teste: Buscar admin por ID"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        admin_row = {
            "admin_id": "123e4567",
            "email": "test@example.com",
            "agent_id": 1,
            "name": "Lucas Lorensi",
            "job_title": "Engineer",
            "city": "SP",
            "agent_name": "LUZ",
            "is_active": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mock_sql.execute_single.return_value = admin_row
        mock_sql.execute.return_value = []  # No features
        
        result = AdminService.get_admin_by_id("123e4567")
        
        assert result["admin_id"] == "123e4567"
        assert result["agent_name"] == "LUZ"
        assert result["features"] == []
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    def test_get_admin_by_id_not_found(self, mock_sql_conn):
        """Teste: Admin não encontrado"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        mock_sql.execute_single.return_value = None
        
        result = AdminService.get_admin_by_id("invalid-id")
        
        assert result is None


class TestAdminServiceUpdate:
    """Testes para AdminService UPDATE methods"""
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    @patch('app.services.admin_service.AdminService.get_admin_by_email_and_agent_active')
    @patch('app.services.admin_service.AdminService.get_admin_by_id')
    @patch('app.services.admin_service.AgentService.is_agent_valid_by_id')
    def test_update_admin_agent_id_success(self, mock_is_valid, mock_get_admin, mock_get_active, mock_sql_conn):
        """Teste: Atualizar agent_id do admin"""
        mock_is_valid.return_value = True
        mock_get_admin.return_value = {"admin_id": "123", "email": "test@example.com", "agent_id": 1}
        mock_get_active.return_value = None  # Não existe admin ativo com esse email/agent_id novo
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        AdminService.update_admin(admin_id="123", agent_id=2)
        
        # Verifica se UPDATE foi executado
        assert mock_sql.execute.called
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    @patch('app.services.admin_service.AdminService.get_admin_by_id')
    @patch('app.services.admin_service.AgentService.is_agent_valid_by_id')
    def test_update_admin_invalid_agent_id(self, mock_is_valid, mock_get_admin, mock_sql_conn):
        """Teste: Atualizar com agent_id inválido"""
        mock_is_valid.return_value = False
        mock_get_admin.return_value = {"admin_id": "123", "email": "test@example.com"}
        
        with pytest.raises(ValueError, match="Agent ID inválido"):
            AdminService.update_admin(admin_id="123", agent_id=999)
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    @patch('app.services.admin_service.AdminService.get_admin_by_email')
    @patch('app.services.admin_service.AgentService.is_agent_valid_by_id')
    def test_update_admin_by_email_success(self, mock_is_valid, mock_get_admin_by_email, mock_sql_conn):
        """Teste: Atualizar admin por email"""
        mock_is_valid.return_value = True
        mock_get_admin_by_email.return_value = {"admin_id": "123", "email": "test@example.com", "agent_id": 1}
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        AdminService.update_admin_by_email(email="test@example.com", agent_id=2)
        
        assert mock_sql.execute.called


class TestAdminServiceDeactivate:
    """Testes para AdminService DEACTIVATE"""
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    def test_deactivate_admin_success(self, mock_sql_conn):
        """Teste: Inactivate (soft delete) de admin"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        # Mock da query que verifica se admin existe
        mock_sql.execute_single.return_value = {"admin_id": "123", "email": "test@example.com", "is_active": True, "name": "Test", "job_title": "Admin", "city": "SP", "agent_id": 1}
        
        result = AdminService.deactivate_admin("123", deactivated_by="admin@test.com")
        
        assert result == True
        assert mock_sql.execute.called  # UPDATE foi executado
    
    @patch('app.services.admin_service.get_sqlserver_connection')
    def test_deactivate_admin_not_found(self, mock_sql_conn):
        """Teste: Inativar admin inexistente"""
        mock_sql = MagicMock()
        mock_sql_conn.return_value = mock_sql
        
        # Mock retorna None quando admin não encontrado
        mock_sql.execute_single.return_value = None
        
        result = AdminService.deactivate_admin("999", deactivated_by="admin@test.com")
        
        assert result == False
