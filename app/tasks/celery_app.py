"""
Configuração do Celery para processamento assincronado.

Tasks são enfileiradas no Redis e processadas por workers.
"""

import logging
import os
from celery import Celery
from kombu import Exchange, Queue

logger = logging.getLogger(__name__)

# Criar app Celery
app = Celery(
    'embeddings',
    broker='redis://localhost:6379/1',  # Redis DB 1 para tasks
    backend='redis://localhost:6379/2'  # Redis DB 2 para resultados
)

# Configurações
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task timeouts
    task_soft_time_limit=300,  # 5 min aviso
    task_time_limit=600,       # 10 min kill
    
    # Retry policy
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Concurrency (max tasks simultâneos)
    worker_concurrency=10,
    worker_prefetch_multiplier=1,  # Pega 1 task por vez
    
    # Queues
    task_default_queue='default',
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('chat', Exchange('chat'), routing_key='chat'),
    ),
    
    # Routing
    task_routes={
        'app.tasks.chat_tasks.*': {'queue': 'chat'},
    },
)

logger.info("[Celery] Configurado com Redis broker")
