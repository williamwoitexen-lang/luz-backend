# AÇÕES PRIORITÁRIAS PÓS-REUNIÃO
## O que criar para ficar 100% completo

---

## 🔴 CRÍTICO (Fazer ANTES da reunião, se possível - 2h)

### 1. Remover Credenciais do `.env`
**Arquivo**: [.env](.env)  
**Ação**: Criar `.env.example` sem valores sensíveis

```bash
# ✅ .env.example (commitável)
APP_ENV=dev
OPENAI_API_KEY=sk-proj-xxxxx...  # MASCARADO
AZURE_TENANT_ID=d2007bef...  # MASCARADO
AZURE_CLIENT_ID=abeecec0...  # MASCARADO
=XXXXX  # MASCARADO
SQLSERVER_CONNECTION_STRING=Driver=...  # MASCARADO
LLM_SERVER_URL=http://localhost:8001
SKIP_LLM_SERVER=true
```

**Por quê**: `.env` real está commitado no Git. Risco de segurança!

---

## 🟡 ALTA PRIORIDADE (Após reunião - 2h cada)

### 1. Criar `docs/CONFIG_KEYS.md`

**Por quê**: Cliente quer: "nome + descrição + onde vem (KeyVault/AppSettings)"

**Template**:
```markdown
# Variáveis de Ambiente e Configuração

| Chave | Tipo | Descrição | Obrigatória | Origem |
|-------|------|-----------|------------|--------|
| AZURE_TENANT_ID | string | ID do tenant Azure Entra ID | Sim | Azure KeyVault |
| AZURE_CLIENT_ID | string | ID da aplicação Azure registrada no Entra | Sim | Azure KeyVault |
|  | string | Segredo da aplicação (SENSÍVEL) | Sim | Azure KeyVault |
| SQLSERVER_CONNECTION_STRING | string | Conexão com SQL Server/Azure SQL | Sim | Azure KeyVault |
| AZURE_STORAGE_CONNECTION_STRING | string | Conexão com Blob Storage | Sim | Azure KeyVault |
| AZURE_STORAGE_ACCOUNT_NAME | string | Nome da storage account | Sim | Azure AppSettings |
| AZURE_STORAGE_CONTAINER_NAME | string | Nome do container para docs | Não | AppSettings (padrão: chat-rh) |
| LLM_SERVER_URL | string | URL do LLM Server (backend IA) | Sim | AppSettings |
| LLM_SERVER_TIMEOUT | int | Timeout em segundos p/ conectar | Não | AppSettings (padrão: 30) |
| SKIP_LLM_SERVER | boolean | Desabilita LLM para testes | Não | AppSettings (padrão: false) |
| OPENAI_API_KEY | string | API key do Azure OpenAI (se usado direto) | Não | Azure KeyVault |
| REDIS_HOST | string | Host do Redis | Não | AppSettings (padrão: localhost) |
| REDIS_PORT | int | Porta do Redis | Não | AppSettings (padrão: 6379) |

## Como Obter em Cada Ambiente

### DEV (Local)
- Copiar `.env.example` → `.env`
- Preencher com credenciais Azure próprias (não commit!)

### STAGING
- Credentials injetadas via Azure Pipeline
- Vêm de KeyVault staging

### PRODUÇÃO
- Credentials injetadas via Azure Pipeline
- Vêm de KeyVault produção
- NUNCA commit de credenciais reais
```

**Checklist**:
- [ ] Documentar TODAS as variáveis em `app/core/config.py`
- [ ] Incluir onde cada uma é usada (qual endpoint/service)
- [ ] Separar OBRIGATÓRIAS vs. OPCIONAIS vs. COM PADRÃO
- [ ] Incluir valores de exemplo

---

### 2. Criar `docs/RUN_LOCAL_GUIDE.md`

**Por quê**: Cliente quer: "How-to passo a passo + troubleshooting"

**Seções**:

