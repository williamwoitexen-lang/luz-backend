"""
Testes unitários para JobTitleRoleService
"""

import pytest
from unittest.mock import Mock, patch
from app.services.job_title_role_service import JobTitleRoleService


class MockSQLConnection:
    """Mock de conexão SQL"""
    
    def __init__(self):
        self.execute_results = []
        self.last_query = None
        self.last_params = None
    
    def execute(self, query: str, params: list = None):
        self.last_query = query
        self.last_params = params
        return self.execute_results


class TestJobTitleRoleService:
    """Testes para JobTitleRoleService"""
    
    @pytest.fixture
    def mock_sql(self):
        """Fixture que retorna mock de conexão SQL"""
        return MockSQLConnection()
    
    def test_get_role_by_job_title_success(self, mock_sql):
        """Testa busca de role por job_title com sucesso"""
        mock_sql.execute_results = [{"role": "Manager", "role_id": 5}]
        
        with patch('app.services.job_title_role_service.get_sqlserver_connection', return_value=mock_sql):
            result = JobTitleRoleService.get_role_by_job_title("SVP Corporate")
            
            assert result is not None
            assert result["role"] == "Manager"
            assert result["role_id"] == 5
    
    def test_get_role_by_job_title_not_found(self, mock_sql):
        """Testa busca de role quando job_title não existe"""
        mock_sql.execute_results = []
        
        with patch('app.services.job_title_role_service.get_sqlserver_connection', return_value=mock_sql):
            result = JobTitleRoleService.get_role_by_job_title("Unknown Title")
            
            assert result is None
    
    def test_get_role_by_job_title_empty_string(self):
        """Testa busca com job_title vazio"""
        result = JobTitleRoleService.get_role_by_job_title("")
        assert result is None
    
    def test_get_role_by_job_title_none(self):
        """Testa busca com job_title None"""
        result = JobTitleRoleService.get_role_by_job_title(None)
        assert result is None
    
    def test_get_role_by_job_title_error(self, mock_sql):
        """Testa tratamento de erro em busca"""
        mock_sql.execute = Mock(side_effect=Exception("DB error"))
        
        with patch('app.services.job_title_role_service.get_sqlserver_connection', return_value=mock_sql):
            result = JobTitleRoleService.get_role_by_job_title("Test Title")
            
            assert result is None
    
    def test_list_all_mappings_success(self, mock_sql):
        """Testa listagem de todos os mapeamentos"""
        mock_sql.execute_results = [
            {"job_title": "Manager", "role": "Manager"},
            {"job_title": "Director", "role": "Director"}
        ]
        
        with patch('app.services.job_title_role_service.get_sqlserver_connection', return_value=mock_sql):
            result = JobTitleRoleService.list_all_mappings()
            
            assert len(result) == 2
            assert result[0]["job_title"] == "Manager"
    
    def test_list_all_mappings_with_limit(self, mock_sql):
        """Testa listagem com limite"""
        mock_sql.execute_results = []
        
        with patch('app.services.job_title_role_service.get_sqlserver_connection', return_value=mock_sql):
            JobTitleRoleService.list_all_mappings(limit=50)
            
            assert mock_sql.last_params == [50]
    
    def test_list_all_mappings_empty(self, mock_sql):
        """Testa listagem vazia"""
        mock_sql.execute_results = []
        
        with patch('app.services.job_title_role_service.get_sqlserver_connection', return_value=mock_sql):
            result = JobTitleRoleService.list_all_mappings()
            
            assert result == []
    
    def test_list_all_mappings_error(self, mock_sql):
        """Testa tratamento de erro na listagem"""
        mock_sql.execute = Mock(side_effect=Exception("DB error"))
        
        with patch('app.services.job_title_role_service.get_sqlserver_connection', return_value=mock_sql):
            result = JobTitleRoleService.list_all_mappings()
            
            assert result == []
    
    def test_add_mapping_success(self, mock_sql):
        """Testa adição de mapeamento com sucesso"""
        mock_sql.execute_results = [{"cnt": 0}]  # Não existe ainda
        
        with patch('app.services.job_title_role_service.get_sqlserver_connection', return_value=mock_sql):
            result = JobTitleRoleService.add_mapping("New Title", "Manager")
            
            assert result is True
            assert "INSERT INTO dim_job_title_roles" in mock_sql.last_query
    
    def test_add_mapping_already_exists(self, mock_sql):
        """Testa adição quando mapeamento já existe"""
        mock_sql.execute_results = [{"cnt": 1}]  # Já existe
        
        with patch('app.services.job_title_role_service.get_sqlserver_connection', return_value=mock_sql):
            result = JobTitleRoleService.add_mapping("Existing Title", "Manager")
            
            assert result is False
    
    def test_add_mapping_empty_job_title(self):
        """Testa adição com job_title vazio"""
        result = JobTitleRoleService.add_mapping("", "Manager")
        assert result is False
    
    def test_add_mapping_empty_role(self):
        """Testa adição com role vazio"""
        result = JobTitleRoleService.add_mapping("Title", "")
        assert result is False
    
    def test_add_mapping_none_values(self):
        """Testa adição com valores None"""
        result = JobTitleRoleService.add_mapping(None, None)
        assert result is False
    
    def test_add_mapping_error(self, mock_sql):
        """Testa tratamento de erro na adição"""
        mock_sql.execute = Mock(side_effect=Exception("DB error"))
        
        with patch('app.services.job_title_role_service.get_sqlserver_connection', return_value=mock_sql):
            result = JobTitleRoleService.add_mapping("New Title", "Manager")
            
            assert result is False
