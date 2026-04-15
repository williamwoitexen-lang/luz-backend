# 📚 DOCUMENTAÇÃO INTEGRADA - Plataforma Luz

**Versão**: 2.1  
**Data de Atualização**: 27 de Março de 2026  
**Status**: ✅ Documentação Completa e Consolidada  
**Idioma**: Português Brasileiro  

---

## 📋 ÍNDICE EXECUTIVO

1. [Visão Geral da Plataforma](#visão-geral-da-plataforma)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Stack Tecnológico](#stack-tecnológico)
4. [Componentes Principais](#componentes-principais)
5. [Fluxos de Negócio](#fluxos-de-negócio)
6. [Autenticação e Segurança](#autenticação-e-segurança)
7. [APIs Completas](#apis-completas)
8. [Configuração e Variáveis de Ambiente](#configuração-e-variáveis-de-ambiente)
9. [Banco de Dados e Migrações](#banco-de-dados-e-migrações)
10. [Guias de Uso e Integração](#guias-de-uso-e-integração)
11. [Solução de Problemas](#solução-de-problemas)
12. [Referência Rápida](#referência-rápida)

---

# VISÃO GERAL DA PLATAFORMA

## O que é Luz?

**Luz** é uma plataforma segura de **gerenciamento de documentos com integração de IA**, desenvolvida para empresas como a Eletrolux. A plataforma permite que colaboradores façam perguntas sobre documentos corporativos (políticas de RH, benefícios, procedimentos) e recebam respostas precisas através de um assistente de IA avançado.

## Principais Funcionalidades

✅ **Upload e Gerenciamento de Documentos**
- Ingestão de documentos em múltiplos formatos (PDF, DOCX, XLSX)
- Versionamento automático com rastreamento de histórico
- Armazenamento seguro em Azure Blob Storage
- Extração automática de metadados com IA

✅ **Chat Inteligente com IA**
- Busca semântica em documentos
- Respostas contextualizadas com inteligência artificial
- Histórico completo de conversas
- Streaming de respostas em tempo real (SSE)
- Sistema de avaliação e feedback

✅ **Controle de Acesso Baseado em Papéis (RBAC)**
- Autenticação via Azure Entra ID (OAuth2)
- Filtros de acesso por país, cidade, departamento
- Gestão granular de permissões
- Auditoria completa de operações

✅ **Gerenciamento Administrativo**
- Sistema de admins com permissões específicas
- Gerenciamento de prompts de IA por agente
- Preferências de usuário e personalização
- Dashboard com métricas de uso

## Benefícios Corporativos

- **Redução de Tempo**: Respostas instantâneas em vez de buscar em múltiplos documentos
- **Consistência**: Informações sempre atualizadas e consistentes
- **Segurança**: Controle granular quem vê o quê
- **Escalabilidade**: Funciona com centenas de documentos
- **Analytics**: Métricas de uso e perguntas frequentes

---

# ARQUITETURA DO SISTEMA

## Visão Geral da Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│                     Frontend (React/Angular)                  │
├──────────────────────────────────────────────────────────────┤
│                           │                                    │
│                    HTTPS/API Gateway                          │
│                           │                                    │
├──────────────────────────────────────────────────────────────┤
│              Backend FastAPI (Python 3.11)                    │
│    ┌────────────────────────────────────────────────┐         │
│    │  Routers (14 aplicações)                       │         │
│    │  - Auth, Documents, Chat                       │         │
│    │  - Dashboard, Master Data, Admin               │         │
│    └────────────────────────────────────────────────┘         │
│                           │                                    │
│    ┌────────────────────────────────────────────────┐         │
│    │  Services (16 componentes)                     │         │
│    │  - document_service, conversation_service      │         │
│    │  - llm_integration, admin_service              │         │
│    └────────────────────────────────────────────────┘         │
│                           │                                    │
│    ┌────────────────────────────────────────────────┐         │
│    │  Providers                                     │         │
│    │  - auth (MSAL), storage (Azure Blob)           │         │
│    │  - llm_server, database (pyodbc)               │         │
│    └────────────────────────────────────────────────┘         │
├──────────────────────────────────────────────────────────────┤
│         Camada de Integração com Serviços Azure               │
│  ┌─────────────────┬──────────────┬──────────────┐           │
│  │   SQL Server    │  Blob Storage │ Azure Search │           │
│  │   (Banco)       │  (Arquivos)   │ (Semântica) │           │
│  └─────────────────┴──────────────┴──────────────┘           │
│  ┌──────────────┬───────────────┬──────────────┐             │
│  │ Entra ID     │ OpenAI (IA)   │ LLM Server   │             │
│  │ (Auth)       │ (Embeddings)   │ (Chat)       │             │
│  └──────────────┴───────────────┴──────────────┘             │
└──────────────────────────────────────────────────────────────┘
```

## Stack Tecnológico

### Backend
- **Framework**: FastAPI 0.104+ (Python 3.11)
- **Servidor**: Uvicorn 0.24+
- **Validação**: Pydantic 2.5+
- **Database**: Python pyodbc + SQL Server
- **Storage**: Azure SDK para Blob Storage
- **Autenticação**: MSAL (Microsoft Authentication Library)

### Frontend
- **Framework**: React ou Angular (TypeScript)
- **Autenticação**: MSAL.js (Microsoft Authentication Library)
- **Requisições**: Axios ou Fetch API

### Serviços Azure
- **Azure SQL Database**: Armazenamento de metadados
- **Azure Blob Storage**: Armazenamento de arquivos
- **Azure Entra ID**: Autenticação central
- **Azure OpenAI**: Modelos de IA (GPT-4o, GPT-4o-mini)
- **Azure AI Search**: Busca semântica com embeddings

### Ferramentas Adicionais
- **Docker/Docker Compose**: Containerização
- **Redis**: Cache distribuído
- **Celery**: Task queue para processamento assincronado

---

# COMPONENTES PRINCIPAIS

## Backend (`/app`)

### Estrutura de Diretórios

```
app/
├── main.py                          # FastAPI principal
├── models.py                        # Modelos Pydantic
│
├── routers/                         # 14 aplicações de endpoints
│   ├── auth.py                      # Login, logout, autenticação
│   ├── documents.py                 # Ingestão e gestão de documentos
│   ├── chat.py                      # Chat com IA
│   ├── dashboard.py                 # Analytics e relatórios
│   ├── master_data.py              # Localidades, cargos, categorias
│   ├── admin.py                     # Gerenciamento de admins
│   ├── prompts.py                   # Gerenciamento de prompts
│   ├── user_preferences.py          # Preferências de usuário
│   ├── job_title_roles.py          # Mapeamento cargo-permissão
│   ├── e42_evaluation.py           # Avaliação de funcionários
│   └── ...                          # + 4 mais
│
├── services/                        # 16 componentes de lógica
│   ├── document_service.py          # Orquestração de ingestão
│   ├── conversation_service.py      # Gerenciamento de conversas
│   ├── sqlserver_documents.py       # Operações diretas SQL
│   ├── admin_service.py             # Lógica de admin
│   ├── task_queue.py                # Fila de tarefas local
│   └── ...
│
├── providers/                       # Adapters para serviços
│   ├── auth_msal.py                 # Azure Entra ID
│   ├── storage.py                   # Azure Blob Storage
│   ├── llm_server.py                # Integração LLM
│   ├── metadata_extractor.py        # Extração de metadados
│   └── format_converter.py          # Conversão de formatos
│
├── core/                            # Compartilhado
│   ├── config.py                    # Configurações e KeyVault
│   ├── sqlserver.py                 # Conexão SQL Server
│   ├── logging_config.py            # Setup de logs
│   └── exceptions.py                # Exceções customizadas
│
├── tasks/                           # Processamento assincronado
│   ├── celery_app.py                # Celery + Redis
│   └── tasks.py                     # Definição de tasks
│
└── utils/                           # Utilitários
    ├── helpers.py                   # Funções auxiliares
    └── temp_storage.py              # Armazenamento temporário
```

### Padrão de 5 Camadas

```
HTTP Layer (FastAPI)
        ↓
  Routers (Endpoints)
        ↓
  Services (Lógica)
        ↓
  Providers (Adapters)
        ↓
  External Services (Azure, LLM)
```

## Database (`/db`)

### Arquivos Principais
- `schema.sql` - Schema principal com todas as tabelas
- `schema_dimensions.sql` - Tabelas de dimensão (países, cidades, cargos)
- `schema_seed.sql` - Dados iniciais
- Migrations - 25+ arquivos incrementais com ALTER TABLE

### Tabelas Principais

#### documents
- Armazena metadados de documentos
- Campos: document_id, title, category_id, allowed_countries, allowed_cities, min_role_level, etc
- Suporta soft-delete com is_active

#### versions
- Histórico de versões de cada documento
- Rastreia qual arquivo está no Azure Blob
- Permite rollback e comparação de versões

#### conversations
- Armazena conversas de chat por usuário
- Links para conversation_messages

#### conversation_messages
- Cada mensagem do chat (user ou assistant)
- Rastreia tokens, modelo LLM usado, tempo de resposta

#### admins
- Usuários com privilégios administrativos
- Associação com agentes e features

#### user_preferences
- Preferências personalizadas por usuário
- Idioma preferido, memory_preferences (JSON)

## Storage (`/storage`)

```
storage/
├── documents/
│   ├── {document_id}/
│   │   ├── 1/                       # Versão 1
│   │   │   └── documento.pdf
│   │   ├── 2/                       # Versão 2
│   │   │   └── documento.pdf
│   │   └── ...
│   └── ...
└── temp/
    ├── {temp_id}/
    │   └── uploaded_file.ext        # Expiram em 10 min
```

---

# FLUXOS DE NEGÓCIO

## Fluxo 1: Ingestão de Documentos (2 Passos)

### Etapa 1: Preview (Extração de Metadados)

```
POST /api/v1/documents/ingest-preview
Content-Type: multipart/form-data

Arquivo: documento.pdf
       │
       ├─ Detecta formato (PDF, DOCX, XLSX)
       ├─ Extrai texto com FormatConverter
       ├─ Limpa texto (remove binário, metadados)
       ├─ Trunca se > 50K caracteres
       ├─ Salva em storage/temp/{temp_id}/
       └─ Chamada ao LLM para extrair metadados
            ├─ Extrai campos sugeridos:
            │  ├─ allowed_countries
            │  ├─ allowed_cities
            │  ├─ min_role_level
            │  └─ category_id
            └─ Retorna confidence score
       
Response:
{
  "temp_id": "uuid",
  "filename": "documento.pdf",
  "extracted_fields": {
    "countries": ["Brazil"],
    "cities": ["São Paulo"],
    "min_role": "Manager"
  }
}
```

**Comportamento**:
- Arquivo armazenado temporariamente por 10 minutos
- Usuário revisa metadados sugeridos
- Se não confirmar, arquivo expira automaticamente

### Etapa 2: Confirm (Ingestão Definitiva)

```
POST /api/v1/documents/ingest-confirm/{temp_id}
Content-Type: multipart/form-data

user_id: emp_12345
allowed_countries: Brazil,USA
allowed_cities: São Paulo
min_role_level: 2
category_id: 5
       │
       ├─ [1] Recupera arquivo do temp storage
       ├─ [2] Valida metadados
       ├─ [3] CHAMA LLM FIRST (falha aqui = tudo falha)
       │       └─ Gera embeddings
       │       └─ Indexa no Azure AI Search
       ├─ [4] INSERT documento no SQL Server
       ├─ [5] INSERT versão (documento_id, version=1, blob_path)
       ├─ [6] Move arquivo temp → permanent
       │       storage/{document_id}/1/documento.pdf
       └─ [7] Delete arquivo temp
       
Response:
{
  "document_id": "uuid",
  "version": 1,
  "status": "ingested"
}
```

**Pontos Críticos**:
- ⚠️ LLM DEVE ter sucesso ou toda operação falha
- ✅ Arquivo é movido para permanent só após sucesso no LLM
- ✅ Metadados são validados antes de processar

### Documentos Inativos

```
POST /api/v1/documents/ingest
is_active: false
       │
       ├─ Versão é SALVA no SQL Server ✅
       ├─ Arquivo é SALVO no Blob Storage ✅
       └─ ❌ NÃO é enviado para LLM
               (não fica disponível no chat)

Para reativar:
POST /api/v1/documents/ingest
document_id: existing_uuid
is_active: true
       │
       └─ Última versão é re-ingestada no LLM ✅
```

## Fluxo 2: Chat com IA

```
Usuário: "Quais benefícios temos?"
       │
       ├─ Frontend envia: POST /api/v1/chat/question
       │
       ├─ Backend:
       │  [1] Valida autenticação (JWT em cookie)
       │  [2] Cria/obtém conversa no banco
       │  [3] Chama LLM Server: POST /api/v1/question
       │      ├─ Busca documentos relevantes (semântica)
       │      ├─ Aplica filtros RBAC:
       │      │  ├─ País do usuário IN allowed_countries
       │      │  ├─ Cidade do usuário IN allowed_cities
       │      │  └─ Função user >= min_role_level
       │      ├─ Passa documentos como contexto
       │      └─ Chama GPT-4o com prompt
       │  [4] INSERT pergunta no banco
       │  [5] INSERT resposta no banco
       │  [6] Retorna resposta com metadados
       │
       └─ Frontend:
          ├─ Exibe resposta
          ├─ Mostra documentos relacionados
          └─ Permite avaliar resposta (rating)
```

**Características**:
- Busca é SEMÂNTICA (não por palavras-chave)
- Cada conversa tem histórico persistente
- Aplicação de RBAC garante segurança dos dados
- Tempo típico: 1-3 segundos

## Fluxo 3: Autenticação OAuth2

```
[1] Frontend → Backend
    GET /api/v1/login
       ├─ Backend gera URL Azure AD
       └─ Redireciona para:
          https://login.microsoftonline.com/{tenant}/oauth2/authorize?...

[2] Usuário loga em Azure AD
       └─ Azure redireciona com código:
          http://localhost:3000/auth/callback?code=ABC123

[3] Frontend → Backend
    GET /api/v1/getatoken?code=ABC123
       ├─ Backend troca código por tokens (via MSAL)
       ├─ Extrai user_id, email, roles
       ├─ Cria JWT interno
       ├─ Seta cookie HTTPOnly
       └─ Redireciona para /app/chat

[4] Cada Requisição
    ├─ Browser envia cookie HTMLOnly automaticamente
    ├─ Backend valida JWT no middleware
    ├─ Se válido: passa request.state.user
    └─ Se inválido: retorna 401 Unauthorized

[5] Logout
    DELETE /api/v1/logout
       └─ Limpa cookie HTTPOnly
```

**Segurança**:
- HTTPOnly: JavaScript não consegue acessar token
- Secure: HTTPS-only em produção
- SameSite: CSRF protection
- Validação: Assinatura JWT verificada contra JWKS do Azure

---

# AUTENTICAÇÃO E SEGURANÇA

## Sistema de Autenticação (MSAL + JWT)

### Tokens Gerados
1. **id_token** (Azure AD): JWT com informações do usuário
2. **access_token** (Azure AD): Token para chamar Microsoft Graph
3. **refresh_token** (Azure AD): Para renovar tokens expirados
4. **JWT Interno** (Backend): Token de sessão da app

### Fluxo Detalhado

```
1. POST /login → Redireciona para Azure AD
2. Usuário autentica em Azure
3. Azure redireciona com ?code=...
4. Backend troca código por tokens
5. Backend cria JWT interno
6. Cookie HTTPOnly setado com JWT
7. Próximas requisições incluem cookie automaticamente
```

### Validação JWT

```python
# Cada request:
token = request.cookies.get("jwt")
payload = jwt.decode(token, key=secret, algorithms=["HS256"])
# Valida assinatura e expiração
```

## Controle de Acesso (RBAC)

### Filtros de Documento

```
Documento pode ser acessado SE:
✓ user.country IN document.allowed_countries
✓ user.city IN document.allowed_cities (if set)
✓ user.role_level >= document.min_role_level

Exemplo:
document = {
  allowed_countries: ["Brazil", "USA"],
  allowed_cities: ["São Paulo", "Rio de Janeiro"],
  min_role_level: 2
}

user1 = { country: "Brazil", city: "São Paulo", role_level: 3 } ✓ Acesso
user2 = { country: "Brazil", city: "Brasília", role_level: 3 } ✗ Sem acesso (city)
user3 = { country: "Brazil", city: "São Paulo", role_level: 1 } ✗ Sem acesso (role)
```

### Roles Pré-definidos

1. **Admin** - Gerenciar sistema, ver tudo
2. **Manager** - Gerenciar equipe, acessar dados do team
3. **Employee** - Acessar documentos públicos + pessoais
4. **Viewer** - Somente leitura

## Encriptação

### Em Trânsito
- HTTPS 1.2+ obrigatório
- TLS 1.3 em produção

### Em Repouso
- SQL Server: Transparent Data Encryption (TDE)
- Azure Blob Storage: Service-Side Encryption (Microsoft-managed keys)
- Redis: Encriptado se necessário

---

# APIs COMPLETAS

## 1. APIs de Autenticação

### Login
```
GET /api/v1/login

• Sem parâmetros
• Redireciona para Azure AD
• Response: Redirect para https://login.microsoftonline.com/...
```

### Get Token (Callback)
```
GET /api/v1/getatoken?code={auth_code}

• Callback automático do Azure
• Troca código por JWT
• Sets HTTPOnly cookie
• Response: Redirect para /app/chat
```

### Check Status
```
GET /api/v1/auth/status

Response:
{
  "authenticated": true,
  "user_id": "emp_12345",
  "email": "user@company.com",
  "roles": ["Employee", "Manager"],
  "expires_at": "2026-03-27T12:00:00Z"
}
```

### Logout
```
GET /api/v1/logout

• Limpa cookie HTTPOnly
• Response: JSON com mensagem de logout
```

## 2. APIs de Documentos

### Ingestão - Preview
```
POST /api/v1/documents/ingest-preview
Content-Type: multipart/form-data

Body:
- file: (binary) documento.pdf

Response (200):
{
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

Response (400):
{
  "detail": "Arquivo não suportado"
}
```

### Ingestão - Confirm
```
POST /api/v1/documents/ingest-confirm/{temp_id}
Content-Type: multipart/form-data

Body:
- user_id: emp_12345
- min_role_level: 2
- allowed_countries: Brazil,USA
- allowed_cities: São Paulo
- category_id: 5
- collar: white
- plant_code: 123

Response (201):
{
  "document_id": "uuid-xxx",
  "version": 1,
  "status": "ingested"
}
```

### Ingestão - Direto
```
POST /api/v1/documents/ingest
Content-Type: multipart/form-data

Body:
- file: documento.pdf
- user_id: emp_12345
- allowed_countries: Brazil
- category_id: 5
- (metadata...)

Response (201):
{
  "document_id": "uuid",
  "version": 1
}
```

### Listar Documentos
```
GET /api/v1/documents?limit=10&offset=0

Response:
{
  "documents": [
    {
      "document_id": "uuid",
      "title": "Benefícios de Saúde",
      "category": "Health",
      "version": 2,
      "created_at": "2026-03-20T10:00:00Z",
      "updated_at": "2026-03-27T14:30:00Z"
    }
  ],
  "total": 245
}
```

### Obter Detalhes
```
GET /api/v1/documents/{document_id}

Response:
{
  "document_id": "uuid",
  "title": "Benefícios",
  "category": "Health",
  "summary": "Resumo gerado por IA",
  "versions": [
    {
      "version": 1,
      "created_at": "2026-03-20T10:00:00Z",
      "filename": "beneficios.pdf"
    },
    {
      "version": 2,
      "created_at": "2026-03-27T14:30:00Z",
      "filename": "beneficios_v2.pdf"
    }
  ],
  "allowed_countries": ["Brazil"],
  "allowed_cities": ["São Paulo", "Curitiba"],
  "min_role_level": 2
}
```

### Download de Documento
```
GET /api/v1/documents/{document_id}/download?version_number=2

Response:
- Content-Type: application/pdf
- Arquivo binário

Sem version_number: retorna versão mais recente
```

### Deletar Versão
```
DELETE /api/v1/documents/{document_id}/versions/{version_number}

Response (204):
- Sucesso (sem body)
```

## 3. APIs de Chat

### Fazer Pergunta
```
POST /api/v1/chat/question

Body:
{
  "chat_id": "session_abc123",
  "user_id": "emp_12345",
  "name": "João Silva",
  "email": "joao@company.com",
  "country": "Brazil",
  "city": "São Paulo",
  "roles": ["Employee"],
  "department": "TI",
  "job_title": "Analista",
  "collar": "white",
  "unit": "Engineering",
  "question": "Quais benefícios temos?"
}

Response (200):
{
  "answer": "Temos os seguintes benefícios...",
  "source_documents": [
    {
      "title": "Benefícios de Saúde",
      "source": "health_benefits.pdf"
    }
  ],
  "message_id": "msg_xyz",
  "total_time_ms": 1849,
  "prompt_tokens": 419,
  "completion_tokens": 93,
  "agente": "general"
}
```

### Chat com Streaming (SSE)
```
POST /api/v1/chat/question/stream

Body: Mesmo do /question

Response Stream (SSE):
data: {"event":"token","token":"A"}\n\n
data: {"event":"token","token":" "}\n\n
data: {"event":"token","token":"política"}\n\n
...
data: {"event":"complete","answer":"Resposta completa..."}\n\n

Cliente JavaScript:
const eventSource = new EventSource('/api/v1/chat/question/stream');
eventSource.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.event === 'token') {
    responseDiv.textContent += data.token;
  }
};
```

### Listar Conversas
```
GET /api/v1/chat/conversations/{user_id}?limit=50

Response:
{
  "conversations": [
    {
      "conversation_id": "conv_abc",
      "title": "Benefícios de Saúde",
      "created_at": "2026-03-20T10:00:00Z",
      "updated_at": "2026-03-27T14:30:00Z",
      "message_count": 5
    }
  ]
}
```

### Detalhes da Conversa
```
GET /api/v1/chat/conversations/{conversation_id}/detail

Response:
{
  "conversation_id": "conv_abc",
  "messages": [
    {
      "role": "user",
      "content": "Quais benefícios?",
      "created_at": "2026-03-20T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Temos...",
      "model": "gpt-4o-mini",
      "prompt_tokens": 419,
      "completion_tokens": 93,
      "created_at": "2026-03-20T10:00:02Z"
    }
  ]
}
```

### Avaliar Resposta
```
POST /api/v1/chat/{chat_id}/rate

Body:
{
  "rating": 4.5,
  "comment": "Resposta útil mas incompleta"
}

Response:
{
  "conversation_id": "conv_abc",
  "rating": 4.5,
  "comment": "Resposta útil...",
  "message": "Avaliação salva com sucesso"
}

Nota: Rating é controlado 100% pelo frontend
```

## 4. APIs de Dados Mestres (Somente Leitura)

### Localidades
```
GET /api/v1/master-data/locations

Response:
[
  {
    "location_id": 8,
    "country": "Brazil",
    "state": "Curitiba",
    "city": "Curitiba",
    "region": "LATAM"
  }
]
```

### Países
```
GET /api/v1/master-data/countries

Response:
[
  { "country_id": 1, "country": "Brazil" },
  { "country_id": 2, "country": "Argentina" }
]
```

### Cidades por País
```
GET /api/v1/master-data/cities-by-country/Brazil

Response:
[
  { "city": "São Paulo", "state": "SP", "region": "LATAM" },
  { "city": "Rio de Janeiro", "state": "RJ", "region": "LATAM" }
]
```

### Categorias
```
GET /api/v1/master-data/categories

Response:
[
  { "category_id": 1, "name": "Saúde", "description": "Benefícios de saúde" },
  { "category_id": 2, "name": "Férias", "description": "Políticas de férias" }
]
```

### Papéis/Funções
```
GET /api/v1/master-data/roles

Response:
[
  { "role_id": 1, "name": "Analista" },
  { "role_id": 2, "name": "Gerente" },
  { "role_id": 3, "name": "Diretor" }
]
```

## 5. API de Gerenciamento de Admins

### Inicializar Primeiro Admin (Bootstrap)
```
POST /api/v1/admins/init

Body:
{
  "email": "admin@company.com",
  "agent_id": 1,
  "feature_ids": [1, 2]
}

Response (201):
{
  "admin_id": "uuid",
  "email": "admin@company.com",
  "agent_id": 1,
  "agent_name": "LUZ",
  "is_active": true,
  "features": [...]
}

Nota: Sem autenticação necessária (apenas 1x no setup)
```

### Criar Novo Admin
```
POST /api/v1/admins

Auth: ✓ Requerida (admin)

Body:
{
  "email": "newadmin@company.com",
  "agent_id": 2,
  "feature_ids": [1]
}

Response (201):
{...admin...}
```

### Listar Admins
```
GET /api/v1/admins

Auth: ✓ Requerida (admin)

Response:
{
  "admins": [...],
  "total": 5
}
```

### Atualizar Admin
```
PATCH /api/v1/admins/{admin_id}

Auth: ✓ Requerida (admin)

Body:
{
  "agent_id": 3,
  "feature_ids": [1, 2, 3]
}

Response (200):
{...admin atualizado...}
```

### Deletar Admin
```
DELETE /api/v1/admins/{admin_id}

Auth: ✓ Requerida (admin)

Response (204): Sem body
```

## 6. API de Gerenciamento de Prompts

### Criar Prompt
```
POST /api/v1/prompts

Auth: ✓ Requerida (admin)

Body:
{
  "agente": "LUZ",
  "system_prompt": "Você é um assistente de RH especializado em..."
}

Response (201):
{
  "prompt_id": 1,
  "agente": "LUZ",
  "system_prompt": "Você é...",
  "version": 1,
  "created_at": "2026-03-20T10:00:00Z"
}
```

### Listar Prompts
```
GET /api/v1/prompts

Auth: ✓ Requerida

Response:
[
  { "agente": "LUZ", "version": 1, "system_prompt": "..." },
  { "agente": "IGP", "version": 2, "system_prompt": "..." }
]
```

### Obter Prompt por Agente
```
GET /api/v1/prompts/{agente}

Auth: ✓ Requerida

Response:
{
  "agente": "LUZ",
  "system_prompt": "Você é...",
  "version": 1
}
```

### Atualizar Prompt
```
PUT /api/v1/prompts/{agente}

Auth: ✓ Requerida (admin)

Body:
{
  "system_prompt": "Nova versão do prompt..."
}

Response (200):
{
  "agente": "LUZ",
  "system_prompt": "Nova versão...",
  "version": 2,  # ← Incrementado automaticamente
  "updated_at": "2026-03-27T14:30:00Z"
}

Nota: Auto-sincroniza com LLM Server com retry
```

### Deletar Prompt
```
DELETE /api/v1/prompts/{agente}

Auth: ✓ Requerida (admin)

Response (204): Sem body
```

## 7. API de Preferências de Usuário

### Obter Preferências
```
GET /api/v1/user/preferences/{user_id}

Auth: ✓ Requerida

Response:
{
  "user_id": "emp_12345",
  "preferred_language": "pt-BR",
  "memory_preferences": {
    "max_history_lines": 4,
    "summary_enabled": true
  }
}
```

### Atualizar Preferências
```
POST /api/v1/user/preferences/{user_id}

Auth: ✓ Requerida

Body:
{
  "preferred_language": "en-US",
  "memory_preferences": { ... }
}

Response (200):
{...preferências atualizadas...}
```

### PATCH Memory Preferences
```
PATCH /api/v1/user/preferences/{user_id}/memory

Auth: ✓ Requerida

Body:
{
  "max_history_lines": 6,
  "summary_enabled": false
}

Response (200):
{...apenas memory_preferences...}
```

## 8. API de Dashboard

### Resumo de Conversas
```
GET /api/v1/chat/dashboard/summary?start_date=2026-03-01&end_date=2026-03-30

Auth: ✓ Requerida

Response:
{
  "period": { "start_date": "2026-03-01", "end_date": "2026-03-30" },
  "conversations": {
    "total": 1245,
    "active": 987,
    "average_per_user": 12.5
  },
  "messages": {
    "total": 5432,
    "average_per_conversation": 4.4
  },
  "llm_usage": {
    "total_tokens": 1275000,
    "models_used": {
      "gpt-4-turbo": { "count": 2850, "tokens": 680000 }
    },
    "cost_estimates": { "total_estimated": 44.25 }
  },
  "performance": {
    "avg_response_time_ms": 2145,
    "p95_response_time_ms": 4200,
    "success_rate": 98.5
  }
}
```

### Detalhes de Conversas
```
GET /api/v1/chat/dashboard/detailed?limit=10&offset=0

Auth: ✓ Requerida

Response:
{
  "conversations": [
    {
      "id": "conv_123",
      "user_id": "alice",
      "title": "Benefícios",
      "message_count": 24,
      "tokens": { "input": 45000, "output": 22500 },
      "avg_response_time_ms": 2100
    }
  ]
}
```

### Exportar Dashboard
```
GET /api/v1/chat/dashboard/export?format=csv&start_date=2026-03-01

Auth: ✓ Requerida

Response:
- CSV com todas as conversas
- Ou JSON conforme formato solicitado
```

## 9. API de Avaliação 4x2 (E42)

### Obter Avaliação Completa
```
POST /api/v1/e42/evaluation

Body:
{
  "user_email": "employee@company.com",
  "identificator": "104"
}

Response (200):
{
  "user_email": "employee@company.com",
  "user_id": "user123",
  "weaknesses": [
    { "comment": "teste8", "selection": "GR: Learning ability" }
  ],
  "strengths": [
    { "comment": "teste2", "selection": "EN: Leading others" }
  ],
  "total_evaluations": 6
}
```

### Obter Apenas Fraquezas
```
POST /api/v1/e42/evaluation/weaknesses-only

Body:
{
  "user_email": "employee@company.com",
  "identificator": "104"
}

Response (200):
{
  "weaknesses": ["teste8", "test7"]
}
```

## 10. APIs de Debug e Teste

### Health Check Ambiente
```
GET /api/v1/debug/env

Response:
{
  "environment": {
    "database": { "connection_status": "✅ Connected" },
    "storage": { "connection_status": "✅ Connected" },
    "llm": { "connection_status": "⚠️ Timeout" }
  }
}
```

### Listar Agentes
```
GET /api/v1/debug/agents

Response:
{
  "agents": [
    { "agent_id": 1, "code": "LUZ", "is_active": true },
    { "agent_id": 2, "code": "IGP", "is_active": true }
  ]
}
```

### Health Check LLM
```
GET /api/v1/debug/llm-health

Response:
{
  "llm_server": {
    "url": "http://llm-server:8001",
    "connection": "✅ Connected",
    "response_time_ms": 125
  }
}
```

## 11. Stress Testing

### Executar Teste de Carga
```
POST /api/v1/chat/stress-test

Body:
{
  "num_requests": 50,
  "concurrency": 10,
  "timeout_seconds": 30
}

Response (200):
{
  "test_id": "stress_test_abc123",
  "summary": {
    "total_requests": 50,
    "successful_requests": 50,
    "total_duration_seconds": 4.5,
    "throughput_requests_per_second": 11.11
  },
  "latency": {
    "min_ms": 245.6,
    "max_ms": 587.3,
    "p95_ms": 550.1,
    "p99_ms": 580.4
  },
  "ttft": {
    "min_ms": 45.2,
    "max_ms": 120.5,
    "p95_ms": 105.2
  },
  "requests": [...]
}
```

---

# CONFIGURAÇÃO E VARIÁVEIS DE AMBIENTE

## Variáveis Obrigatórias (Críticas)

| Variável | Tipo | Origem | Sensível |
|----------|------|--------|----------|
| `AZURE_TENANT_ID` | UUID | KeyVault | ⚠️ Não |
| `AZURE_CLIENT_ID` | UUID | KeyVault | ⚠️ Não |
| `AZURE_CLIENT_SECRET` | String | KeyVault | 🔴 **SIM** |
| `SQLSERVER_CONNECTION_STRING` | String | KeyVault | 🔴 **SIM** |
| `AZURE_STORAGE_CONNECTION_STRING` | String | KeyVault | 🔴 **SIM** |
| `LLM_SERVER_URL` | URL | AppSettings | ⚠️ Não |
| `AZURE_OPENAI_KEY` | API Key | KeyVault | 🔴 **SIM** |

## Variáveis Recomendadas

| Variável | Default | Descrição |
|----------|---------|-----------|
| `AZURE_STORAGE_ACCOUNT_NAME` | chat-rh | Nome da storage account |
| `AZURE_STORAGE_CONTAINER_NAME` | chat-rh | Container de documentos |
| `AZURE_SEARCH_API_KEY` | (required) | Chave Azure AI Search |
| `LLM_SERVER_TIMEOUT` | 30 | Timeout em segundos |

## Variáveis Opcionais

| Variável | Default | Descrição |
|----------|---------|-----------|
| `APP_ENV` | dev | dev, staging, prod |
| `DEBUG_MODE` | false | Ativar endpoints debug |
| `SKIP_LLM_SERVER` | false | Desabilitar LLM (testes) |
| `SKIP_LLM_METADATA_EXTRACTION` | false | Pular extração com LLM |
| `CORS_ORIGINS` | localhost | Origens CORS permitidas |
| `USE_PYODBC_MOCK` | false | Usar mock do pyodbc |
| `REDIS_HOST` | localhost | Host do Redis |
| `REDIS_PORT` | 6379 | Porta do Redis |

## Configuração por Ambiente

### Desenvolvimento Local
```bash
# .env
APP_ENV=dev
AZURE_TENANT_ID=xxxxx
AZURE_CLIENT_ID=yyyyy
AZURE_CLIENT_SECRET=zzzzz
SQLSERVER_CONNECTION_STRING=...
AZURE_STORAGE_CONNECTION_STRING=...
AZURE_OPENAI_KEY=...
SKIP_LLM_SERVER=true  # Desabilitar para testes rápidos
USE_PYODBC_MOCK=false
LLM_SERVER_URL=http://localhost:8001
CORS_ORIGINS=http://localhost:3000,http://localhost:4200
```

### Staging
```bash
# Azure Pipeline injeta automaticamente do KeyVault
APP_ENV=staging
SKIP_LLM_SERVER=false
LLM_SERVER_URL=https://staging-llm.internal
CORS_ORIGINS=https://staging-app.company.com
```

### Produção
```bash
# Azure Pipeline injeta automaticamente do KeyVault
APP_ENV=prod
SKIP_LLM_SERVER=false
LLM_SERVER_URL=https://prod-llm.internal
CORS_ORIGINS=https://app.company.com
LLM_SERVER_TIMEOUT=60
```

---

# BANCO DE DADOS E MIGRAÇÕES

## Modelo de Dados Principal

### Tabela: documents
```sql
CREATE TABLE documents (
  document_id VARCHAR(36) PRIMARY KEY,
  title VARCHAR(255),
  category_id INT,
  summary TEXT,
  allowed_countries VARCHAR(500),  -- CSV: BR,US,MX
  allowed_cities VARCHAR(1000),    -- CSV: SP,RJ
  min_role_level INT DEFAULT 1,
  collar VARCHAR(50),              -- white, blue, all
  plant_code INT,
  created_at DATETIME DEFAULT GETDATE(),
  created_by VARCHAR(255),
  updated_at DATETIME,
  updated_by VARCHAR(255),
  is_active BIT DEFAULT 1
);
```

### Tabela: versions
```sql
CREATE TABLE versions (
  version_id VARCHAR(36) PRIMARY KEY,
  document_id VARCHAR(36) NOT NULL,
  version_number INT NOT NULL,
  file_path VARCHAR(500),           -- blob://container/path
  filename VARCHAR(255),            -- nome original
  created_at DATETIME DEFAULT GETDATE(),
  created_by VARCHAR(255),
  updated_by VARCHAR(255),
  status VARCHAR(20) DEFAULT 'active',
  FOREIGN KEY (document_id) REFERENCES documents(document_id)
);
```

### Tabela: conversations
```sql
CREATE TABLE conversations (
  conversation_id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  title VARCHAR(500),
  status VARCHAR(20) DEFAULT 'open',
  created_at DATETIME DEFAULT GETDATE(),
  updated_at DATETIME,
  message_count INT DEFAULT 0
);
```

### Tabela: conversation_messages
```sql
CREATE TABLE conversation_messages (
  message_id VARCHAR(36) PRIMARY KEY,
  conversation_id VARCHAR(36) NOT NULL,
  user_id VARCHAR(255),
  role VARCHAR(20),                 -- user, assistant
  content VARCHAR(MAX),
  model_used VARCHAR(50),
  prompt_tokens INT,
  completion_tokens INT,
  response_time_ms INT,
  created_at DATETIME DEFAULT GETDATE(),
  FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);
```

### Tabela: admins
```sql
CREATE TABLE admins (
  admin_id INT PRIMARY KEY IDENTITY,
  user_id VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) NOT NULL,
  agent_id INT,
  role VARCHAR(50) DEFAULT 'support',
  created_at DATETIME DEFAULT GETDATE(),
  created_by VARCHAR(255),
  updated_at DATETIME,
  updated_by VARCHAR(255),
  is_active BIT DEFAULT 1
);
```

### Tabela: user_preferences
```sql
CREATE TABLE user_preferences (
  user_id VARCHAR(255) PRIMARY KEY,
  preferred_language VARCHAR(10) DEFAULT 'pt-BR',
  memory_preferences NVARCHAR(MAX),  -- JSON
  last_update DATETIME DEFAULT GETDATE()
);
```

## Histórico de Migrações

25+ migrações incrementais aplicadas em orden:
1. Schema base (documents, versions, chunks)
2. Tabela de admins
3. Roles permitidas (allowed_roles)
4. Categorias de documentos
5. Mapeamento cargo-papel
6. Update timestamps e auditoria
7. Preferências de usuário
8. Dashboard views
9. ... e mais

## Como Aplicar Migrações

### Local (Docker)
```bash
# Iniciar serviços
docker-compose up

# Aplicar schema e seed
docker-compose exec api python db/run_schema.py
```

### Azure (CI/CD Pipeline)
```bash
# Pipeline automaticamente executa:
sqlcmd -S your-server.database.windows.net -U user -P pwd -d luz_db -i db/add_*.sql
```

---

# GUIAS DE USO E INTEGRAÇÃO

## Guia: Como Rodar Localmente

### Pre-requisitos
- Python 3.11+
- pip + venv
- ODBC Driver 18 para SQL Server
- Git

### Instalação Passo a Passo

**1. Clone o Repositório**
```bash
git clone <repo-url>
cd Embeddings
```

**2. Criar Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou: .\venv\Scripts\activate  # Windows
```

**3. Instalar Dependências**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Configurar .env**
```bash
cp .env.example .env
nano .env  # Editar com suas credenciais Azure
```

**5. Rodar Servidor**
```bash
# Sem LLM (mais rápido para testes)
SKIP_LLM_SERVER=true uvicorn app.main:app --reload --port 8000

# Com LLM
uvicorn app.main:app --reload --port 8000
```

**6. Testar**
```bash
# Em novo terminal
curl http://localhost:8000/
# Acessar Swagger UI: http://localhost:8000/docs
```

## Guia: Fazer Upload de Documento

### Via API

**1. Preview (Extração de Metadados)**
```bash
curl -X POST http://localhost:8000/api/v1/documents/ingest-preview \
  -F "file=@documento.pdf" \
  -H "Authorization: Bearer <token>"

# Resposta:
{
  "temp_id": "abc123",
  "extracted_fields": {
    "countries": ["Brazil"],
    "cities": ["São Paulo"]
  }
}
```

**2. Confirm (Ingestão Definitiva)**
```bash
curl -X POST http://localhost:8000/api/v1/documents/ingest-confirm/abc123 \
  -F "user_id=emp_12345" \
  -F "allowed_countries=Brazil" \
  -F "allowed_cities=São Paulo" \
  -H "Authorization: Bearer <token>"
```

### Via Postman
1. Importar `docs/Luz-API.postman_collection.json`
2. Selecionar request "Ingest Preview"
3. Escolher arquivo em "Body → Binary"
4. Click "Send"

## Guia: Fazer uma Pergunta ao Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat/question \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "session_1",
    "user_id": "emp_12345",
    "name": "João Silva",
    "email": "joao@company.com",
    "country": "Brazil",
    "city": "São Paulo",
    "roles": ["Employee"],
    "department": "TI",
    "job_title": "Analista",
    "collar": "white",
    "unit": "Engineering",
    "question": "Quais benefícios temos?"
  }'
```

## Guia: Integração Frontend

### Autenticação com MSAL

```typescript
// frontend/src/auth.service.ts
import { PublicClientApplication } from '@azure/msal-browser';

const msalConfig = {
  auth: {
    clientId: 'YOUR_CLIENT_ID',
    authority: 'https://login.microsoftonline.com/YOUR_TENANT_ID',
    redirectUri: 'http://localhost:3000/auth/callback'
  }
};

const pca = new PublicClientApplication(msalConfig);

async function login() {
  const loginResponse = await pca.loginPopup({
    scopes: ['openid', 'profile', 'email']
  });
  
  const token = loginResponse.accessToken;
  // Usar token em requisições à API
}
```

### Chamar API de Chat

```typescript
async function askQuestion(question: string) {
  const response = await fetch('/api/v1/chat/question', {
    method: 'POST',
    credentials: 'include',  // Envia cookies
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      chat_id: 'session_1',
      user_id: currentUser.id,
      name: currentUser.name,
      email: currentUser.email,
      country: 'Brazil',
      city: 'São Paulo',
      roles: currentUser.roles,
      question: question
    })
  });
  
  const data = await response.json();
  return data.answer;
}
```

### Streaming de Resposta

```typescript
async function askQuestionStreaming(question: string) {
  const eventSource = new EventSource(
    `/api/v1/chat/question/stream?q=${encodeURIComponent(JSON.stringify({...}))}`
  );
  
  let completeAnswer = '';
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.event === 'token') {
      // Exibir token (efeito de digitação)
      responseElement.textContent += data.token;
    } else if (data.event === 'complete') {
      completeAnswer = data.answer;
      eventSource.close();
    }
  };
}
```

## Guia: Gerenciar Admins

### Inicializar Primeiro Admin (Setup)

```bash
# Sem autenticação necessária (uma única vez)
curl -X POST http://localhost:8000/api/v1/admins/init \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "agent_id": 1,
    "feature_ids": [1, 2]
  }'
```

### Criar Novo Admin

```bash
curl -X POST http://localhost:8000/api/v1/admins \
  -H "Authorization: Bearer <token>" \
  -d '{
    "email": "newadmin@company.com",
    "agent_id": 2,
    "feature_ids": [1]
  }'
```

### Adicionar Feature a Admin

```bash
curl -X POST http://localhost:8000/api/v1/admins/{admin_id}/features/3 \
  -H "Authorization: Bearer <token>"
```

## Guia: Gerenciar Prompts

### Criar Novo Prompt

```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Authorization: Bearer <token>" \
  -d '{
    "agente": "LUZ",
    "system_prompt": "Você é um assistente de RH especializado..."
  }'
