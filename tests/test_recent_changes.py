"""
Testes para validar as mudanças recentes:
1. role_id (int) no chat
2. allowed_roles (lista de IDs) na ingestão
3. rating system
4. serialização de roles
"""
import json
from app.services.document_service import DocumentService
from app.models import QuestionRequest, RatingRequest

def test_serialize_roles_with_integers():
    """Teste serialização de lista de inteiros"""
    result = DocumentService._serialize_roles([4, 5, 6])
    assert result == "[4, 5, 6]"
    print("✅ test_serialize_roles_with_integers PASSED")

def test_serialize_roles_with_string():
    """Teste serialização de string com vírgulas"""
    result = DocumentService._serialize_roles("admin, manager, supervisor")
    expected = '["admin", "manager", "supervisor"]'
    assert result == expected
    print("✅ test_serialize_roles_with_string PASSED")

def test_serialize_roles_with_none():
    """Teste serialização de None"""
    result = DocumentService._serialize_roles(None)
    assert result is None
    print("✅ test_serialize_roles_with_none PASSED")

def test_serialize_roles_with_empty_list():
    """Teste serialização de lista vazia retorna None"""
    result = DocumentService._serialize_roles([])
    # Lista vazia é tratada como "nenhuma role" e retorna None
    assert result is None
    print("✅ test_serialize_roles_with_empty_list PASSED")

def test_question_request_role_id():
    """Teste model QuestionRequest com role_id (int)"""
    req = QuestionRequest(
        chat_id="test_123",
        question="Qual é a política de férias?",
        user_id="emp_001",
        name="João Silva",
        email="joao@company.com",
        role_id=2  # integer, não lista
    )
    assert req.role_id == 2
    assert isinstance(req.role_id, int)
    print("✅ test_question_request_role_id PASSED")

def test_question_request_default_role_id():
    """Teste default role_id = 1"""
    req = QuestionRequest(
        chat_id="test_123",
        question="teste",
        user_id="emp_001",
        name="João",
        email="joao@company.com"
    )
    assert req.role_id == 1
    print("✅ test_question_request_default_role_id PASSED")

def test_rating_request():
    """Teste RatingRequest com valores válidos"""
    # 4.5 estrelas
    rating_req = RatingRequest(rating=4.5)
    assert rating_req.rating == 4.5
    print("✅ test_rating_request (4.5) PASSED")
    
    # 5.0 estrelas
    rating_req = RatingRequest(rating=5.0)
    assert rating_req.rating == 5.0
    print("✅ test_rating_request (5.0) PASSED")
    
    # 0.0 estrelas
    rating_req = RatingRequest(rating=0.0)
    assert rating_req.rating == 0.0
    print("✅ test_rating_request (0.0) PASSED")

if __name__ == "__main__":
    print("\n🧪 Iniciando testes das mudanças recentes...\n")
    
    try:
        test_serialize_roles_with_integers()
        test_serialize_roles_with_string()
        test_serialize_roles_with_none()
        test_serialize_roles_with_empty_list()
        test_question_request_role_id()
        test_question_request_default_role_id()
        test_rating_request()
        
        print("\n" + "="*50)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("="*50)
    except Exception as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        import traceback
        traceback.print_exc()