```markdown
# Como Rodar Localmente - Guia Completo

## 1. Pre-requisitos

- [ ] Python 3.11+ instalado
- [ ] pip/venv disponível
- [ ] Git
- [ ] Docker + Docker Compose (RECOMENDADO)

### Verificar Versão Python
\`\`\`bash
python3 --version
# Deve ser 3.11+
\`\`\`

## 2. Setup (Opção A: SEM Docker - 5 min)

### Passo 1: Clone e Navegue
\`\`\`bash
git clone <repo-url>
cd Embeddings
\`\`\`

### Passo 2: Criar Virtual Environment
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
# Windows: .\\venv\\Scripts\\activate
\`\`\`

### Passo 3: Instalar Dependências
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### Passo 4: Configurar .env
\`\`\`bash
cp .env.example .env
# Editar .env com suas credenciais Azure
\`\`\`

**O que preencher**:
- `AZURE_TENANT_ID` - Do seu Azure AD
- `AZURE_CLIENT_ID` - Aplicação registrada
- `` - Segredo gerado
- `SQLSERVER_CONNECTION_STRING` - Seu SQL Server
- Opcionalmente: Azure Storage, LLM Server

### Passo 5: Rodar Server
\`\`\`bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

**Output esperado**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Passo 6: Testar
\`\`\`bash
curl http://localhost:8000/
# Deve retornar JSON com versão da API
\`\`\`

## 3. Setup (Opção B: COM Docker - 3 min)

\`\`\`bash
# 1. Copiar .env
cp .env.example .env

# 2. Subir containers (API + Redis)
docker-compose up --build

# 3. Aguardar "Application startup complete"
# 4. Acessar http://localhost:8000/docs
\`\`\`

## 4. Rodar Testes

\`\`\`bash
# Todos os testes
pytest

# Com coverage
pytest --cov=app tests/

# Teste específico
pytest tests/test_auth.py::test_login -v

# Sem captura de output (vê logs)
pytest -s
\`\`\`

## 5. Rodar Linter

\`\`\`bash
# Pylint (se instalado)
pylint app/

# Ou flake8
flake8 app/ --max-line-length=120
\`\`\`

## 6. Verificar Saúde

\`\`\`bash
# Health check
curl http://localhost:8000/

# Swagger UI
open http://localhost:8000/docs

# Status de autenticação
curl http://localhost:8000/api/v1/auth/status
\`\`\`

## Troubleshooting

### Erro: "ODBC Driver 17 not found"
\`\`\`bash
# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install odbc-driver-17-for-sql-server

# macOS
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew install mssql-tools17

# Windows
Baixar do: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
\`\`\`

### Erro: "Connection refused" (SQL Server)
- [ ] Verificar se SQL Server está online
- [ ] Copiar exato SQLSERVER_CONNECTION_STRING
- [ ] Testar conexão: \`sqlcmd -S server -U user -P password\`
- [ ] Checar firewall

### Erro: "LLM Server timeout"
Três opções:
1. Desabilitar LLM: \`SKIP_LLM_SERVER=true\`
2. Certifiquar que LLM Server roda em \`localhost:8001\`
3. Aumentar timeout: \`LLM_SERVER_TIMEOUT=60\`

### Erro: "ModuleNotFoundError"
- [ ] Verificar que venv está ativado: \`which python\`
- [ ] Re-rodar: \`pip install -r requirements.txt\`
- [ ] Limpar cache: \`pip cache purge\`

### Erro: "MSAL authentication failed"
- [ ] Verificar AZURE_TENANT_ID na sua organização
- [ ] Verificar AZURE_CLIENT_ID registrado em Azure
- [ ] Renovar  (pode ter expirado)

## Ambiente de Teste

Para testar **sem credenciais reais**, configure:

\`\`\`bash
# .env.test
APP_ENV=test
SKIP_LLM_SERVER=true
SQLSERVER_CONNECTION_STRING=sqlite:///:memory:  # ou test DB
STORAGE_TYPE=local  # Use local storage
\`\`\`

## Docker Compose Detalhes

\`docker-compose.yml\` inicia:
1. **Redis** na porta 6379 (cache + sessions)
2. **API** na porta 8000 (FastAPI)

Para ver logs em tempo real:
\`\`\`bash
docker-compose logs -f api
docker-compose logs -f redis
\`\`\`

Para parar:
\`\`\`bash
docker-compose down
\`\`\`

Para limpar volumes (CUIDADO):
\`\`\`bash
docker-compose down -v
\`\`\`

## Próximos Passos

Após rodar localmente:
1. Acessar Swagger UI em http://localhost:8000/docs
2. Testar endpoints (veja API_EXAMPLES.http)
3. Ver logs em console (DEBUG mode)
4. Rodar testes com \`pytest\`

## Suporte

Se alguma coisa não funcionar:
1. Checar este guia (Troubleshooting acima)
2. Verificar valor de .env
3. Rodar \`docker-compose down && docker-compose up --build\` (reset completo)
4. Abrir issue no GitHub com logs completos
```

