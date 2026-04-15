# Background Tasks & Task Queue - Documentação

**Data**: 16 de Março de 2026  
**Versão**: 1.0  
**Status**: ✅ Documentação Completa

---

## Visão Geral

O sistema utiliza **duas estratégias complementares** para processamento assincronado:

1. **ThreadPoolExecutor (Local)** - `app/services/task_queue.py`
   - Para tarefas rápidas e locais (não compartilhadas entre instâncias)
   - Exemplo: Salvar chat em background, processar indíces

2. **Celery + Redis** - `app/tasks/celery_app.py`
   - Para tarefas distribuídas e long-running
   - Compartilhadas entre instâncias
   - Exemplo: Processamento pesado, agendamentos

---

## ThreadPoolExecutor - Task Queue Local

### O que é

Sistema de fila local com pool de workers que processa tarefas em threads separadas.

- **Max Workers**: 5 simultâneos
- **Max Queue Size**: 1000 tarefas
- **Timeout**: Nenhum (executa até completar)
- **Fallback**: Se fila encher, task é descartada (log de erro)

### Uso

**Enfileirar uma tarefa:**

```python
from app.services.task_queue import enqueue_task

def save_chat_async(chat_id: str, message: str):
    """Salvar chat em background"""
    # Lógica aqui...
    print(f"Chat {chat_id} salvo")

# Enfileirar
enqueue_task(save_chat_async, chat_id="conv_123", message="Hello")
```

**Na aplicação:**

```python
from fastapi import APIRouter
from app.services.task_queue import enqueue_task

@app.post("/ask")
def ask_question(request: ChatRequest):
    # 1. Processar pergunta (rápido)
    answer = process_question(request.text)
    
    # 2. Salvar em background (assincronamente)
    enqueue_task(save_to_database, chat_id=request.chat_id, answer=answer)
    
    # 3. Retornar resposta imediatamente (não bloqueia)
    return {"answer": answer}
```

### Arquitetura

```
Cliente HTTP
   ↓
POST /api/v1/chat/question
   ↓
Backend processa pergunta (rápido: 0.5s)
   ├─ Chama LLM
   └─ Prepara resposta
   ↓
enqueue_task(save_database, ...)  ← Não bloqueia
   ├─ Adiciona à fila
   └─ Retorna imediatamente
   ↓
ThreadPoolExecutor (5 workers)
   ├─ Worker 1: Executando task 1
   ├─ Worker 2: Executando task 2
   ├─ Worker 3: Esperando
   ├─ Queue: [task_4, task_5, task_6, ...]
   └─ Tarefas executam em paralelo

Cliente HTTP recebe resposta em 0.5s
Workers salvam dados em background (1-2s)
```

### Limitações Conhecidas

| Limitação | Impacto | Solução |
|-----------|---------|---------|
| Não sincroniza entre instâncias | Task em A não vê tasks de B | Usar Celery para multi-instance |
| Queue em RAM (max 1000) | Pode perder tasks se app cair | Usar Celery + Redis |
| Workers por instância | 5 workers × N instâncias = N×5 | Aceitável se tasks são rápidas |
| Sem timeout | Task longa bloqueia worker | Adicionar timeout ou usar Celery |

---

## Celery + Redis - Task Queue Distribuída

### O que é

Task queue distribuída que sincroniza tarefas entre múltiplas instâncias via Redis.

- **Broker**: Redis DB 1 (enfileiramento)
- **Backend**: Redis DB 2 (resultados)
- **Workers**: Processam tasks do Redis
- **Sincronização**: Compartilhado entre instâncias

### Configuração

**`app/tasks/celery_app.py`:**

```python
from celery import Celery

app = Celery(
    'embeddings',
    broker='redis://localhost:6379/1',      # Redis para fila
    backend='redis://localhost:6379/2'      # Redis para resultados
)

app.conf.update(
    task_soft_time_limit=300,      # 5 min aviso
    task_time_limit=600,           # 10 min hard limit
    task_serializer='json',
)
```

### Uso

**Definaçãao de tarefa:**

```python
from app.tasks.celery_app import app

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: int):
    """Tarefa long-running no background"""
    try:
        # Processar documento
        result = expensive_operation(document_id)
        return {"status": "success", "result": result}
    except Exception as exc:
        # Retry com backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

**Chamar tarefa:**

```python
from app.tasks.tasks import process_document

# Enfileirar
task = process_document.delay(document_id=123)

# Esperar resultado (com timeout)
result = task.get(timeout=300)  # 5 min