```

### Atualizar Prompt (Incrementa Versão)

```bash
curl -X PUT http://localhost:8000/api/v1/prompts/LUZ \
  -H "Authorization: Bearer <token>" \
  -d '{
    "system_prompt": "Nova versão v2 do prompt..."
  }'

# version é incrementado automaticamente (1 → 2 → 3...)
```

---

# SOLUÇÃO DE PROBLEMAS

## Erro: "ModuleNotFoundError: No module named 'pyodbc'"

**Causa**: Dependências não instaladas

**Solução**:
```bash
source venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

## Erro: "ODBC Driver 17/18 not found"

**Causa**: Driver ODBC para SQL Server não está instalado

**Solução (Linux)**:
```bash
sudo apt update
sudo apt install -y odbc-driver-18-for-sql-server
odbcinst -q -l -d  # Verificar
```

**Solução (macOS)**:
```bash
brew tap microsoft/mssql-release
brew install mssql-tools18
```

**Solução (Windows)**:
- Baixar installer: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
- Executar .msi installer
- **REINICIAR Windows**

## Erro: "Connection refused" (SQL Server)

**Causa**: SQL Server offline ou firewall bloqueando

**Solução**:
```bash
# Testar conexão
sqlcmd -S your-server.database.windows.net -U user -P password

# Se Azure SQL, adicionar firewall rule:
az sql server firewall-rule create \
  --server my-server \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

## Erro: "Connection refused" (LLM Server)

**Causa**: LLM Server está offline

**Solução**:
```bash
# Dev: Desabilitar LLM
SKIP_LLM_SERVER=true uvicorn app.main:app --reload

