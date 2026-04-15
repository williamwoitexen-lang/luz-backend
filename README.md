# Embeddings Service (Azure-only)

This repository implements a document ingestion and vector search service powered by:
- **Azure SQL Database** for document metadata and versioning
- **Azure Blob Storage** for file persistence
- **Azure AI Search** for semantic search and chunks
- **Azure OpenAI** for embeddings and LLM operations
- **Entra ID** for authentication

This README covers the new preview/confirm ingestion flow, how to run locally, tests and environment variables for LLM configuration.

---

## Preview / Confirm ingestion flow

We added a two-step ingestion flow so an LLM can suggest metadata fields before finalizing ingestion.

1. Preview

- Endpoint: `POST /api/v1/documents/ingest-preview`
- Body: multipart/form-data with `file=@yourfile.ext`
- What it does: stores the uploaded file under `storage/temp/{temp_id}/`, calls an LLM to extract suggested fields (creator, allowed countries/cities, min role level, collar, plant code), and returns a `temp_id` and the suggestions.

Example:

```
curl -s -X POST "http://127.0.0.1:8000/api/v1/documents/ingest-preview" -F "file=@tmp_test.txt"

# Response
{
  "status": "preview_ready",
  "temp_id": "<uuid>",
  "filename": "tmp_test.txt",
  "extracted_fields": { ... },
  "expires_in_seconds": 600
}
```

2. Confirm

- Endpoint: `POST /api/v1/documents/ingest-confirm/{temp_id}`
- You may either:
  - Send final form values (e.g. `user_id`, `allowed_countries`, ...) and/or
  - Re-send the file as `file=@file` (optional). If you provide a `file` here it overrides the temp file saved in preview.
- `allowed_countries` and `allowed_cities` can be provided as a JSON array string (recommended) or as a comma-separated string. If left empty, the values suggested by the LLM (from preview) are used.

Example (using temp file saved during preview):

```
curl -s -X POST "http://127.0.0.1:8000/api/v1/documents/ingest-confirm/<temp_id>" \
  -F "user_id=alice" \
  -F "allowed_countries=[\"BR\"]"
```

Example (override file at confirm):

```
curl -s -X POST "http://127.0.0.1:8000/api/v1/documents/ingest-confirm/<temp_id>" \
  -F "file=@other.txt" -F "user_id=bob"
```

Notes:
- Temporary files live under `storage/temp/{temp_id}/` and auto-delete after 10 minutes.
- The original single-step `POST /api/v1/documents/ingest` remains unchanged for quick ingests.

---

## Field formats and behavior

- `allowed_countries` / `allowed_cities` accepted formats:
  - JSON array string: `'["BR","US"]'` (recommended when calling via curl/programmatic)
  - Comma-separated string: `BR,US`
  - Empty: fallback to LLM suggestion (from preview)
- `collar` values: `"w"` (white), `"b"` (blue) or empty string.

---

## Running locally

### Without Docker

Install dependencies (in dev environment):

```
pip install -r requirements.txt
```

Start the API server (dev):

```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### With Docker (Recommended)

```bash
chmod +x docker-dev.sh
./docker-dev.sh
```

Open http://127.0.0.1:8000/docs to use the interactive Swagger UI.

**See [DEPLOYMENT_LOCAL.md](./DEPLOYMENT_LOCAL.md) for detailed local setup instructions.**

---

## Tests

Run the unit tests with `PYTHONPATH=.` to ensure `app` package is resolved:

```
PYTHONPATH=. pytest -q
```

**Note:** Tests have been migrated to use Azure infrastructure. Local DuckDB testing is no longer supported. Tests require SQL Server and Azure Blob Storage connectivity.

---

## LLM configuration (OpenAI / Azure OpenAI)

The LLM module (`app/llm.py`) supports using either OpenAI.com or Azure OpenAI depending on environment variables.

- For OpenAI.com set:
  - `OPENAI_API_KEY`
  - optional `OPENAI_MODEL` (default `gpt-3.5-turbo`)

- For Azure OpenAI set:
  - `AZURE_OPENAI_ENDPOINT` (the endpoint URL)
  - ``
  - optional `AZURE_OPENAI_DEPLOYMENT` (model/deployment name)
  - optional `AZURE_OPENAI_API_VERSION`

The preview endpoint uses the configured LLM to suggest metadata. If you do not configure an API key, the preview will attempt to run but will return empty suggestions when the LLM client fails.

---

## Embeddings configuration (OpenAI / Azure OpenAI)

The embeddings module (`app/embeddings.py`) also supports both OpenAI.com and Azure OpenAI.

**Using OpenAI.com:**
```bash
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=text-embedding-3-small  # optional
```

**Using Azure OpenAI:**
```bash
export AZURE_OPENAI_ENDPOINT=https://myaccount.openai.azure.com/
export =...
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small  # optional
export AZURE_OPENAI_API_VERSION=2023-05-15  # optional
```

The module auto-detects which provider to use based on the `AZURE_OPENAI_ENDPOINT` variable.

---

## Storage Configuration

The service supports both **local filesystem** and **Azure ADLS Gen2** storage via environment variables.

### Local Storage (default)

```bash
export STORAGE_TYPE=local
export LOCAL_STORAGE_PATH=storage/documents  # optional, defaults to storage/documents
```

Files are stored at: `storage/documents/{document_id}/{version_number}/{filename}`

### Azure ADLS Gen2 Storage

Install Azure SDK:
```bash
pip install azure-storage-blob azure-identity
```

Configure environment variables:
```bash
export STORAGE_TYPE=azure
export AZURE_STORAGE_ACCOUNT_NAME=myaccount
export AZURE_STORAGE_CONTAINER_NAME=documents  # optional, defaults to 'documents'

