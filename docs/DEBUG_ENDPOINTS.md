# Debug Endpoints - Diagnóstico e Troubleshooting

**Data**: 16 de Março de 2026  
**Versão**: 1.0  
**Status**: ✅ Documentação Completa

---

## Visão Geral

Os **Debug Endpoints** são ferramentas para diagnóstico e troubleshooting do sistema em desenvolvimento. Eles fornecem informações sobre configurações, variáveis de ambiente e estado da aplicação.

⚠️ **Atenção**: Estes endpoints são **apenas para desenvolvimento**. Em produção, devem ser desabilitados ou protegidos com autenticação admin.

---

## Endpoints

### 1. Diagnóstico de Variáveis de Ambiente

**GET** `/api/v1/debug/env`

Retorna diagnóstico completo de todas as variáveis de ambiente necessárias para funcionamento da aplicação.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-03-16T10:30:45.123Z",
  "environment": {
    "database": {
      "sqlserver_server": "embeddings-sqlserver.database.windows.net",
      "sqlserver_database": "embeddings_db",
      "sqlserver_user": "sa",
      "has_password": true,
      "connection_status": "✅ Connected"
    },
    "storage": {
      "azure_storage_account": "embeddings-storage",
      "azure_container": "documents",
      "connection_status": "✅ Connected"
    },
    "search": {
      "azure_search_service": "embeddings-search",
      "azure_search_index": "documents",
      "connection_status": "✅ Connected"
    },
    "llm": {
      "llm_server_url": "http://localhost:8001/api/v1",
      "llm_server_timeout": "30s",
      "connection_status": "⚠️ Timeout (LLM Server offline)",
      "openai_api_version": "2024-08-01-preview",
      "openai_model": "gpt-4o-mini"
    },
    "auth": {
      "azure_tenant_id": "xxxx-xxxx-xxxx",
      "has_client_id": true,
      "has_client_secret": true,
      "auth_scopes": "api://embeddings-api/.default"
    },
    "application": {
      "environment": "development",
      "debug_mode": true,
      "skip_llm_server": false,
      "skip_llm_metadata_extraction": false,
      "port": 8000
    }
  }
}
```

**Campo Status Detalhado:**

- ✅ **OK**: Componente funcionando corretamente
- ⚠️ **Warning**: Componente com problema mas sistema funciona parcialmente
- ❌ **Error**: Componente offline, sistema não funciona
- ⏭️ **Skipped**: Componente desabilitado via environment variable

**Como Usar:**

```bash
# Teste simples
curl http://localhost:8000/api/v1/debug/env

# Com pretty print
curl http://localhost:8000/api/v1/debug/env | jq .

# Salvar em arquivo
curl http://localhost:8000/api/v1/debug/env > debug_report.json
```

**Troubleshooting Comum:**

| Componente | Status | Solução |
|-----------|--------|--------|
| SQL Server | ❌ Error | Verificar `SQLSERVER_SERVER`, `SQLSERVER_USER`, ``, firewall |
| Azure Storage | ❌ Error | Verificar `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_ACCOUNT_KEY` |
| Azure Search | ❌ Error | Verificar `AZURE_SEARCH_SERVICE_NAME`, `AZURE_SEARCH_API_KEY` |
| LLM Server | ⚠️ Timeout | Iniciar LLM Server ou usar `SKIP_LLM_SERVER=true` para desenvolvimento |
| Auth | ⚠️ Warning | Desenvolvedor local, verificar `AZURE_TENANT_ID`, `AZURE_CLIENT_ID` |

---

## 2. Listar Agentes Configurados

**GET** `/api/v1/debug/agents`

Retorna lista de agentes configurados no sistema e suas permissões.

**Response:**
```json
{
  "status": "ok",
  "agents": [
    {
      "agent_id": 1,
      "code": "LUZ",
      "name": "RH e Assuntos Gerais",
      "description": "Gerenciador de assuntos de RH, dúvidas gerais e relacionamento",
      "is_active": true,
      "created_at": "2026-01-15T08:00:00Z"
    },
    {
      "agent_id": 2,
      "code": "IGP",
      "name": "IGP",
      "description": "Gerenciador IGP (a ser definido)",
      "is_active": true,
      "created_at": "2026-01-15T08:00:00Z"
    },
    {
      "agent_id": 3,
      "code": "SMART",
      "name": "Smart",
      "description": "Gerenciador Smart (a ser definido)",
      "is_active": true,
      "created_at": "2026-01-15T08:00:00Z"
    }
  ]
}
```

**Como Usar:**

```bash
# Listar agentes
curl http://localhost:8000/api/v1/debug/agents