# Verificar status
task.status  # 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'RETRY'
```

### Exemplo Completo

**Tarefa (arquivo: `app/tasks/tasks.py`):**

```python
from app.tasks.celery_app import app
import logging

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3)
def index_document(self, document_id: int, file_path: str):
    """
    Tarefa: Indexar documento no Azure Search
    
    Executada em background via Celery workers
    """
    try:
        logger.info(f"Indexando documento {document_id}...")
        
        # 1. Ler arquivo
        content = read_from_blob(file_path)
        
        # 2. Indexar
        index_result = azure_search_client.upload_documents([{
            "id": document_id,
            "content": content,
            "indexed_at": datetime.now()
        }])
        
        logger.info(f"✅ Documento {document_id} indexado com sucesso")
        return {"status": "success", "indexed_at": datetime.now().isoformat()}
        
    except Exception as exc:
        logger.error(f"❌ Erro indexando {document_id}: {exc}")
        # Retry automático com exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

**Usar tarefa (em routers):**

```python
from app.tasks.tasks import index_document

@app.post("/documents/ingest")
def ingest_document(file: UploadFile):
    # 1. Salvar arquivo no blob
    file_path = save_to_blob(file)
    
    # 2. Criar documento no DB
    doc = create_document(filename=file.filename, file_path=file_path)
    
    # 3. Enfileirar indexação (não bloqueia)
    task = index_document.delay(
        document_id=doc.id,
        file_path=file_path
    )
    
    return {
        "document_id": doc.id,
        "task_id": task.id,
        "status": "indexing_in_background"
    }

# Endpoint para checar progresso
@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    from app.tasks.celery_app import app
    
    task = app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.successful() else None,
        "error": str(task.info) if task.failed() else None
    }
```

---

## Comparação: ThreadPool vs Celery

| Aspecto | ThreadPool | Celery |
|--------|-----------|--------|
| **Sincronização** | Local (não sincroniza) | Distribuída (Redis) |
| **Multi-Instance** | ❌ Não funciona | ✅ Funciona |
| **Persistência** | ❌ RAM (perde se cair) | ✅ Redis |
| **Retry Automático** | ❌ Não | ✅ Sim (com backoff) |
| **Escalabilidade** | ⚠️ Limitada | ✅ Ilimitada |
| **Setup** | ✓ Simples | ⏳ Mais complexo |
| **Casos de Uso** | Tarefas rápidas | Tarefas long-running |

---

## Quando Usar Cada Uma

### Use ThreadPool quando:
- ✅ Tarefa é rápida (< 1 segundo)
- ✅ Não precisa sincronizar entre instâncias
- ✅ OK se perder alguns dados
- ✅ Exemplo: Log em background, cache invalidation

### Use Celery quando:
- ✅ Tarefa é longa (> 5 segundos)
- ✅ Precisa sincronizar entre instâncias
- ✅ Importante não perder a tarefa
- ✅ Precisa de retry automático
- ✅ Exemplo: Indexação, processamento pesado, agendamentos

---

## Monitoramento

### ThreadPool

```python
from app.services.task_queue import task_queue, executor

# Tamanho atual da fila
print(f"Queue size: {task_queue.qsize()}/1000")

# Info de workers
print(f"Active threads: {executor._work_queue.qsize()}")
```

### Celery

```bash
# Monitorar tasks
celery -A app.tasks.celery_app inspect active

# Ver registered tasks
celery -A app.tasks.celery_app inspect registered

# Flores UI (dashboard)
celery -A app.tasks.celery_app flower
# Acessa em http://localhost:5555
```

---

## Troubleshooting

### "Task descartada - Fila cheia"

```
[TaskQueue] ⚠️ Fila cheia! Task descartada.
```

**Solução:**
- Aumentar `maxsize` em task_queue.py
- Ou usar Celery (melhor escalabilidade)

### Celery não processa tasks

```bash
# 1. Verificar se Redis está rodando
redis-cli ping

# 2. Verificar se workers estão rodando
celery -A app.tasks.celery_app worker --loglevel=info

# 3. Checar broker connection
celery -A app.tasks.celery_app inspect active
```

### Task nunca completa

```python
# Aumentar timeout
@app.task(time_limit=600)  # 10 minutos
def long_task():
    pass
```

---

## Próximos Passos

- [ ] Adicionar monitoramento de fila (métricas)
- [ ] Dashboard Flower para Celery em produção
- [ ] Alertas se fila crescer muito
- [ ] Documentar tasks específicas do projeto
