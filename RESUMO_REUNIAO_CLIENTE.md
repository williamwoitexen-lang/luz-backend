# RESUMO EXECUTIVO - Reunião Cliente
## Backend Python + LLM + Infraestrutura

**Data**: 20 de Março de 2026  
**Duração Proposta**: 70 minutos  
**Para**: Cliente (explicar o que temos)

---

## 📊 QUICK FACTS

| Item | Status |
|------|--------|
| **Framework** | FastAPI + Python 3.11 ✅ |
| **Documentação Técnica** | Completa em português ✅ |
| **Exemplos de API** | 50+ chamadas (HTTP) ✅ |
| **Arquitetura de Código** | 14 routers + 16 serviços ✅ |
| **Integrações Azure** | 6 serviços integrados ✅ |
| **Testes Automatizados** | Pytest ✅ |
| **Containerização** | Docker + Docker-Compose ✅ |

---

## 1️⃣ VISÃO DO BACKEND (10 min)

### Framework: FastAPI
- REST API de alta performance
- Validação automática com Pydantic
- Documentação interativa (Swagger UI)
- Suporte a async/await nativo

### Arquitetura em 5 Camadas

```
┌─────────────────────────────────────┐
│  ROUTERS (14)                       │  ← Endpoints HTTP
├─────────────────────────────────────┤
│  SERVICES (16)                      │  ← Lógica de negócio
├─────────────────────────────────────┤
│  PROVIDERS                          │  ← Integrações externas
│  ├─ Auth (Azure MSAL)               │
│  ├─ LLM Server client               │
│  ├─ Blob Storage client             │
│  └─ SQL / Metadata extraction       │
├─────────────────────────────────────┤
│  CORE (Config, Database, Utils)     │  ← Infraestrutura
└─────────────────────────────────────┘
```

### Responsabilidades por Camada

| Camada | O quê? | Exemplos |
|--------|--------|----------|
| **Routers** | Recebe HTTP, valida, retorna JSON | GET /documents, POST /chat/question |
| **Services** | Orquestra lógica + chamar providers | DocumentService, ConversationService |
| **Providers** | Fala com externos (Azure, LLM) | auth_msal.py, llm_integration.py |
| **Core** | Config, DB connection, logging | KeyVaultConfig, sqlserver.py |

### Routers Implementados
- ✅ `auth.py` - Login/logout com Entra ID
- ✅ `documents.py` - Ingest (2-step), CRUD, busca
- ✅ `chat.py` - Perguntas + histórico de conversas
- ✅ `master_data.py` - Locais, cargos, categorias (read-only)
- ✅ `admin.py` - Gestão de admins e auditoria
- ✅ `dashboard.py` - Métricas e análise de conversas
- ✅ `prompts.py` - Gestão de prompts de IA
- ✅ `user_preferences.py` - Preferências do usuário
- ✅ `job_title_roles.py`, `e42_evaluation.py`, `stress_test.py`, etc.

---

## 2️⃣ CONTRATOS E ENDPOINTS (15 min)

### Padrões da API

**Versionamento**: Todos com `/api/v1/`  
**Autenticação**: JWT em cookie HTTPOnly  
**Formato**: JSON request/response

### Endpoints Principais

#### Documentos
```
POST   /api/v1/documents/ingest-preview    Upload + LLM extrai metadados
POST   /api/v1/documents/ingest-confirm    Confirma + indexa
GET    /api/v1/documents                   Lista com filtros
DELETE /api/v1/documents/{id}              Deleta
```

#### Chat
```
POST   /api/v1/chat/question               Faz pergunta
GET    /api/v1/chat/conversations/{user}   Historico de conversas
```

#### Dados Mestres (leitura)
```
GET /api/v1/master-data/locations          Cidades/países/regiões
GET /api/v1/master-data/roles              Cargos
GET /api/v1/master-data/categories         Categorias
```

### Recursos Avançados

- ✅ **Paginação**: `?limit=10&offset=0` ou `?page=1`
- ✅ **Filtros**: `?country=Brazil&active_only=true`
- ✅ **Ordenação**: `?sort=created_at&order=desc`

### Respostas Padronizadas

```json
{
  "status": "success",
  "data": [ ... ],
  "pagination": {
    "total": 100,
    "page": 1,
    "limit": 10
  }
}
```

### Códigos HTTP
- `200` - OK
- `201` - Created
- `400` - Bad Request (validação)
- `401` - Unauthorized (auth falhou)
- `404` - Not Found
- `500` - Server Error

### Verificação Rápida
- ✅ Temos: **50+ exemplos** em `API_EXAMPLES.http` (REST Client do VS Code)
- ❌ Falta: **Postman Collection** (.json para importar no Postman/Insomnia)

---

## 3️⃣ INTEGRAÇÕES E DEPENDÊNCIAS (10 min)

### Stack de Infraestrutura

