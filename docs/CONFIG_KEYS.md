# 🔐 Variáveis de Ambiente e Configuração

**Documento de referência completo de todas as variáveis de ambiente utilizadas pelo backend.**

---

## 📋 Tabela Completa de Variáveis

### 🔴 Variáveis Obrigatórias (Críticas)

| Chave | Tipo | Descrição | Origem | Padrão | Sensível |
|-------|------|-----------|--------|--------|----------|
| `AZURE_TENANT_ID` | UUID | ID do tenant Azure Entra ID | Azure KeyVault | ❌ Nenhum | ⚠️ Não-crítico |
| `AZURE_CLIENT_ID` | UUID | ID da aplicação registrada no Azure Entra ID | Azure KeyVault | ❌ Nenhum | ⚠️ Não-crítico |
| `` | string | Segredo da aplicação (para MSAL) | Azure KeyVault | ❌ Nenhum | 🔴 **SIM** |
| `SQLSERVER_CONNECTION_STRING` | string | Connection string para SQL Server/Azure SQL | Azure KeyVault | `Driver={...};Authentication=ActiveDirectoryMsi;` | 🔴 **SIM** |
| `AZURE_STORAGE_CONNECTION_STRING` | string | Connection string para Azure Blob Storage | Azure KeyVault | ❌ Nenhum | 🔴 **SIM** |
| `LLM_SERVER_URL` | URL | URL do backend LLM (embeddings + busca) | Azure AppSettings | ❌ Nenhum | ⚠️ Não-crítico |
| `` | API Key | Chave da API Azure OpenAI | Azure KeyVault | ❌ Nenhum | 🔴 **SIM** |

### 🟡 Variáveis Recomendadas (Muito Importantes)

| Chave | Tipo | Descrição | Origem | Padrão | Sensível |
|-------|------|-----------|--------|--------|----------|
| `AZURE_STORAGE_ACCOUNT_NAME` | string | Nome da storage account (ex: `mystorageaccount`) | Azure AppSettings | `chat-rh` | ⚠️ Não |
| `AZURE_STORAGE_CONTAINER_NAME` | string | Nome do container onde documentos são armazenados | Azure AppSettings | `chat-rh` | ⚠️ Não |
| `AZURE_SEARCH_API_KEY` | API Key | Chave da API Azure AI Search (semantic search) | Azure KeyVault | ❌ Nenhum | 🔴 **SIM** |
| `LLM_SERVER_TIMEOUT` | int | Timeout em segundos para chamadas ao LLM Server | Azure AppSettings | `30` | ⚠️ Não |

### 🟢 Variáveis Opcionais (Com Padrões)

| Chave | Tipo | Descrição | Origem | Padrão | Sensível |
|-------|------|-----------|--------|--------|----------|
| `APP_ENV` | string | Ambiente da aplicação | Azure AppSettings | `dev` | ⚠️ Não |
| `SKIP_LLM_SERVER` | boolean | Desabilita LLM Server (útil para testes) | Azure AppSettings | `false` | ⚠️ Não |
| `CORS_ORIGINS` | string (CSV) | Origens CORS permitidas | Azure AppSettings | `http://localhost:4200,http://localhost:3000` | ⚠️ Não |
| `LANGCHAIN_BASE_URL` | URL | URL base do Langchain (fallback para LLM_SERVER_URL) | Azure AppSettings | ❌ Nenhum | ⚠️ Não |
| `AZURE_CONTENT_SAFETY_API_KEY` | API Key | Chave da API Azure Content Safety (moderation) | Azure KeyVault | ❌ Nenhum (não implementado) | 🔴 **SIM** |
| `USE_PYODBC_MOCK` | boolean | Forçar uso de mock pyodbc (dev/teste) | AppSettings Local | `false` | ⚠️ Não |
| `REDIS_HOST` | string | Host do Redis (para cache) | Azure AppSettings | `localhost` | ⚠️ Não |
| `REDIS_PORT` | int | Porta do Redis | Azure AppSettings | `6379` | ⚠️ Não |
| `STORAGE_TYPE` | string | Tipo de storage: `azure` ou `local` | AppSettings Local | `azure` | ⚠️ Não |

---

## 🌍 Mapeamento por Ambiente

### DEV (Desenvolvimento Local)

```bash
# .env local (NÃO COMMITAR)
APP_ENV=dev
SKIP_LLM_SERVER=true           # Desabilitar LLM para testes rápidos

# Azure Credentials (usar suas próprias)
AZURE_TENANT_ID=<seu-tenant-id>
AZURE_CLIENT_ID=<sua-client-id>
=<seu-secret>
SQLSERVER_CONNECTION_STRING=Driver={ODBC...};Server=localhost;...
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpoints...
=<sua-openai-key>
AZURE_SEARCH_API_KEY=<sua-search-key>

# Local Services
LLM_SERVER_URL=http://localhost:8001
REDIS_HOST=localhost
REDIS_PORT=6379
STORAGE_TYPE=local

# Optional
CORS_ORIGINS=http://localhost:4200,http://localhost:3000
USE_PYODBC_MOCK=false  # true se não tiver ODBC Driver
```