# Choose ONE of the following for authentication:

# Option 1: Connection string
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=myaccount;..."

# Option 2: Account key
export AZURE_STORAGE_ACCOUNT_KEY="..."

# Option 3: Managed Identity (for Container Apps / AKS)
# No extra config needed - uses DefaultAzureCredential
```

Files are stored at: `azure://container_name/documents/{document_id}/{version_number}/{filename}`

---

## GET /api/v1/get_role (Entra ID Integration)

Endpoint to extract user role from Entra ID token.

Request:
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/get_role" \
  -H "Authorization: Bearer <entra_id_token>"
```

Response:
```json
{
  "email": "user@company.com",
  "role": "viewer",
  "name": "John Doe",
  "oid": "user-object-id"
}
```

**Note**: Currently returns hardcoded `role`. Configure app roles in Entra ID and include them in token claims for dynamic role extraction.

---

## Download Endpoint

Download documents by version:

```bash
# Latest version
curl -X GET "http://127.0.0.1:8000/api/v1/documents/{document_id}/download" \
  -o document.txt

# Specific version by version_id (UUID)
curl -X GET "http://127.0.0.1:8000/api/v1/documents/{document_id}/download?version_id=abc123def456" \
  -o document_v1.txt

# Specific version by version number
curl -X GET "http://127.0.0.1:8000/api/v1/documents/{document_id}/download?version=2" \
  -o document_v2.txt
```

File paths are stored in the database per version, making it easy to:
- Track file locations
- Download specific versions by ID or version number
- Get the latest version by default
- Switch storage backends (local → Azure) transparently
- Support versioning per document

---

## Azure Setup

This service is **Azure-only**. It requires:

1. **Azure SQL Database**: Stores documents, versions, and permissions metadata
2. **Azure Blob Storage**: Stores uploaded files
3. **Azure AI Search**: Provides semantic search and chunk indexing
4. **Azure OpenAI**: Provides embeddings and LLM operations
5. **Entra ID**: Provides user authentication via OAuth2/OIDC

Follow [DEPLOYMENT_AZURE.md](./DEPLOYMENT_AZURE.md) for complete setup instructions including:
- Infrastructure provisioning with Terraform
- Docker image build and deployment
- Configuration of Managed Identity for SQL Server access
- Key Vault setup for sensitive credentials 

---

## 📚 Documentação Adicional

### Admin Management API
A plataforma inclui um sistema completo de gerenciamento de admins com controle granular de permissões.

**Acesse**: [ADMIN_MANAGEMENT_API.md](./docs/ADMIN_MANAGEMENT_API.md)

**Recursos principais**:
- Criar e gerenciar administradores do sistema
- Associar features (permissões) a admins
- Controlar acesso por agente (LUZ, IGP, SMART)
- Bootstrap do primeiro admin (sem autenticação)
- Query e listagem de admins com paginação

### Prompts Management API
Sistema de gerenciamento de prompts customizados para cada agente com sincronização automática com LLM Server.

**Acesse**: [PROMPTS_MANAGEMENT_API.md](./docs/PROMPTS_MANAGEMENT_API.md)

**Recursos principais**:
- Criar/atualizar/deletar prompts por agente
- Versionamento automático de prompts
- Sincronização fail-safe com LLM Server
- Retry automático com backoff exponencial
- Histórico completo com timestamps

### Documentação Completa
Para uma visão geral de toda a plataforma, consulte:

- [COMPLETE_DOCUMENTATION.md](./docs/COMPLETE_DOCUMENTATION.md) - Documentação técnica completa
- [CHAT_API.md](./docs/CHAT_API.md) - API de Chat
- [MASTER_DATA_API.md](./docs/MASTER_DATA_API.md) - Dados Mestres
- [DOCUMENT_INGESTION.md](./docs/DOCUMENT_INGESTION.md) - Ingestão de Documentos
- [FRONTEND_INTEGRATION.md](./docs/FRONTEND_INTEGRATION.md) - Integração Frontend
- [USER_PREFERENCES_API.md](./docs/USER_PREFERENCES_API.md) - Preferências de Usuário

---
