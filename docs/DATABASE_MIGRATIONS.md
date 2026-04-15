# 🗄️ Database - Migrations & Schema

Guia completo sobre migrações de banco de dados, schema DDL, histórico de mudanças e como aplicar novas migrações.

---

## 📋 Overview

**Sistema de Versioning**: Migrações incrementais em SQL

**Localização**: `/workspaces/Embeddings/db/`

**Banco**: Azure SQL Server (compatível com SQL Server 2019+)

**Histórico**: 25+ migrações aplicadas desde inception

---

## 1️⃣ Localização dos Arquivos

```
/workspaces/Embeddings/db/
├── schema.sql                                    # Schema base (tabelas principais)
├── schema_seed.sql                              # Dados iniciais (seed)
├── schema_sqlserver.sql                        # Schema SQL Server flavor
├── schema_dimensions.sql                        # Dimensões para BI
│
├── Migrações (histórico cronológico):
├── add_admins_table.sql                        # Adicionar tabela de admins
├── add_allowed_agents.sql                      # Adicionar allowed_agents
├── add_allowed_roles_column.sql                # Coluna de roles permitidas
├── add_category_fk.sql                         # Foreign key para categorias
├── add_created_updated_by_to_admins.sql       # Audit fields em admins
├── add_document_categories_json.sql            # Categorias em JSON
├── add_document_category_id.sql                # ID de categoria
├── add_filename_updated_by_to_versions.sql    # Audit em versions
├── add_job_title_roles_mapping.sql            # Mapeamento cargo-role
├── add_rating_comment.sql                      # Campos de avaliação
├── add_response_times_to_messages.sql         # Performance tracking
├── add_role_id_to_job_title_roles.sql         # Role ID normalization
├── add_summary_to_documents.sql                # Resumo de documentos
├── add_translations_to_metadata.sql            # Suporte a traduções
├── add_unmapped_role.sql                       # Role padrão para não-mapeados
├── add_user_preferences.sql                    # User preferences table
├── add_user_preferences_corrected.sql         # Correção de preferences
├── add_user_preferences_old.sql               # Backup de preferences
├── apply_dashboard_migration.sql              # Dashboard views
│
├── Migrações Python (aplicar dados):
├── migrate_conversations.py                   # Migração de conversa​s
├── migrate_locations_data.py                  # Localidades
├── migrate_temp_uploads.py                    # Uploads temporários
├── migrate_temp_uploads_nullable_user_id.py  # Fix nullable user_id
│
├── Views & Relatórios:
├── queries_allowed_roles.sql                 # VIEW de roles permitidas
│
└── Utilitários:
├── run_schema.py                              # Script para aplicar schema
```

---

## 2️⃣ Schema Principal

### Tabelas Principais

#### `documents`

```sql
CREATE TABLE documents (
    document_id           VARCHAR(36) PRIMARY KEY,
    title                 VARCHAR(255) NOT NULL,
    summary               TEXT,                          -- Resumo gerado por LLM
    category_id           INT,
    created_at            DATETIME DEFAULT GETDATE(),
    created_by            VARCHAR(255),                  -- user_id
    updated_at            DATETIME,
    updated_by            VARCHAR(255),
    allowed_countries     VARCHAR(500),                  -- CSV: "BR,US,MX"
    allowed_cities        VARCHAR(1000),                 -- CSV: "SP,RJ,CURITIBA"
    min_role_level        INT DEFAULT 1,                 -- RBAC filter
    collar                VARCHAR(50),                   -- "white", "blue", "all"
    plant_code            INT,                           -- Identificador de planta
    address_location_name VARCHAR(255),                  -- Localização física
    status                VARCHAR(20) DEFAULT 'active',  -- active, archived, deleted
    document_categories   JSON                           -- Metadata multilingue
);

-- Índices
CREATE INDEX idx_documents_created_by ON documents(created_by);
CREATE INDEX idx_documents_category_id ON documents(category_id);
CREATE INDEX idx_documents_status ON documents(status);
```

**O que significa**:
- **document_id**: UUID (550e8400-e29b-41d4-a716-...)
- **allowed_countries**: RBAC - document só visível para esses países
- **allowed_cities**: RBAC - filtro por cidade (São Paulo, Rio de Janeiro)
- **collar**: "white collar" = gestão, "blue collar" = operacional
- **document_categories**: JSON com categorias multilíngues

