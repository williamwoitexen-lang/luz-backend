# Dashboard API - Análise e Relatórios

Endpoints para análise de convergências de chat, uso do sistema e métricas de LLM.

## Base URL

```
{{baseUrl}}/chat/dashboard
```

---

## 📊 Endpoints

### 1. GET `/summary`

**Obter resumo agregado de conversas e análise de chat**

#### Query Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `start_date` | string | Não | Data início (YYYY-MM-DD). Padrão: 30 dias atrás |
| `end_date` | string | Não | Data fim (YYYY-MM-DD). Padrão: hoje |
| `user_id` | string | Não | Filtrar por usuário específico |

#### Response (200 OK)

```json
{
  "period": {
    "start_date": "2026-02-20",
    "end_date": "2026-03-20",
    "total_days": 30
  },
  "conversations": {
    "total": 1245,
    "active": 987,
    "archived": 258,
    "average_per_user": 12.5
  },
  "messages": {
    "total": 5432,
    "user_messages": 2716,
    "ai_messages": 2716,
    "average_per_conversation": 4.4,
    "average_per_user": 54.3
  },
  "llm_usage": {
    "total_tokens": {
      "input": 850000,
      "output": 425000,
      "total": 1275000
    },
    "cost_estimates": {
      "currency": "USD",
      "gpt4_turbo": 25.50,
      "gpt4o": 18.75,
      "total_estimated": 44.25
    },
    "models_used": {
      "gpt-4-turbo": {
        "count": 2850,
        "percentage": 52.4,
        "tokens": 680000
      },
      "gpt-4o": {
        "count": 2290,
        "percentage": 42.1,
        "tokens": 450000
      },
      "gpt-35-turbo": {
        "count": 292,
        "percentage": 5.4,
        "tokens": 145000
      }
    }
  },
  "performance": {
    "avg_response_time_ms": 2145,
    "p50_response_time_ms": 1800,
    "p95_response_time_ms": 4200,
    "p99_response_time_ms": 6800,
    "success_rate": 98.5,
    "failed_requests": 81,
    "total_requests": 5432
  },
  "top_users": [
    {
      "user_id": "alice",
      "message_count": 450,
      "conversation_count": 85,
      "tokens_used": 125000,
      "last_activity": "2026-03-20T14:32:10Z"
    },
    {
      "user_id": "bob",
      "message_count": 380,
      "conversation_count": 62,
      "tokens_used": 98000,
      "last_activity": "2026-03-20T13:15:45Z"
    }
  ],
  "completion_metrics": {
    "conversations_completed": 456,
    "conversations_open": 234,
    "completion_rate": 66.1,
    "average_duration_minutes": 24.5
  }
}
```

#### Exemplos cURL

**Últimos 30 dias (padrão):**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/summary"
```

**Período específico:**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/summary?start_date=2026-03-01&end_date=2026-03-20"
```

**Usuário específico:**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/summary?user_id=alice"
```

---

### 2. GET `/detailed`

**Obter lista detalhada de conversas para análise profunda**

#### Query Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `start_date` | string | Não | Data início (YYYY-MM-DD) |
| `end_date` | string | Não | Data fim (YYYY-MM-DD) |
| `user_id` | string | Não | Filtrar por usuário |
| `limit` | integer | Não | Resultados por página (1-1000, padrão: 100) |
| `offset` | integer | Não | Offset para paginação (padrão: 0) |
| `order_by` | string | Não | Campo para ordenar: `created_at`, `message_count`, `updated_at` (padrão: created_at) |

#### Response (200 OK)

```json
{
  "total_conversations": 1245,
  "returned_count": 2,
  "limit": 100,
  "offset": 0,
  "conversations": [
    {
      "id": "conv_550e8400-e29b-41d4",
      "user_id": "alice",
      "title": "Benefícios de Saúde 2026",
      "created_at": "2026-03-18T10:30:00Z",
      "updated_at": "2026-03-20T14:32:10Z",
      "status": "active",
      "message_count": 24,
      "llm_requests": 12,
      "tokens": {
        "input": 45000,
        "output": 22500,
        "total": 67500
      },
      "models_used": ["gpt-4-turbo"],
      "avg_response_time_ms": 2100,
      "messages_preview": [
        {
          "id": "msg_1",
          "role": "user",
          "content": "Quais são os benefícios disponíveis?",
          "created_at": "2026-03-18T10:30:00Z"
        },
        {
          "id": "msg_2",
          "role": "assistant",
          "content": "Temos os seguintes benefícios...",
          "created_at": "2026-03-18T10:32:15Z"
        }
      ]
    },
    {
      "id": "conv_660e8400-e29b-41d4",
      "user_id": "bob",
      "title": "Processo de Folha de Pagamento",
      "created_at": "2026-03-19T14:15:00Z",
      "updated_at": "2026-03-19T16:45:00Z",
      "status": "completed",
      "message_count": 8,
      "llm_requests": 5,
      "tokens": {
        "input": 20000,
        "output": 8500,
        "total": 28500
      },
      "models_used": ["gpt-4o"],
      "avg_response_time_ms": 1950,
      "messages_preview": []
    }
  ],
  "pagination": {
    "total_pages": 13,
    "current_page": 1,
    "has_next": true,
    "has_previous": false
  }
}
```

#### Exemplos cURL

**Últimas conversas (ordenadas por data):**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/detailed?limit=10&offset=0&order_by=created_at"
```

**Conversas por usuário, paginadas:**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/detailed?user_id=alice&limit=20&offset=0"
```

**Conversas com mais mensagens:**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/detailed?order_by=message_count&limit=10"
```

