# 🏗️ Backend - Visão Geral Arquitetônica

Explicação completa da arquitetura Python do backend: Framework, estrutura de camadas, padrões arquiteturais e responsabilidades.

---

## 📋 Sumário Executivo

**Plataforma de Gestão de Conhecimento com IA**

- **Framework**: FastAPI (Python 3.11)
- **Arquitetura**: 5 camadas (Routers → Services → Providers → Core + Models)
- **Integrações**: Azure SQL Server, Blob Storage, Entra ID, OpenAI, AI Search, LLM Server
- **Padrão**: RESTful com versionamento (`/api/v1/`), JWT em cookies HTTP-Only
- **Deployment**: Docker + Docker Compose (local) / Azure App Services (produção)

---

## 1️⃣ Framework: FastAPI

### O que é?

FastAPI é um framework web moderno e rápido para construir APIs REST em Python.

**Por que FastAPI?**

| Aspecto | FastAPI | Django REST | Flask |
|--------|---------|------------|-------|
| Performance | ⭐⭐⭐⭐⭐ (~2x mais rápido) | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Type Hints | ⭐⭐⭐⭐⭐ (nativo Pydantic) | ⭐⭐⭐ | ⭐⭐ |
| Async/Await | ⭐⭐⭐⭐⭐ (nativo) | ⭐⭐⭐ | ⭐⭐⭐ |
| Documentação | ⭐⭐⭐⭐⭐ (Swagger auto) | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Curva de aprendizado | ⭐⭐⭐⭐ (fácil) | ⭐⭐⭐ (complexo) | ⭐⭐⭐⭐ (muito fácil) |

**Nossa versão**:
```python
# app/main.py
from fastapi import FastAPI

app = FastAPI(
    title="Luz - Backend",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json"
)
```

### Inicialização (app/main.py)

```python
# 1. Criar app FastAPI
app = FastAPI()

# 2. Registrar middlewares (CORS, logging, etc)
app.add_middleware(CORSMiddleware, allow_origins=[...])

# 3. Registrar routers (endpoints)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
# ... mais routers

# 4. Handlers de erro global
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={...})

# 5. Startup/Shutdown events
@app.on_event("startup")
async def startup():
    logger.info("Backend iniciando...")
```

**Versão da dependência**:
```
fastapi==0.104.1
uvicorn==0.24.0  # Servidor ASGI
pydantic==2.5.0  # Validação de dados
```

---

## 2️⃣ Arquitetura de 5 Camadas

```
┌─────────────────────────────────────────┐
│      HTTP Layer (FastAPI)               │
│  POST /api/v1/documents/ingest          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Routers (14 aplicações)            │
│  - auth.py (login/logout/roles)         │
│  - documents.py (ingest/manage)         │
│  - chat.py (questions/conversations)    │
│  - dashboard.py (analytics)             │
│  - admin.py (gerenciamento)             │
│  - master_data.py (dados mestres)       │
│  - user_preferences.py (settings)       │
│  - etc                                  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Services (16 repositórios)         │
│  - document_service.py                  │
│  - conversation_service.py              │
│  - llm_integration.py                   │
│  - job_title_role_service.py            │
│  - admin_service.py                     │
│  - etc                                  │
│  ⚠️ Lógica de negócio aqui              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Providers & Utils                  │
│  - auth_provider.py (MSAL, JWT)         │
│  - storage_provider.py (Blob)           │
│  - llm_provider.py (OpenAI SDK)         │
│  - database_provider.py (pyodbc)        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Core (Compartilhado)               │
│  - config.py (KeyVaultConfig)           │
│  - sqlserver.py (DB connection)         │
│  - logging_config.py                    │
│  - models.py (Pydantic schemas)         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      External Services                  │
│  - Azure SQL Server (dados)             │
│  - Azure Blob Storage (arquivos)        │
│  - Azure Entra ID (autenticação)        │
│  - Azure OpenAI / LLM Server (IA)       │
│  - Azure AI Search (busca semântica)    │
│  - Redis (cache)                        │
└─────────────────────────────────────────┘
```