#### `versions`

```sql
CREATE TABLE versions (
    version_id      VARCHAR(36) PRIMARY KEY,
    document_id     VARCHAR(36) NOT NULL,
    version_number  INT NOT NULL,
    file_path       VARCHAR(500),                  -- blob://container/path/file.pdf
    filename        VARCHAR(255),                  -- Nome original do arquivo
    created_at      DATETIME DEFAULT GETDATE(),
    created_by      VARCHAR(255),
    updated_by      VARCHAR(255),
    status          VARCHAR(20) DEFAULT 'active',
    
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

CREATE INDEX idx_versions_document_id ON versions(document_id);
CREATE INDEX idx_versions_version_number ON versions(version_number);
```

**Propósito**: Histórico de versões de documentos
- Versão 1: PDF original
- Versão 2: PDF atualizado (novo conteúdo - nova ingestão)
- Cada versão tem embeddings separados

#### `chunks`

```sql
CREATE TABLE chunks (
    chunk_id        VARCHAR(36) PRIMARY KEY,
    document_id     VARCHAR(36) NOT NULL,
    version_id      VARCHAR(36) NOT NULL,
    chunk_index     INT NOT NULL,                  -- 0, 1, 2, ...
    content         VARCHAR(MAX),                  -- Conteúdo do chunk
    embedding       VARBINARY(MAX),                -- Vector embedding (float32 array)
    metadata        JSON,                          -- {"page": 1, "section": "..."}
    allowed_countries VARCHAR(500),                -- Herda do document
    allowed_cities    VARCHAR(1000),
    min_role_level    INT,
    created_at      DATETIME DEFAULT GETDATE(),
    
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES versions(version_id) ON DELETE CASCADE
);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_version_id ON chunks(version_id);
```

**Propósito**: Fragmentos do documento para busca semântica
- 1 documento = N chunks (ex: 10 chunks de 512 tokens cada)
- Cada chunk tem um embedding (vetor 1536D para GPT-4)
- Azure AI Search faz busca semântica nos embeddings

#### `conversations`

```sql
CREATE TABLE conversations (
    conversation_id    VARCHAR(36) PRIMARY KEY,
    user_id            VARCHAR(255) NOT NULL,
    title              VARCHAR(500),
    status             VARCHAR(20) DEFAULT 'open',  -- open, closed, archived
    created_at         DATETIME DEFAULT GETDATE(),
    updated_at         DATETIME,
    last_message_at    DATETIME,
    message_count      INT DEFAULT 0
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
```

#### `conversation_messages`

```sql
CREATE TABLE conversation_messages (
    message_id         VARCHAR(36) PRIMARY KEY,
    conversation_id    VARCHAR(36) NOT NULL,
    user_id            VARCHAR(255),
    role               VARCHAR(20),              -- "user" ou "assistant"
    content            VARCHAR(MAX),
    tokens             INT,                      -- Token count
    response_time_ms   INT,                      -- Tempo de resposta do LLM
    created_at         DATETIME DEFAULT GETDATE(),
    model_used         VARCHAR(50),              -- "gpt-4-turbo", "gpt-4o"
    
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_conversation_id ON conversation_messages(conversation_id);
```

#### `admins`

```sql
CREATE TABLE admins (
    admin_id          INT PRIMARY KEY IDENTITY(1,1),
    user_id           VARCHAR(255) UNIQUE NOT NULL,  -- Azure AD user_id
    email             VARCHAR(255) NOT NULL,
    name              VARCHAR(255),
    role              VARCHAR(50) DEFAULT 'support',  -- support, manager, owner
    created_at        DATETIME DEFAULT GETDATE(),
    created_by        VARCHAR(255),
    updated_at        DATETIME,
    updated_by        VARCHAR(255),
    is_active         BIT DEFAULT 1
);
```

#### `audit_log`

```sql
CREATE TABLE audit_log (
    log_id            INT PRIMARY KEY IDENTITY(1,1),
    user_id           VARCHAR(255),
    action            VARCHAR(100),              -- "document_uploaded", "admin_added"
    resource_type     VARCHAR(50),               -- "document", "admin", "conversation"
    resource_id       VARCHAR(255),
    details           JSON,
    status            VARCHAR(20),               -- "success", "failure"
    error_message     VARCHAR(500),
    ip_address        VARCHAR(45),
    user_agent        VARCHAR(500),
    created_at        DATETIME DEFAULT GETDATE()
);

CREATE INDEX idx_audit_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_created_at ON audit_log(created_at);
```