**Período específico:**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/detailed?start_date=2026-03-01&end_date=2026-03-20&limit=50"
```

---

### 3. GET `/export`

**Exportar dados do dashboard em diferentes formatos**

#### Query Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `format` | string | Sim | `json` ou `csv` |
| `start_date` | string | Não | Data início (YYYY-MM-DD) |
| `end_date` | string | Não | Data fim (YYYY-MM-DD) |
| `user_id` | string | Não | Filtrar por usuário |

#### Response

**Format: JSON (200 OK)**
```json
{
  "format": "json",
  "exported_at": "2026-03-20T15:30:00Z",
  "data": {
    "summary": {...},
    "conversations": [...]
  }
}
```

**Format: CSV (200 OK)**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="dashboard_export_2026-03-20.csv"

user_id,conversation_id,title,created_at,updated_at,message_count,tokens_used,model
alice,conv_550e8400-e29b-41d4,Benefícios de Saúde,2026-03-18T10:30:00Z,2026-03-20T14:32:10Z,24,67500,gpt-4-turbo
bob,conv_660e8400-e29b-41d4,Processo de Folha,2026-03-19T14:15:00Z,2026-03-19T16:45:00Z,8,28500,gpt-4o
```

#### Exemplos cURL

**Exportar como JSON:**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/export?format=json" \
  > dashboard_report.json
```

**Exportar como CSV:**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/export?format=csv" \
  > dashboard_report.csv
```

**Exportar período específico em CSV:**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/export?format=csv&start_date=2026-03-01&end_date=2026-03-20" \
  > report_march.csv
```

---

## 🔒 Segurança e Permissões

- ✅ Todos endpoints requerem **JWT autenticado**
- ✅ Usuários veem apenas **dados de suas próprias conversas**
- ✅ Admins podem filtrar por `user_id` para ver dados de outros
- ✅ Logs de auditoria registram todos os acessos

## 📈 Casos de Uso Comuns

### 1. Dashboard de Executivos (semanal)

```bash
# Obter resumo semanal
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/summary?start_date=2026-03-14&end_date=2026-03-20"
```

**Resultado:** Métricas de uso, custos de LLM, usuários mais ativos.

### 2. Análise de Desempenho

```bash
# Identificar gargalos (conversas lentas)
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/detailed?order_by=created_at&limit=50" | jq '.conversations[] | select(.avg_response_time_ms > 3000)'
```

### 3. Relatório para Cliente/Stakeholder

```bash
# Exportar tudo em CSV para análise em Excel
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/export?format=csv" \
  > relatorio_${date +%Y-%m-%d}.csv
```

### 4. Monitoramento de Custos

```bash
# Verificar gastos com LLM
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/summary" | jq '.llm_usage.cost_estimates'
```

### 5. Auditoria por Usuário

```bash
# Ver todas as atividades de um usuário
curl -X GET "http://localhost:8000/api/v1/chat/dashboard/detailed?user_id=alice&limit=1000"
```

---

## 🧮 Métricas Explicadas

### LLM Usage
- **total_tokens**: Soma de tokens de entrada + saída
- **cost_estimates**: Baseado em preços atuais do OpenAI (pode variar)
- **models_used**: Breakdown por modelo (GPT-4, GPT-4o, etc)

### Performance
- **p50 (mediana)**: 50% das requisições são mais rápidas que isso
- **p95**: 95% das requisições são mais rápidas que isso
- **p99**: 99% das requisições são mais rápidas que isso

### Top Users
- Baseado em mensagens enviadas
- Útil para identificar power-users e casos de uso comuns

### Completion Metrics
- **completion_rate**: % de conversas que foram encerradas/respondidas
- **average_duration**: Tempo médio de uma conversa (em minutos)

---

## 🐛 Troubleshooting

### "Sem dados retornados"
- Verificar se há conversas no período especificado
- Usar `end_date=hoje` para garantir que esteja buscando dados recentes

### "Tokens gastos = 0"
- Confirmar que o LLM Server retornou token counts
- Ver `LLM_TROUBLESHOOTING.md` se houver problemas com LLM

### "Erro ao exportar CSV"
- Tentar em JSON primeiro para verificar dados
- Verificar permissões e quota de usuário

### "Performance muito lenta"
- Usar filtros (`user_id`, período) para reduzir dados
- Considerar exportar em CSV para análise offline em vez de consultas em tempo real

---

## 📝 Integração com Frontend

### Widget de Dashboard

```javascript
// Buscar resumo a cada 5 minutos
setInterval(async () => {
  const response = await fetch('/api/v1/chat/dashboard/summary');
  const data = await response.json();
  
  // Atualizar cards de métrica
  document.getElementById('total-conversations').textContent = data.conversations.total;
  document.getElementById('total-tokens').textContent = data.llm_usage.total_tokens;
  document.getElementById('cost').textContent = `$${data.llm_usage.cost_estimates.total_estimated}`;
}, 5 * 60 * 1000);
```

### Gráfico de Linha (Últimas 7 conversas)

```javascript
// Buscar conversas recentes
const response = await fetch('/api/v1/chat/dashboard/detailed?limit=100&order_by=created_at');
const data = await response.json();

// Agrupar por dia e plotar
const dailyData = groupBy(data.conversations, 'created_at');
renderChart(dailyData);
```

### Relatório em PDF (via export)

```javascript
// Exportar como JSON, converter para PDF no frontend ou backend
const csv = await fetch('/api/v1/chat/dashboard/export?format=csv');
downloadFile(csv, 'dashboard_report.csv');
```

---

## 🔗 Documen​tação Relacionada

- [CHAT_API.md](CHAT_API.md) - Endpoints de chat
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md#dashboard-api) - Problemas com Dashboard
- [CONFIG_KEYS.md](CONFIG_KEYS.md) - Configurações de analytics
- [SECURITY.md](SECURITY.md#audit-logging) - Logging de auditoria

