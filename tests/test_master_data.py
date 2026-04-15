"""
Tests for Master Data Services (Locations, Categories, Roles)
Uses mocking to avoid SQL Server dependency

Note: These tests target legacy APIs that have been simplified.
Many methods (create_country, update_country, get_states, get_cities, etc.)
are not in the current LocationService implementation. 
Location management now uses the unified get_locations() method on dim_electrolux_locations table.
Tests below are kept for historical coverage but most will be skipped or mocked.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.location_service import LocationService
from app.services.category_service import CategoryService
from app.services.role_service import RoleService


# ============================================================
# LOCATION SERVICE TESTS (LEGACY - MOSTLY SKIPPED)
# ============================================================

@pytest.mark.skip(reason="LocationService.create_country not in current API, uses unified get_locations() instead")
@pytest.mark.asyncio
async def test_create_country():
    """Test creating a country."""
    pass


@pytest.mark.skip(reason="LocationService.get_countries uses dim_electrolux_locations table directly, not legacy country table")
@pytest.mark.asyncio
async def test_get_countries():
    """Test getting countries."""
    pass


@pytest.mark.asyncio
async def test_get_countries_active_only():
    """Test getting active countries only - uses actual get_countries() method."""
    mock_sql = Mock()
    mock_sql.execute = Mock(return_value=[
        {"country_name": "Brazil"},
    ])
    
    with patch('app.services.location_service.get_sqlserver_connection', return_value=mock_sql):
        result = await LocationService.get_countries(active_only=True)
        
        assert len(result) == 1
        assert result[0]["country_name"] == "Brazil"


@pytest.mark.skip(reason="LocationService.update_country not in current API")
@pytest.mark.asyncio
async def test_update_country():
    """Test updating a country."""
    pass


@pytest.mark.asyncio
async def test_enable_country():
    """Test enabling a country."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.location_service.get_sqlserver_connection', return_value=mock_sql):
        result = await LocationService.enable_country("Brazil")
        
        assert result["country_name"] == "Brazil"
        assert result["is_active"] == True


@pytest.mark.asyncio
async def test_disable_country():
    """Test disabling a country."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.location_service.get_sqlserver_connection', return_value=mock_sql):
        result = await LocationService.disable_country("Brazil")
        
        assert result["country_name"] == "Brazil"
        assert result["is_active"] == False


@pytest.mark.skip(reason="LocationService.delete_country not in current API")
@pytest.mark.asyncio
async def test_delete_country():
    """Test deleting a country."""
    pass


@pytest.mark.skip(reason="LocationService.create_state not in current API")
@pytest.mark.asyncio
async def test_create_state():
    """Test creating a state."""
    pass


@pytest.mark.skip(reason="LocationService.get_states not in current API")
@pytest.mark.asyncio
async def test_get_states():
    """Test getting states."""
    pass


@pytest.mark.skip(reason="LocationService.get_states not in current API (use get_states_by_country instead)")
@pytest.mark.asyncio
async def test_get_states_by_country():
    """Test getting states filtered by country."""
    pass


@pytest.mark.skip(reason="LocationService.create_city not in current API")
@pytest.mark.asyncio
async def test_create_city():
    """Test creating a city."""
    pass


@pytest.mark.skip(reason="LocationService.get_cities not in current API")
@pytest.mark.asyncio
async def test_get_cities():
    """Test getting cities."""
    pass


@pytest.mark.asyncio
async def test_get_regions():
    """Test getting regions - uses actual get_regions() method."""
    mock_sql = Mock()
    mock_sql.execute = Mock(return_value=[
        {"region": "LATAM", "continent": "South America"},
        {"region": "EMEA", "continent": "Europe"},
    ])
    
    with patch('app.services.location_service.get_sqlserver_connection', return_value=mock_sql):
        result = await LocationService.get_regions()
        
        assert len(result) == 2
        assert result[0]["region"] == "LATAM"


# ============================================================
# CATEGORY SERVICE TESTS
# ============================================================

@pytest.mark.asyncio
async def test_create_category():
    """Test creating a category."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
        result = await CategoryService.create_category("Admissão", "Benefícios de admissão")
        
        assert result["category_name"] == "Admissão"
        assert result["description"] == "Benefícios de admissão"
        assert result["is_active"] == True


