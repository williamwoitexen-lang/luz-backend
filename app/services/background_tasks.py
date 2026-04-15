"""
Tarefas em background usando fila gerenciada.

Usa ThreadPoolExecutor com limite de workers.
Evita travamento SQL.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def save_chat_message_worker(
    conversation_id: str,
    user_id: str,
    question: str,
    llm_response: Dict[str, Any],
    document_categories_used: Optional[Dict[str, Any]] = None
) -> None:
    """
    Worker que salva pergunta e resposta (roda em thread do executor).
    
    Args:
        conversation_id: ID da conversa
        user_id: ID do usuário
        question: Pergunta do usuário
        llm_response: Resposta do LLM
        document_categories_used: Categorias usadas (optional)
    """
    try:
        logger.info(f"[SaveChat] Iniciando salvamento: conversation={conversation_id}, user={user_id}")
        
        from app.services.conversation_service import ConversationService
        
        result = ConversationService.save_question_and_answer(
            conversation_id=conversation_id,
            user_id=user_id,
            question=question,
            llm_response=llm_response,
            document_categories_used=document_categories_used
        )
        
        logger.info(f"[SaveChat] ✅ Salvamento concluído: {result.get('message_id', 'N/A')}")
        
    except Exception as e:
        logger.error(f"[SaveChat] ❌ Erro ao salvar: {e}", exc_info=True)


def save_chat_message_async(
    conversation_id: str,
    user_id: str,
    question: str,
    llm_response: Dict[str, Any],
    document_categories_used: Optional[Dict[str, Any]] = None
) -> None:
    """
    Enfileirar salvamento de pergunta e resposta (não bloqueia).
    
    A task entra na fila e é processada por um dos 5 workers.
    Se todos os 5 workers estão ocupados, aguarda na fila.
    
    Args:
        conversation_id: ID da conversa
        user_id: ID do usuário
        question: Pergunta do usuário
        llm_response: Resposta do LLM
        document_categories_used: Categorias usadas (optional)
    """
    from app.services.task_queue import enqueue_task
    
    enqueue_task(
        save_chat_message_worker,
        conversation_id,
        user_id,
        question,
        llm_response,
        document_categories_used
    )
    logger.debug(f"[SaveChat] Task enfileirada para {conversation_id}")

