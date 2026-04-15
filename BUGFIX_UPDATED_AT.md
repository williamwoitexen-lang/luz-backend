# Correção: Last Update Date não aparecia no GET de documentos

## Problema
- O endpoint GET de documentos não retornava a "Data Atualização" corretamente
- O campo `updated_at` ficava igual a `created_at` mesmo após atualizações do documento

## Causa Raiz
1. Quando uma nova versão era criada (`create_version`), o campo `updated_at` da tabela `documents` não era atualizado
2. Não havia trigger no banco de dados para atualizar automaticamente este campo

## Solução Implementada

### 1. Update em Python (Imediato)
**Arquivo:** `app/services/sqlserver_documents.py`
- Adicionado UPDATE do `updated_at` na função `create_version()`
- Agora sempre que uma nova versão é criada, o documento é marcado como atualizado

```python
# Atualizar updated_at do documento para refletir a nova versão
update_doc_query = "UPDATE documents SET updated_at = ? WHERE document_id = ?"
sql.execute(update_doc_query, [now, document_id])
logger.info(f"[create_version] Updated document.updated_at = {now}")
```

### 2. Trigger SQL Server (Robustez)
**Arquivo:** `db/add_trigger_updated_at.sql`
- Criado trigger SQL Server que atualiza `updated_at` automaticamente em qualquer UPDATE
- Protegido contra loop infinito usando `IF UPDATE()` para verificar quais colunas foram alteradas
- Evita recursão ao ignorar atualizações que modifiquem apenas `updated_at`

## Como Aplicar

### Executar a migration:
```bash
# Conectar ao SQL Server
sqlcmd -S <server> -U <user> -P <password> -d <database> -i db/add_trigger_updated_at.sql
```

Ou executar manualmente pelo SQL Server Management Studio:
```sql
-- Copiar e colar o conteúdo de db/add_trigger_updated_at.sql
```

## Verificação

Após aplicar, testar:
```python
# GET /api/v1/documents
# Checkar se "updated_at" está retornando com valor recente
{
  "documents": [
    {
      "document_id": "...",
      "created_at": "2025-03-13T10:30:00",
      "updated_at": "2025-03-23T12:44:00",  # ← Agora diferente de created_at
      ...
    }
  ]
}
```

## Campos Afetados pelo Trigger
O trigger atualiza `updated_at` quando qualquer destes campos muda:
- `title`
- `category_id`
- `is_active`
- `min_role_level`
- `allowed_roles`, `allowed_countries`, `allowed_cities`, `location_ids`
- `collar`, `plant_code`
- `summary`

## Compatibilidade
- ✅ Funciona com SQL Server 2012+
- ✅ Não causa loop infinito
- ✅ Logging detalhado em `create_version()`