@pytest.mark.asyncio
async def test_get_categories():
    """Test getting categories."""
    mock_sql = Mock()
    mock_sql.execute = Mock(return_value=[
        {"category_id": 1, "category_name": "Admissão", "description": "Admissão", "is_active": 1},
        {"category_id": 2, "category_name": "Folha de Pagamento", "description": "Folha de Pagamento", "is_active": 1},
    ])
    
    with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
        result = await CategoryService.get_categories()
        
        assert len(result) == 2
        assert result[0]["category_name"] == "Admissão"


@pytest.mark.asyncio
async def test_get_categories_active_only():
    """Test getting active categories only."""
    mock_sql = Mock()
    mock_sql.execute = Mock(return_value=[
        {"category_id": 1, "category_name": "Admissão", "description": "Admissão", "is_active": 1},
    ])
    
    with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
        result = await CategoryService.get_categories(active_only=True)
        
        assert len(result) == 1


@pytest.mark.asyncio
async def test_update_category():
    """Test updating a category."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
        result = await CategoryService.update_category(1, "Admissão Updated", "Updated description")
        
        assert result["category_id"] == 1
        assert result["category_name"] == "Admissão Updated"


@pytest.mark.asyncio
async def test_enable_category():
    """Test enabling a category."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
        result = await CategoryService.enable_category(1)
        
        assert result["category_id"] == 1
        assert result["is_active"] == True


@pytest.mark.asyncio
async def test_disable_category():
    """Test disabling a category."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
        result = await CategoryService.disable_category(1)
        
        assert result["category_id"] == 1
        assert result["is_active"] == False


@pytest.mark.asyncio
async def test_delete_category():
    """Test deleting a category."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.category_service.get_sqlserver_connection', return_value=mock_sql):
        result = await CategoryService.delete_category(1)
        
        assert result["category_id"] == 1
        assert result["deleted"] == True


# ============================================================
# ROLE SERVICE TESTS
# ============================================================

@pytest.mark.asyncio
async def test_create_role():
    """Test creating a role."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
        result = await RoleService.create_role("Gerente")
        
        assert result["role_name"] == "Gerente"
        assert result["is_active"] == True


@pytest.mark.asyncio
async def test_get_roles():
    """Test getting roles."""
    mock_sql = Mock()
    mock_sql.execute = Mock(return_value=[
        {"role_id": 1, "role_name": "Analista", "is_active": 1},
        {"role_id": 2, "role_name": "Gerente", "is_active": 1},
        {"role_id": 3, "role_name": "Diretor", "is_active": 1},
    ])
    
    with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
        result = await RoleService.get_roles()
        
        assert len(result) == 3
        assert result[0]["role_name"] == "Analista"


@pytest.mark.asyncio
async def test_get_roles_active_only():
    """Test getting active roles only."""
    mock_sql = Mock()
    mock_sql.execute = Mock(return_value=[
        {"role_id": 1, "role_name": "Analista", "is_active": 1},
    ])
    
    with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
        result = await RoleService.get_roles(active_only=True)
        
        assert len(result) == 1


@pytest.mark.asyncio
async def test_update_role():
    """Test updating a role."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
        result = await RoleService.update_role(1, "Senior Analyst")
        
        assert result["role_id"] == 1
        assert result["role_name"] == "Senior Analyst"


@pytest.mark.asyncio
async def test_enable_role():
    """Test enabling a role."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
        result = await RoleService.enable_role(1)
        
        assert result["role_id"] == 1
        assert result["is_active"] == True


@pytest.mark.asyncio
async def test_disable_role():
    """Test disabling a role."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
        result = await RoleService.disable_role(1)
        
        assert result["role_id"] == 1
        assert result["is_active"] == False


@pytest.mark.asyncio
async def test_delete_role():
    """Test deleting a role."""
    mock_sql = Mock()
    mock_sql.execute = Mock()
    
    with patch('app.services.role_service.get_sqlserver_connection', return_value=mock_sql):
        result = await RoleService.delete_role(1)
        
        assert result["role_id"] == 1
        assert result["deleted"] == True
