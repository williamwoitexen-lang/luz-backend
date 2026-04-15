# DOCUMENTAÇÃO COMPLETA - Plataforma Luz

**Data**: 04 de Fevereiro de 2026  
**Versão**: 1.1  
**Status**: ✅ Completo

---

# 📋 ÍNDICE GERAL

1. [Visão Geral e Arquitetura](#visão-geral-e-arquitetura)
2. [Componentes do Sistema](#componentes-do-sistema)
3. [Fluxos Principais](#fluxos-principais)
4. [Autenticação](#autenticação)
5. [APIs de Chat](#apis-de-chat)
6. [APIs de Documentos](#apis-de-documentos)
7. [APIs de Dados Mestres](#apis-de-dados-mestres)
8. [Admin Management API](#admin-management-api)
9. [Prompts Management API](#prompts-management-api)
10. [Integração Frontend](#integração-frontend)
11. [Estrutura de Dados](#estrutura-de-dados)
12. [Deployment](#deployment)

---

# 1. VISÃO GERAL E ARQUITETURA

## O que é a Plataforma Luz?

**Luz** é uma plataforma segura de gerenciamento de documentos com integração de IA/LLM, autenticação Azure AD e busca semântica avançada.

## Stack Tecnológico
- **Backend**: FastAPI + Python 3.11
- **Frontend**: React/Angular (TypeScript)
- **Autenticação**: Azure Entra ID (OAuth2/MSAL)
- **Database**: SQL Server (Azure)
- **Storage**: Azure Blob Storage
- **LLM Server**: FastAPI (embeddings + semantic search)
- **Containerização**: Docker + Docker Compose

## Arquitetura Geral

```
┌─────────────┐         ┌──────────────┐         ┌────────────────┐
│  Frontend   │◄───────►│  Backend     │◄───────►│  LLM Server    │
│  (React)    │         │  (FastAPI)   │         │  (FastAPI)     │
└─────────────┘         └──────────────┘         └────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                ┌──────────┐      ┌──────────┐
                │ SQL Srv  │      │ Blob Svc │
                │          │      │ (Azure)  │
                └──────────┘      └──────────┘
```

---

# 2. COMPONENTES DO SISTEMA

## Backend (`/app`)

### Estrutura de Diretórios

```
app/
├── main.py                 # FastAPI principal
├── models.py              # Pydantic models
├── core/
│   ├── config.py          # Configurações
│   └── sqlserver.py       # Conexão SQL
├── providers/
│   ├── auth_msal.py       # Azure Entra ID
│   ├── llm_server.py      # Cliente LLM
│   ├── format_converter.py# Conversão de formatos
│   ├── storage.py         # Azure Blob
│   └── metadata_extractor.py
├── routers/
│   ├── auth.py            # Autenticação
│   ├── documents.py       # Gestão de docs
│   ├── chat.py            # Chat com LLM
│   ├── master_data.py     # Dados mestres
│   ├── dashboard.py       # Analytics
│   └── job_title_roles.py # Mapeamento cargos
├── services/
│   ├── document_service.py       # Orquestração
│   ├── sqlserver_documents.py    # SQL ops
│   ├── conversation_service.py   # Chat
│   └── job_title_role_service.py # Cargos
├── tasks/
│   └── cleanup_temp_uploads.py   # Background tasks
└── utils/
    └── helpers.py
```

### Componentes Principais

#### 1. **Provedores** (`/providers`)
- **auth_msal.py**: Autenticação via Azure Entra ID com MSAL
- **llm_server.py**: Cliente para comunicação com LLM Server
- **format_converter.py**: Converte PDF/DOCX/XLSX para CSV (extração de texto)
- **storage.py**: Interface com Azure Blob Storage
- **metadata_extractor.py**: Extração de metadados

#### 2. **Roteadores** (`/routers`)
- **auth.py**: Endpoints de login/logout
- **documents.py**: CRUD de documentos
- **chat.py**: Chat com LLM
- **master_data.py**: Localidades, cargos, categorias
- **dashboard.py**: Analytics e métricas

#### 3. **Serviços** (`/services`)
- **document_service.py**: Orquestração de ingestão
- **sqlserver_documents.py**: Operações diretas no SQL
- **conversation_service.py**: Gerenciamento de conversas

## Database (`/db`)

- `schema_sqlserver.sql` - Schema principal
- `schema_dimensions.sql` - Tabelas dimensão
- Migrations para evolução do schema

## Storage (`/storage`)

- `documents/` - Documentos permanentes
- `temp/` - Uploads temporários (expiram em 10 min)

## Testes (`/tests`)

- Unit tests
- Integration tests
- Fixtures compartilhadas

---

# 3. FLUXOS PRINCIPAIS

## Fluxo 1: Ingestão de Documentos

### Etapa 1: PREVIEW

```bash
POST /ingest-preview
├─ Upload arquivo
├─ Converte para CSV (extrai texto)
├─ Salva em __temp__ storage
├─ Chama LLM para extrair metadados
└─ Retorna temp_id + metadados sugeridos
```

**Request:**
```bash
POST /api/v1/documents/ingest-preview
Content-Type: multipart/form-data

file: documento.pdf
```

**Response:**
```json
{
  "status": "success",
  "temp_id": "uuid-xxx",
  "filename": "documento.pdf",
  "extracted_fields": {
    "min_role": "Manager",
    "countries": ["Brazil"],
    "cities": ["São Paulo"],
    "collar": "white",
    "confidence": "high"
  }
}
```

### Etapa 2: CONFIRM

```bash
POST /ingest-confirm/{temp_id}
├─ Recupera arquivo do __temp__
├─ Detecta formato (DOCX, PDF, XLSX, etc)
├─ Extrai texto corretamente por formato
├─ Limpa texto (remove binário, metadados)
├─ Trunca se > 50K chars
├─ Chama LLM FIRST (falha aqui = tudo falha)
├─ Salva em blob storage permanente
├─ Cria documento em SQL Server
├─ Cria versão (rastreia histórico)
└─ Deleta arquivo temporário
```

**Request:**
```bash
POST /api/v1/documents/ingest-confirm/{temp_id}
Content-Type: multipart/form-data

user_id: john_doe
min_role_level: 2
allowed_countries: Brazil,USA
allowed_cities: São Paulo
collar: white
plant_code: 123
```

**Response:**
```json
{
  "status": "success",
  "document_id": "uuid-xxx",
  "version": 1,
  "message": "Document ingested successfully"
}
```

### ⚠️ Documentos Inativos

Quando um documento é marcado com `is_active=false`:

```bash
POST /api/v1/documents/ingest
Content-Type: multipart/form-data

user_id: john_doe
is_active: false
file: documento.pdf
```

**Comportamento:**
- ✅ Versão é salva no SQL Server
- ✅ Arquivo é salvo no Blob Storage
- ❌ **NÃO é enviado para LLM Server** (não fica disponível no chat)

**Para reativar:**
```bash
POST /api/v1/documents/ingest
user_id: john_doe
document_id: existing_uuid
is_active: true
# Sem arquivo - apenas update de metadados
```

A última versão será re-ingestada no LLM automaticamente.

## Fluxo 2: Chat com LLM

```
Frontend
   ↓
POST /api/v1/chat/question
   ↓
Backend:
  1. Cria/obtém conversa
  2. Chama LLM Server: POST /api/v1/question
  3. Salva pergunta + resposta no banco
  4. Retorna resposta
   ↓
Frontend exibe resposta + documentos + agente
```

## Fluxo 3: Atualização de Metadados

```bash
POST /ingest (sem arquivo)
├─ Detecta mudanças (allowed_cities, category_id, etc)
├─ Se is_active=false → remove do LLM
├─ Se mudou metadados → re-ingesta no LLM
│  ├─ Recupera arquivo do blob
│  ├─ Converte para CSV
│  ├─ Reenvia para LLM com novos metadados
│  └─ LLM atualiza embeddings
└─ Retorna status
```

## Fluxo 4: Autenticação OAuth2

### FRONTEND LOGIN FLOW

```
1. POST /api/v1/login
   └─ Redireciona para Azure AD

2. Usuário loga em Azure
   └─ Azure redireciona para /api/v1/getatoken?code=...

3. Backend troca código por token
   ├─ Valida com MSAL
   ├─ Extrai user_id, email, roles
   └─ Seta cookies HTTPOnly

4. Redireciona para /app/chat
   └─ Frontend mantém session em cookie
```

### CADA REQUISIÇÃO

```
├─ Middleware valida JWT em cookie
├─ Se válido → passa request.state.user
└─ Se inválido → 401 Unauthorized
```

---

# 4. AUTENTICAÇÃO

## Azure Entra ID (OAuth2/MSAL)

### Fluxo de Token

1. **Redirecionamento para Azure AD**
   - URL gerada por MSAL
   - Scopes: `openid profile email offline_access https://graph.microsoft.com/User.Read`

2. **Troca de Código**
   - Azure retorna código de autorização
   - Backend usa MSAL para trocar por tokens

3. **Tokens Gerados**
   - `id_token` - JWT com user info
   - `access_token` - Token Graph para Microsoft Graph API
   - `refresh_token` - Para renovar tokens

4. **Armazenamento**
   - `session` cookie - HTTPOnly, Secure, SameSite=None
   - Contém `id_token` (valida requisições)
   - Expira junto com token

5. **Validação em Requisições**
   - Middleware intercepta
   - Lê JWT de cookie
   - Valida assinatura contra JWKS do Azure
   - Extrai claims (email, roles, oid)
   - Passa para `request.state.user`

### Segurança

- ✅ HTTPOnly cookies (JS não acessa)
- ✅ Secure flag (HTTPS only)
- ✅ SameSite=None (cross-site permitido)
- ✅ Validação de assinatura JWT
- ✅ Expiração de token

### Endpoints de Autenticação

- `GET /api/v1/login` - Iniciar login Azure
- `GET /api/v1/getatoken` - Callback Azure (interno)
- `GET /api/v1/logout` - Fazer logout
- `GET /api/v1/auth/status` - Status de autenticação

---

# 5. APIs DE CHAT

## 5.1 Fazer Pergunta e Obter Resposta

**POST** `/api/v1/chat/question`

**Request:**
```json
{
  "chat_id": "session_abc123",
  "user_id": "emp_12345",
  "name": "João Silva",
  "email": "joao.silva@company.com",
  "country": "Brazil",
  "city": "Sao Carlos",
  "roles": ["Employee"],
  "department": "TI",
  "job_title": "Analista de TI",
  "collar": "white",
  "unit": "Engineering",
  "question": "o que você pode me dizer sobre futebol?"
}
```

**Response:**
```json
{
  "answer": "Olá, João! 😊 Eu sou a Luz, assistente de RH...",
  "source_documents": [],
  "num_documents": 0,
  "classification": {
    "category": "general",
    "confidence": 0.9
  },
  "retrieval_time": 0,
  "llm_time": 1.03,
  "total_time": 1.85,
  "total_time_ms": 1849,
  "message_id": "02353418-913e-4acc-beb8-673597ff98d7",
  "provider": "azure_openai",
  "model": "gpt-4o-mini",
  "generated_at": "2026-01-09T16:42:20.446004Z",
  "rbac_filter_applied": "min_role_level le 1 AND ...",
  "documents_returned": 5,
  "documents_filtered": 3,
  "top_sources": ["health_benefits_brazil.pdf"],
  "agente": "general",
  "prompt_tokens": 419,
  "completion_tokens": 93
}
```

## 5.2 Listar Conversas

**GET** `/api/v1/chat/conversations/{user_id}?limit=50`

**Response:**
```json
[
  {
    "conversation_id": "conv_abc123",
    "user_id": "emp_12345",
    "title": "Benefícios de Saúde",
    "created_at": "2026-01-09T10:00:00",
    "updated_at": "2026-01-09T16:42:20",
    "is_active": true,
    "message_count": 5
  }
]
```

## 5.3 Obter Detalhes da Conversa

**GET** `/api/v1/chat/conversations/{conversation_id}/detail`

**Response:**
```json
{
  "conversation_id": "conv_abc123",
  "user_id": "emp_12345",
  "title": "Benefícios de Saúde",
  "created_at": "2026-01-09T10:00:00",
  "updated_at": "2026-01-09T16:42:20",
  "is_active": true,
  "rating": 4.5,
  "rating_timestamp": "2026-01-09T16:50:00",
  "rating_comment": "Resposta muito útil",
  "messages": [
    {
      "message_id": "msg_001",
      "conversation_id": "conv_abc123",
      "role": "user",
      "content": "Quais são os benefícios de saúde?",
      "model": null,
      "created_at": "2026-01-09T10:00:00"
    },
    {
      "message_id": "msg_002",
      "conversation_id": "conv_abc123",
      "role": "assistant",
      "content": "Os benefícios de saúde incluem plano Unimed...",
      "model": "gpt-4o-mini",
      "prompt_tokens": 450,
      "completion_tokens": 120,
      "created_at": "2026-01-09T10:00:02"
    }
  ]
}
```

## 5.4 Deletar Conversa

**DELETE** `/api/v1/chat/conversations/{conversation_id}`

**Response:**
```json
{
  "message": "Conversa deletada com sucesso",
  "conversation_id": "conv_abc123"
}
```

## 5.5 Avaliar Resposta (Rating)

**POST** `/api/v1/chat/{chat_id}/rate`

**Request:**
```json
{
  "rating": 4.5,
  "comment": "Resposta muito útil, mas faltou um detalhe"
}
```

**Parameters:**
- `chat_id`: ID da conversa
- `rating`: Nota de 0.0 a 5.0 em múltiplos de 0.5
- `comment`: Comentário opcional (obrigatório se rating = 1.0)

**Response:**
```json
{
  "conversation_id": "conv_abc123",
  "rating": 4.5,
  "comment": "Resposta muito útil, mas faltou um detalhe",
  "message": "Avaliação salva com sucesso"
}
```

**Notas:**
- Endpoint controlado 100% pelo frontend
- Sistema de rating automático foi removido
- Rating = 1.0 requer comentário obrigatório

---

# 6. APIs DE DOCUMENTOS

## 6.1 Ingerir Novo Documento

**POST** `/api/v1/documents/ingest`

**Request (modo novo):**
```bash
user_id: john_doe
file: documento.pdf
title: Benefícios de Saúde (opcional)
category_id: 5
is_active: true
min_role_level: 1
allowed_roles: Employee,Manager
allowed_countries: Brazil,USA
allowed_cities: São Paulo
collar: white
plant_code: 123
```

**Response:**
```json
{
  "status": "success",
  "document_id": 1,
  "version": 1,
  "chunks_count": 25,
  "blob_path": "https://storage.blob.core.windows.net/chat-rh/1/documento.pdf",
  "message": "Document ingested successfully"
}
```

## 6.2 Atualizar Versão de Documento

**POST** `/api/v1/documents/ingest`

**Request (com document_id):**
```bash
user_id: john_doe
document_id: 1
file: documento_v2.pdf
# Sistema cria versão 2
```

**Response:**
```json
{
  "status": "success",
  "document_id": 1,
  "version": 2,
  "message": "Document updated with new version"
}
```

## 6.3 Atualizar Apenas Metadados

**POST** `/api/v1/documents/ingest`

**Request (sem arquivo):**
```bash
user_id: john_doe
document_id: 1
is_active: true
# Apenas update, nenhuma versão criada
```

## 6.4 Listar Documentos

**GET** `/api/v1/documents?category_id=5&is_active=true`

**Response:**
```json
[
  {
    "document_id": 1,
    "title": "Benefícios de Saúde",
    "category_id": 5,
    "is_active": true,
    "min_role_level": 1,
    "created_at": "2026-01-09T10:00:00",
    "version_count": 2
  }
]
```

## 6.5 Obter Detalhes do Documento

**GET** `/api/v1/documents/{id}`

**Response:**
```json
{
  "document_id": 1,
  "title": "Benefícios de Saúde",
  "user_id": "john_doe",
  "category_id": 5,
  "category_name": "Saúde e Bem-Estar",
  "is_active": true,
  "min_role_level": 1,
  "allowed_roles": ["Employee", "Manager"],
  "allowed_countries": ["Brazil", "USA"],
  "allowed_cities": ["São Paulo"],
  "collar": "white",
  "plant_code": 123,
  "summary": "Documento que descreve os benefícios...",
  "versions": [
    {
      "version_number": 1,
      "blob_path": "...",
      "filename": "documento.pdf",
      "is_active": false,
      "created_at": "2026-01-09T10:00:00",
      "updated_by": "john_doe"
    },
    {
      "version_number": 2,
      "blob_path": "...",
      "filename": "documento_v2.pdf",
      "is_active": true,
      "created_at": "2026-01-15T14:30:00",
      "updated_by": "john_doe"
    }
  ]
}
```

## 6.6 Obter Todas as Versões

**GET** `/api/v1/documents/{id}/versions`

## 6.7 Deletar Versão

**DELETE** `/api/v1/documents/{id}/versions/{version}`

## 6.8 Download de Documento

**GET** `/api/v1/documents/{id}/download`

- Retorna arquivo com extension preservada
- Suporta caracteres especiais em nomes (RFC 5987)

---

# 7. APIs DE DADOS MESTRES

**IMPORTANTE**: API somente leitura (GET apenas).

## 7.1 API de Localidades

### Obter Todas as Localidades

```
GET /api/v1/master-data/locations
?country=Brazil&region=LATAM&active_only=true
```

### Obter Todos os Países

```
GET /api/v1/master-data/countries
?active_only=false
```

**Países Disponíveis**: Brasil, Argentina, Chile, México, USA, Suécia, Itália, Polônia, Hungria, França, Espanha, Reino Unido, China, Tailândia, Índia, Austrália

### Obter Estados por País

```
GET /api/v1/master-data/states-by-country/Brazil
```

### Obter Cidades por País

```
GET /api/v1/master-data/cities-by-country/Brazil
```

### Obter Cidades por Região

```
GET /api/v1/master-data/cities-by-region/LATAM
```

### Obter Hierarquia Completa

```
GET /api/v1/master-data/hierarchy
```

**Regiões Disponíveis:**
- LATAM (América do Sul) - Ativa
- NA (América do Norte) - Pré-preenchida
- EMEA (Europa/Oriente Médio/África) - Pré-preenchida
- APAC (Ásia Pacífico) - Pré-preenchida

## 7.2 API de Categorias

### Obter Todas as Categorias

```
GET /api/v1/master-data/categories
```

**Categorias Pré-preenchidas** (13):
1. Admissão
2. Folha de Pagamento
3. Férias e Ausências
4. Jornada e Ponto
5. Saúde e Bem-Estar
6. Desenvolvimento e Carreira
7. Movimentações Internas
8. Políticas e Normas
9. Diversidade e Inclusão
10. Segurança da Informação
11. Relações Trabalhistas
12. Desligamento
13. RH Geral

### Obter Detalhes da Categoria

```
GET /api/v1/master-data/categories/{category_id}
```

## 7.3 API de Funções

### Obter Todas as Funções

```
GET /api/v1/master-data/roles
```

**Funções Pré-preenchidas** (15):
1. Analista
2. Aprendiz
3. Assistente
4. Coordenador
5. Diretor
6. Especialista
7. Estagiário
8. Gerente
9. Gerente Sênior
10. Head
11. Operacional
12. Presidente
13. Supervisor
14. Técnico
15. Vice-Presidente

### Obter Detalhes da Função

```
GET /api/v1/master-data/roles/{role_id}
```

---

# 8. INTEGRAÇÃO FRONTEND

> 📄 **Documentação Frontend**: Ver repositório do Frontend para detalhes completos de implementação, componentes, tipos TypeScript e exemplos de código.

## Fluxo de Comunicação

```
Frontend (Angular/React)
    ↓
POST /api/v1/chat/question
    ↓
Backend (FastAPI)
├─ Cria/obtém conversa no banco
├─ Chama LLM Server: POST /api/v1/question
├─ Salva pergunta + resposta no banco
└─ Retorna resposta ao frontend
    ↓
Frontend exibe resposta + agente + documentos
```

## Endpoints Utilizados

O frontend consome os seguintes endpoints do backend:

### Chat
- `POST /api/v1/chat/question` - Fazer pergunta
- `GET /api/v1/chat/conversations/{user_id}` - Listar conversas
- `GET /api/v1/chat/conversations/{conversation_id}/detail` - Detalhes da conversa
- `DELETE /api/v1/chat/conversations/{conversation_id}` - Deletar conversa
- `POST /api/v1/chat/{chat_id}/rate` - Avaliar resposta

### Documentos
- `POST /api/v1/documents/ingest-preview` - Preview de upload
- `POST /api/v1/documents/ingest-confirm/{temp_id}` - Confirmar ingestão
- `GET /api/v1/documents` - Listar documentos
- `GET /api/v1/documents/{id}` - Detalhes do documento
- `GET /api/v1/documents/{id}/download` - Download

### Dados Mestres
- `GET /api/v1/master-data/countries` - Países
- `GET /api/v1/master-data/categories` - Categorias
- `GET /api/v1/master-data/roles` - Funções
- `GET /api/v1/master-data/hierarchy` - Hierarquia completa

### Autenticação
- `GET /api/v1/login` - Iniciar login
- `GET /api/v1/getatoken` - Callback (interno)
- `GET /api/v1/logout` - Fazer logout
- `GET /api/v1/auth/status` - Status autenticação

## Considerações para Integração

1. **CORS**: Configurar `CORS_ORIGINS` com URL do frontend
2. **Cookies**: Token armazenado em HTTPOnly cookie
3. **Timeout**: Chat pode levar até 300s (esperar resposta LLM)
4. **Retry**: Sistema já retenta automaticamente em erros

---

# 9. ESTRUTURA DE DADOS

## Tabela: `conversations`

```sql
CREATE TABLE conversations (
    conversation_id NVARCHAR(36) PRIMARY KEY,
    user_id NVARCHAR(255) NOT NULL,
    document_id INT,
    title NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    is_active BIT DEFAULT 1,
    rating FLOAT,                           -- 0.0 a 5.0
    rating_timestamp DATETIME2,
    rating_comment NVARCHAR(MAX),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_rating (rating)
);
```

## Tabela: `conversation_messages`

```sql
CREATE TABLE conversation_messages (
    message_id NVARCHAR(36) PRIMARY KEY,
    conversation_id NVARCHAR(36) NOT NULL,
    user_id NVARCHAR(255) NOT NULL,
    role NVARCHAR(50) NOT NULL,             -- 'user' ou 'assistant'
    content NVARCHAR(MAX) NOT NULL,
    tokens_used INT,
    model NVARCHAR(100),
    retrieval_time FLOAT,
    llm_time FLOAT,
    total_time FLOAT,
    document_categories_used NVARCHAR(MAX), -- JSON
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_user_id (user_id)
);
```

## Tabela: `documents`

```sql
CREATE TABLE documents (
    document_id INT PRIMARY KEY,
    title NVARCHAR(255),
    user_id NVARCHAR(255),
    category_id INT,
    is_active BIT DEFAULT 1,
    min_role_level INT,
    allowed_roles NVARCHAR(MAX),            -- JSON
    allowed_countries NVARCHAR(MAX),        -- JSON
    allowed_cities NVARCHAR(MAX),           -- JSON
    collar NVARCHAR(50),
    plant_code INT,
    summary NVARCHAR(MAX),
    created_at DATETIME2,
    updated_at DATETIME2,
    FOREIGN KEY (category_id) REFERENCES dim_categories(category_id),
    INDEX idx_user_id (user_id),
    INDEX idx_category_id (category_id),
    INDEX idx_is_active (is_active)
);
```

## Tabela: `versions`

```sql
CREATE TABLE versions (
    version_id NVARCHAR(36) PRIMARY KEY,
    document_id INT,
    version_number INT,
    blob_path NVARCHAR(500),
    filename NVARCHAR(255),
    file_type NVARCHAR(10),                 -- pdf, docx, xlsx, etc
    is_active BIT,
    created_at DATETIME2,
    updated_by NVARCHAR(255),               -- Quem fez upload
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    UNIQUE (document_id, version_number),
    INDEX idx_document_id (document_id)
);
```

## Tabela: `dim_categories`

```sql
CREATE TABLE dim_categories (
    category_id INT PRIMARY KEY,
    category_name NVARCHAR(255),
    description NVARCHAR(MAX),
    is_active BIT,
    INDEX idx_category_name (category_name)
);
```

---

# 10. DEPLOYMENT

## Ambientes

- **Local**: `docker-compose.yml`
- **Azure**: Container Apps + SQL Server + Blob Storage

## Variáveis de Ambiente

```bash
# Azure AD
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
=...

# URLs
APP_BASE_URL_BACKEND=https://backend.example.com
APP_BASE_URL_FRONTEND=https://frontend.example.com

# LLM Server (com Retry Logic)
LLM_SERVER_URL=https://llm-server.example.com
LLM_SERVER_TIMEOUT=300                # Timeout em segundos
LLM_SERVER_MAX_RETRIES=3              # Máximo de tentativas
LLM_SERVER_RETRY_DELAY=1              # Delay inicial (exponential backoff)

# Blob Storage
AZURE_STORAGE_ACCOUNT_NAME=...
AZURE_STORAGE_ACCOUNT_KEY=...

# SQL Server
DB_HOST=sql-server.example.com
DB_NAME=luz_db
DB_USER=admin
DB_PASSWORD=...

# CORS
CORS_ORIGINS=https://frontend.example.com

# Features
SKIP_LLM_SERVER=false
SKIP_LLM_METADATA_EXTRACTION=false
```

### LLM Server - Retry Logic

O cliente LLM Server possui retry automático com exponential backoff para aumentar a resiliência:

**Comportamento:**
- ✅ Retenta automaticamente em **connection errors** (timeout, conexão recusada)
- ✅ Retenta em **5xx server errors** (problema temporário no LLM Server)
- ❌ Não retenta em **4xx client errors** (erro na requisição - não adianta repetir)
- ✅ **Exponential backoff**: Delay dobra a cada tentativa (1s → 2s → 4s)

**Exemplo de log:**
```
[Retry] Connection error to LLM Server: ConnectionError. Retrying in 1s... (attempt 1/3)
[Retry] Connection error to LLM Server: ConnectionError. Retrying in 2s... (attempt 2/3)
[Retry] Successfully connected on attempt 3
```

**Configuração padrão:**
- 3 tentativas máximas
- 1 segundo de delay inicial
- Aplicado em: `ingest_document()` e `ask_question()`

Customize ajustando as variáveis `LLM_SERVER_MAX_RETRIES` e `LLM_SERVER_RETRY_DELAY`.

## Build & Deploy Local

```bash
docker-compose up
```

## Deploy Azure

```bash
az containerapp create \
  --resource-group myresourcegroup \
  --name luz-backend \
  --image containerregistry.azurecr.io/luz:latest \
  --environment mycontainerenv
```

---

## Tratamento de Erros

| Erro | Causa | Solução |
|------|-------|--------|
| 422 Unprocessable Entity | Texto > 50K chars | Backend trunca automaticamente |
| 500 LLM connection error | LLM Server offline | Subir LLM Server ou usar SKIP_LLM_SERVER=true |
| 500 LLM timeout | LLM Server lento | Aumentar LLM_SERVER_TIMEOUT |
| 400 Bad request | Arquivo inválido | Verificar arquivo enviado |
| 404 Not found | Documento não existe | Verificar document_id |
| 401 Unauthorized | Token expirado | Fazer login novamente |

---

## Logging

- **Level**: INFO por padrão
- **Output**: stdout (Docker)
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Tags Úteis

```
[ingest_confirm] Formato docx detectado
[ingest_confirm] Texto processado: 250K -> 50K chars
[ingest_confirm] ✅ Enviado para LLM Server com sucesso
[chat_question] Chamando LLM Server
[chat_question] Resposta salva: conversation_id=conv_123
```

---

## Próximas Melhorias

- [ ] Migrations automáticas de schema
- [ ] Rate limiting
- [ ] Audit log completo
- [ ] Métricas Prometheus
- [ ] Health checks robustos
- [ ] Suporte a S3 em paralelo

---

**Data de Última Atualização**: 04 de Fevereiro de 2026  
**Versão**: 1.1  
**Status**: ✅ Completo e Consolidado
