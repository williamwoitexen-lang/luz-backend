# Stress Testing - Testes de Carga e Performance

**Data**: 16 de Março de 2026  
**Versão**: 1.0  
**Status**: ✅ Documentação Completa

---

## Visão Geral

O **Stress Testing Endpoint** permite testar a performance e carga do sistema de chat sob condições de stress. Gera métricas detalhadas como latência (p50, p95, p99), throughput e TTFT (Time-To-First-Token).

Útil para:
- ✅ Validar performance antes de deployment
- ✅ Simular carga de usuários
- ✅ Identificar gargalos
- ✅ Estabelecer baseline de performance
- ✅ Testar capacidade de auto-scaling

---

## Endpoint

### Executar Stress Test no Chat

**POST** `/api/v1/chat/stress-test`

Executa múltiplas requisições de chat em paralelo e coleta métricas de performance.

**Request:**
```json
{
  "num_requests": 10,
  "concurrency": 5,
  "timeout_seconds": 30,
  "user_id": "emp_stress_test",
  "name": "Stress Test User",
  "email": "test@company.com",
  "country": "Brazil",
  "city": "San Paulo",
  "role_id": 1,
  "department": "IT",
  "job_title": "Engineer",
  "collar": "white",
  "unit": "Tech",
  "agent_id": 1
}
```

**Response:**
```json
{
  "status": "ok",
  "test_id": "stress_test_abc123",
  "summary": {
    "total_requests": 10,
    "successful_requests": 10,
    "failed_requests": 0,
    "total_duration_seconds": 4.5,
    "throughput_requests_per_second": 2.22
  },
  "latency": {
    "min_ms": 245.6,
    "max_ms": 587.3,
    "mean_ms": 389.2,
    "median_ms": 381.5,
    "p95_ms": 550.1,
    "p99_ms": 580.4
  },
  "ttft": {
    "min_ms": 45.2,
    "max_ms": 120.5,
    "mean_ms": 78.3,
    "p95_ms": 105.2,
    "p99_ms": 115.8
  },
  "tokens": {
    "total_prompt_tokens": 4190,
    "total_completion_tokens": 930,
    "mean_prompt_tokens": 419,
    "mean_completion_tokens": 93
  },
  "requests": [
    {
      "request_id": 1,
      "status": "success",
      "latency_ms": 389.2,
      "ttft_ms": 78.3,
      "prompt_tokens": 419,
      "completion_tokens": 93,
      "error": null
    },
    {
      "request_id": 2,
      "status": "success",
      "latency_ms": 392.1,
      "ttft_ms": 80.1,
      "prompt_tokens": 419,
      "completion_tokens": 93,
      "error": null
    }
    // ... 8 mais requisições
  ]
}
```

---

## Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `num_requests` | int | 10 | Total de requisições a executar |
| `concurrency` | int | 5 | Número de requisições simultâneas |
| `timeout_seconds` | int | 30 | Timeout para cada requisição |
| `user_id` | string | "stress_test_user" | ID do usuário (qualquer valor) |
| `name` | string | "Stress Test" | Nome do usuário |
| `email` | string | "test@company.com" | Email do usuário |
| `country` | string | "Brazil" | País |
| `city` | string | "San Paulo" | Cidade |
| `role_id` | int | 1 | ID da função |
| `agent_id` | int | 1 | ID do agente |

**Exemplos:**

```bash
# Teste leve (10 requisições, 2 simultâneas)
curl -X POST http://localhost:8000/api/v1/chat/stress-test \
  -H "Content-Type: application/json" \
  -d '{
    "num_requests": 10,
    "concurrency": 2
  }'

# Teste moderado (50 requisições, 10 simultâneas)
curl -X POST http://localhost:8000/api/v1/chat/stress-test \
  -H "Content-Type: application/json" \
  -d '{
    "num_requests": 50,
    "concurrency": 10
  }'

# Teste pesado (100 requisições, 20 simultâneas)
curl -X POST http://localhost:8000/api/v1/chat/stress-test \
  -H "Content-Type: application/json" \
  -d '{
    "num_requests": 100,
    "concurrency": 20,
    "timeout_seconds": 60
  }'
```

---

## Interpretação de Resultados

### **Latência (Latency)**

Tempo total entre envio da requisição e recebimento da resposta completa.

- **min_ms**: Melhor caso de resposta
- **max_ms**: Pior caso de resposta
- **mean_ms**: Média aritmética
- **median_ms**: Mediana (50º percentil)
- **p95_ms**: 95º percentil (95% das requisições são mais rápidas)
- **p99_ms**: 99º percentil (99% das requisições são mais rápidas)

**Interpretação:**
```
✅ Bom:  p95 < 500ms, p99 < 1000ms
⚠️ OK:   p95 < 1000ms, p99 < 2000ms
❌ Ruim: p95 > 1000ms ou p99 > 2000ms
```