### Fluxo de uma Requisição

```
1. Cliente → HTTP POST /api/v1/documents/ingest

2. FastAPI
   - Parse JSON body
   - Validação com Pydantic
   - Injeção de dependências (user_id, etc)
   - Routing→ documents.py

3. Router (documents.py)
   - Validação de permissões
   - Parse parameters
   - Chamada → DocumentService.ingest()
   - Return response JSON

4. Service (document_service.py)
   - Lógica de negócio
   - Chamar múltiplos providers
   - Tratamento de erros
   - Logging estruturado

5. Providers
   - Storage → upload para Blob
   - LLM → extração de metadata
   - DB → garantir integridade

6. External Services
   - Azure SQL: INSERT document_metadata
   - Blob: WRITE arquivo.pdf
   - LLM Server: INDEX vector embeddings

7. Response
   - ✅ 200 OK com document_id
   - ❌ 400/401/500 com erro estruturado
```

---

## 3️⃣ Padrões Arquiteturais

### A. Dependency Injection (DI)

FastAPI usa DI nativo para gerenciar dependências.

```python
# app/routers/documents.py

from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/documents")

# Dependência: extrai user_id do JWT
def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    user_id = decode_jwt(token)
    return {"user_id": user_id}

@router.get("/")
async def list_documents(
    user_id: dict = Depends(get_current_user),  # ← DI aqui
    limit: int = Query(10),
    offset: int = Query(0)
):
    """Listar documentos do usuário"""
    docs = await DocumentService.list_documents(
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return {"documents": docs}
```

**Benefícios**:
- ✅ Suporte a testes (mockar dependências)
- ✅ Reuso de lógica (validação, autenticação)
- ✅ Type hints completos
- ✅ Documentação automática (Swagger)

### B. Configuration Management

**Pattern**: Singleton com ambiente-specific overrides

```python
# app/core/config.py

from pydantic_settings import BaseSettings
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class KeyVaultConfig(BaseSettings):
    """
    Configurações gerenciadas por Azure KeyVault em PROD
    e variáveis de ambiente em DEV/LOCAL
    """
    
    # Core configs
    ENVIRONMENT: str = "dev"  # dev, staging, prod
    DEBUG: bool = False
    
    # Secrets (carregadas de KeyVault em PROD)
    AZURE_CLIENT_ID: str
    : str
    SQLSERVER_CONNECTION_STRING: str
    AZURE_STORAGE_CONNECTION_STRING: str
    
    # URLs das dependências
    LLM_SERVER_URL: str = "http://llm-server:8001"
    
    class Config:
        env_file = ".env"  # Carregar de .env em desenvolvimento
        
    @classmethod
    def from_keyvault(cls):
        """Carregar secrets de Azure KeyVault em PROD"""
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=VAULT_URL, credential=credential)
        
        return cls(
            AZURE_CLIENT_ID=client.get_secret("CLIENT-ID").value,
            =client.get_secret("CLIENT-SECRET").value,
            # ...
        )

# Uso globalmente
config = KeyVaultConfig()

# Em app/main.py
if config.ENVIRONMENT == "prod":
    config = KeyVaultConfig.from_keyvault()
else:
    config = KeyVaultConfig()
```

### C. Provider Pattern (Adapter Pattern)

Isolam acesso a serviços externos.

```python
# app/providers/auth_provider.py
from msal import PublicClientApplication
from azure.identity import DefaultAzureCredential

class AuthProvider:
    """Adapter para Azure Entra ID + JWT"""
    
    def __init__(self, config: KeyVaultConfig):
        self.config = config
        self.app = PublicClientApplication(
            client_id=config.AZURE_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{config.AZURE_TENANT_ID}"
        )
    
    def validate_token(self, token: str) -> dict:
        """Validar JWT + verificar Graph (permissões)"""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid token")

# Uso em um service
class DocumentService:
    def __init__(self, auth_provider: AuthProvider):
        self.auth = auth_provider
    
    async def ingest_document(self, user_id: str, file):
        user = self.auth.validate_user_permissions(user_id)
        # ... rodar ingestão
        return document_id
```