### STAGING (Ambiente de Preparação)

```bash
# ⚠️ Todas as credenciais vêm do Azure KeyVault
# Azure Pipeline injeta automaticamente

APP_ENV=staging
SKIP_LLM_SERVER=false

# ✅ Automaticamente injetados pelo pipeline:
# AZURE_TENANT_ID              (from KeyVault staging-*)
# AZURE_CLIENT_ID              (from KeyVault staging-*)
#           (from KeyVault staging-*)
# SQLSERVER_CONNECTION_STRING  (from KeyVault staging-*)
# AZURE_STORAGE_CONNECTION_STRING (from KeyVault staging-*)
#             (from KeyVault staging-*)
# AZURE_SEARCH_API_KEY        (from KeyVault staging-*)

# AppSettings (não sensível)
LLM_SERVER_URL=https://staging-llm.internal
REDIS_HOST=staging-redis.internal
STORAGE_TYPE=azure

# Opcional
CORS_ORIGINS=https://staging-app.company.com
```

### PROD (Produção)

```bash
# ⚠️ Todas as credenciais vêm do Azure KeyVault
# Azure Pipeline injeta automaticamente
# NUNCA fazer commit de credenciais

APP_ENV=prod
SKIP_LLM_SERVER=false

# ✅ Automaticamente injetados pelo pipeline:
# AZURE_TENANT_ID              (from KeyVault prod-*)
# AZURE_CLIENT_ID              (from KeyVault prod-*)
#           (from KeyVault prod-*)
# SQLSERVER_CONNECTION_STRING  (from KeyVault prod-*)
# AZURE_STORAGE_CONNECTION_STRING (from KeyVault prod-*)
#             (from KeyVault prod-*)
# AZURE_SEARCH_API_KEY        (from KeyVault prod-*)

# AppSettings (não sensível)
LLM_SERVER_URL=https://prod-llm.internal
REDIS_HOST=prod-redis.internal
STORAGE_TYPE=azure
LLM_SERVER_TIMEOUT=60

# Domínio CORS
CORS_ORIGINS=https://app.company.com
```

---

## 🔍 Detalhamento por Serviço

### 1. Autenticação (MSAL + Entra ID)

**Variáveis necessárias:**
```
AZURE_TENANT_ID
AZURE_CLIENT_ID

```

**Erro se faltar:**
```
ValueError:  não definida
msal.error.MsalError: A credencial não foi fornecida
```

**Onde obter:**
1. Azure Portal → Entra ID → App registrations → Sua aplicação
2. Overview: copiar `Directory (tenant) ID` → `AZURE_TENANT_ID`
3. Overview: copiar `Application (client) ID` → `AZURE_CLIENT_ID`
4. Certificates & secrets → New client secret → copiar valor → ``

---

### 2. SQL Server (Azure SQL)

**Variáveis necessárias:**
```
SQLSERVER_CONNECTION_STRING
```

**Opções de connection string:**

**Opção A: SQL Server Authentication (com usuário/senha)**
```
Driver={ODBC Driver 18 for SQL Server};
Server=myserver.database.windows.net;
Database=mydatabase;
UID=myuser@myserver;
PWD=mypassword;
Encrypt=yes;
TrustServerCertificate=no;
Connection Timeout=30
```

**Opção B: Managed Identity (em produção, sem senha)**
```
Driver={ODBC Driver 18 for SQL Server};
Server=myserver.database.windows.net;
Database=mydatabase;
Encrypt=yes;
TrustServerCertificate=no;
Connection Timeout=30;
Authentication=ActiveDirectoryMsi
```

**Erro se faltar:**
```
KeyError: SQLSERVER_CONNECTION_STRING
pyodbc.OperationalError: [HY000] ODBC Driver 17/18 not found
```

**Onde obter:**
1. Azure Portal → SQL Servers → Seu servidor
2. Connection strings: copiar string ODBC
3. Substituir `{your_username}` e `{your_password}`

---

### 3. Azure Storage (Blob)

**Variáveis necessárias:**
```
AZURE_STORAGE_ACCOUNT_NAME
AZURE_STORAGE_CONTAINER_NAME
AZURE_STORAGE_CONNECTION_STRING
```

**Connection string format:**
```
DefaultEndpointsProtocol=https;
EndpointSuffix=core.windows.net;
AccountName=mystorageaccount;
AccountKey=your-account-key;
BlobEndpoint=https://mystorageaccount.blob.core.windows.net/
```