# Ou iniciar LLM Server
python -m llm_server.main
```

## Erro: "Variável AZURE_CLIENT_SECRET não definida"

**Causa**: Variável falta no .env

**Solução**:
```bash
grep AZURE_CLIENT_SECRET .env
# Se vazio:
echo "AZURE_CLIENT_SECRET=<seu-valor>" >> .env
```

## Erro: "LLM Server timeout"

**Causa**: LLM está lento ou timeout pequeno demais

**Solução**:
```bash
# Aumentar timeout
LLM_SERVER_TIMEOUT=60 uvicorn app.main:app --reload

# Ou em .env:
LLM_SERVER_TIMEOUT=60
```

## Erro: "Port 8000 already in use"

**Causa**: Outro processo usando porta 8000

**Solução**:
```bash
# Ver processo
lsof -i :8000

# Matar
kill -9 <PID>

# Ou rodar em porta diferente
uvicorn app.main:app --port 8001
```

## Erro: "ImportError" ao atualizar requirements

**Causa**: pip cache corrompido

**Solução**:
```bash
pip cache purge
pip install --force-reinstall -r requirements.txt
```

## Erro: "401 Unauthorized" em endpoints

**Causa**: JWT expirado ou cookie não enviado

**Solução**:
```bash
# 1. Fazer login novamente
curl http://localhost:8000/api/v1/login