---

## 3️⃣ Histórico de Migrações

### Ordem de Aplicação

| # | Data | Arquivo | O que foi feito | Status |
|---|------|---------|-----------------|--------|
| 1 | - | schema.sql | Tabelas base (documents, versions, chunks) | ✅ Base |
| 2 | - | schema_seed.sql | Dados iniciais (seed) | ✅ Seed |
| 3 | Mar 2 | add_admins_table.sql | Criar tabela de admins | ✅ |
| 4 | Mar 2 | add_allowed_agents.sql | Coluna allowed_agents | ✅ |
| 5 | Mar 2 | add_allowed_roles_column.sql | Coluna allowed_roles | ✅ |
| 6 | Jan 9 | add_category_fk.sql | FK para categorias | ✅ |
| 7 | Mar 2 | add_created_updated_by_to_admins.sql | Audit em admins | ✅ |
| 8 | Mar 2 | add_document_categories_json.sql | document_categories JSON | ✅ |
| 9 | Mar 2 | add_document_category_id.sql | category_id coluna | ✅ |
| 10 | Mar 2 | add_filename_updated_by_to_versions.sql | Audit em versions | ✅ |
| 11 | Mar 2 | add_job_title_roles_mapping.sql | Mapeamento cargo-role | ✅ |
| 12 | Mar 2 | add_rating_comment.sql | Avaliação de respostas | ✅ |
| 13 | Mar 2 | add_response_times_to_messages.sql | Rastreamento de perf | ✅ |
| 14 | Mar 2 | add_role_id_to_job_title_roles.sql | Normalizar role_id | ✅ |
| 15 | Mar 2 | add_summary_to_documents.sql | Resumo (LLM) | ✅ |
| 16 | Mar 3 | add_translations_to_metadata.sql | Suporte multilíngue | ✅ |
| 17 | Mar 2 | add_unmapped_role.sql | Role default | ✅ |
| 18 | Mar 2 | add_user_preferences.sql | Preferências de usuário | ✅ |
| 19 | Mar 2 | add_user_preferences_corrected.sql | Correção | ✅ |
| 20 | Mar 2 | apply_dashboard_migration.sql | Dashboard views | ✅ |

---

## 4️⃣ Como Aplicar Migrações

### Pré-requisitos

```bash
# 1. Conectar ao SQL Server
# Opção 1: Local (via Docker Compose)
docker-compose up -d

# Opção 2: Azure (via Cloud Shell)
az sql db show --resource-group myRG --server myserver --name mydb

# 2. Obter connection string
# Local: Server=localhost;Database=luz_db;User Id=sa;Password=...
# Azure: Server=myserver.database.windows.net;Database=luz_db;Authentication=ActiveDirectoryInteractive;...
```

### Aplicar Schema Base

**Opção 1: Python Script**

```bash
cd /workspaces/Embeddings/db

python run_schema.py \
  --server localhost \
  --database luz_db \
  --user sa \
  --password "YourPassword123!"
```

**Opção 2: sqlcmd (CLI)**

```bash
# Local (Docker)
sqlcmd -S localhost \
  -U sa \
  -P "YourPassword123!" \
  -d luz_db \
  -i schema.sql
```

**Opção 3: Azure Portal**

1. Ir para **Azure Portal** → SQL Databases
2. Selecionar banco
3. **Query Editor**
4. Copiar conteúdo de `schema.sql`
5. Executar

### Aplicar Migrações Incrementais

**Executar uma migração específica:**

```bash
# Adicionar tabela de admins
sqlcmd -S localhost -U sa -P "pwd" -d luz_db -i db/add_admins_table.sql

# Adicionar campo category_id
sqlcmd -S localhost -U sa -P "pwd" -d luz_db -i db/add_document_category_id.sql
```

**Aplicar todas as migrações (ordem sequencial):**

