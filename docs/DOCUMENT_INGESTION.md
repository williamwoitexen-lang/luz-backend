# Ingestão de Documentos com Extração de Metadados

## Fluxo de Ingestão em 2 Passos

### **Step 1: Preview (Extração de Metadados)**

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

### **Step 2: Confirm (Ingestão Definitiva)**

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

---

## ⚠️ Documentos Inativos

Quando um documento é marcado com `is_active=false`:

```bash
POST /api/v1/documents/ingest
Content-Type: multipart/form-data

user_id: john_doe
is_active: false
file: documento.pdf
```

**Comportamento:**
- ✅ Versão é salva no SQL Server (banco de dados)
- ✅ Arquivo é salvo no Blob Storage
- ❌ **NÃO é enviado para LLM Server** (documentação não fica disponível no chat)

**Quando reativar o documento:**
```bash
POST /api/v1/documents/ingest
user_id: john_doe
document_id: existing_uuid
is_active: true
# Sem arquivo - apenas update de metadados
```

- A **última versão** será re-ingestada no LLM Server automaticamente
- Conhecimento volta a estar disponível no chat

---

## Tratamento de Falhas do LLM Server

Se o LLM Server estiver indisponível:

### **Opção 1: Pular extração (dev local)**

```bash
export SKIP_LLM_METADATA_EXTRACTION=true
```

Retorna metadados vazios com confidence="low"

### **Opção 2: Deixar falhar (produção)**

Sem a variável, `ingest-preview` vai falhar e retornar erro 500.

---

## Download de Documentos com Versionamento

### Obter Versão Específica de um Documento

**GET** `/api/v1/documents/{document_id}/download?version_number=N`

Permite baixar uma versão anterior de um documento já ingestado.

**Parameters:**
- `document_id` (required): ID do documento
- `version_number` (optional): Número da versão (ex: 1, 2, 3). Se omitido, retorna a versão mais recente.

**Exemplo - Baixar versão específica:**

```bash
# Baixar versão 2 de um documento
curl -X GET "http://localhost:8000/api/v1/documents/doc-123/download?version_number=2" \
  -H "Authorization: Bearer {token}" \
  -o documento_v2.pdf
```

**Exemplo - Baixar versão mais recente (padrão):**

```bash
# Baixar versão mais recente (sem especificar version_number)
curl -X GET "http://localhost:8000/api/v1/documents/doc-123/download" \
  -H "Authorization: Bearer {token}" \
  -o documento_latest.pdf
```

**Response:** Arquivo binário do documento

**Exemplos de Cliente:**

**JavaScript:**
```javascript
// Baixar versão específica
const response = await fetch(
  `/api/v1/documents/${documentId}/download?version_number=2`,
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);

const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'document_v2.pdf';
a.click();
```

---

## Gerenciamento de Localidades (Location IDs)

### Especificar Localidades Permitidas na Ingestão

Quando ingesta um documento, você pode especificar em quais localidades esse documento é acessível. Isso é útil para restringir acesso a documentos por localização geográfica ou operacional.

### **Formato de Entrada**

O campo `allowed_locations` ou `location_ids` aceita três formatos:

**Formato 1: JSON Array String (Recomendado)**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/ingest" \
  -F "file=@documento.pdf" \
  -F "user_id=emp_12345" \
  -F "allowed_locations=[1,2,3,4]"
```

**Formato 2: Comma-Separated String**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/ingest" \
  -F "file=@documento.pdf" \
  -F "user_id=emp_12345" \
  -F "allowed_locations=1,2,3,4"
```

**Formato 3: JSON String**
```bash
-F "allowed_locations=[1, 2, 3, 4]"
```

**Formato 4: Sem Especificar (Vazio/Null)**
```bash
# O documento fica disponível em TODAS as localidades
curl -X POST "http://localhost:8000/api/v1/documents/ingest" \
  -F "file=@documento.pdf" \
  -F "user_id=emp_12345"
```

### **Localidades Disponíveis**

O sistema possui localidades Eletrolux predefinidas:

| location_id | País | Cidade | Tipo | Exemplo |
|-------------|------|--------|------|---------|
| 1 | Argentina | Buenos Aires | Office | Buenos Aires Office |
| 3 | Argentina | Rosario | Factory | Rosario Plant |
| 8 | Brazil | Curitiba | Warehouse | Guabirotuba |
| 9 | Brazil | Curitiba | Warehouse | COP |
| 18 | Brazil | Manaus | Factory | Fábrica Manaus |
| 23 | Brazil | São Carlos | Factory | Fábrica São Carlos |
| 29 | Brazil | São Paulo | Office | Torre Z |
| 34 | Chile | Santiago | Factory | Santiago Plant |
| ... | ... | ... | ... | ... |

Para lista completa de localidades, consulte [dim_electrolux_locations na schema](../db/schema_sqlserver_complete.sql).

### Exemplo Completo - Ingestão com Location IDs

```bash
# Ingestir documento disponível em 3 localidades específicas
curl -X POST "http://localhost:8000/api/v1/documents/ingest-preview" \
  -F "file=@beneficios_saude.pdf" \
  -F "user_id=emp_12345" \
  -F "allowed_locations=[8,9,23]"  # Curitiba, Manaus, São Carlos

# Obter temp_id da resposta, depois confirmar:
curl -X POST "http://localhost:8000/api/v1/documents/ingest-confirm/{temp_id}" \
  -F "user_id=emp_12345" \
  -F "allowed_locations=[8,9,23]"
```

### Exemplos em Diferentes Linguagens

**Python:**
```python
import requests

document_data = {
    'user_id': 'emp_12345',
    'allowed_locations': '[8, 9, 23]',  # JSON string format
}

files = {
    'file': open('documento.pdf', 'rb')
}

response = requests.post(
    'http://localhost:8000/api/v1/documents/ingest-preview',
    data=document_data,
    files=files
)

print(response.json())
```

**JavaScript:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('user_id', 'emp_12345');
formData.append('allowed_locations', JSON.stringify([8, 9, 23]));

const response = await fetch('/api/v1/documents/ingest-preview', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result.temp_id);
```

### Comportamento de Restrição

- Se `allowed_locations` está vazio/null: documento disponível em **TODAS** as localidades
- Se `allowed_locations` tem valores: documento disponível **APENAS** nas localidades especificadas
- Quando um usuário faz uma pergunta no chat, o sistema filtra documentos pela sua localidade

---

## Variáveis de Ambiente

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| `LLM_SERVER_URL` | URL do servidor LLM | Sim |
| `SKIP_LLM_METADATA_EXTRACTION` | Se true, pula extração de metadados | Não (dev) |
| `SKIP_LLM_SERVER` | Se true, pula toda integração LLM | Não |

---

## Tratamento de Erros

| Erro | Causa | Solução |
|------|-------|--------|
| 500 - "LLM Server connection error" | LLM Server offline | Subir LLM Server ou usar SKIP_LLM_METADATA_EXTRACTION=true |
| 500 - "LLM Server timeout" | LLM Server lento | Aumentar LLM_SERVER_TIMEOUT |
| 400 - "Bad request" | Arquivo inválido | Verificar arquivo enviado |

