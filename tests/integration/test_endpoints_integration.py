"""
Testes de integração para endpoints principais.
Foca em validar que:
1. Endpoints estão acessíveis (não 404)
2. Helpers funcionam corretamente
3. Dados fluem sem erros de sintaxe
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from io import BytesIO
import json

# Import app
from app.main import app

client = TestClient(app)


# ===== TESTS: ENDPOINTS EXISTEM =====

def test_health_check_endpoint_exists():
    """Validate health check endpoint is accessible"""
    response = client.get("/health")
    # Should not be 404 (endpoint exists)
    assert response.status_code != 404
    # Should be 200 or 500 (depends on implementation)
    assert response.status_code in [200, 500]


def test_documents_list_endpoint_exists():
    """Validate /api/v1/documents endpoint is accessible"""
    with patch('app.providers.dependencies.get_current_user') as mock_auth:
        async def get_user():
            return {"id": "user-123", "roles": [4]}
        mock_auth.side_effect = get_user
        
        response = client.get('/api/v1/documents?skip=0&limit=10')
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404


def test_documents_get_endpoint_exists():
    """Validate /api/v1/documents/{id} endpoint is accessible"""
    with patch('app.providers.dependencies.get_current_user') as mock_auth:
        async def get_user():
            return {"id": "user-123", "roles": [4]}
        mock_auth.side_effect = get_user
        
        response = client.get('/api/v1/documents/test-id')
        # Should not be 404 (endpoint exists - might be 500 due to db mock)
        assert response.status_code != 404


def test_chat_endpoints_exist():
    """Validate chat endpoints are accessible"""
    # These endpoints might require auth or fail, but shouldn't be 404
    endpoints = [
        ('/api/v1/chat/question', 'POST'),
        ('/api/v1/chat/conversations/user-123', 'GET'),
    ]
    
    for endpoint, method in endpoints:
        if method == 'POST':
            response = client.post(endpoint, json={"test": "data"})
        else:
            response = client.get(endpoint)
        
        # Shouldn't be 404 (endpoint exists)
        # Might be 401/403 (auth), 422 (validation), 500 (error), but not 404
        assert response.status_code != 404, f"Endpoint {endpoint} returned 404 ({method})"


# ===== TESTS: HELPER FUNCTIONS (Core Tests) =====

def test_normalize_input_helper():
    """Test _normalize_input helper function"""
    from app.services.document_service import DocumentService
    
    # Test comma-separated string
    result = DocumentService._normalize_input("São Paulo,Rio de Janeiro")
    assert result == ["São Paulo", "Rio de Janeiro"]
    
    # Test JSON string
    result = DocumentService._normalize_input('["São Paulo", "Rio de Janeiro"]')
    assert result == ["São Paulo", "Rio de Janeiro"]
    
    # Test list
    result = DocumentService._normalize_input(["São Paulo", "Rio de Janeiro"])
    assert result == ["São Paulo", "Rio de Janeiro"]
    
    # Test empty
    result = DocumentService._normalize_input("")
    assert result == []


def test_safe_json_loads_helper():
    """Test _safe_json_loads helper function"""
    from app.services.document_service import DocumentService
    
    # Valid JSON
    result = DocumentService._safe_json_loads('{"key": "value"}')
    assert result == {"key": "value"}
    
    # Invalid JSON with default
    result = DocumentService._safe_json_loads('not json', default={})
    assert result == {}
    
    # Invalid JSON with None default
    result = DocumentService._safe_json_loads('broken')
    assert result is None


def test_ensure_json_string_helper():
    """Test _ensure_json_string helper function"""
    from app.services.document_service import DocumentService
    
    # Valid JSON string
    result = DocumentService._ensure_json_string('{"key": "value"}')
    assert result == '{"key": "value"}'
    
    # Dict input
    result = DocumentService._ensure_json_string({"key": "value"})
    assert json.loads(result) == {"key": "value"}
    
    # List input
    result = DocumentService._ensure_json_string([1, 2, 3])
    assert json.loads(result) == [1, 2, 3]
    
    # None input
    result = DocumentService._ensure_json_string(None)
    assert result is None


# ===== TESTS: DATA FLOW =====

def test_helpers_are_importable():
    """Verify helper functions are available and callable"""
    from app.services.document_service import DocumentService
    
    # Helpers should exist and be callable
    assert callable(DocumentService._normalize_input)
    assert callable(DocumentService._safe_json_loads)
    assert callable(DocumentService._ensure_json_string)