```bash
# Script para aplicar em ordem
#!/bin/bash
MIGRATIONS=(
    "add_admins_table.sql"
    "add_allowed_agents.sql"
    "add_allowed_roles_column.sql"
    # ... resto
)

for migration in "${MIGRATIONS[@]}"; do
    echo "Applying $migration..."
    sqlcmd -S localhost -U sa -P "pwd" -d luz_db -i "db/$migration"
    [ $? -ne 0 ] && echo "FAILED: $migration" && exit 1
done

echo "✅ All migrations applied!"
```

### Dados Iniciais (Seed)

```bash
# Inserir dados padrão
sqlcmd -S localhost -U sa -P "pwd" -d luz_db -i db/schema_seed.sql
```

**Verifica**:
- Tabela `roles` com roles padrão
- Tabela `job_titles` com cargos
- Tabela `categories` com categorias de documentos
- Tabela `locations` com países/cidades

---

## 5️⃣ Criar Nova Migração

### Template

```sql
-- db/add_new_feature.sql
-- Data: 2026-03-20
-- Descrição: Adicionar suporte para feature XYZ

-- Verificação: não falhar se já existir
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='documents' AND COLUMN_NAME='new_column')
BEGIN
    ALTER TABLE documents
    ADD new_column VARCHAR(100);
    
    PRINT 'Column new_column added to documents';
END
ELSE
BEGIN
    PRINT 'Column new_column already exists - skipping';
END;

-- Índice para performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_documents_new_column')
BEGIN
    CREATE INDEX idx_documents_new_column ON documents(new_column);
    PRINT 'Index created';
END;
```

### Passo-a-passo

1. **Criar arquivo de migração**:
   ```bash
   touch db/add_my_feature_YYYYMMDD.sql
   ```

2. **Escrever SQL com guards** (IF NOT EXISTS):
   ```sql
   IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'my_table')
   BEGIN
       CREATE TABLE my_table (id INT PRIMARY KEY);
   END;
   ```

3. **Testar localmente**:
   ```bash
   docker-compose up -d
   sqlcmd -S localhost -U sa -P "pwd" -d luz_db -i db/add_my_feature.sql
   
   # Verificar
   sqlcmd -S localhost -U sa -P "pwd" -d luz_db -Q "SELECT * FROM my_table;"
   ```

4. **Commit no git**:
   ```bash
   git add db/add_my_feature_YYYYMMDD.sql
   git commit -m "db: add new migration for feature XYZ"
   ```

5. **CI/CD aplica na PROD**:
   - Pipeline executa `sqlcmd -i db/add_my_feature.sql`

---

## 6️⃣ Rollback (Desfazer)

**Não temos sistema automático de rollback.**

### Opção 1: Revertida Manual

```sql
-- db/rollback_add_my_feature.sql

-- Remover coluna
ALTER TABLE documents DROP COLUMN my_column;

-- Remover tabela
DROP TABLE IF EXISTS my_table;

-- Remover view
DROP VIEW IF EXISTS my_view;

PRINT 'Rollback completed';
```

Depois:
```bash
sqlcmd -S localhost -U sa -P "pwd" -d luz_db -i db/rollback_add_my_feature.sql
```

### Opção 2: Restore a Backup

```bash
# Azure: Restore de backup automático
az sql db restore \
  --resource-group myRG \
  --server myserver \
  --name luz_db \
  --restore-point-in-time "2026-03-20T14:00:00Z"
```

---

## 7️⃣ Verificar Schema Atual

### Tabelas Existentes

```bash
sqlcmd -S localhost -U sa -P "pwd" -d luz_db -Q "
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'dbo'
ORDER BY TABLE_NAME;
"
```

### Colunas de uma Tabela

```bash
sqlcmd -S localhost -U sa -P "pwd" -d luz_db -Q "
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'documents'
ORDER BY ORDINAL_POSITION;
"
```

### Índices

```bash
sqlcmd -S localhost -U sa -P "pwd" -d luz_db -Q "
SELECT name, type_desc 
FROM sys.indexes 
WHERE object_id = OBJECT_ID('documents')
AND name IS NOT NULL;
"
```

### Foreign Keys

```bash
sqlcmd -S localhost -U sa -P "pwd" -d luz_db -Q "
SELECT CONSTRAINT_NAME, TABLE_NAME, REFERENCED_TABLE_NAME 
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE CONSTRAINT_TYPE = 'FOREIGN KEY';
"
```

---

## 8️⃣ Performance & Indices

### Índices Críticos

**Buscas principais**:

