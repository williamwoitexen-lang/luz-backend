# Multi-Instance Refactoring - Preparação para Auto-Scaling

**Data**: 16 de Março de 2026  
**Versão**: 1.0  
**Status**: 📋 Planejamento de Refatoração

---

## Problema Identificado - Atualizado com Descobertas Reais

Atualmente, a aplicação tem **estado distribuído em múltiplas áreas** não sincronizadas entre instâncias.

### Áreas Identificadas

**✅ JÁ RESOLVIDO:**

1. **`app/utils/temp_storage.py`** - Tem Redis integrado com fallback
   - `REDIS_AVAILABLE = True` (redis>=4.0.0 em requirements.txt)
   - Auto-fallback para em-memória se Redis falhar
   - Status: ✅ Pronto, só aguarda Redis disponível em produção

2. **`app/tasks/celery_app.py`** - Celery já usa Redis
   - `broker='redis://localhost:6379/1'`
   - `backend='redis://localhost:6379/2'`
   - Status: ✅ Pronto, só aguarda Redis disponível em produção

**❌ AINDA PRECISA CORRIGIR:**

1. **`app/routers/stress_test.py`** - Estado em RAM local
   ```python
   active_tests: Dict[str, Dict] = {}  # ❌ Em-memória
   ```
   - Problema: Metadados de testes não sincronizados entre instâncias
   - Solução: Migrar para Redis (1-2 horas)
   - Impacto: Média (apenas para testing em debug)

2. **`app/services/task_queue.py`** - ThreadPoolExecutor local + Queue
   ```python
   task_queue = queue.Queue(maxsize=1000)  # ❌ Em-memória
   executor = ThreadPoolExecutor(max_workers=5)
   ```
   - Problema: Se existe overlap com Celery, haverá estado duplicado
   - Investigação: Precisa verificar se está sendo usado ou se Celery substituiu
   - Solução: A/B) Remover e usar Celery exclusivamente, ou B) Aceitar que cada instância tem sua fila local
   - Impacto: Baixa (background tasks são lentas, perder uma não é crítico)

### Sintomas

- ⚠️ Auto-scaling desabilitado em Azure (`MIN_REPLICAS=1`, `MAX_REPLICAS=1`)
- ❌ Stress test com 2+ instâncias não funciona
- ⏳ Task queue pode perder tasks se instância cair (mas Celery continua)

### Causa Raiz

---

## Impacto

### Em Desenvolvimento (Local)
✅ Funciona perfeitamente com 1 instância

### Em Staging/Produção (Multi-Instance)
❌ **Não funciona** porque:
- Requisição 1 vai para instância A (arquivo salvo em RAM da instância A)
- Requisição 2 vai para instância B (não consegue acessar arquivo da instância A)
- Operações falham com: **"Temporary file not found"**

### Exemplo do Problema

```
Cliente HTTP
   ↓
POST /ingest-preview (vai para instância A)
   ├─ Salva arquivo em /temp/instance_A_memory/
   └─ Retorna temp_id = "abc123"
   ↓
POST /ingest-confirm/abc123 (vai para instância B)
   ├─ Procura arquivo em /temp/instance_B_memory/
   └─ ❌ Erro: temp file not found!
```

---

## Solução Proposta

### ⚡ Caminho Rápido: Redis (Quando Liberado)

Se Redis for liberado como serviço compartilhado, a solução é **significativamente mais simples**:

```python
# Problema Atual (RAM - não sincronizado)
_storage = {}  # ❌ Cada instância tem seu próprio dicionário

# Solução com Redis (Sincronizado)
redis_client.set(f"temp:{file_id}", content)  # ✅ Compartilhado entre instâncias
```

**Implementação:**
- Usar Redis para sincronizar `temp_storage.py` entre instâncias
- Usar Redis para guardar estado de stress tests
- TTL automático nas chaves (10 min para temp files)
- Sem dependência de Blob Storage (mais simples)

**Estimativa**: **4-6 horas** total

**Timeline**: 
- Assim que Redis for liberado: implementação em 1 dia
- Auto-scaling habilitado imediatamente após testes

---

