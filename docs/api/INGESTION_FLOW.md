# Fluxo de Ingestão de Documentos

## Resumo
- **Novo documento**: Envia arquivo SEM `document_id` → Sistema gera ID sequencial (1, 2, 3...)
- **Update existente**: Envia arquivo COM `document_id` → Sistema cria nova versão (v1 → v2 → v3)

---

## 1. NOVO DOCUMENTO (Ingestão Normal)

### Request
```bash
curl -X POST http://localhost:8000/api/v1/documents/ingest \
  -F "file=@documento.pdf" \
  -F "user_id=user@company.com" \
  -F "min_role_level=2"
  # ❌ NÃO incluir document_id
```

### Fluxo Interno
```
1. Router (/ingest) recebe form data
2. Valida min_role_level (converte "0" → 0, depois max(0,1) = 1)
3. Chama DocumentService.ingest_document()
4. create_document() é chamado SEM document_id
5. SQL Server: get_next_document_id() executa MAX(document_id)+1
   - Primeiro doc: 1
   - Segundo doc: 2
   - Terceiro doc: 3
6. Documento criado com ID gerado
7. Versão criada com version_number=1
8. Arquivo salvo em Blob: /1/documento.pdf
9. Enviado para LLM Server com:
   - document_id: 1
   - version_id: 1
10. Response retorna document_id=1, version=1
```

### Response (200 OK)
```json
{
  "status": "success",
  "document_id": 1,
  "version": 1,
  "chunks_count": 25,
  "blob_path": "https://storage.blob.core.windows.net/chat-rh/1/documento.pdf",
  "message": "Document ingested successfully with 25 chunks"
}
```

---

## 2. UPDATE DE DOCUMENTO EXISTENTE

### Request (Frontend envia document_id)
```bash
curl -X POST http://localhost:8000/api/v1/documents/ingest \
  -F "file=@documento_v2.pdf" \
  -F "user_id=user@company.com" \
  -F "min_role_level=2" \
  -F "document_id=1"
  # ✅ INCLUIR document_id do documento existente
```

### Fluxo Interno
```
1. Router (/ingest) recebe form data COM document_id=1
2. Valida min_role_level
3. Chama DocumentService.ingest_document(document_id=1)
4. create_document() é chamado COM document_id=1
5. SQL Server: INSERT INTO documents com document_id=1
6. create_version() é chamado:
   - Query: SELECT MAX(version_number)+1 FROM versions WHERE document_id=1
   - Primeira update: version=2
   - Segunda update: version=3
   - Etc.
7. Documento usa ID existente (não cria novo)
8. Versão criada com version_number=2
9. Arquivo salvo em Blob: /1/documento_v2.pdf
10. Enviado para LLM Server com:
   - document_id: 1
   - version_id: 2 (nova versão!)
11. Response retorna document_id=1, version=2
```

### Response (200 OK)
```json
{
  "status": "success",
  "document_id": 1,
  "version": 2,
  "chunks_count": 28,
  "blob_path": "https://storage.blob.core.windows.net/chat-rh/1/documento_v2.pdf",
  "message": "Document updated successfully with 28 chunks"
}
```

---

## 3. DOCUMENTOS INATIVOS (is_active=false)

Quando você envia um documento com `is_active=false`:

### Request
```bash
curl -X POST http://localhost:8000/api/v1/documents/ingest \
  -F "file=@documento.pdf" \
  -F "user_id=user@company.com" \
  -F "is_active=false"
```

### Fluxo Interno
```
1. Router recebe form data com is_active=false
2. Valida user_id, file, etc
3. Chama DocumentService.ingest_document(is_active=false)
4. SQL Server: Cria/atualiza documento com is_active=0
5. Blob Storage: Salva arquivo normalmente
6. Cria versão no SQL Server
7. ❌ NÃO chama llm_client.ingest_document()
   → Documento não fica disponível no LLM chat
8. Response retorna com warning
```

### Response (200 OK)
```json
{
  "status": "success",
  "document_id": 5,
  "version": 1,
  "is_active": false,
  "message": "Document saved but NOT sent to LLM Server (is_active=false)"
}
```

### Reativar Documento Depois

Enviar requisição **SEM arquivo** (apenas update de metadados):

```bash
curl -X POST http://localhost:8000/api/v1/documents/ingest \
  -F "user_id=user@company.com" \
  -F "document_id=5" \
  -F "is_active=true"
  # ❌ NÃO incluir "file"
```

### Fluxo de Reativação
```
1. Router detecta: file é None + is_active=true + document_id fornecido
2. Entra em "MODO 2: Update de Metadados"
3. SQL Server: UPDATE documents SET is_active=1 WHERE document_id=5
4. Busca última versão do documento (version_id=1)
5. Recupera arquivo do Blob Storage
6. ✅ Chama llm_client.ingest_document() com última versão
   → Documento volta a estar disponível no chat
7. Response retorna com sucesso
```

### Response (200 OK)
```json
{
  "status": "success",
  "document_id": 5,
  "is_active": true,
  "message": "Document metadata updated and re-ingested in LLM Server"
}
```

---

## 4. Estrutura de Dados no SQL Server

