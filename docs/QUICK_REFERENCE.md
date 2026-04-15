# ⚡ Quick Reference - Admin & Prompts APIs

**Versão**: 1.0 | **Data**: 23 de Fevereiro de 2026

---

## 🔐 Admin Management API - Quick Ref

### Base URL
```
/api/v1/admins
```

### Endpoints

| Método | Endpoint | Auth | Descrição |
|--------|----------|------|-----------|
| POST | `/init` | ❌ | Inicializar primeiro admin (bootstrap) |
| GET | `/` | ✅ | Listar todos os admins |
| GET | `/{admin_id}` | ✅ | Obter admin por ID |
| POST | `` | ✅ | Criar novo admin |
| PATCH | `/{admin_id}` | ✅ | Atualizar admin (agent + features) |
| DELETE | `/{admin_id}` | ✅ | Deletar admin (soft delete) |
| POST | `/{admin_id}/features/{feature_id}` | ✅ | Adicionar feature |
| DELETE | `/{admin_id}/features/{feature_id}` | ✅ | Remover feature |
| GET | `/allowed-agents` | ✅ | Listar agentes disponíveis |

### Quick Examples

#### Inicializar primeiro admin
```bash
curl -X POST http://localhost:8000/api/v1/admins/init \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@company.com", "agent_id": 1, "feature_ids": [1,2]}'
```

#### Criar novo admin
```bash
curl -X POST http://localhost:8000/api/v1/admins \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "newadmin@company.com", "agent_id": 2}'
```

#### Listar admins
```bash
curl -X GET "http://localhost:8000/api/v1/admins?limit=10&offset=0" \
  -H "Authorization: Bearer <token>"
```

#### Atualizar features (substitui todas)
```bash
curl -X PATCH http://localhost:8000/api/v1/admins/{admin_id} \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"feature_ids": [1, 2, 3]}'
```

#### Adicionar feature
```bash
curl -X POST http://localhost:8000/api/v1/admins/{admin_id}/features/3 \
  -H "Authorization: Bearer <token>"
```

### Response Structure

```json
{
  "admin_id": "uuid",
  "email": "admin@company.com",
  "agent_id": 1,
  "agent_name": "LUZ",
  "is_active": true,
  "features": [
    {
      "feature_id": 1,
      "code": "PROMPT_MGT",
      "name": "Gerenciamento de Prompts",
      "description": "...",
      "agente": "LUZ",
      "is_active": true,
      "created_at": "2026-02-20T10:30:00"
    }
  ],
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-23T15:00:00"
}
```

### Agentes Disponíveis
```
- 1: LUZ (Agente principal)
- 2: IGP (Agente especializado)
- 3: SMART (Agente inteligente)
```

### Códigos HTTP

| Código | Significado |
|--------|-------------|
| 200 | ✅ Sucesso (GET, PATCH, DELETE com resposta) |
| 201 | ✅ Criado com sucesso (POST) |
| 204 | ✅ Deletado com sucesso (DELETE) |
| 400 | ❌ Bad Request (dados inválidos) |
| 401 | ❌ Não autenticado |
| 403 | ❌ Não é admin (sem permissão) |
| 404 | ❌ Não encontrado |
| 500 | ❌ Erro interno |

---

## 🤖 Prompts Management API - Quick Ref

### Base URL
```
/api/v1/prompts
```

### Endpoints

| Método | Endpoint | Auth | Descrição |
|--------|----------|------|-----------|
| POST | `` | ✅ Admin | Criar novo prompt |
| GET | `` | ✅ User | Listar todos os prompts |
| GET | `/{agente}` | ✅ User | Obter prompt por agente |
| PUT | `/{agente}` | ✅ Admin | Atualizar prompt |
| DELETE | `/{agente}` | ✅ Admin | Deletar prompt |

### Quick Examples

#### Criar novo prompt
```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "agente": "LUZ",
    "system_prompt": "Você é um assistente de RH..."
  }'
```

#### Listar prompts
```bash
curl -X GET http://localhost:8000/api/v1/prompts \
  -H "Authorization: Bearer <token>"
```

#### Obter prompt específico
```bash
curl -X GET http://localhost:8000/api/v1/prompts/LUZ \
  -H "Authorization: Bearer <token>"
```

#### Atualizar prompt (incrementa versão)
```bash
curl -X PUT http://localhost:8000/api/v1/prompts/LUZ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "Versão 2: Novo texto..."}'
```

#### Deletar prompt
```bash
curl -X DELETE http://localhost:8000/api/v1/prompts/IGP \
  -H "Authorization: Bearer <token>"
```

### Response Structure

```json
{
  "prompt_id": 1,
  "agente": "LUZ",
  "system_prompt": "Você é um assistente de RH...",
  "version": 2,
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-23T15:00:00"
}
```

### Agentes Disponíveis
```
- LUZ (Agente principal)
- IGP (Agente especializado)
- SMART (Agente inteligente)
```

### Versionamento

- **Primeira criação**: `version = 1`
- **Cada PUT**: `version += 1`
- O `updated_at` registra quando foi alterado

### Fluxo de Sincronização