**Benefícios**:
- ✅ Fácil de testar (mockar provider)
- ✅ Trocar implementação sem afetar serviço
- ✅ Reutilizar entre services

### D. Error Handling Pattern

```python
# app/core/exceptions.py

from fastapi import HTTPException

class LuzException(HTTPException):
    """Base para todas as exceções da Luz"""
    pass

class DocumentNotFoundError(LuzException):
    def __init__(self, doc_id: str):
        super().__init__(
            status_code=404,
            detail=f"Document {doc_id} not found"
        )

class InsufficientPermissionsError(LuzException):
    def __init__(self, resource: str, user_id: str):
        super().__init__(
            status_code=403,
            detail=f"User {user_id} cannot access {resource}"
        )

# Uso
@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    doc = await DocumentService.get_by_id(doc_id)
    if not doc:
        raise DocumentNotFoundError(doc_id)  # ← 404
    return doc
```

---

## 4️⃣ Padrão de Resposta HTTP

### Success Response (2xx)

```json
{
  "status": "success",
  "data": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "policy.pdf",
    "created_at": "2026-03-20T14:30:00Z"
  },
  "metadata": {
    "version": "1.0.0",
    "timestamp": "2026-03-20T14:30:01Z"
  }
}
```

**Status Codes Comuns**:

| Código | Significado | Exemplo |
|--------|-------------|---------|
| **200 OK** | Sucesso | GET, PUT, PATCH bem-sucedidos |
| **201 Created** | Recurso criado | POST /documents → document_id |
| **204 No Content** | Sucesso sem corpo | DELETE bem-sucedido |
| **206 Partial Content** | Paginação | GET /documents?limit=10&offset=20 |

### Error Response (4xx/5xx)

```json
{
  "status": "error",
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Document with ID 550e8400-e29b-41d4 not found",
    "details": {
      "document_id": "550e8400-e29b-41d4",
      "searched_at": "2026-03-20T14:30:00Z"
    }
  },
  "request_id": "req_abc123xyz",
  "timestamp": "2026-03-20T14:30:01Z"
}
```

**HTTP Error Codes**:

| Código | Situação | Exemplo da API |
|--------|----------|-----------------|
| **400 Bad Request** | Request inválido | `POST /chat/question` sem `question` field |
| **401 Unauthorized** | Sem autenticação | JWT expirado ou inválido |
| **403 Forbidden** | Sem permissão | User não tem acesso ao documento |
| **404 Not Found** | Recurso não existe | GET `/documents/invalid-id` |
| **409 Conflict** | Estado inconsistente | Tentar confirmar ingestão 2x |
| **422 Unprocessable** | Validação falhou | Campo obrigatório ausente |
| **429 Too Many Requests** | Rate limit excedido | LLM rate limit atingido |
| **500 Internal Error** | Erro no server | DB connection off |
| **502 Bad Gateway** | Serviço externo off | LLM Server indisponível |
| **503 Unavailable** | Server em manutenção | Restart do backend |

---

## 5️⃣ Estrutura de Diretórios