### ❌ Caminho Longo: Blob Storage (Se Redis Não Estiver Disponível)

Se Redis não for viável, usar Azure Blob Storage como fallback:

**Arquivo**: `app/utils/temp_storage.py`

**Antes (RAM Local):**
```python
class TempStorage:
    _storage = {}  # ❌ Em-memory, não compartilhado entre instâncias
    
    @staticmethod
    def save(file_id: str, content: bytes):
        TempStorage._storage[file_id] = content
```

**Depois (Azure Blob Storage):**
```python
class TempStorage:
    @staticmethod
    async def save(file_id: str, content: bytes):
        # Salvar em 'embeddings/temp/{file_id}.bin' no Blob
        await blob_client.upload_blob(
            container="embeddings",
            name=f"temp/{file_id}.bin",
            data=content
        )
```

**Estimativa**: **2-3 dias** total

- Blob Storage upload/download: ~50-100ms network latency
- Arquivo compartilhado entre instâncias
- Auto-cleanup com TTL

---

## Recomendação

| Cenário | Solução | Timeline | Esforço |
|---------|---------|----------|--------|
| **Redis liberado** ✅ | Usar Redis para temp storage | 1 dia | 4-6 horas |
| Redis não disponível | Migrar para Blob Storage | 2-3 dias | 2-3 dias |
**Recomendado**: Aguardar liberação do Redis → implementação rápida

---

## Checklist de Implementação (Com Redis)

### ✅ Fase 1: Integração Redis

---

---

## Checklist de Implementação (Com Redis)

### ✅ Fase 1: Ativar Redis em Produção (Ambiente Azure)

Redis já está integrado no código! Só precisa:

- [ ] Liberar acesso a Redis em Azure (REDIS_HOST, REDIS_PORT)
- [ ] Atualizar `deploy-azure.sh` com REDIS_HOST e REDIS_PORT
- [ ] Testar temp_storage.py com 2 instâncias
- [ ] Testar Celery tasks com 2 instâncias

**Timeline:** 1 hora (só configuração)

### ✅ Fase 2: Corrigir Stress Test

- [ ] Migrar `app/routers/stress_test.py`:
  - Remover `active_tests: Dict[str, Dict] = {}`
  - Usar `redis_client.hset(f"stress:{test_id}", ...)` para armazenar testes
  - Usar `redis_client.ttl()` para cleanup automático
- [ ] Testar com múltiplas instâncias
- [ ] Verificar que dados de stress test são compartilhados

**Timeline:** 1-2 horas

### ✅ Fase 3: Investigar task_queue.py

Precisa verificar se `app/services/task_queue.py` está sendo usado:

- [ ] `grep -r "enqueue_task\|task_queue" app/` para encontrar referências
- [ ] Se não está sendo usado: Remover arquivo e usar Celery exclusivamente
- [ ] Se está sendo usado: Avaliar se pode aceitar perda de tasks ou migrar para Celery

**Timeline:** 1 hora (análise)

### ✅ Fase 4: Habilitar Auto-Scaling

**Docker/Local:**
```bash
# Testar com 2 instâncias em paralelo
docker-compose up --scale api=2
# Fazer requisições em paralelo, verificar Redis
```

**Azure Deploy:**
```bash
# Atualizar deploy-azure.sh
MIN_REPLICAS=2
MAX_REPLICAS=10  # Ou mais
```

**Testes:**
- [ ] POST `/ingest-preview` em instância A
- [ ] POST `/ingest-confirm` em instância B (mesmo temp_id)
- [ ] Verificar que arquivo foi encontrado em B
- [ ] GET `/debug/agents` em ambas instâncias (sincronizado)
- [ ] Stress test distribuído: 50 requisições, 10 simultâneas

**Timeline:** 2-3 horas

---

## Impacto na Performance

### Com Redis

**Latência de Temp File Storage:**
```
Salvar arquivo: ~5-10ms (network to Redis)
Recuperar arquivo: ~5-10ms (network to Redis)
Total overhead: 10-20ms (vs 10ms em-memory)

✅ Imperceptível para usuário
✅ Múltiplas instâncias funcionam
```