```
PUT /prompts/{agente}
    ↓
[1] Validar agente
    ↓
[2] Sincronizar com LLM Server
    ├─ Se FALHA → ❌ Erro 502 (DB não toca)
    └─ Se SUCESSO → Continua
    ↓
[3] UPDATE versão no DB
    ↓
[4] ✅ Retornar prompt atualizado
```

### Retry Automático

```
LLM_SERVER_MAX_RETRIES = 3 tentativas
LLM_SERVER_RETRY_DELAY = 1 segundo (backoff exponencial)

Tentativa 1: após 1s
Tentativa 2: após 2s
Tentativa 3: após 4s
```

### Códigos HTTP

| Código | Significado |
|--------|-------------|
| 200 | ✅ Sucesso (GET, PUT) |
| 201 | ✅ Criado (POST) |
| 204 | ✅ Deletado |
| 400 | ❌ Agente inválido ou prompt existe |
| 401 | ❌ Não autenticado |
| 403 | ❌ Não é admin (POST/PUT/DELETE) |
| 404 | ❌ Prompt não encontrado |
| 502 | ⚠️ Erro ao sincronizar com LLM Server |
| 500 | ❌ Erro interno |

---

## 🔀 Operações Comum

### Inicializar Sistema (Admin)

```bash
# 1. Criar primeiro admin
curl -X POST http://localhost:8000/api/v1/admins/init \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "agent_id": 1,
    "feature_ids": [1, 2]
  }'

# 2. Login com a conta Azure do admin
# (autenticação feita no frontend com MSAL)

# 3. Criar prompts para agentes
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "agente": "LUZ",
    "system_prompt": "Você é um assistente de IA..."
  }'
```

### Gerenciar Admin (Admin)

```bash
# Criar novo admin
POST /api/v1/admins
{
  "email": "newadmin@company.com",
  "agent_id": 2,
  "feature_ids": [1]
}

# Mudar agent e features
PATCH /api/v1/admins/{admin_id}
{
  "agent_id": 3,
  "feature_ids": [1, 2, 3]
}

# Adicionar uma feature
POST /api/v1/admins/{admin_id}/features/3

# Remover uma feature
DELETE /api/v1/admins/{admin_id}/features/2
```

### Gerenciar Prompts (Admin)

```bash
# Criar
POST /api/v1/prompts
{
  "agente": "LUZ",
  "system_prompt": "..."
}

# Atualizar (incrementa versão)
PUT /api/v1/prompts/LUZ
{
  "system_prompt": "Novo texto..."
}

# Deletar
DELETE /api/v1/prompts/LUZ
```

### Consultar (User)

```bash
# Listar todos admins (admin only)
GET /api/v1/admins

# Obter admin específico (admin only)
GET /api/v1/admins/{admin_id}

# Listar prompts
GET /api/v1/prompts

# Obter prompt de agente
GET /api/v1/prompts/LUZ

# Listar agentes permitidos
GET /api/v1/admins/allowed-agents
```

---

## 🚨 Tratamento de Erros

### Admin Management Erros

| Erro | Motivo | Solução |
|------|--------|---------|
| `"Admin já existe"` | Email duplicado | Use email único |
| `"Agent ID inválido"` | agent_id não é 1, 2 ou 3 | Use IDs válidos |
| `"Admin não encontrado"` | ID não existe | Verifique admin_id |
| `"Usuário não é admin"` | Sem permissão | Autentique como admin |
| `"Not authenticated"` | Token ausente | Inclua Authorization header |

### Prompts Management Erros

| Erro | Motivo | Solução |
|------|--------|---------|
| `"Agente inválido"` | Agente não é LUZ, IGP ou SMART | Use agente válido |
| `"Prompt já existe"` | Agente já tem prompt | Use PUT para atualizar |
| `"Prompt não encontrado"` | Agente sem prompt | Crie primeiro |
| `"Erro ao sincronizar com LLM Server"` | LLM Server offline | Verifique conectividade |
| `"Usuário não é admin"` | Sem permissão | Autentique como admin |

---

## 🔗 Documentos Relacionados

- [Admin Management API (Completo)](../ADMIN_MANAGEMENT_API.md)
- [Prompts Management API (Completo)](../PROMPTS_MANAGEMENT_API.md)
- [Complete Documentation](../COMPLETE_DOCUMENTATION.md)
- [Documentation Index](../DOCUMENTATION_INDEX.md)

---

## 💡 Dicas

1. **POST vs PATCH para Features**
   - POST: Adiciona UMA feature
   - PATCH: **Substitui TODAS** as features

2. **Versionamento de Prompts**
   - Cada PUT incrementa versão
   - Histórico completo com timestamps
   - Útil para rollback

3. **Sincronização de Prompts**
   - Falha no LLM Server = DB não touch
   - Retry automático 3x com backoff
   - Use PUT, não DELETE + POST

4. **Permissões**
   - Admin pode criar/gerenciar admin
   - Admin apenas para POST/PUT/DELETE
   - User pode GET (consultar)

---

**Última atualização**: 23 de Fevereiro de 2026  
**Status**: Production
