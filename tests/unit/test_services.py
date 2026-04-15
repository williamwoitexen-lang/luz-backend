"""
Testes unitários para CategoryService e RoleService
Aumenta cobertura testando services com mocks
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.category_service import CategoryService
from app.services.role_service import RoleService


class MockSQLConnection:
    """Mock de conexão SQL para testes"""
    
    def __init__(self):
        self.execute_results = []
        self.execute_single_result = None
        self.last_query = None
        self.last_params = None
    
    def execute(self, query: str, params: list = None):
        self.last_query = query
        self.last_params = params
        return self.execute_results
    
    def execute_single(self, query: str, params: list = None):
        self.last_query = query
        self.last_params = params
        return self.execute_single_result


class TestCategoryService:
    """Testes para CategoryService"""
    
    @pytest.fixture
    def mock_sql(self):
        """Fixture que retorna mock de conexão SQL"""
        return MockSQLConnection()
    
    @pytest.mark.asyncio
    async def test_create_category_success(self, mock_sql):
        """Testa criação de categoria com sucesso"""
        with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
            result = await CategoryService.create_category("Benefits", "Employee benefits")
            
            assert result["category_name"] == "Benefits"
            assert result["description"] == "Employee benefits"
            assert result["is_active"] == True
            assert "INSERT INTO dim_categories" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_get_categories_all(self, mock_sql):
        """Testa busca de todas as categorias"""
        mock_sql.execute_results = [
            {"category_id": 1, "category_name": "Benefits", "description": "Desc", "is_active": True},
            {"category_id": 2, "category_name": "Policies", "description": None, "is_active": True}
        ]
        
        with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
            result = await CategoryService.get_categories()
            
            assert len(result) == 2
            assert result[0]["category_name"] == "Benefits"
            assert result[1]["category_name"] == "Policies"
    
    @pytest.mark.asyncio
    async def test_get_categories_active_only(self, mock_sql):
        """Testa busca apenas categorias ativas"""
        mock_sql.execute_results = [
            {"category_id": 1, "category_name": "Benefits", "description": "Desc", "is_active": True}
        ]
        
        with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
            result = await CategoryService.get_categories(active_only=True)
            
            assert len(result) == 1
            assert "WHERE is_active = 1" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_update_category_success(self, mock_sql):
        """Testa atualização de categoria"""
        with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
            result = await CategoryService.update_category(1, "Benefits Updated", "New description")
            
            assert result["category_id"] == 1
            assert result["category_name"] == "Benefits Updated"
            assert "UPDATE dim_categories" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_enable_category(self, mock_sql):
        """Testa habilitar categoria"""
        with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
            result = await CategoryService.enable_category(1)
            
            assert result["category_id"] == 1
            assert result["is_active"] == True
            assert "is_active = 1" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_disable_category(self, mock_sql):
        """Testa desabilitar categoria"""
        with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
            result = await CategoryService.disable_category(1)
            
            assert result["category_id"] == 1
            assert result["is_active"] == False
            assert "is_active = 0" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_get_category_by_id_success(self, mock_sql):
        """Testa busca de categoria por ID"""
        mock_sql.execute_single_result = {
            "category_id": 1, "category_name": "Benefits", "description": "Desc", "is_active": True
        }
        
        with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
            result = await CategoryService.get_category_by_id(1)
            
            assert result["category_id"] == 1
            assert result["category_name"] == "Benefits"
    
    @pytest.mark.asyncio
    async def test_get_category_by_id_not_found(self, mock_sql):
        """Testa busca de categoria não encontrada"""
        mock_sql.execute_single_result = None
        
        with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
            with pytest.raises(ValueError, match="Category 999 not found"):
                await CategoryService.get_category_by_id(999)
    
    @pytest.mark.asyncio
    async def test_delete_category(self, mock_sql):
        """Testa exclusão de categoria"""
        with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
            result = await CategoryService.delete_category(1)
            
            assert result["category_id"] == 1
            assert result["deleted"] == True
            assert "DELETE FROM dim_categories" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_create_category_error(self, mock_sql):
        """Testa erro ao criar categoria"""
        mock_sql.execute = Mock(side_effect=Exception("DB error"))
        
        with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
            with pytest.raises(Exception, match="DB error"):
                await CategoryService.create_category("Test", "Desc")


class TestRoleService:
    """Testes para RoleService"""
    
    @pytest.fixture
    def mock_sql(self):
        """Fixture que retorna mock de conexão SQL"""
        return MockSQLConnection()
    
    @pytest.mark.asyncio
    async def test_create_role_success(self, mock_sql):
        """Testa criação de role com sucesso"""
        with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
            result = await RoleService.create_role("Manager")
            
            assert result["role_name"] == "Manager"
            assert result["is_active"] == True
            assert "INSERT INTO dim_roles" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_get_roles_all(self, mock_sql):
        """Testa busca de todas as roles"""
        mock_sql.execute_results = [
            {"role_id": 1, "role_name": "Admin", "is_active": True},
            {"role_id": 2, "role_name": "Manager", "is_active": True}
        ]
        
        with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
            result = await RoleService.get_roles()
            
            assert len(result) == 2
            assert result[0]["role_name"] == "Admin"
    
    @pytest.mark.asyncio
    async def test_get_roles_active_only(self, mock_sql):
        """Testa busca apenas roles ativas"""
        mock_sql.execute_results = []
        
        with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
            result = await RoleService.get_roles(active_only=True)
            
            assert "WHERE is_active = 1" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_update_role_success(self, mock_sql):
        """Testa atualização de role"""
        with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
            result = await RoleService.update_role(1, "Senior Manager")
            
            assert result["role_id"] == 1
            assert result["role_name"] == "Senior Manager"
            assert "UPDATE dim_roles" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_enable_role(self, mock_sql):
        """Testa habilitar role"""
        with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
            result = await RoleService.enable_role(1)
            
            assert result["role_id"] == 1
            assert result["is_active"] == True
            assert "is_active = 1" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_disable_role(self, mock_sql):
        """Testa desabilitar role"""
        with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
            result = await RoleService.disable_role(1)
            
            assert result["role_id"] == 1
            assert result["is_active"] == False
            assert "is_active = 0" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_get_role_by_id_success(self, mock_sql):
        """Testa busca de role por ID"""
        mock_sql.execute_single_result = {"role_id": 1, "role_name": "Admin", "is_active": True}
        
        with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
            result = await RoleService.get_role_by_id(1)
            
            assert result["role_id"] == 1
            assert result["role_name"] == "Admin"
    
    @pytest.mark.asyncio
    async def test_get_role_by_id_not_found(self, mock_sql):
        """Testa busca de role não encontrada"""
        mock_sql.execute_single_result = None
        
        with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
            with pytest.raises(ValueError, match="Role 999 not found"):
                await RoleService.get_role_by_id(999)
    
    @pytest.mark.asyncio
    async def test_delete_role(self, mock_sql):
        """Testa exclusão de role"""
        with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
            result = await RoleService.delete_role(1)
            
            assert result["role_id"] == 1
            assert result["deleted"] == True
            assert "DELETE FROM dim_roles" in mock_sql.last_query
    
    @pytest.mark.asyncio
    async def test_create_role_error(self, mock_sql):
        """Testa erro ao criar role"""
        mock_sql.execute = Mock(side_effect=Exception("DB error"))
        
        with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
            with pytest.raises(Exception, match="DB error"):
                await RoleService.create_role("Test")
