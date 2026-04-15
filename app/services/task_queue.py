"""
Gerenciador de fila para tarefas em background.

Usa ThreadPoolExecutor para limitar workers simultâneos.
Evita travamento SQL com limite de inserts.
"""

import logging
import queue
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any

logger = logging.getLogger(__name__)

# Fila global de tasks
task_queue = queue.Queue(maxsize=1000)

# ThreadPoolExecutor com max 5 workers (inserts simultâneos)
executor = ThreadPoolExecutor(
    max_workers=5,
    thread_name_prefix="task-worker"
)

logger.info("[TaskQueue] Inicializado com 5 workers máximo")


def enqueue_task(task_func: Callable, *args, **kwargs) -> None:
    """
    Enfileirar uma tarefa para processar.
    
    Se queue estiver cheia (>1000), loga aviso.
    
    Args:
        task_func: Função a executar
        *args, **kwargs: Argumentos da função
    """
    try:
        task_queue.put((task_func, args, kwargs), block=False)
        queue_size = task_queue.qsize()
        logger.debug(f"[TaskQueue] Task enfileirada. Fila: {queue_size}/1000")
    except queue.Full:
        logger.error("[TaskQueue] ⚠️ Fila cheia! Task descartada.")


def _worker_loop():
    """
    Worker que processa tasks da fila continuamente.
    
    Executa em thread do ThreadPoolExecutor.
    """
    while True:
        try:
            task_func, args, kwargs = task_queue.get()
            
            try:
                logger.debug(f"[TaskQueue] Processando: {task_func.__name__}")
                task_func(*args, **kwargs)
                logger.debug(f"[TaskQueue] ✅ Concluído: {task_func.__name__}")
            except Exception as e:
                logger.error(f"[TaskQueue] ❌ Erro em {task_func.__name__}: {e}", exc_info=True)
            
            task_queue.task_done()
            
        except Exception as e:
            logger.error(f"[TaskQueue] Erro crítico no worker: {e}", exc_info=True)


# Iniciar workers
for i in range(5):
    executor.submit(_worker_loop)
    logger.debug(f"[TaskQueue] Worker {i+1}/5 iniciado")

logger.info("[TaskQueue] ✅ Sistema de fila pronto")
