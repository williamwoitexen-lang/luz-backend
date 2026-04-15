# Luz - Secure Document & Identity Platform

**Visão Geral**: Platform de gerenciamento seguro de documentos com integração de IA (LLM), autenticação Azure AD e busca semântica.

## 📋 Índice
1. [Arquitetura](#arquitetura)
2. [Componentes](#componentes)
3. [Fluxos Principais](#fluxos-principais)
4. [APIs](#apis)
5. [Autenticação](#autenticação)
6. [Deployment](#deployment)

---

## Arquitetura

### Visão Geral
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

### Stack Tecnológico
- **Backend**: FastAPI + Python 3.11
- **Frontend**: React (TypeScript)
- **Autenticação**: Azure Entra ID (OAuth2/MSAL)
- **Database**: SQL Server (Azure)
- **Storage**: Azure Blob Storage
- **LLM Server**: FastAPI (embeddings + semantic search)
- **Containerização**: Docker + Docker Compose

---

## Componentes

### 1. **Backend** (`/app`)

#### Core
- `main.py` - Aplicação FastAPI principal
- `models.py` - Modelos Pydantic

#### Provedores (`/providers`)
- `auth_msal.py` - Autenticação Azure Entra ID com MSAL
- `auth.py` - Backup/alternativa de auth
- `llm_server.py` - Cliente para comunicação com LLM Server
- `format_converter.py` - Converte PDF/DOCX/XLSX para CSV (extração de texto)
- `storage.py` - Interface com Azure Blob Storage
- `metadata_extractor.py` - Extração de metadados

#### Roteadores (`/routers`)
- `auth.py` - `/api/v1/login`, `/api/v1/logout`, `/api/v1/auth/status`
- `documents.py` - `/api/v1/documents/*` (CRUD de documentos)
- `chat.py` - `/api/v1/chat/*` (chat com LLM)
- `master_data.py` - `/api/v1/master-data/*` (localizações, cargos, categorias)
- `dashboard.py` - `/api/v1/dashboard/*` (analytics)
- `job_title_roles.py` - `/api/v1/job-title-roles/*` (mapeamento de cargos)

#### Serviços (`/services`)
- `document_service.py` - Orquestração: blob storage + SQL + LLM Server
- `sqlserver_documents.py` - Operações SQL Server (CRUD)
- `job_title_role_service.py` - Gestão de cargos e roles

#### Core (`/core`)
- `sqlserver.py` - Conexão e execução SQL
- `config.py` - Configurações da aplicação

#### Tasks (`/tasks`)
- `cleanup_temp_uploads.py` - Background task para limpeza de uploads temp

**Nota**: Sistema de rating automático foi removido. Avaliação é controlada exclusivamente pelo frontend via endpoints dedicados.

### 2. **Database** (`/db`)
- `schema_sqlserver.sql` - Schema principal
- `schema_dimensions.sql` - Tabelas dimensão (cargos, categorias, etc)
- Migrations (vários `.sql` para evolução do schema)

### 3. **Storage** (`/storage`)
- `documents/` - Documentos permanentes
- `temp/` - Uploads temporários (expiram em 10 min)

### 4. **Testes** (`/tests`)
- Unit tests
- Integration tests
- Fixtures compartilhadas

### 5. **Documentação** (`/docs`)
- Guias de API
- Fluxos de integração
- Deployment

---

## Fluxos Principais

### 1️⃣ Fluxo de Ingestão de Documentos

```
ETAPA 1: PREVIEW
  POST /ingest-preview
  ├─ Upload arquivo
  ├─ Converte para CSV (extrai texto)
  ├─ Salva em __temp__ storage
  ├─ Chama LLM para extrair metadados
  └─ Retorna temp_id + metadados sugeridos

ETAPA 2: CONFIRM
  POST /ingest-confirm/{temp_id}
  ├─ Recupera arquivo do __temp__
  ├─ Detecta formato (DOCX, PDF, XLSX, etc)
  ├─ Extrai texto corretamente por formato:
  │  ├─ DOCX/XLSX → usa FormatConverter
  │  └─ PDF/TXT → decode UTF-8
  ├─ Limpa texto (remove binário, metadados)
  ├─ Trunca se > 50K chars (limite LLM)
  ├─ Chama LLM FIRST (falha aqui = tudo falha)
  ├─ Salva em blob storage permanente
  ├─ Cria documento em SQL Server
  ├─ Cria versão (rastreia histórico)
  └─ Deleta arquivo temporário

ETAPA 3: LISTAGEM
  GET /documents
  ├─ Busca do SQL Server
  ├─ Parse JSON fields (roles, cities)
  ├─ Resolve filename vazio
  │  └─ Usa: title + extensão detectada
  └─ Retorna com filtros opcionais
```

### 2️⃣ Fluxo de Chat com LLM

```
POST /chat/ask
├─ Valida autenticação (middleware)
├─ Busca contexto de documentos relevantes
├─ Chama LLM Server com:
│  ├─ Pergunta do usuário
│  ├─ Documentos relevantes
│  ├─ Contexto de usuário (role, país, cidade)
│  └─ Histórico de conversa
└─ Retorna resposta com referências
```

### 3️⃣ Fluxo de Atualização de Metadados

```
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

### 4️⃣ Fluxo de Autenticação

```
FRONTEND LOGIN FLOW:
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

CADA REQUISIÇÃO:
  ├─ Middleware valida JWT em cookie
  ├─ Se válido → passa request.state.user
  └─ Se inválido → 401 Unauthorized
```

---

## APIs

### Documentos
- `POST /api/v1/documents/ingest-preview` - Preview com metadados
- `POST /api/v1/documents/ingest-confirm/{temp_id}` - Confirmar ingestão
- `POST /api/v1/documents/ingest` - Ingerir direto OU atualizar metadados
- `GET /api/v1/documents` - Listar com filtros
- `GET /api/v1/documents/{id}` - Detalhes completos
- `GET /api/v1/documents/{id}/versions` - Todas as versões
- `DELETE /api/v1/documents/{id}/versions/{version}` - Deletar versão

### Chat
- `POST /api/v1/chat/ask` - Fazer pergunta ao LLM
- `POST /api/v1/chat/conversations/{id}/rate` - Avaliar resposta (controlado pelo frontend)
- `GET /api/v1/chat/conversations` - Histórico de conversas
- `GET /api/v1/chat/conversations/{id}` - Detalhes da conversa com mensagens

### Master Data (Somente Leitura)
- `GET /api/v1/master-data/locations` - Todas as localidades
- `GET /api/v1/master-data/countries` - Todos os países
- `GET /api/v1/master-data/regions` - Todas as regiões
- `GET /api/v1/master-data/states-by-country/{country_name}` - Estados por país
- `GET /api/v1/master-data/cities-by-country/{country_name}` - Cidades por país
- `GET /api/v1/master-data/cities-by-region/{region}` - Cidades por região
- `GET /api/v1/master-data/hierarchy` - Hierarquia completa de localidades
- `GET /api/v1/master-data/categories` - Categorias de benefícios
- `GET /api/v1/master-data/categories/{category_id}` - Detalhes de uma categoria
- `GET /api/v1/master-data/roles` - Funções/níveis de trabalho
- `GET /api/v1/master-data/roles/{role_id}` - Detalhes de uma função

**Nota**: API é somente leitura (GET). Dados mestres são gerenciados via migrations e scripts administrativos.

### Autenticação
- `GET /api/v1/login` - Iniciar login Azure
- `GET /api/v1/getatoken` - Callback Azure (interno)
- `GET /api/v1/logout` - Fazer logout
- `GET /api/v1/auth/status` - Status de autenticação

---

## Autenticação

### Fluxo OAuth2 com Azure Entra ID

**Provedores**: `auth_msal.py` e `auth.py`

1. **Redirecionamento para Azure AD**
   - URL gerada por MSAL
   - Scopes: `openid profile email offline_access https://graph.microsoft.com/User.Read`

2. **Troca de Código**
   - Azure retorna código de autorização
   - Backend usa MSAL para trocar por tokens

3. **Tokens Gerados**
   - `id_token` - JWT com user info (para autenticação app)
   - `access_token` - Token Graph para chamar Microsoft Graph API
   - `refresh_token` - Para renovar tokens quando expirarem

4. **Armazenamento**
   - `session` cookie - HTTPOnly, Secure, SameSite=None
   - Contém `id_token` (usado para validar requisições)
   - Expira junto com o token

5. **Validação em Cada Requisição**
   - Middleware intercepta requisição
   - Lê JWT de cookie
   - Valida assinatura contra JWKS do Azure
   - Extrai claims (email, roles, oid)
   - Passa para `request.state.user`

### Segurança
- ✅ HTTPOnly cookies (JS não consegue acessar)
- ✅ Secure flag (HTTPS only)
- ✅ SameSite=None (cross-site permitido para API)
- ✅ Validação de assinatura JWT
- ✅ Expiração de token

---

## Deployment

### Ambientes
- **Local**: `docker-compose.yml`
- **Azure**: Container Apps + SQL Server + Blob Storage

### Variáveis de Ambiente

```bash
# Azure
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
=...

# URLs
APP_BASE_URL_BACKEND=...
APP_BASE_URL_FRONTEND=...

# LLM Server
LLM_SERVER_URL=https://...

# Blob Storage
AZURE_STORAGE_ACCOUNT_NAME=...
AZURE_STORAGE_ACCOUNT_KEY=...

# SQL Server
DB_HOST=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...

# CORS
CORS_ORIGINS=...

# Features
SKIP_LLM_SERVER=false
SKIP_LLM_METADATA_EXTRACTION=false
```

### Build & Deploy

```bash
# Local
docker-compose up

# Azure
az containerapp create --resource-group ... --name luz-backend \
  --image containerregistry.azurecr.io/luz:latest \
  --environment ...
```

---

## Estrutura de Dados

### Tabela `documents`
- `document_id` (UUID) - PK
- `title` - Nome do documento
- `user_id` - Dono do documento
- `category_id` (FK) - Categoria (HR, Finance, etc)
- `is_active` - Soft delete
- `min_role_level` - Nível de acesso mínimo
- `allowed_roles` (JSON) - Roles específicos
- `allowed_countries` (JSON) - Países
- `allowed_cities` (JSON) - Cidades
- `collar` - White-collar/blue-collar
- `plant_code` - Unidade da empresa
- `summary` - Resumo gerado por LLM
- `created_at`, `updated_at`

### Tabela `versions`
- `version_id` (UUID) - PK
- `document_id` (FK)
- `version_number` - 1, 2, 3...
- `blob_path` - Caminho no Azure
- `filename` - Nome original (pode ser NULL para docs antigos)
- `is_active` - Versão ativa
- `created_at`
- `updated_by` - Quem atualizou

### Tabela `dim_categories`
- `category_id` (PK)
- `category_name`
- `description`

---

## Tratamento de Erros Comuns

### 422 Unprocessable Entity (LLM)
**Causa**: Texto > 50K caracteres
**Solução**: Backend trunca automaticamente antes de enviar

### filename vazio em versões antigas
**Causa**: Documentos criados antes de adicionar campo `filename`
**Solução**: Backend resolve automaticamente de:
1. `blob_path` (último componente)
2. `title + extensão`

### Arquivo não encontrado no blob
**Causa**: Versão deletada ou blob expirado
**Solução**: GET endpoint retorna 404, não erro 500

---

## Logging

- **Level**: INFO por padrão
- **Output**: stdout (capturado pelo Docker)
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Tags**: `[ingest_confirm]`, `[get_document_details]`, etc

Exemplo de log util:
```
[ingest_confirm] Formato docx: usando FormatConverter para extração correta
[ingest_confirm] Texto extraído e processado: 250000 chars -> 50000 chars
[ingest_confirm] ✅ Documento enviado para LLM Server com sucesso
```

---

## Próximas Melhorias

- [ ] Migrations automáticas de schema
- [ ] Rate limiting
- [ ] Audit log completo
- [ ] Métricas Prometheus
- [ ] Health checks mais robustos
- [ ] Retry logic para LLM Server
- [ ] Suporte a S3 em paralelo com Azure