**Checklist**:
- [ ] Instruções SEM Docker + COM Docker
- [ ] Pre-requisitos listados
- [ ] Troubleshooting dos 5 errors mais comuns
- [ ] Como testar após rodar
- [ ] Como desligar e limpar

---

### 3. Converter `API_EXAMPLES.http` → Postman Collection

**Por quê**: `API_EXAMPLES.http` é ótimo para VS Code, mas cliente pode usar Postman/Insomnia

**Opção A: Usar ferramenta online** (5 min)
- Exportar cada exemplo manualmente
- Salvar como `Luz-API.postman_collection.json`

**Opção B: Auto-gerar** (30 min)
- Script Python que lê API_Examples.http e gera JSON Postman
- Colocar em `/scripts/generate_postman_collection.py`

**Colocar em**: `/docs/Luz-API.postman_collection.json`

**Checklist**:
- [ ] Collection com 50+ requests
- [ ] Agrupados por tags (docs, chat, auth, master-data)
- [ ] Variáveis de environment: `{{baseUrl}}`, `{{token}}`, etc
- [ ] Exemplos antes/depois (request + response)

---

## 🟢 MÉDIA PRIORIDADE (Pós-reunião - 1h cada)

### 1. Criar Diagrama Mermaid do Fluxo

**Arquivo**: `docs/ARCHITECTURE_DIAGRAMS.md`

```markdown
# Diagramas de Arquitetura

## Fluxo de Ingestão de Documento

\`\`\`mermaid
sequenceDiagram
    participant User as Frontend
    participant API as Backend FastAPI
    participant Blob as Blob Storage
    participant DB as SQL Server
    participant LLM as LLM Server
    
    User->>API: POST /ingest-preview
    API->>Blob: Salva arquivo temp
    Blob-->>API: OK
    API->>LLM: Extrai metadados
    LLM-->>API: Metadados sugeridos
    API-->>User: temp_id + sugestões
    
    User->>API: POST /ingest-confirm/{temp_id}
    API->>Blob: Recupera arquivo temp
    API->>LLM: POST /ingest (chunks)
    LLM-->>API: Indexed + chunks_count
    API->>DB: Salva documento + versão
    API->>Blob: Move temp → permanent
    API-->>User: Success + document_id
\`\`\`

## Fluxo de Chat

\`\`\`mermaid
sequenceDiagram
    participant User as Frontend
    participant API as Backend
    participant DB as SQL Server
    participant LLM as LLM Server
    participant Search as AI Search
    participant OpenAI as Azure OpenAI
    
    User->>API: POST /chat/question
    API->>DB: Cria/obtém conversa
    API->>LLM: POST /question (pergunta)
    LLM->>Search: Busca docs relevantes
    Search-->>LLM: Top 5 docs
    LLM->>OpenAI: GPT-4o com contexto
    OpenAI-->>LLM: Resposta + cite sources
    LLM-->>API: Resposta estruturada
    API->>DB: Salva mensagem user + assistant
    API-->>User: Resposta + top_sources
\`\`\`

## Integrações

\`\`\`mermaid
graph TB
    API["Backend<br/>FastAPI"]
    
    AUTH["Azure Entra ID<br/>+ MSAL"]
    DB["Azure SQL<br/>Server"]
    BLOB["Azure Blob<br/>Storage"]
    LLMS["LLM Server<br/>FastAPI"]
    SEARCH["Azure AI<br/>Search"]
    OPENAI["Azure<br/>OpenAI"]
    REDIS["Redis<br/>Cache"]
    
    API -->|Autentica| AUTH
    API -->|CRUD docs| DB
    API -->|Upload/Download| BLOB
    API -->|POST ingest<br/>POST delete| LLMS
    LLMS -->|PUT embeddings| SEARCH
    LLMS -->|Chama| OPENAI
    API -->|Cache session| REDIS
\`\`\`
```

