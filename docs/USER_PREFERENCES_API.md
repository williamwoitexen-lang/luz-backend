# User Preferences & Memory API

## Overview

A API de preferências do usuário gerencia as configurações individuais incluindo idioma preferido e preferências de memória do agente de IA.

## Database Schema

```sql
CREATE TABLE user_preferences (
    user_id VARCHAR(255) PRIMARY KEY,
    preferred_language VARCHAR(10) DEFAULT 'pt-BR',
    memory_preferences NVARCHAR(MAX),  -- JSON
    last_update DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

## Fields

- **user_id**: Identificador único do usuário
- **preferred_language**: Idioma preferido (ex: "pt-BR", "en-US")
- **memory_preferences**: Configurações de memória em formato JSON (4 linhas de histórico por padrão)
- **last_update**: Timestamp da última atualização

## Memory Preferences Structure

```json
{
  "max_history_lines": 4,           // Número de linhas do histórico
  "summary_enabled": true,           // Habilitar resumo de conversas
  "context_window": "4_lines",       // Tamanho da janela de contexto
  "memory_type": "long_term",        // short_term ou long_term
  "custom_preferences": {}           // Preferências customizadas adicionais
}
```

## Endpoints

### 1. GET - Obter preferências completas do usuário

**Endpoint:** `GET /api/v1/user/preferences/{user_id}`

**Descrição:** Retorna todas as preferências e configurações de memória do usuário.

**Exemplo de Requisição:**
```bash
curl -X GET "http://localhost:8000/api/v1/user/preferences/user_123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Resposta (200):**
```json
{
  "user_id": "user_123",
  "preferred_language": "pt-BR",
  "memory_preferences": {
    "max_history_lines": 4,
    "summary_enabled": true,
    "context_window": "4_lines",
    "memory_type": "long_term",
    "custom_preferences": null
  },
  "last_update": "2026-02-13T10:30:45.123456"
}
```

**Resposta (404):**
```json
{
  "detail": "Preferências não encontradas para usuário user_123"
}
```

---

### 2. POST - Criar ou atualizar preferências

**Endpoint:** `POST /api/v1/user/preferences/{user_id}`

**Descrição:** Cria ou atualiza as preferências completas do usuário.

**Exemplo de Requisição:**
```bash
curl -X POST "http://localhost:8000/api/v1/user/preferences/user_123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "preferred_language": "pt-BR",
    "memory_preferences": {
      "max_history_lines": 4,
      "summary_enabled": true,
      "context_window": "4_lines",
      "memory_type": "long_term",
      "custom_preferences": {
        "tone": "formal",
        "response_length": "concise"
      }
    }
  }'
```

**Resposta (200):**
```json
{
  "user_id": "user_123",
  "preferred_language": "pt-BR",
  "memory_preferences": {
    "max_history_lines": 4,
    "summary_enabled": true,
    "context_window": "4_lines",
    "memory_type": "long_term",
    "custom_preferences": {
      "tone": "formal",
      "response_length": "concise"
    }
  },
  "last_update": "2026-02-13T10:35:22.654321"
}
```

---

### 3. PUT - Atualizar preferências (idêntico ao POST)

**Endpoint:** `PUT /api/v1/user/preferences/{user_id}`

**Descrição:** Mesmo comportamento do POST.

```bash
curl -X PUT "http://localhost:8000/api/v1/user/preferences/user_123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "preferred_language": "en-US",
    "memory_preferences": {
      "max_history_lines": 6,
      "summary_enabled": true,
      "context_window": "6_lines",
      "memory_type": "long_term"
    }
  }'
```

---

### 4. GET - Obter apenas preferências de memória

**Endpoint:** `GET /api/v1/user/preferences/{user_id}/memory`

**Descrição:** Retorna apenas as configurações de memória do usuário.

**Exemplo:**
```bash
curl -X GET "http://localhost:8000/api/v1/user/preferences/user_123/memory" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Resposta (200):**
```json
{
  "max_history_lines": 4,
  "summary_enabled": true,
  "context_window": "4_lines",
  "memory_type": "long_term",
  "custom_preferences": null
}
```

---

### 5. PATCH - Atualizar apenas preferências de memória

**Endpoint:** `PATCH /api/v1/user/preferences/{user_id}/memory`

**Descrição:** Atualiza apenas as preferências de memória, deixando as demais configurações intactas.

**Exemplo:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/user/preferences/user_123/memory" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "max_history_lines": 6,
    "summary_enabled": false,
    "context_window": "6_lines",
    "memory_type": "long_term",
    "custom_preferences": {
      "prioritize_recent": true
    }
  }'
```

**Resposta (200):**
```json
{
  "max_history_lines": 6,
  "summary_enabled": false,
  "context_window": "6_lines",
  "memory_type": "long_term",
  "custom_preferences": {
    "prioritize_recent": true
  }
}
```

---

## Exemplos de Integração

### JavaScript/TypeScript
```javascript
// Obter preferências
async function getUserPreferences(userId, token) {
  const response = await fetch(`/api/v1/user/preferences/${userId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}

// Atualizar memória
async function updateMemoryPreferences(userId, memory, token) {
  const response = await fetch(
    `/api/v1/user/preferences/${userId}/memory`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(memory)
    }
  );
  return response.json();
}
```

### Python
```python
import requests

def get_user_preferences(user_id: str, token: str):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'http://localhost:8000/api/v1/user/preferences/{user_id}',
        headers=headers
    )
    return response.json()

def update_memory_preferences(user_id: str, memory_prefs: dict, token: str):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.patch(
        f'http://localhost:8000/api/v1/user/preferences/{user_id}/memory',
        json=memory_prefs,
        headers=headers
    )
    return response.json()
```

---

## Notas Importantes

1. **Validação de Token:** Todos os endpoints requerem autenticação via Bearer Token
2. **User ID:** Deve corresponder ao `user_id` autenticado
3. **JSON Storage:** `memory_preferences` é armazenado como JSON no banco (SQL Server)
4. **Default Values:** Se não fornecidos, valores padrão são aplicados:
   - `max_history_lines`: 4
   - `summary_enabled`: true
   - `context_window`: "4_lines"
   - `memory_type`: "short_term"

5. **Auto-creation:** Se o usuário não existir, será criado automaticamente no PATCH

---

## Fluxo Recomendado

1. **Primeira requisição (login):** Use POST para criar preferências padrão
2. **Atualizações pontuais:** Use PATCH para atualizar apenas memory_preferences
3. **Sincronização:** Busque preferências ao inicializar o chat com GET

```
[Login] → POST /preferences/{user_id}
[Chat Init] → GET /preferences/{user_id}/memory
[During Chat] → PATCH /preferences/{user_id}/memory (quando necessário)
```