```
/workspaces/Embeddings/
├── app/
│   ├── main.py                    # Entrada FastAPI
│   ├── models.py                  # Pydantic schemas (request/response)
│   │
│   ├── routers/                   # 14 aplicações de endpoints
│   │   ├── auth.py               # Login, logout, roles
│   │   ├── documents.py          # Ingest, manage
│   │   ├── chat.py               # Questions, conversations
│   │   ├── dashboard.py          # Analytics
│   │   ├── master_data.py        # Locations, roles, categories
│   │   ├── admin.py              # Admin operations
│   │   └── ...                   # + 8 mais
│   │
│   ├── services/                  # 16 serviços (lógica de negócio)
│   │   ├── document_service.py   # Preview, confirm, manage docs
│   │   ├── conversation_service.py
│   │   ├── llm_integration.py
│   │   ├── admin_service.py
│   │   └── ...
│   │
│   ├── providers/                 # Adapters para serviços externos
│   │   ├── auth_provider.py      # MSAL + JWT
│   │   ├── storage_provider.py   # Blob Storage
│   │   ├── llm_server_provider.py # Langchain Backend
│   │   ├── database_provider.py  # pyodbc
│   │   └── cache_provider.py     # Redis
│   │
│   ├── core/                      # Compartilhado
│   │   ├── config.py             # KeyVaultConfig + environment vars
│   │   ├── sqlserver.py          # Conexão DB (DataClasses)
│   │   ├── logging_config.py     # Logger setup
│   │   ├── exceptions.py         # Custom exceptions
│   │   └── dependencies.py       # DI functions
│   │
│   ├── migrations/                # Alembic migrations (futuro)
│   └── utils/                     # Utilities
│
├── db/
│   ├── schema.sql                 # Schema DDL principal
│   ├── schema_seed.sql           # Dados iniciais
│   ├── migrations/
│   │   ├── add_admins_table.sql
│   │   ├── add_documents_json.sql
│   │   └── ... (histórico)
│   └── migrate_*.py              # Scripts de migração
│
├── tests/
│   ├── test_documents.py
│   ├── test_chat.py
│   └── ...
│
├── docker-compose.yml             # Redis, DB local
├── Dockerfile                      # Container image
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Test config
└── .env.example                  # Template de variáveis
```

---

## 6️⃣ Principais Componentes

### Routers (14)

| Router | Responsabilidade | Endpoints |
|--------|------------------|-----------|
| **auth.py** | Autenticação Entra ID | `/login`, `/logout`, `/me/role` |
| **documents.py** | Upload, ingest, manage | `/documents/ingest`, `/documents/{id}`, `/documents/delete` |
| **chat.py** | Chat semântico | `/chat/question`, `/chat/conversations` |
| **master_data.py** | Dados mestres | `/master-data/locations`, `/roles`, `/categories` |
| **dashboard.py** | Analytics | `/chat/dashboard/summary`, `/detailed`, `/export` |
| **admin.py** | Gerenciamento | `/admin/admins`, `/audit` |
| **user_preferences.py** | Preferências do usuário | `/user-preferences/{user_id}` |
| **job_title_roles.py** | Mapeamento cargos | `/job-title-roles` |
| **prompts.py** | Gerenciar prompts LLM | `/prompts` |
| **e42_evaluation.py** | E42 API | `/e42/evaluate` |
| **debug.py** | Endpoints debug | `/debug/status`, `/debug/config` |
| **stress_test.py** | Teste de carga | `/stress-test/run` |

### Services (16)

Implementam lógica de negócio:

| Service | O que faz |
|---------|----------|
| **document_service.py** | Orquestra ingestão 2-step, valida metadata, chama LLM |
| **conversation_service.py** | Gerencia conversas, histórico, dashboard |
| **llm_integration.py** | Abstração para LLM Server (retry, timeout, logging) |
| **admin_service.py** | Gerenciar admins, audit log |
| **auth_service.py** | Autenticação com Entra ID, JWT |
| **cache_service.py** | Redis para caching de documents |
| **job_title_role_service.py** | Mapeamento cargo → permitido |

### Providers

```python
# Exemplos de uso

# 1. Auth Provider
auth_provider = AuthProvider(config)
user_data = auth_provider.validate_token(jwt_token)

# 2. Storage Provider
storage = StorageProvider(config)
url = storage.upload_file(file_bytes, container="documents")

# 3. LLM Provider
llm = LLMProvider(config)
embeddings = llm.generate_embeddings(text)

# 4. Database Provider
db = DatabaseProvider(config)
results = db.execute_query("SELECT * FROM documents WHERE user_id = ?", [user_id])
```

---

## 7️⃣ Flow Completo: Ingestão de Documento