```
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND FASTAPI                          │
├────────────────────────────────────────────────────────────┐
│ ┌────────────────┐ ┌───────────────┐ ┌────────────────────┐│
│ │  SQL Server    │ │ Blob Storage  │ │  Entra ID / MSAL   ││
│ │  (Dados)       │ │  (Arquivos)   │ │  (Autenticação)    ││
│ └────────────────┘ └───────────────┘ └────────────────────┘│
│                                                              │
│ ┌────────────────┐ ┌───────────────┐ ┌────────────────────┐│
│ │  LLM Server    │ │  Redis        │ │  OpenAI / Azure    ││
│ │  (IA)          │ │  (Cache)      │ │  (Embeddings)      ││
│ └────────────────┘ └───────────────┘ └────────────────────┘│
└────────────────────────────────────────────────────────────┘
```

### Cada Integração

| Serviço | Papel | Quando |
|---------|-------|--------|
| **SQL Server** | Armazena documentos, conversas, usuários | Toda operação CRUD |
| **Blob Storage** | Arquivos PDF/DOCX/XLSX | Upload e storage |
| **Entra ID + MSAL** | Autentica usuários corporativos | Login |
| **LLM Server** | Embeddings + busca semântica | Ingest + chat |
| **Azure OpenAI** | GPT-4o, GPT-4o-mini | Processamento IA |
| **Redis** | Cache de sessões | Cache + background jobs |

### Configuração por Ambiente

**DEV (local)**
```
SQLSERVER_CONNECTION_STRING = localhost SQL Server (ou Azure)
LLM_SERVER_URL = http://localhost:8001
SKIP_LLM_SERVER = true (para testar sem LLM)
STORAGE_TYPE = local ou azure
```

**STAGING**
```
Credenciais via KeyVault
LLM_SERVER_URL = staging-llm.internal
STORAGE_TYPE = azure
```

**PRODUÇÃO**
```
Credenciais via KeyVault (injetadas no deployment)
LLM_SERVER_URL = prod-llm-internal
STORAGE_TYPE = azure garantido
```

### Migrações de Banco

Toda mudança de schema está em `/db/`:
- `schema_sqlserver.sql` - Schema inicial
- `add_admins_table.sql`, `add_user_preferences.sql`, etc. - Evoluções

Executar: `python db/run_schema.py`

---

## 4️⃣ LLM: COMO O BACKEND CONSOME (20 min)

### Onde Acontece?

**Arquivo**: `app/services/llm_integration.py`  
**Responsável**: Comunicação com LLM Server  
**Chamadas ao LLM**:

1. **Ingestão** - quando documento é confirmado
2. **Chat** - quando usuário faz pergunta
3. **Limpeza** - quando documento é deletado

### Fluxo de Ingestão (Simplificado)

```
UPLOAD DO ARQUIVO
    ↓
Converter PDF/DOCX/XLSX → texto limpo
    ↓
Truncar se > 50K characters
    ↓
POST /llm/ingest (enviar chunks)
    ↓
LLM Server:
  - Gera embeddings
  - Indexa no Azure AI Search
  - Salva metadados
    ↓
SUCESSO: Documento pronto para busca
ERRO: Volta e pede retry
```

### Fluxo de Chat

```
PERGUNTA DO USUÁRIO
    ↓
Backend:
  1. Busca docs relevantes (descrição + permissões)
  2. Filtra por: role do user, país, cidade, etc
    ↓
POST /llm/question (enviar pergunta + contexto)
    ↓
LLM Server:
  1. Busca semanticamente no Azure AI Search
  2. Chama GPT-4o-mini com documentos relevantes
  3. Retorna resposta + fontes
    ↓
Backend salva em DB:
  - Conversação
  - Histórico
    ↓
RESPOSTA para Frontend
```

### Validação de Entrada

```python
# 1. Pydantic valida schema
# 2. Arquivo: detecta formato
# 3. Texto: extrai e limpa
# 4. Tamanho: trunca se > 50K chars
# 5. Metadados: valida usuarios, cargos, lugares
```

### Timeouts e Retries

| Cenário | Timeout | Retry | Fallback |
|---------|---------|-------|----------|
| Ingest | 30s | Sim (2x) | Erro ao usuário |
| Chat question | 30s (config) | Sim (2x) | "Tente de novo" |
| Delete | 10s | Sim (1x) | Log + continua |

### Observabilidade

Cada chamada ao LLM registra:
```json
{
  "service": "llm_integration",
  "operation": "ingest",
  "document_id": "...",
  "status": "success",
  "duration_ms": 1250,
  "chunks_processed": 5,
  "timestamp": "2026-03-20T10:30:00Z"
}
```

**Logs sensíveis**: 
- ✅ User IDs loggados
- ❌ Conteúdo de documentos **NÃO** loggado
- ❌ Respostas de chat **NÃO** armazenadas em logs

---

## 5️⃣ COMO RODAR LOCAL (15 min)

### Pre-requisitos

- Python 3.11+
- ODBC Driver 17 para SQL Server (se SQL local)
- Docker + Docker Compose (opcional, mas recomendado)

### Opção 1: Sem Docker (Dev Rápido)