# Validar que um agente existe
curl http://localhost:8000/api/v1/debug/agents | jq '.agents[] | select(.code == "LUZ")'
```

---

## 3. Testar Conectividade do LLM Server

**GET** `/api/v1/debug/llm-health`

Testa conectividade e saúde do LLM Server.

**Response (Sucesso):**
```json
{
  "status": "ok",
  "llm_server": {
    "url": "http://llm-server:8001/api/v1",
    "connection": "✅ Connected",
    "response_time_ms": 125,
    "version": "1.2.3",
    "models_available": ["gpt-4o-mini", "gpt-4o"],
    "features": ["chat", "embeddings", "classification"]
  }
}
```

**Response (Erro):**
```json
{
  "status": "error",
  "llm_server": {
    "url": "http://llm-server:8001/api/v1",
    "connection": "❌ Connection refused",
    "error": "Cannot connect to http://llm-server:8001/api/v1",
    "suggestion": "Verificar se LLM Server está rodando no host/porta correto"
  }
}
```

**Como Usar:**

```bash
curl http://localhost:8000/api/v1/debug/llm-health
```

---

## Variáveis de Ambiente de Debug

Essas variáveis controlam o comportamento dos endpoints de debug:

| Variável | Default | Descrição |
|----------|---------|-----------|
| `DEBUG_MODE` | `false` | Habilita endpoints debug |
| `DEBUG_SHOW_PASSWORDS` | `false` | Se `true`, mostra senhas (PERIGOSO - nunca em prod) |
| `DEBUG_SHOW_SECRETS` | `false` | Se `true`, mostra secrets/keys completos |

**Como Ativar Debug em Desenvolvimento:**

```bash
# Shell
export DEBUG_MODE=true
export DEBUG_SHOW_SECRETS=false  # Ainda oculta secrets por segurança

# .env file
DEBUG_MODE=true
DEBUG_SHOW_SECRETS=false

# Docker
docker run -e DEBUG_MODE=true -e DEBUG_SHOW_SECRETS=false ...
```

---

## Casos de Uso

### **Caso 1: Verificar Configuração Antes de Deploy**

```bash
# Antes de fazer deploy em staging
curl http://localhost:8000/api/v1/debug/env | jq '.environment'

# Verificar se todos componentes têm status ✅
curl http://localhost:8000/api/v1/debug/env | jq '.environment | .[] | .connection_status'
```

### **Caso 2: Troubleshooting de Problema em Chat**

```bash
# 1. Diagnosticar componentes
curl http://localhost:8000/api/v1/debug/env

# 2. Verificar LLM Server
curl http://localhost:8000/api/v1/debug/llm-health

# 3. Listar agentes
curl http://localhost:8000/api/v1/debug/agents
```

### **Caso 3: Verificar se Agente Está Disponível**

```bash
# Listar todos agentes
curl http://localhost:8000/api/v1/debug/agents | jq '.agents[] | {code, is_active}'

# Saída:
# {
#   "code": "LUZ",
#   "is_active": true
# }
```

### **Caso 4: Monitoramento Básico (Health Check)**

```bash
#!/bin/bash

# Verificar se API está respondendo
if curl -s http://localhost:8000/api/v1/debug/env | jq '.status' | grep -q "ok"; then
  echo "✅ API está saudável"
else
  echo "❌ API com problema"
  exit 1
fi
```

---

## Segurança em Produção

⚠️ **Importante**: Estes endpoints devem ser **desabilitados em produção**.

**Opção 1: Desabilitar via Variável de Ambiente**

```bash
debug_mode = false  # Desabilita todos endpoints debug
```

**Opção 2: Proteger com Middleware de Autenticação**

```python
# No app/core/security.py
def require_debug_access(request: Request):
    if not DEBUG_MODE or not is_admin(request):
        raise HTTPException(status_code=403)
```

**Opção 3: Limitar por IP**

```python
# Apenas localhost pode acessar debug
ALLOWED_DEBUG_IPS = ["127.0.0.1", "::1"]
```

---

## Próximos Passos

- [ ] Implementar rate limiting para debug endpoints
- [ ] Adicionar logging detalhado de acesso
- [ ] Criar dashboard com status em tempo real
- [ ] Integrar com sistema de alertas