```
┌─ Cliente (Frontend) ─┐
│  Upload polítca.pdf  │
└──────────┬───────────┘
          │
          ↓
   POST /api/v1/documents/ingest-preview
   (multipart/form-data: file)
          │
          ↓ Router (documents.py)
   ┌──────────────────────────────────┐
   │ 1. Validação:                    │
   │    - File size < 50MB?           │
   │    - Type = PDF/TXT?             │
   │    - User authenticated?         │
   └──────────┬───────────────────────┘
              │
              ↓ Service (document_service.py)
   ┌──────────────────────────────────┐
   │ 2. Upload temp:                  │
   │    - Criar temp_id               │
   │    - Upload para Blob/temp/      │
   │    - Salvar temp no DB           │
   └──────────┬───────────────────────┘
              │
              ↓ Provider (llm_provider.py)
   ┌──────────────────────────────────┐
   │ 3. Chamar LLM Server:            │
   │    - Extract text                │
   │    - Generate metadata           │
   │      (title, category, etc)      │
   │    - Timeout: 30s                │
   │    - Retry: 3x com backoff      │
   └──────────┬───────────────────────┘
              │
              ↓
   Resposta: ✅ 200 OK
   {
     "temp_id": "550e8400...",
     "filename": "policy.pdf",
     "suggested_metadata": {
       "title": "Política de Benefícios",
       "category_id": 2,
       "allowed_countries": ["BR", "US"]
     }
   }
   
          │
          ↓ Cliente confirma
   POST /api/v1/documents/ingest-confirm/550e8400...
   {
     "user_id": "alice",
     "allowed_countries": ["BR"],
     "category_id": 2,
     "title": "Benefícios Brasil 2026"
   }
          │
          ↓ Router
   ┌──────────────────────────────────┐
   │ 4. Confirmar:                    │
   │    - Recuperar temp file         │
   │    - Validar metadados           │
   │    - Chamar LLM para index       │
   │    - INSERT no SQL               │
   │    - Mover arquivo perm          │
   │    - DELETE temp                 │
   └──────────┬───────────────────────┘
              │
              ↓
   Resposta: ✅ 201 Created
   {
     "document_id": "550e8400...",
     "status": "indexed",
     "indexed_at": "2026-03-20T14:30:00Z"
   }

   ✅ Documento pronto para busca semântica!
```

---

## 8️⃣ Tratamento de Erros

```python
# app/main.py - Global exception handler

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Pydantic validation errors → 422"""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc),
                "details": exc.errors()
            }
        }
    )

@app.exception_handler(LuzException)
async def luz_exception_handler(request, exc):
    """Custom business logic errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": exc.error_code,
                "message": exc.detail
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Unexpected errors → 500"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            }
        }
    )
```

---

## 9️⃣ Middleware & Cross-Cutting Concerns

```python
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://seu-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Logging (middleware customizado)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    logger.info(
        f"{request.method} {request.url.path} "
        f"→ {response.status_code} ({duration:.3f}s)"
    )
    return response
```

---

## 🔟 Padrão de Inicialização

### Development (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env
cp .env.example .env
# Editar .env com credenciais DEV

# 3. Run backend
uvicorn app.main:app --reload --port 8000

# 4. Acessar
# - API: http://localhost:8000/api/v1
# - Docs: http://localhost:8000/docs (Swagger)
# - ReDoc: http://localhost:8000/redoc
```

### Production (Docker)

```bash
# 1. Build image
docker build -t luz-backend:latest .

# 2. Run container
docker run \
  --env-file .env.prod \
  --port 8000:8000 \
  luz-backend:latest

# 3. Enviar para Azure Container Registry
az acr build --registry myregistry --image luz-backend:latest .

# 4. Deploy via App Services ou AKS
az webapp deployment container config ...
```

---

## 📚 Documentação Complementar

- [CONFIG_KEYS.md](CONFIG_KEYS.md) - Todas as variáveis de ambiente
- [RUN_LOCAL_COMPLETE_GUIDE.md](RUN_LOCAL_COMPLETE_GUIDE.md) - Setup passo-a-passo
- [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) - Diagramas Mermaid
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problemas comuns
- [DATABASE_MIGRATIONS.md](DATABASE_MIGRATIONS.md) - Schema e DDL
- [API Reference](Luz-API-Postman-Collection.json) - Postman Collection

---

## 🔗 Referências

- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Azure Python SDKs](https://learn.microsoft.com/en-us/python/azure/)
