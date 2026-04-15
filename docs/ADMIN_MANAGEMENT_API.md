# Admin Management API

**Data**: 23 de Fevereiro de 2026  
**Versão**: 1.0  
**Status**: ✅ Completo  

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Conceitos Fundamentais](#conceitos-fundamentais)
3. [Endpoints](#endpoints)
4. [Modelos de Dados](#modelos-de-dados)
5. [Exemplos de Uso](#exemplos-de-uso)
6. [Fluxos Principais](#fluxos-principais)
7. [Tratamento de Erros](#tratamento-de-erros)

---

## Visão Geral

A **Admin Management API** fornece funcionalidades para:
- ✅ Gerenciar administradores do sistema
- ✅ Controlar acesso por agente (LUZ, IGP, SMART)
- ✅ Associar e remover features de acesso
- ✅ Inicializar o primeiro admin (bootstrap)
- ✅ Listar e consultar admins
- ✅ Auditar todas as alterações com rastreamento por email do usuário

### Autenticação

Todos os endpoints requerem um usuário autenticado via Azure Entra ID (MSAL). Apenas **admins existentes** podem criar ou gerenciar novos admins.

**Exceção**: O endpoint `/init` permite criar o primeiro admin **sem autenticação** (para bootstrap do sistema).

### Autorização

| Operação | Requer Admin | Notas |
|----------|-------------|-------|
| POST `/init` | ❌ Não | Apenas se nenhum admin existe |
| GET `/` | ✅ Sim | Listar admins |
| GET `/{admin_id}` | ✅ Sim | Buscar admin por ID |
| POST `""` | ✅ Sim | Criar novo admin |
| PATCH `/{admin_id}` | ✅ Sim | Atualizar admin |
| DELETE `/{admin_id}` | ✅ Sim | Soft delete de admin |
| POST `/{admin_id}/features/{feature_id}` | ✅ Sim | Adicionar feature |
| DELETE `/{admin_id}/features/{feature_id}` | ✅ Sim | Remover feature |
| GET `/{admin_id}/audit` | ✅ Sim | Obter histórico de auditoria |

---

## Conceitos Fundamentais

### Admin

Um **Admin** é um usuário com permissões elevadas para gerenciar o sistema. Cada admin:
- Tem um `email` único
- Está associado a um `agent_id` (1=LUZ, 2=IGP, 3=SMART)
- Tem um conjunto de `features` permitidas (acesso granular)
- Pode ser ativado/desativado

**Estrutura**:
```json
{
  "admin_id": "uuid-string",
  "email": "admin@example.com",
  "agent_id": 1,
  "agent_name": "LUZ",
  "is_active": true,
  "features": [
    {
      "feature_id": 1,
      "code": "PROMPT_MGT",
      "name": "Gerenciamento de Prompts",
      "description": "Permitir criação/edição de prompts",
      "agente": "LUZ",
      "is_active": true,
      "created_at": "2026-02-20T10:30:00"
    }
  ],
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-22T15:45:00"
}
```

### Agent (Agente)

Os agentes permitidos no sistema:

| ID | Code | Nome | Descrição |
|----|------|------|-----------|
| 1 | `LUZ` | LUZ | Agente principal de IA |
| 2 | `IGP` | IGP | Agente especializado |
| 3 | `SMART` | SMART | Agente inteligente |

### Feature (Funcionalidade)

Uma **Feature** é uma permissão granular que controla o que um admin pode fazer:

| ID | Code | Nome | Descrição | Agente |
|----|------|------|-----------|--------|
| 1 | `PROMPT_MGT` | Gerenciamento de Prompts | Criar/atualizar/deletar prompts | LUZ, IGP, SMART |
| 2 | `ADMIN_MGT` | Gerenciamento de Admins | Gerenciar admins do sistema | LUZ, IGP, SMART |
| 3 | `USER_MGMT` | Gestão de Usuários | Gerenciar usuários | LUZ, IGP |

---

## 🔐 Sistema de Auditoria

O **Sistema de Auditoria** registra **todas as alterações** feitas em admins, criando um histórico imutável e completo.

### Características Principais

- ✅ **Imutável**: Os registros nunca são modificados ou deletados, apenas novos registros são adicionados
- ✅ **Granular**: Rastreia cada campo alterado com valores antes e depois
- ✅ **Rastreabilidade**: Registra quem fez a alteração (email do Azure AD), quando e de qual IP (se disponível)
- ✅ **Histórico Completo**: Mantém histórico de CRIAÇÃOs, UPDATEs e DELETEs
- ✅ **Múltiplas Alterações**: Se 3 pessoas alteram um admin, há 3 registros diferentes (nunca sobrescreve)

### Tipos de Eventos Auditados

| Evento | Descrição | Dados Registrados |
|--------|-----------|------------------|
| **CREATE** | Admin criado | Todos os campos iniciais (email, name, job_title, city, agent_id) |
| **UPDATE** | Admin atualizado | Campos alterados + valores antigos e novos |
| **DELETE** | Admin deletado (soft delete) | Todos os dados do admin antes da exclusão |

### Exemplo de Auditoria Completa

**Cenário**: 3 usuários alteram um admin em sequência

**Registro 1 - CREATE** (10:30 AM):
```json
{
  "log_id": 1,
  "action": "CREATE",
  "changed_by": "admin1@company.com",
  "changed_at": "2024-01-15T10:30:00Z",
  "changed_fields": ["email", "name", "job_title", "city", "agent_id"],
  "old_values": {},
  "new_values": {
    "email": "carlos@company.com",
    "name": "Carlos Silva",
    "job_title": "Gerente",
    "city": "São Paulo",
    "agent_id": 1
  },
  "details": "Admin criado: carlos@company.com"
}
```

**Registro 2 - UPDATE** (14:00 PM - mesmo dia):
```json
{
  "log_id": 2,
  "action": "UPDATE",
  "changed_by": "admin2@company.com",
  "changed_at": "2024-01-15T14:00:00Z",
  "changed_fields": ["job_title"],
  "old_values": {
    "job_title": "Gerente"
  },
  "new_values": {
    "job_title": "Diretor"
  },
  "details": "Fields alterados: job_title"
}
```

**Registro 3 - UPDATE** (16:30 PM - próximo dia):
```json
{
  "log_id": 3,
  "action": "UPDATE",
  "changed_by": "admin3@company.com",
  "changed_at": "2024-01-16T16:30:00Z",
  "changed_fields": ["city"],
  "old_values": {
    "city": "São Paulo"
  },
  "new_values": {
    "city": "Rio de Janeiro"
  },
  "details": "Fields alterados: city"
}
```

**Visualização Completa**:
```
Histórico de Alterações para carlos@company.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CREATE por admin1@company.com em 15/01/2024 10:30
   ├─ email: ∅ → carlos@company.com
   ├─ name: ∅ → Carlos Silva
   ├─ job_title: ∅ → Gerente
   ├─ city: ∅ → São Paulo
   └─ agent_id: ∅ → 1 (LUZ)

✏️ UPDATE por admin2@company.com em 15/01/2024 14:00
   └─ job_title: "Gerente" → "Diretor"

✏️ UPDATE por admin3@company.com em 16/01/2024 16:30
   └─ city: "São Paulo" → "Rio de Janeiro"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### API de Auditoria

Para consultar o histórico de auditoria, use o endpoint:

```
GET /api/v1/admins/{admin_id}/audit?limit=50&offset=0
```

Veja [Seção 10 - Obter Histórico de Auditoria](#10-obter-histórico-de-auditoria-de-um-admin) para detalhes completos.

---

## Endpoints

### Base URL
```
POST /api/v1/admins/init
GET  /api/v1/admins
GET  /api/v1/admins/{admin_id}
POST /api/v1/admins
PATCH /api/v1/admins/{admin_id}
DELETE /api/v1/admins/{admin_id}
POST /api/v1/admins/{admin_id}/features/{feature_id}
DELETE /api/v1/admins/{admin_id}/features/{feature_id}
GET  /api/v1/admins/{admin_id}/audit
GET  /api/v1/admins/allowed-agents
```

---

### 1. Inicializar Primeiro Admin (Bootstrap)

**Endpoint**:
```
POST /api/v1/admins/init
```

**Autenticação**: ❌ Não requerida (apenas se nenhum admin existe)

**Request Body**:
```json
{
  "email": "admin@example.com",
  "agent_id": 1,
  "feature_ids": [1, 2]
}
```

**Parâmetros**:
- `email` (string, obrigatório): Email único do admin
- `agent_id` (int, opcional, padrão=1): ID do agente (1=LUZ, 2=IGP, 3=SMART)
- `feature_ids` (array de int, opcional): IDs das features permitidas

**Respostas**:

✅ **201 Created**:
```json
{
  "admin_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "agent_id": 1,
  "agent_name": "LUZ",
  "is_active": true,
  "features": [
    {
      "feature_id": 1,
      "code": "PROMPT_MGT",
      "name": "Gerenciamento de Prompts",
      "description": "Criar/atualizar/deletar prompts",
      "agente": "LUZ",
      "is_active": true,
      "created_at": "2026-02-20T10:30:00"
    }
  ],
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-20T10:30:00"
}
```

❌ **400 Bad Request**: Se admin já existe ou dados inválidos
```json
{
  "detail": "Admin já existe"
}
```

---

### 2. Listar Todos os Admins

**Endpoint**:
```
GET /api/v1/admins
```

**Autenticação**: ✅ Requerida (admin)

**Query Parameters**:
- `limit` (int, opcional, padrão=100): Número máximo de resultados
- `offset` (int, opcional, padrão=0): Deslocamento para pagination
- `active_only` (bool, opcional, padrão=true): Listar apenas admins ativos

**Respostas**:

✅ **200 OK**:
```json
{
  "admins": [
    {
      "admin_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "admin@example.com",
      "agent_id": 1,
      "agent_name": "LUZ",
      "is_active": true,
      "features": [...],
      "created_at": "2026-02-20T10:30:00",
      "updated_at": "2026-02-20T10:30:00"
    }
  ],
  "total": 5
}
```

❌ **401 Unauthorized**: Usuário não autenticado

❌ **403 Forbidden**: Usuário não é admin

---

### 3. Obter Admin por ID

**Endpoint**:
```
GET /api/v1/admins/{admin_id}
```

**Autenticação**: ✅ Requerida (admin)

**Path Parameters**:
- `admin_id` (string): ID único do admin (UUID)

**Respostas**:

✅ **200 OK**:
```json
{
  "admin_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "agent_id": 1,
  "agent_name": "LUZ",
  "is_active": true,
  "features": [
    {
      "feature_id": 1,
      "code": "PROMPT_MGT",
      "name": "Gerenciamento de Prompts",
      "description": "Criar/atualizar/deletar prompts",
      "agente": "LUZ",
      "is_active": true,
      "created_at": "2026-02-20T10:30:00"
    }
  ],
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-20T10:30:00"
}
```

❌ **404 Not Found**: Admin não encontrado

❌ **403 Forbidden**: Usuário não é admin

---

### 4. Criar Novo Admin

**Endpoint**:
```
POST /api/v1/admins
```

**Autenticação**: ✅ Requerida (admin)

**Request Body**:
```json
{
  "email": "newadmin@example.com",
  "agent_id": 2,
  "feature_ids": [1, 3]
}
```

**Parâmetros**:
- `email` (string, obrigatório): Email único do novo admin
- `agent_id` (int, opcional, padrão=1): ID do agente (1=LUZ, 2=IGP, 3=SMART)
- `feature_ids` (array de int, opcional): IDs das features permitidas

**Respostas**:

✅ **201 Created**:
```json
{
  "admin_id": "550e8400-e29b-41d4-a716-446655440001",
  "email": "newadmin@example.com",
  "agent_id": 2,
  "agent_name": "IGP",
  "is_active": true,
  "features": [
    {
      "feature_id": 1,
      "code": "PROMPT_MGT",
      "name": "Gerenciamento de Prompts",
      "description": "Criar/atualizar/deletar prompts",
      "agente": "IGP",
      "is_active": true,
      "created_at": "2026-02-20T11:00:00"
    }
  ],
  "created_at": "2026-02-20T11:00:00",
  "updated_at": "2026-02-20T11:00:00"
}
```

❌ **400 Bad Request**: Email já existe ou agent_id inválido

❌ **403 Forbidden**: Usuário não é admin

---

### 5. Atualizar Admin

**Endpoint**:
```
PATCH /api/v1/admins/{admin_id}
```

**Autenticação**: ✅ Requerida (admin)

**Path Parameters**:
- `admin_id` (string): ID único do admin

**Request Body**:
```json
{
  "agent_id": 3,
  "feature_ids": [1, 2, 3]
}
```

**Parâmetros**:
- `agent_id` (int, opcional): Novo ID do agente (substitui o anterior)
- `feature_ids` (array de int, opcional): Nova lista de features (substitui TODAS as anteriores)

**Respostas**:

✅ **200 OK**:
```json
{
  "admin_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "agent_id": 3,
  "agent_name": "SMART",
  "is_active": true,
  "features": [
    {
      "feature_id": 1,
      "code": "PROMPT_MGT",
      "name": "Gerenciamento de Prompts",
      "description": "Criar/atualizar/deletar prompts",
      "agente": "SMART",
      "is_active": true,
      "created_at": "2026-02-20T10:30:00"
    },
    {
      "feature_id": 2,
      "code": "ADMIN_MGT",
      "name": "Gerenciamento de Admins",
      "description": "Gerenciar admins do sistema",
      "agente": "SMART",
      "is_active": true,
      "created_at": "2026-02-20T10:30:00"
    }
  ],
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-23T15:00:00"
}
```

❌ **404 Not Found**: Admin não encontrado

❌ **400 Bad Request**: agent_id inválido

❌ **403 Forbidden**: Usuário não é admin

---

### 6. Deletar Admin (Soft Delete)

**Endpoint**:
```
DELETE /api/v1/admins/{admin_id}
```

**Autenticação**: ✅ Requerida (admin)

**Path Parameters**:
- `admin_id` (string): ID único do admin

**Respostas**:

✅ **204 No Content**: Deletado com sucesso

❌ **404 Not Found**: Admin não encontrado

❌ **403 Forbidden**: Usuário não é admin

---

### 7. Adicionar Feature a um Admin

**Endpoint**:
```
POST /api/v1/admins/{admin_id}/features/{feature_id}
```

**Autenticação**: ✅ Requerida (admin)

**Path Parameters**:
- `admin_id` (string): ID único do admin
- `feature_id` (int): ID da feature a adicionar

**Respostas**:

✅ **200 OK**:
```json
{
  "admin_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "agent_id": 1,
  "agent_name": "LUZ",
  "is_active": true,
  "features": [
    {
      "feature_id": 1,
      "code": "PROMPT_MGT",
      "name": "Gerenciamento de Prompts",
      "description": "Criar/atualizar/deletar prompts",
      "agente": "LUZ",
      "is_active": true,
      "created_at": "2026-02-20T10:30:00"
    },
    {
      "feature_id": 2,
      "code": "ADMIN_MGT",
      "name": "Gerenciamento de Admins",
      "description": "Gerenciar admins do sistema",
      "agente": "LUZ",
      "is_active": true,
      "created_at": "2026-02-23T15:05:00"
    }
  ],
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-23T15:05:00"
}
```

❌ **404 Not Found**: Admin não encontrado

❌ **400 Bad Request**: Feature já existe para este admin

❌ **403 Forbidden**: Usuário não é admin

---

### 8. Remover Feature de um Admin

**Endpoint**:
```
DELETE /api/v1/admins/{admin_id}/features/{feature_id}
```

**Autenticação**: ✅ Requerida (admin)

**Path Parameters**:
- `admin_id` (string): ID único do admin
- `feature_id` (int): ID da feature a remover

**Respostas**:

✅ **200 OK**:
```json
{
  "admin_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "agent_id": 1,
  "agent_name": "LUZ",
  "is_active": true,
  "features": [
    {
      "feature_id": 1,
      "code": "PROMPT_MGT",
      "name": "Gerenciamento de Prompts",
      "description": "Criar/atualizar/deletar prompts",
      "agente": "LUZ",
      "is_active": true,
      "created_at": "2026-02-20T10:30:00"
    }
  ],
  "created_at": "2026-02-20T10:30:00",
  "updated_at": "2026-02-23T15:10:00"
}
```

❌ **404 Not Found**: Admin não encontrado

❌ **403 Forbidden**: Usuário não é admin

---

### 9. Listar Agentes Permitidos

**Endpoint**:
```
GET /api/v1/admins/allowed-agents
```

**Autenticação**: ✅ Requerida

**Respostas**:

✅ **200 OK**:
```json
{
  "agents": [
    {
      "agent_id": 1,
      "code": "LUZ",
      "name": "LUZ",
      "description": "Agente principal de IA",
      "is_active": true
    },
    {
      "agent_id": 2,
      "code": "IGP",
      "name": "IGP",
      "description": "Agente especializado",
      "is_active": true
    },
    {
      "agent_id": 3,
      "code": "SMART",
      "name": "SMART",
      "description": "Agente inteligente",
      "is_active": true
    }
  ]
}
```

---

### 10. Obter Histórico de Auditoria de um Admin

**Endpoint**:
```
GET /api/v1/admins/{admin_id}/audit
```

**Autenticação**: ✅ Requerida (admin)

**Path Parameters**:
- `admin_id` (string): ID único do admin

**Query Parameters**:
- `limit` (int, opcional, padrão=50, máximo=500): Número máximo de registros a retornar
- `offset` (int, opcional, padrão=0): Deslocamento para paginação

**Descrição**:
Retorna o histórico completo de auditoria de um admin, incluindo todas as criações, atualizações e deleções.
Cada alteração feita por um usuário diferente aparece como um registro separado, com:
- **action**: Tipo de operação (CREATE, UPDATE, DELETE)
- **changed_fields**: Lista dos campos que foram alterados
- **old_values**: JSON com os valores antigos
- **new_values**: JSON com os valores novos
- **changed_by**: Email do usuário Azure AD que fez a alteração
- **changed_at**: Data e hora da alteração (UTC)
- **details**: Descrição adicional da alteração

**Exemplo de Uso**:
```bash
curl -X GET "https://api.example.com/api/v1/admins/550e8400-e29b-41d4-a716-446655440000/audit?limit=10&offset=0" \
  -H "Authorization: Bearer {token}"
```

**Respostas**:

✅ **200 OK** - Com histórico de alterações:
```json
{
  "admin_id": "550e8400-e29b-41d4-a716-446655440000",
  "total": 3,
  "logs": [
    {
      "log_id": 1,
      "admin_id": "550e8400-e29b-41d4-a716-446655440000",
      "action": "CREATE",
      "changed_fields": ["email", "name", "job_title", "city", "agent_id"],
      "old_values": {},
      "new_values": {
        "email": "admin@example.com",
        "name": "João Silva",
        "job_title": "Gerente",
        "city": "São Paulo",
        "agent_id": 1
      },
      "changed_by": "user@company.com",
      "changed_at": "2024-01-15T10:30:00",
      "ip_address": "192.168.1.1",
      "details": "Admin criado: admin@example.com"
    },
    {
      "log_id": 2,
      "admin_id": "550e8400-e29b-41d4-a716-446655440000",
      "action": "UPDATE",
      "changed_fields": ["job_title"],
      "old_values": {
        "job_title": "Gerente"
      },
      "new_values": {
        "job_title": "Diretor"
      },
      "changed_by": "manager@company.com",
      "changed_at": "2024-01-16T14:00:00",
      "ip_address": "192.168.1.5",
      "details": "Fields alterados: job_title"
    },
    {
      "log_id": 3,
      "admin_id": "550e8400-e29b-41d4-a716-446655440000",
      "action": "UPDATE",
      "changed_fields": ["city"],
      "old_values": {
        "city": "São Paulo"
      },
      "new_values": {
        "city": "Rio de Janeiro"
      },
      "changed_by": "user@company.com",
      "changed_at": "2024-01-17T09:15:00",
      "ip_address": "192.168.1.1",
      "details": "Fields alterados: city"
    }
  ]
}
```

❌ **404 Not Found**: Admin não encontrado
```json
{
  "detail": "Admin 550e8400-e29b-41d4-a716-446655440000 não encontrado"
}
```

❌ **403 Forbidden**: Usuário não é admin
```json
{
  "detail": "Sem permissão"
}
```

---

## Modelos de Dados

### AdminResponse
```python
{
  "admin_id": str        # UUID
  "email": str           # Email único
  "agent_id": int        # 1=LUZ, 2=IGP, 3=SMART
  "agent_name": str      # Nome do agente (LUZ, IGP, SMART)
  "is_active": bool      # Status do admin
  "features": List[FeatureDetail]
  "created_at": datetime
  "created_by": str      # Nome do usuário que criou
  "updated_at": datetime
  "updated_by": str      # Nome do usuário que atualizou
}
```

### FeatureDetail
```python
{
  "feature_id": int
  "code": str            # PROMPT_MGT, ADMIN_MGT, etc
  "name": str
  "description": str
  "agente": str          # Agente associado
  "is_active": bool
  "created_at": datetime
}
```

### AdminCreate
```python
{
  "email": str           # Obrigatório
  "agent_id": int        # Opcional (padrão: 1)
  "feature_ids": List[int]  # Opcional
}
```

### AdminUpdate
```python
{
  "agent_id": int        # Opcional
  "feature_ids": List[int]  # Opcional (substitui TODAS)
}
```

### AdminAuditLogEntry
```python
{
  "log_id": int          # ID único do registro de auditoria
  "admin_id": str        # ID do admin alterado
  "action": str          # CREATE, UPDATE ou DELETE
  "changed_fields": List[str]  # Lista de campos alterados
  "old_values": Dict[str, Any]  # Valores antes da alteração
  "new_values": Dict[str, Any]  # Valores depois da alteração
  "changed_by": str      # Email do usuário Azure AD que fez a alteração
  "changed_at": datetime # Data/hora da alteração (UTC)
  "ip_address": str      # IP do cliente (opcional)
  "details": str         # Descrição adicional (opcional)
}
```

### AdminAuditLogResponse
```python
{
  "admin_id": str        # ID do admin auditado
  "total": int           # Total de registros de auditoria
  "logs": List[AdminAuditLogEntry]  # Lista paginada de registros
}
```

---

## Exemplos de Uso

### cURL

#### 1. Inicializar primeiro admin
```bash
curl -X POST http://localhost:8000/api/v1/admins/init \
  -H "Content-Type: application/json" \
  -d '{
    "email": "firstadmin@company.com",
    "agent_id": 1,
    "feature_ids": [1, 2, 3]
  }'
```

#### 2. Criar novo admin
```bash
curl -X POST http://localhost:8000/api/v1/admins \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newadmin@company.com",
    "agent_id": 2,
    "feature_ids": [1, 3]
  }'
```

#### 3. Obtém admin por ID
```bash
curl -X GET http://localhost:8000/api/v1/admins/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

#### 4. Atualizar admin (mudar agent e features)
```bash
curl -X PATCH http://localhost:8000/api/v1/admins/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": 3,
    "feature_ids": [1, 2]
  }'
```

#### 5. Adicionar feature
```bash
curl -X POST http://localhost:8000/api/v1/admins/550e8400-e29b-41d4-a716-446655440000/features/3 \
  -H "Authorization: Bearer <token>"
```

#### 6. Remover feature
```bash
curl -X DELETE http://localhost:8000/api/v1/admins/550e8400-e29b-41d4-a716-446655440000/features/2 \
  -H "Authorization: Bearer <token>"
```

#### 7. Listar todos os admins
```bash
curl -X GET "http://localhost:8000/api/v1/admins?limit=10&offset=0&active_only=true" \
  -H "Authorization: Bearer <token>"
```

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer <token>", "Content-Type": "application/json"}

# Criar novo admin
response = requests.post(
    f"{BASE_URL}/admins",
    headers=HEADERS,
    json={
        "email": "manager@company.com",
        "agent_id": 1,
        "feature_ids": [1, 2]
    }
)
admin = response.json()
print(f"Admin criado: {admin['admin_id']}")

# Obter admin por ID
response = requests.get(
    f"{BASE_URL}/admins/{admin['admin_id']}",
    headers=HEADERS
)
print(response.json())

# Adicionar feature
response = requests.post(
    f"{BASE_URL}/admins/{admin['admin_id']}/features/3",
    headers=HEADERS
)
print(f"Feature adicionada: {response.json()}")

# Remover feature
response = requests.delete(
    f"{BASE_URL}/admins/{admin['admin_id']}/features/2",
    headers=HEADERS
)
print(f"Feature removida: {response.status_code}")

# Obter histórico de auditoria
response = requests.get(
    f"{BASE_URL}/admins/{admin['admin_id']}/audit?limit=10&offset=0",
    headers=HEADERS
)
audit_data = response.json()
print(f"Total de alterações registradas: {audit_data['total']}")
for log_entry in audit_data['logs']:
    print(f"\n  - {log_entry['action']} por {log_entry['changed_by']} em {log_entry['changed_at']}")
    if log_entry['changed_fields']:
        print(f"    Campos alterados: {', '.join(log_entry['changed_fields'])}")
    if log_entry['old_values']:
        print(f"    Valores antigos: {log_entry['old_values']}")
    if log_entry['new_values']:
        print(f"    Valores novos: {log_entry['new_values']}")
```

### JavaScript/TypeScript

```typescript
const baseUrl = "http://localhost:8000/api/v1";
const headers = {
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json"
};

// Criar novo admin
const createAdminResponse = await fetch(`${baseUrl}/admins`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    email: "developer@company.com",
    agent_id: 2,
    feature_ids: [1]
  })
});
const admin = await createAdminResponse.json();
console.log(`Admin criado: ${admin.admin_id}`);

// Obter admin
const getAdminResponse = await fetch(
  `${baseUrl}/admins/${admin.admin_id}`,
  { headers }
);
const adminData = await getAdminResponse.json();
console.log(adminData);

// Listar todos os admins
const listAdminsResponse = await fetch(
  `${baseUrl}/admins?limit=20&active_only=true`,
  { headers }
);
const adminList = await listAdminsResponse.json();
console.log(`Total de admins: ${adminList.total}`);

// Obter histórico de auditoria
const auditResponse = await fetch(
  `${baseUrl}/admins/${admin.admin_id}/audit?limit=10&offset=0`,
  { headers }
);
const auditData = await auditResponse.json();
console.log(`Total de alterações registradas: ${auditData.total}`);
auditData.logs.forEach(log => {
  console.log(`
  - ${log.action} por ${log.changed_by} em ${log.changed_at}
    Campos alterados: ${log.changed_fields.join(', ')}
    Valores antigos: ${JSON.stringify(log.old_values)}
    Valores novos: ${JSON.stringify(log.new_values)}
  `);
});
```

---

## Fluxos Principais

### Fluxo 1: Inicializar Sistema (Bootstrap)

```
┌─────────────┐
│  Nenhum     │
│  Admin      │
│  Existe     │
└──────┬──────┘
       │
       v
┌──────────────────┐
│ POST /init       │
│ (sem auth)       │
└──────┬───────────┘
       │
       v
┌──────────────────┐
│ Primeiro admin   │
│ criado com       │
│ features básicas │
└──────────────────┘
```

### Fluxo 2: Criar novo Admin com Features

```
┌──────────────┐
│ Admin        │
│ autenticado  │
└──────┬───────┘
       │
       v
┌──────────────────────┐
│ POST /admins         │
│ email, agent_id,     │
│ feature_ids          │
└──────┬───────────────┘
       │
       v
┌──────────────────┐
│ Admin criado     │
│ com features     │
│ associadas       │
└──────────────────┘
```

### Fluxo 3: Atualizar features de um Admin

```
┌──────────────┐
│ Admin existe │
└──────┬───────┘
       │
       v
┌──────────────────────┐
│ PATCH /admins/:id    │
│ feature_ids (nova    │
│ lista completa)      │
└──────┬───────────────┘
       │
       v
┌──────────────────┐
│ Features         │
│ substituídas     │
│ (DELETE all +    │
│ INSERT new)      │
└──────────────────┘
```

### Fluxo 4: Gerenciar features incrementalmente

```
┌──────────────┐
│ Admin existe │
└──────┬───────┘
       │
       ├─────────────────┬──────────────────┐
       │                 │                  │
       v                 v                  v
┌────────────┐    ┌────────────┐    ┌────────────┐
│ POST add   │    │ DELETE     │    │ PATCH      │
│ /features/ │    │ /features/ │    │ (replace   │
│ {id}       │    │ {id}       │    │ all)       │
└──────┬─────┘    └──────┬─────┘    └──────┬─────┘
       │                 │                  │
       └────────┬────────┴──────────────────┘
                │
                v
        ┌───────────────┐
        │ Features      │
        │ atualizadas   │
        └───────────────┘
```

---

## Tratamento de Erros

### 400 Bad Request

**Causas comuns**:
- Email duplicado
- Agent ID inválido (não é 1, 2 ou 3)
- Feature ID inválido
- JSON malformado

**Exemplo**:
```json
{
  "detail": "Agent ID inválido: 99. IDs válidos: 1 (LUZ), 2 (IGP), 3 (SMART)"
}
```

### 401 Unauthorized

**Causa**: Token JWT ausente ou inválido

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

**Causa**: Usuário autenticado mas não é admin

```json
{
  "detail": "Usuário não é admin"
}
```

### 404 Not Found

**Causa**: Admin não existe

```json
{
  "detail": "Admin não encontrado"
}
```

### 500 Internal Server Error

**Causa**: Erro interno do servidor (DB, etc)

```json
{
  "detail": "Erro ao buscar admin: <erro específico>"
}
```

---

## Database Schema

### Tabela `admins`
```sql
CREATE TABLE admins (
  admin_id VARCHAR(36) PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NULL,
  job_title VARCHAR(255) NULL,
  city VARCHAR(255) NULL,
  agent_id INT NOT NULL,
  is_active BIT DEFAULT 1,
  created_at DATETIME DEFAULT GETUTCDATE(),
  created_by NVARCHAR(255) NULL,
  updated_at DATETIME DEFAULT GETUTCDATE(),
  updated_by NVARCHAR(255) NULL,
  FOREIGN KEY (agent_id) REFERENCES allowed_agents(agent_id)
);
```

### Tabela `admin_features`
```sql
CREATE TABLE admin_features (
  admin_id VARCHAR(36) NOT NULL,
  feature_id INT NOT NULL,
  created_at DATETIME DEFAULT GETUTCDATE(),
  PRIMARY KEY (admin_id, feature_id),
  FOREIGN KEY (admin_id) REFERENCES admins(admin_id),
  FOREIGN KEY (feature_id) REFERENCES features(feature_id)
);
```

### Tabela `allowed_agents`
```sql
CREATE TABLE allowed_agents (
  agent_id INT PRIMARY KEY,
  code VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(255),
  is_active BIT DEFAULT 1
);
```

### Tabela `features`
```sql
CREATE TABLE features (
  feature_id INT PRIMARY KEY,
  code VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(255),
  agente VARCHAR(50),
  is_active BIT DEFAULT 1,
  created_at DATETIME DEFAULT GETUTCDATE()
);
```

---

## Melhores Práticas

### 1. Atualizar Features

**❌ Não faça**:
```python
# Não adicione manualmente usando POST várias vezes se precisa replacar
for feature_id in [1, 2, 3]:
    requests.post(f"/admins/{admin_id}/features/{feature_id}", headers=headers)
```

**✅ Faça**:
```python
# Use PATCH para replacar todas as features de uma vez
requests.patch(
    f"/admins/{admin_id}",
    headers=headers,
    json={"feature_ids": [1, 2, 3]}
)
```

### 2. Verificar Permissões

Sempre valide se o usuário é admin antes de operações sensíveis:
```python
if not user.get("is_admin"):
    raise PermissionError("Usuário não tem permissão")
```

### 3. Logging

Log todas as operações de admin para auditoria:
```python
logger.info(f"Admin {admin_id} criado por {current_user_email}")
logger.info(f"Feature {feature_id} adicionada ao admin {admin_id}")
```

---

## Versionamento da API

- **Versão Atual**: 1.0
- **Data da última atualização**: 23 de Fevereiro de 2026
- **Status**: Produção