# 2. Verificar se cookie foi setado
curl -v http://localhost:8000/api/v1/auth/status

# 3. Usar -b (cookies) em curl
curl -b cookies.txt http://localhost:8000/api/v1/documents
```

## Erro: "422 Unprocessable Entity" na ingestão

**Causa**: Arquivo muito grande (> 50KB de texto)

**Solução**:
```bash
# Backend trunca automaticamente
# Mas se falhar:
# 1. Dividir documento em partes
# 2. Upload cada parte separadamente
```

## Erro: LLM retorna "Invalid request format"

**Causa**: Prompt tem caracteres inválidos

**Solução**:
```bash
# Verificar encoding
file documento.txt
# Se não UTF-8:
iconv -f latin1 -t utf-8 documento.txt > documento_utf8.txt
```

## Debug: Verificar que tudo está conectado

```bash
# 1. Health check
curl http://localhost:8000/

# 2. Debug environment
curl http://localhost:8000/api/v1/debug/env | jq '.'

# 3. Listar agentes
curl http://localhost:8000/api/v1/debug/agents

# 4. Health LLM
curl http://localhost:8000/api/v1/debug/llm-health
```

---

# REFERÊNCIA RÁPIDA

## Endpoints Mais Comuns

| Operação | Método | URL | Auth |
|----------|--------|-----|------|
| Login | GET | `/api/v1/login` | ❌ |
| Upload Preview | POST | `/api/v1/documents/ingest-preview` | ✅ |
| Confirmar Upload | POST | `/api/v1/documents/ingest-confirm/{temp_id}` | ✅ |
| Listar Documentos | GET | `/api/v1/documents` | ✅ |
| Baixar Documento | GET | `/api/v1/documents/{id}/download` | ✅ |
| Fazer Pergunta | POST | `/api/v1/chat/question` | ✅ |
| Chat Streaming | POST | `/api/v1/chat/question/stream` | ✅ |
| Listar Conversas | GET | `/api/v1/chat/conversations/{user_id}` | ✅ |
| Avaliar Resposta | POST | `/api/v1/chat/{chat_id}/rate` | ✅ |
| Listar Localidades | GET | `/api/v1/master-data/locations` | ✅ |
| Listar Categories | GET | `/api/v1/master-data/categories` | ✅ |
| Init Admin | POST | `/api/v1/admins/init` | ❌ |
| Criar Prompt | POST | `/api/v1/prompts` | ✅ Admin |
| Atualizar Prompt | PUT | `/api/v1/prompts/{agente}` | ✅ Admin |
| Dashboard Summary | GET | `/api/v1/chat/dashboard/summary` | ✅ |
| Stress Test | POST | `/api/v1/chat/stress-test` | ⚠️ |

## Códigos HTTP Comuns

| Código | Significado | Ação |
|--------|-------------|------|
| 200 | ✅ Sucesso | Solicitar processou com sucesso |
| 201 | ✅ Criado | Recurso foi criado |
| 204 | ✅ Sem conteúdo | Sucesso sem resposta |
| 400 | ❌ Bad Request | Dados inválidos - verificar input |
| 401 | ❌ Unauthorized | Faz login ou renova token |
| 403 | ❌ Forbidden | Dados sem permissão |
| 404 | ❌ Not Found | Recurso não existe |
| 422 | ❌ Unprocessable | Validação falhou |
| 429 | ❌ Too Many Requests | Rate limit - aguarde |
| 500 | ❌ Internal Server | Erro no backend - ver logs |
| 502 | ❌ Bad Gateway | LLM Server offline |
| 503 | ❌ Unavailable | Server em manutenção |

## Modelos de Request Comuns

### Request de Chat
```json
{
  "chat_id": "session_1",
  "user_id": "emp_12345",
  "name": "João Silva",
  "email": "joao@company.com",
  "country": "Brazil",
  "city": "São Paulo",
  "roles": ["Employee"],
  "department": "TI",
  "job_title": "Analista",
  "collar": "white",
  "unit": "Engineering",
  "question": "Pergunta aqui?"
}
```

### Response de Chat
```json
{
  "answer": "Resposta aqui...",
  "source_documents": [
    { "title": "Doc1", "source": "doc1.pdf" }
  ],
  "total_time_ms": 1234,
  "prompt_tokens": 419,
  "completion_tokens": 93
}
```

## Variáveis de Ambiente Rápidas

```bash
# Dev Rápido (sem LLM ou Database)
SKIP_LLM_SERVER=true
USE_PYODBC_MOCK=true
REDIS_HOST=localhost