```sql
-- Documentos por usuário
SELECT * FROM documents WHERE created_by = '@id' → idx_documents_created_by

-- Conversas por usuário
SELECT * FROM conversations WHERE user_id = '@id' → idx_conversations_user_id

-- Chunks por documento
SELECT * FROM chunks WHERE document_id = '@id' → idx_chunks_document_id

-- Mensagens por conversa
SELECT * FROM conversation_messages WHERE conversation_id = '@id' → idx_messages_conversation_id
```

Todos têm índices.

### Monitorar Performance

```bash
# Ver tamanho de tabelas
sqlcmd -S localhost -U sa -P "pwd" -d luz_db -Q "
SELECT 
    t.NAME AS TableName,
    s.name AS SchemaName,
    p.rows AS RowCounts,
    SUM(au.total_pages) * 8 AS TotalSpaceKB
FROM sys.tables t
INNER JOIN sys.indexes i ON t.OBJECT_ID = i.object_id
INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN sys.allocation_units au ON p.partition_id = au.container_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
GROUP BY t.NAME, s.name, p.rows
ORDER BY SUM(au.total_pages) DESC;
"
```

---

## 9️⃣ Troubleshooting

### "Cannot insert NULL into column X"

**Causa**: Coluna não-nullable mas sem default, e tentando inserir dados antigos

**Solução**:
```sql
-- Opção 1: Adicionar DEFAULT
ALTER TABLE documents
ADD CONSTRAINT DF_documents_status DEFAULT 'active' FOR status;

-- Opção 2: Atualizar dados existentes primeiro
UPDATE documents SET new_column = 'default_value' WHERE new_column IS NULL;
```

### "The INSERT, UPDATE, or DELETE statement conflicted with a FOREIGN KEY constraint"

**Causa**: Tentando inserir/deletar documento que viola FK

**Solução**:
```sql
-- Ver FKs
SELECT CONSTRAINT_NAME 
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
WHERE TABLE_NAME = 'documents' 
AND CONSTRAINT_TYPE = 'FOREIGN KEY';

-- Desativar temporariamente
ALTER TABLE documents NOCHECK CONSTRAINT ALL;

-- Fazer operação

-- Reativar
ALTER TABLE documents CHECK CONSTRAINT ALL;
```

### "Timeout expired"

**Causa**: Migração muito grande, schema lock atingido

**Solução**:
```bash
# Aumentar timeout
sqlcmd -S localhost -U sa -P "pwd" -d luz_db -C 300 -i migration.sql

# Ou adicionar com ONLINE=ON para operações menores
ALTER TABLE documents ADD COLUMN new_col INT ONLINE = ON;
```

---

## 🔟 CI/CD Integration

### Azure Pipeline

```yaml
# azure-pipelines.yml

stages:
- stage: ApplyMigrations
  jobs:
  - job: RunMigrations
    steps:
    - task: AzureCLI@2
      inputs:
        azureSubscription: 'my-subscription'
        scriptType: 'bash'
        scriptLocation: 'scriptPath'
        scriptPath: '$(Build.SourcesDirectory)/deploy-db-migrations.sh'
        
# deploy-db-migrations.sh

#!/bin/bash
set -e

# 1. Obter connection string de KeyVault
CONN_STRING=$(az keyvault secret show --vault-name mykvault --name SqlServerConnString --query value -o tsv)

# 2. Executar migrações na ordem
for migration in db/add_*.sql; do
    echo "Applying $migration..."
    sqlcmd -S myserver.database.windows.net \
           -U $DB_USER \
           -P $DB_PASSWORD \
           -d luz_db \
           -i "$migration"
done

echo "✅ All migrations applied successfully"
```

---

## 📚 Documentação Relacionada

- [BACKEND_OVERVIEW.md](BACKEND_OVERVIEW.md) - Arquitetura geral
- [CONFIG_KEYS.md](CONFIG_KEYS.md) - Variáveis de banco
- [RUN_LOCAL_COMPLETE_GUIDE.md](RUN_LOCAL_COMPLETE_GUIDE.md) - Setup local com DB
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md#database) - Problemas SQL

---

## 🔗 Referências

- [SQL Server Documentation](https://learn.microsoft.com/en-us/sql/sql-server/)
- [Azure SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/)
- [sqlcmd Reference](https://learn.microsoft.com/en-us/sql/tools/sqlcmd-utility)