### Alternativa: Com Blob Storage (sem Redis)

**Tempo de Ingestão Esperado:**

**Antes (RAM Local):**
```
Salvar arquivo: ~5ms (em memória)
Recuperar arquivo: ~5ms (lookup em dict)
Total: 10ms overhead
```

**Depois (Blob Storage):**
```
Upload para blob: ~50-100ms (network)
Download de blob: ~50-100ms (network)
Total: 100-200ms overhead

Mas: Arquivo persiste, múltiplas instâncias funcionam
```

---

## Rollout Strategy

**Fase de Desenvolvimento:**
- [ ] Implementar em branch `refactor/multi-instance`
- [ ] Testes completos em local
- [ ] Code review obrigatório

**Fase de Staging:**
- [ ] Deploy com 2 replicas
- [ ] Monitorar por 48h
- [ ] Teste de carga gradual (5%→25%→100%)

**Fase de Produção:**
- [ ] Deploy com 2 replicas (blue-green)
- [ ] Monitorar por 24h
- [ ] Habilitar auto-scaling
- [ ] Caso de problema → rollback automático

---

## Arquitetura Após Refatoração (Com Redis)

```
┌─────────────────────────────────────┐
│       Azure Container Apps          │
├─────────────────────────────────────┤
│  Instance 1    Instance 2    Instance 3+
│  (API Port    (API Port     (API Port
│   8000)        8000)         8000)
│     │            │             │
│     └────────────┴─────────────┘
│                  │
│          Shared Redis Cache
│       (temp files + results)
│
│          SQL Server
│         + Azure Search
└─────────────────────────────────────┘
```

**Benefícios:**
- ✅ Stateless design
- ✅ Fault tolerant
- ✅ Auto-scaling habilitado
- ✅ Regional redundancy possível
- ✅ Simples implementação (não precisa Blob Storage)

---

## Roadmap Realista (Com Redis Já Integrado)

| Fase | Tarefa | Estimativa | Prioridade | Status |
|------|--------|-----------|-----------|--------|
| 1 | Ativar Redis em produção (config) | 1 hora | 🔴 Alta | ⏳ Aguarda liberação |
| 2 | Corrigir stress_test.py | 1-2 horas | 🟡 Média | ❌ Em progresso |
| 3 | Investigar task_queue.py | 1 hora | 🟡 Média | ❌ Em progresso |
| 4 | Testes + habilitar auto-scaling | 1-2 horas | 🔴 Alta | ⏳ Após fases 1-3 |

**Total Estimado:** **4-6 horas de trabalho** (1 dia desenvolvimento)

**Vs. Blob Storage:** 2-3 dias

---

## Documentação de Referência

- [Redis Documentation](https://redis.io/documentation)
- [Azure Cache for Redis](https://docs.microsoft.com/en-us/azure/azure-cache-for-redis/)
- [AWS ElastiCache for Redis](https://aws.amazon.com/elasticache/redis/)
- [Azure Container Apps Scaling](https://docs.microsoft.com/en-us/azure/container-apps/scale-app)

---

## Próximos Passos (Ação Imediata)

1. **Quando Redis for liberado em Azure:**
   - Adicionar REDIS_HOST e REDIS_PORT em deploy-azure.sh ou environment
   - Testar temp_storage com 2 instâncias
   - Testar Celery tasks com 2 instâncias

2. **Corrigir stress_test.py (paralelo):**
   - Migrar `active_tests` para Redis
   - Testar stress test com múltiplas instâncias

3. **Verificar task_queue.py:**
   - Rodar `grep -r "enqueue_task" app/` para ver se está em uso
   - Se não: Remover arquivo
   - Se sim: Avaliar criticidade de perda de tasks

4. **Habilitar auto-scaling:**
   ```bash
   MIN_REPLICAS=2
   MAX_REPLICAS=10
   ```

---

## Notas

- Redis JÁ está integrado no código - não precisa refatorar do zero
- Celery JÁ está configurado - background tasks já funcionam
- Só faltam: config de ambiente + corrigir stress_test.py
- Muito mais simples do que parecia inicialmente!