# Production
SKIP_LLM_SERVER=false
DEBUG_MODE=false
APP_ENV=prod

# Troubleshooting
DEBUG_MODE=true
LLM_SERVER_TIMEOUT=60
```

## Dicas de Troubleshooting Rápido

**Erro de autenticação?**
→ Verificar JWT em browser dev tools (Application → Cookies → jwt)

**Documento não aparece no chat?**
→ Verificar allowed_countries, allowed_cities, min_role_level

**LLM não responde?**
→ Checar `GET /api/v1/debug/llm-health`

**Documentos deletados aparecem?**
→ Verificar is_active=false (soft delete)

**Performance lenta?**
→ Rodar `POST /api/v1/chat/stress-test` para ver baseline

**Confuso sobre qual endpoint?**
→ Acessar `http://localhost:8000/docs` (Swagger UI)

---

## 📍 Resumo Executivo

**Luz** é uma plataforma enterprise de gerenciamento inteligente de documentos. Utiliza Azure como infraestrutura, FastAPI como backend, e IA avançada para proporcionar experiência de chat natural com acesso a documentos corporativos.

- ✅ 11 categorias de APIs documentadas
- ✅ Multi-tenant com RBAC granular
- ✅ Busca semântica com IA
- ✅ Armazenamento seguro e escalável
- ✅ Auditoria completa de operações

**Para começar**: Consulte [Guia: Como Rodar Localmente](#guia-como-rodar-localmente)

**Para integrar**:  Consulte [Guia: Integração Frontend](#guia-integração-frontend)

---

**Documentação Consolidada - Versão 2.1**  
**Apresentação Consolidada e Traduzida para Português Brasileiro**  
**Pronta para exportar para Word ou PDF**  
**Data: 27 de Março de 2026**