**Checklist**:
- [ ] Diagrama de ingestão (sequência)
- [ ] Diagrama de chat (sequência)
- [ ] Diagrama de integrações (graph)
- [ ] Validar que é consistente com código

---

### 2. Criar `docs/SECURITY.md`

**Conteúdo**:
```markdown
# Segurança

## Autenticação
- Azure Entra ID + MSAL
- JWT em cookie HTTPOnly
- Refresh token automático

## Autorização
- RBAC: roles definem o que cada usuário acessa
- Documentos: filtrados por allowed_countries, allowed_cities, min_role_level
- Admin: auditoria de toda ação

## Dados Sensíveis em Logs
- ✅ User IDs loggados
- ✅ Resource IDs
- ❌ Senhas
- ❌ Tokens
- ❌ Conteúdo de chat/docs
- ❌ OPENAI_API_KEY

## Encriptação
- Em trânsito: HTTPS (TLS 1.2+)
- Em repouso: Azure Storage encryption
- SQL: Encrypted at rest via Azure

## Validação de Input
- Pydantic models validam tudo
- Whitelist de campos aceitos
- File type detection + validation
```

---

## 🔵 BAIXA PRIORIDADE (Otimizações)

### 1. Criar `docs/PERFORMANCE.md`
- Índices de DB
- Caching strategy
- Query optimization

### 2. Criar `docs/MONITORING.md`
- Donde logs vão
- Alerts configurados
- Dashboards

### 3. Adicionar OpenAPI/Swagger Export
- Gerar `openapi.json`
- Exportar como PDF durante CI/CD

---

## 📊 TIMELINE RECOMENDADA

| Quando | O Quê | Tempo |
|--------|-------|-------|
| **ANTES da reunião** | Remover credenciais do .env | 30 min |
|  | Garantir .env.example existe | 5 min |
| **DIA APÓS reunião** | CONFIG_KEYS.md | 2h |
|  | RUN_LOCAL_GUIDE.md | 2h |
|  | Postman Collection | 1h |
| **SEMANA SEGUINTE** | Diagramas Mermaid | 1h |
|  | SECURITY.md | 1h |

**Prioridade Total**: 10 horas

---

## ✅ CHECKLIST FINAL

- [ ] `.env.example` sem credenciais (antes da reunião)
- [ ] Levar notebook com API rodando localmente
- [ ] Levar slides com diagramas
- [ ] Mostrar Swagger UI (`/docs`)
- [ ] Fazer 2-3 chamadas de API ao vivo

Pós-reunião:
- [ ] Commitar CONFIG_KEYS.md
- [ ] Commitar RUN_LOCAL_GUIDE.md
- [ ] Commitar Postman Collection
- [ ] Commitar/atualizar diagramas
- [ ] Remover credenciais do repositório (se commitadas)
- [ ] Configurar `.gitignore` para `.env`