### Tabela: documents
```sql
CREATE TABLE documents (
  document_id       INT PRIMARY KEY,      -- 1, 2, 3, ... (gerado sequencialmente)
  title             NVARCHAR(255),
  user_id           NVARCHAR(255),
  min_role_level    INT,                  -- 1=Employee, 2=Manager, 3=CEO
  allowed_countries NVARCHAR(MAX),
  allowed_cities    NVARCHAR(MAX),
  collar            NVARCHAR(50),
  plant_code        INT,
  created_at        DATETIME,
  updated_at        DATETIME
);
```

### Tabela: versions
```sql
CREATE TABLE versions (
  version_id        VARCHAR(36) PRIMARY KEY,  -- UUID
  document_id       INT FOREIGN KEY,           -- referencia documents.document_id
  version_number    INT,                       -- 1, 2, 3, ... por documento
  blob_path         NVARCHAR(500),             -- URL no Azure Blob
  created_at        DATETIME,
  is_active         BIT
);
```

### Exemplo: Histórico de Updates
```
documents table:
- ID=1, title="Benefits 2024", updated_at=2025-12-01

versions table:
- v1: document_id=1, version=1, blob=/1/benefits_original.pdf, created=2025-12-01
- v2: document_id=1, version=2, blob=/1/benefits_updated_jan.pdf, created=2025-12-15
- v3: document_id=1, version=3, blob=/1/benefits_final_feb.pdf, created=2025-12-20
```

---

## 5. Validação de min_role_level

### Código no Router (documents.py, linhas 364-370)
```python
# Converter string para int se necessário, depois garantir >= 1
try:
    min_role_level = int(min_role_level) if isinstance(min_role_level, str) else min_role_level
except (ValueError, TypeError):
    min_role_level = 1

min_role_level = max(min_role_level, 1)
```

### Exemplos de Conversão
| Input | After int() | After max() | Resultado |
|-------|-------------|-------------|-----------|
| "0" | 0 | max(0,1)=1 | ✅ 1 |
| "0" (int) | 0 | max(0,1)=1 | ✅ 1 |
| "2" | 2 | max(2,1)=2 | ✅ 2 |
| "" | ValueError | exception → 1 | ✅ 1 |
| "abc" | ValueError | exception → 1 | ✅ 1 |

**Resultado**: min_role_level SEMPRE chega no LLM Server como >= 1 ✓

---

## 5. Endpoint do LLM Server

### POST /api/v1/documents
Payload enviado:
```json
{
  "document_id": 1,
  "source_file": "documento.pdf",
  "doc_type": "pdf",
  "content": "... arquivo em CSV ...",
  "allowed_countries": ["Brazil", "Mexico"],
  "allowed_cities": ["São Paulo", "Rio de Janeiro"],
  "min_role_level": 1,
  "document_type": "policy",
  "language": "pt",
  "version_id": 1
}
```

### Validação do LLM Server
```python
# LLM Server Pydantic model
class DocumentIngestion(BaseModel):
    document_id: int
    min_role_level: int
    # ...

    @field_validator('min_role_level')
    def validate_min_role_level(cls, v):
        if v < 1:
            raise ValueError('Input should be greater than or equal to 1')  # Este é o erro 422!
        return v
```

Como nosso router agora **SEMPRE** envia `min_role_level >= 1`, o LLM Server aceitará ✓

---

## 6. Fluxo Frontend (Conceitual)

### Novo Documento
```javascript
async function uploadNewDocument(file, metadata) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", getCurrentUserId());
  formData.append("min_role_level", metadata.min_role_level || 1);
  // ❌ NÃO adicionar document_id
  
  const response = await fetch("/api/v1/documents/ingest", {
    method: "POST",
    body: formData
  });
  
  const result = await response.json();
  console.log(`✓ Documento criado com ID ${result.document_id}, Versão 1`);
}
```

### Update de Documento
```javascript
async function updateDocument(documentId, file, metadata) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", getCurrentUserId());
  formData.append("min_role_level", metadata.min_role_level);
  formData.append("document_id", documentId);  // ✅ Enviar o ID existente
  
  const response = await fetch("/api/v1/documents/ingest", {
    method: "POST",
    body: formData
  });
  
  const result = await response.json();
  console.log(`✓ Documento ID ${documentId} atualizado para versão ${result.version}`);
}
```

---

## 7. Resumo para o Usuário

### Como Funciona

**Novo documento**:
```
1. Front envia arquivo (sem document_id)
2. Backend gera ID sequencial: 1, 2, 3, ...
3. Cria versão 1 automaticamente
4. Salva em Blob com caminho /1/arquivo.pdf
```

**Update de documento**:
```
1. Front envia arquivo + document_id existente
2. Backend usa ID fornecido (não gera novo)
3. Cria versão 2 (próxima sequencial)
4. Salva em Blob com caminho /1/arquivo_v2.pdf
5. Histórico preservado (v1, v2, v3...)
```

### Validação
```
✅ min_role_level SEMPRE >= 1 (requisito LLM Server)
✅ document_id SEMPRE numérico e sequencial
✅ version_id SEMPRE incrementado para updates
✅ Blob Storage organizado por document_id
```

---

## Status da Implementação

- ✅ Geração sequencial de document_id
- ✅ Validação de min_role_level >= 1
- ✅ Criação automática de versão para updates
- ✅ Integração com LLM Server
- ✅ Armazenamento em Blob Storage
- ✅ SQL Server metadados

**Pronto para usar!** 🚀