### **TTFT (Time-To-First-Token)**

Tempo entre envio da requisição e recebimento do primeiro token da resposta.

Importante para UX de streaming em tempo real.

**Interpretação:**
```
✅ Excelente: TTFT < 100ms
✅ Bom:       TTFT < 200ms
⚠️ OK:        TTFT < 500ms
❌ Ruim:      TTFT > 500ms (usuário percebe lag)
```

### **Throughput**

Número de requisições processadas por segundo.

**Interpretação:**
```
✅ Bom:  > 2 req/s
⚠️ OK:   1-2 req/s
❌ Ruim: < 1 req/s
```

### **Taxa de Sucesso**

```
✅ Excelente: 100% sucesso
⚠️ OK:        > 99% sucesso
❌ Ruim:      < 99% sucesso
```

---

## Casos de Uso

### **Caso 1: Validar Performance Baseline**

Executar teste antes de mudanças de código para estabelecer baseline:

```bash
curl -X POST http://localhost:8000/api/v1/chat/stress-test \
  -H "Content-Type: application/json" \
  -d '{"num_requests": 50, "concurrency": 10}' \
  | jq '.latency'

# Resultado esperado:
# {
#   "p95_ms": 450,
#   "p99_ms": 800,
#   "mean_ms": 380
# }
```

**Guardar este resultado para comparação futura.**

### **Caso 2: Testar Impacto de Mudança de Código**

Após mudança, executar novamente e comparar:

```bash
# Antes
curl ... | jq '.summary.throughput_requests_per_second'
# resultado: 2.5 req/s

# Depois de mudança
curl ... | jq '.summary.throughput_requests_per_second'
# resultado: 2.1 req/s (4% degradação)
```

### **Caso 3: Encontrar Limite de Capacidade**

Aumentar concorrência até encontrar ponto de queda:

```bash
# Teste com concorrência crescente
for concurrence in 5 10 20 30 40; do
  echo "Testando com concorrência $concurrence"
  curl -X POST http://localhost:8000/api/v1/chat/stress-test \
    -d "{\"concurrency\": $concurrence}" | jq '.latency.p95_ms'
  sleep 10
done

# Encontrar onde p95 começa a piorar significativamente
```

### **Caso 4: Simular Carga de Produção**

Se em produção você espera 50 requisições simultâneas:

```bash
curl -X POST http://localhost:8000/api/v1/chat/stress-test \
  -d '{"num_requests": 100, "concurrency": 50}'
```

---

## Limitações Conhecidas

⚠️ **Estado Em Memória**: O sistema atual não é thread-safe para múltiplas instâncias. Stress test só funciona com 1 réplica.

❌ Não suporta:
- Múltiplas instâncias em paralelo
- Distributed load testing
- Testes com dados reais de produção (uses LLM Server mock)

✅ Suporta:
- Testes locais de performance
- Baseline de throughput e latência
- Identificação de gargalos em single instance

---

## Scriptando Stress Tests

**Python:**
```python
import requests
import json
from datetime import datetime

def run_stress_test(num_requests, concurrency):
    payload = {
        "num_requests": num_requests,
        "concurrency": concurrency,
        "user_id": "stress_test"
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/chat/stress-test",
        json=payload
    )
    
    result = response.json()
    
    print(f"Test ID: {result['test_id']}")
    print(f"Success: {result['summary']['successful_requests']}/{result['summary']['total_requests']}")
    print(f"P95 Latency: {result['latency']['p95_ms']:.2f}ms")
    print(f"Throughput: {result['summary']['throughput_requests_per_second']:.2f} req/s")
    
    return result

# Executar teste
result = run_stress_test(num_requests=50, concurrency=10)

# Salvar resultado
with open(f"stress_test_{datetime.now().isoformat()}.json", "w") as f:
    json.dump(result, f, indent=2)
```

**Bash:**
```bash
#!/bin/bash

NUM_REQUESTS=50
CONCURRENCY=10

response=$(curl -s -X POST http://localhost:8000/api/v1/chat/stress-test \
  -H "Content-Type: application/json" \
  -d "{\"num_requests\": $NUM_REQUESTS, \"concurrency\": $CONCURRENCY}")

# Extrair métricas
p95=$(echo $response | jq '.latency.p95_ms')
throughput=$(echo $response | jq '.summary.throughput_requests_per_second')
success_rate=$(echo $response | jq '.summary.successful_requests / .summary.total_requests * 100')

echo "P95 Latency: ${p95}ms"
echo "Throughput: ${throughput} req/s"
echo "Success Rate: ${success_rate}%"
```

---

## Próximos Passos

- [ ] Implementar distributed load testing (múltiplas instâncias)
- [ ] Adicionar histórico comparativo para trends
- [ ] Integrar com sistema de alertas (PagerDuty, Slack)
- [ ] Dashboard em tempo real de metrics
- [ ] Teste com dados reais de documentos