```bash
# 1. Clonar e navegar
git clone <repo>
cd Embeddings

# 2. Ambiente Python
python3 -m venv venv
source venv/bin/activate  # ou `.\venv\Scripts\activate` no Windows

# 3. Instalar deps
pip install -r requirements.txt

# 4. Copiar .env e preencher credenciais
cp .env.example .env
# Editar .env com:
#   - AZURE_TENANT_ID
#   - AZURE_CLIENT_ID
#   - 
#   - SQLSERVER_CONNECTION_STRING

# 5. Rodar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ✅ Acessar em http://localhost:8000/docs
```

### Opção 2: Com Docker (Recomendado)

```bash
# 1. Copiar .env
cp .env.example .env

# 2. Subir containers (Redis + API)
docker-compose up --build

# 3. API em http://localhost:8000
```

### Rodar Testes

```bash
# Todos os testes
pytest

# Com coverage
pytest --cov=app tests/

# Específico
pytest tests/test_auth.py -v
```

### Troubleshooting Comum

| Problema | Solução |
|----------|---------|
| "ODBC Driver 17 not found" | `apt install odbc-driver-17-for-sql-server` (Linux) ou baixar do site da MS |
| "Connection refused" em SQL | Chacar SQLSERVER_CONNECTION_STRING, firewall, IP |
| "LLM Server timeout" | Verificar se LLM Server está rodando em localhost:8001 ou desabilitar com SKIP_LLM_SERVER |
| "MSAL error" | Verificar AZURE_TENANT_ID, AZURE_CLIENT_ID,  |
| "Module not found" | Garantir que pip install rodou e venv está ativo |

---

## 📦 ENTREGÁVEIS PARA ESTA REUNIÃO

### ✅ O QUE TEMOS PRONTO

1. **API_EXAMPLES.http** - 50+ exemplos de chamadas (curl/REST Client)
2. **Documentação em Português**:
   - `PROJECT_OVERVIEW.md` - Arquitetura
   - `COMPLETE_DOCUMENTATION.md` - Tudo consolidado
   - `DOCUMENT_INGESTION.md` - Fluxo de ingestão
   - `FRONTEND_INTEGRATION.md` - Como frontend chama backend
   - `LLM_SERVER_ENDPOINTS.md` - Especificação de LLM Server
   - `CHAT_API.md` - API de chat
   - `MASTER_DATA_API.md` - Dados mestres

3. **Setup Local** - Tudo pronto (venv, Docker, requirements)

### ❌ O QUE NÃO TEMOS AINDA

1. **Postman Collection** (.json) - para importar no Postman/Insomnia
2. **Config Keys Document** - tabela de todas as variáveis de ambiente
3. **Run Local Step-by-Step** - guia passo a passo com troubleshooting
4. **Diagrama Visual** - fluxo em Mermaid ou imagem

### 📋 LEVAR PARA A REUNIÃO

```
✅ Laptop com Swagger UI aberta (http://localhost:8000/docs)
✅ API_EXAMPLES.http disponível
✅ Documentação em PDF/digital
✅ Demo: fazer chamada POST e mostrar resposta
✅ Mostrar código do router/service key
```

---

## 🎯 ESTRUTURA DA APRESENTAÇÃO (70 min)

| Tempo | Tópico | Formato |
|-------|--------|---------|
| 0-10 min | **Visão Geral (Backend)** | Slide + Swagger UI |
| 10-25 min | **Endpoints (Contratos)** | API_Examples.http + demo |
| 25-35 min | **Integrações** | Diagrama + explicação |
| 35-55 min | **LLM Integration** | Fluxo visual + código |
| 55-70 min | **Run Local** | Demo ao vivo |
| 70+ | **Q&A** | Painel |

---

## 📞 RESPOSTAS RÁPIDAS PARA O CLIENTE

**P: Que framework vocês usaram?**  
R: FastAPI + Python 3.11. É leve, rápido e perfeito para IA.

**P: Como vocês autenticam?**  
R: Azure Entra ID com MSAL. Cada usuário loga no Azure, backend valida com JWT.

**P: Como funciona a busca semântica?**  
R: Documentos são convertidos em embeddings (Azure OpenAI) e indexados no Azure AI Search. Busca por similitude de sentido, não apenas palavras-chave.

**P: Vocês rastreiam quem fez o quê?**  
R: Sim. Auditoria em `admin_audit_service.py`. Todo acesso tem log: quem, quando, o quê.

**P: Posso rodar isso localmente?**  
R: Sim! Com `pip install + uvicorn` ou `docker-compose up`. Leva 5 minutos.

**P: Qual é a segurança?**  
R: - JWT em cookie HTTPOnly
  - Entra ID para autenticação
  - RBAC (role-based) para autorização
  - Dados em Azure SQL (encrypted at rest)
  - Blobs em Blob Storage (também encrypted)

**P: E se o LLM Server falhar?**  
R: Tentamos 2 vezes com retry. Se falhar, retornamos erro ao usuário. Nada é perdido - usuário pode tentar de novo.

