"""
Mocks funcionais para SQL Server e LLM Server
Simula comportamento real sem conexões externas
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any


class MockSQLServerConnection:
    """Mock funcional de SQLServerConnection com estado em memória"""
    
    def __init__(self):
        """Inicializa com storage em memória"""
        self.documents = {}  # id -> doc data
        self.messages = {}   # id -> message data
        self.conversations = {}  # id -> conversation data
        self.users = {}  # user_id -> user data
    
    async def get_document_metadata(self, doc_id: str) -> Optional[Dict]:
        """Retorna metadados do documento"""
        return self.documents.get(doc_id)
    
    async def save_document_metadata(self, **kwargs) -> str:
        """Salva documento em memória e retorna ID"""
        doc_id = kwargs.get('id', str(uuid4()))
        self.documents[doc_id] = {
            'id': doc_id,
            'name': kwargs.get('name', 'test_doc'),
            'user_id': kwargs.get('user_id', 'test-user'),
            'content': kwargs.get('content', ''),
            'created_at': datetime.now().isoformat(),
            'summary': kwargs.get('summary', 'Test summary'),
            'version': 1,
            'is_active': True,
        }
        return doc_id
    
    async def list_documents(self, user_id: str, **filters) -> List[Dict]:
        """Lista documentos do usuário"""
        docs = [
            d for d in self.documents.values() 
            if d['user_id'] == user_id and d.get('is_active', True)
        ]
        return docs
    
    async def delete_document(self, doc_id: str) -> bool:
        """Marca documento como deletado"""
        if doc_id in self.documents:
            self.documents[doc_id]['is_active'] = False
            return True
        return False
    
    async def search_documents(self, user_id: str, query: str, **filters) -> List[Dict]:
        """Busca documentos por query (simples busca por substring)"""
        docs = [
            d for d in self.documents.values()
            if d['user_id'] == user_id 
            and d.get('is_active', True)
            and (query.lower() in d['content'].lower() or query.lower() in d['name'].lower())
        ]
        return docs
    
    async def create_conversation(self, user_id: str, title: str = "New Conversation") -> str:
        """Cria conversa em memória"""
        conv_id = str(uuid4())
        self.conversations[conv_id] = {
            'id': conv_id,
            'user_id': user_id,
            'title': title,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': [],
            'is_active': True,
        }
        return conv_id
    
    async def get_conversation(self, user_id: str, conv_id: str) -> Optional[Dict]:
        """Obtém conversa"""
        conv = self.conversations.get(conv_id)
        if conv and conv['user_id'] == user_id:
            return conv
        return None
    
    async def get_user_conversations(self, user_id: str) -> List[Dict]:
        """Lista conversas do usuário"""
        convs = [
            c for c in self.conversations.values()
            if c['user_id'] == user_id and c.get('is_active', True)
        ]
        return convs
    
    async def save_message(self, user_id: str, conv_id: str, role: str, content: str) -> str:
        """Salva mensagem em conversa"""
        if conv_id not in self.conversations:
            return None
        
        msg_id = str(uuid4())
        message = {
            'id': msg_id,
            'role': role,
            'content': content,
            'created_at': datetime.now().isoformat(),
        }
        self.conversations[conv_id]['messages'].append(message)
        self.conversations[conv_id]['updated_at'] = datetime.now().isoformat()
        return msg_id
    
    async def get_messages(self, user_id: str, conv_id: str) -> List[Dict]:
        """Obtém mensagens da conversa"""
        conv = self.conversations.get(conv_id)
        if conv and conv['user_id'] == user_id:
            return conv['messages']
        return []


class MockLLMServerClient:
    """Mock funcional de LLMServerClient com respostas realistas"""
    
    def __init__(self):
        """Inicializa mock LLM"""
        self.call_count = 0
        self.last_request = None
    
    async def ask_question(
        self, 
        question: str, 
        documents: List[Dict] = None,
        role_id: int = 1,
        cities: List[str] = None,
        chat_id: str = None,
        user_id: str = None,
        **kwargs
    ) -> Dict:
        """Simula resposta do LLM com base na questão"""
        self.call_count += 1
        self.last_request = {
            'question': question,
            'role_id': role_id,
            'cities': cities,
            'documents_count': len(documents) if documents else 0,
        }
        
        # Validação de role_id (simula validação do LLM)
        if role_id == 0:
            raise ValueError("LLM Server 422: role_id must be 1-15 or 99. Got: 0")
        
        if role_id < 1 or (role_id > 15 and role_id != 99):
            raise ValueError(f"LLM Server 422: role_id must be 1-15 or 99. Got: {role_id}")
        
        # Respostas mockadas baseadas na questão
        responses = {
            "embeddings": "Embeddings são representações matemáticas de texto em forma de vetores numéricos.",
            "capital": "A capital da França é Paris.",
            "machine learning": "Machine Learning é um ramo da IA que permite que sistemas aprendam com dados.",
            "default": f"Resposta baseada em {len(documents) if documents else 0} documentos encontrados."
        }
        
        response_text = None
        for key, resp in responses.items():
            if key.lower() in question.lower():
                response_text = resp
                break
        
        if not response_text:
            response_text = responses["default"]
        
        return {
            "answer": response_text,
            "sources": [d.get('id', str(uuid4())) for d in documents] if documents else [],
            "confidence": 0.85,
            "response_time_ms": 234,
            "documents_used": len(documents) if documents else 0,
        }
    
    async def ingest_document(
        self,
        content: str,
        filename: str,
        doc_id: str,
        **kwargs
    ) -> Dict:
        """Simula ingestão de documento"""
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": filename,
            "chunks_created": len(content) // 500 + 1,  # Simples simulação
            "vectors_created": 10,
            "message": "Document ingested successfully"
        }
    
    async def extract_metadata(self, content: str, filename: str) -> Dict:
        """Extrai metadados simulados"""
        return {
            "title": filename.replace('.pdf', '').replace('.docx', ''),
            "description": f"Document {filename}",
            "language": "pt",
            "category": "general",
            "key_terms": ["test", "document"],
        }


class MockAzureStorageClient:
    """Mock funcional de Azure Blob Storage"""
    
    def __init__(self):
        """Inicializa storage em memória"""
        self.blobs = {}  # path -> content
    
    async def upload_file(self, file_content: bytes, file_path: str) -> str:
        """Simula upload para Azure Blob Storage"""
        self.blobs[file_path] = file_content
        return f"https://mock-storage.blob.core.windows.net/{file_path}"
    
    async def download_file(self, file_path: str) -> bytes:
        """Simula download do Azure Blob Storage"""
        return self.blobs.get(file_path, b"")
    
    async def delete_file(self, file_path: str) -> bool:
        """Simula deleção do Azure Blob Storage"""
        if file_path in self.blobs:
            del self.blobs[file_path]
            return True
        return False
    
    async def list_files(self, prefix: str) -> List[str]:
        """Lista arquivos com prefixo"""
        return [p for p in self.blobs.keys() if p.startswith(prefix)]


def create_mock_sqlserver() -> MockSQLServerConnection:
    """Factory para criar mock SQL Server"""
    return MockSQLServerConnection()


def create_mock_llm_server() -> MockLLMServerClient:
    """Factory para criar mock LLM Server"""
    return MockLLMServerClient()


def create_mock_storage() -> MockAzureStorageClient:
    """Factory para criar mock Azure Storage"""
    return MockAzureStorageClient()


async def mock_sqlserver_fixture():
    """Pytest fixture para mock SQL Server"""
    return create_mock_sqlserver()


async def mock_llm_server_fixture():
    """Pytest fixture para mock LLM Server"""
    return create_mock_llm_server()


async def mock_storage_fixture():
    """Pytest fixture para mock Storage"""
    return create_mock_storage()