**Erro se faltar:**
```
ValueError: AZURE_STORAGE_CONNECTION_STRING não definida
azure.core.exceptions.ClientAuthenticationError: Failed to authenticate
```

**Onde obter:**
1. Azure Portal → Storage accounts → Sua conta
2. Access keys: copiar `Connection string`

---

### 4. LLM Server (Embeddings + Busca Semântica)

**Variáveis necessárias:**
```
LLM_SERVER_URL

```

**Variáveis opcionais:**
```
LLM_SERVER_TIMEOUT=30  # padrão
SKIP_LLM_SERVER=false  # padrão
```

**Erro se faltar:**
```
ValueError: LLM_SERVER_URL não definida
requests.exceptions.ConnectionError: Connection refused
```

**Onde obter:**
- `LLM_SERVER_URL`: configuração do seu time de IA (URL interna do LLM Server)
- ``: Azure Portal → OpenAI resources → Keys and Endpoint

---

### 5. Busca Semântica (Azure AI Search)

**Variáveis necessárias (se não via LLM Server):**
```
AZURE_SEARCH_API_KEY
```

**Nota:** Normalmente o LLM Server encapsula isso. Usar apenas se chamar diretamente.

**Onde obter:**
1. Azure Portal → AI Search resources
2. Keys: copiar `Admin key` ou `Query key`

---

## ✅ Checklist de Setup

### DEV (Local)

- [ ] Copiar `.env.example` → `.env`
- [ ] Preencher `AZURE_TENANT_ID` (seu Azure AD)
- [ ] Preencher `AZURE_CLIENT_ID`
- [ ] Preencher ``
- [ ] Preencher `SQLSERVER_CONNECTION_STRING`
- [ ] Preencher `AZURE_STORAGE_CONNECTION_STRING`
- [ ] Preencher ``
- [ ] Preencher `AZURE_SEARCH_API_KEY`
- [ ] Definir `LLM_SERVER_URL=http://localhost:8001` (ou sim se rodando localmente)
- [ ] Definir `SKIP_LLM_SERVER=true` (para testes iniciais sem LLM)
- [ ] **NÃO commitar `.env`** (está em `.gitignore`)

### STAGING/PROD

- [ ] Credenciais configuradas no Azure KeyVault
- [ ] Azure Pipeline configura as env vars automaticamente
- [ ] `APP_ENV` = `staging` ou `prod`
- [ ] URLs de serviços apontam para ambiente correto
- [ ] Testar deployment com `az webapp log tail`

---

## 🚨 Problemas Comuns

### " não definida"

**Causa:** Variável não foi definida no `.env` ou pipeline

**Solução:**
```bash
# Local
cp .env.example .env
# Editar e preencher 

# Pipeline (Azure DevOps)
# Verificar variable groups estão linked
az keyvault secret list --vault-name your-keyvault
```

---

### "SQLSERVER_CONNECTION_STRING: Connection refused"

**Causa:** SQL Server offline ou firewall bloqueando

**Solução:**
```bash
# Testar conexão
sqlcmd -S your-server.database.windows.net -U user -P password

# Ou via Azure CLI
az sql server firewall-rule create --name allow-my-ip \
  --resource-group my-rg \
  --server my-server \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

---

### "ODBC Driver 18/17 not found"

**Causa:** Driver ODBC para SQL Server não instalado

**Solução:**
```bash
# Linux (Debian/Ubuntu)
sudo apt update
sudo apt install -y odbc-driver-18-for-sql-server

# macOS
brew tap microsoft/mssql-release
brew install mssql-tools18

# Windows
# Baixar do: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

---

### "LLM_SERVER_URL timeout"

**Causa:** LLM Server offline ou URL incorreta

**Solução:**
```bash
# Se for dev/teste
SKIP_LLM_SERVER=true

# Se for produção
# Verificar se LLM Server está rodando
curl https://your-llm-server/health

# Aumentar timeout
LLM_SERVER_TIMEOUT=60
```

---

## 🔗 Referências

- [Azure Entra ID - App Registration](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Azure SQL - Connection Strings](https://learn.microsoft.com/en-us/azure/azure-sql/database/connect-query-python)
- [Azure Storage - Connection String](https://learn.microsoft.com/en-us/azure/storage/common/storage-configure-connection-string)
- [Azure OpenAI - Keys](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference)
- [ODBC Driver Download](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

---

## 📞 Suporte

Se alguma variável não estiver clara:
1. Checar `.env.example` com descrições
2. Rodar `python -c "from app.core.config import KeyVaultConfig; print(KeyVaultConfig.__doc__)"`
3. Consultar este documento
4. Abrir issue no GitHub com logs completos
