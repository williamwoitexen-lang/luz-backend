"""
Service para gerenciar conversas com histórico de perguntas e respostas.
"""
import logging
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.sqlserver import get_sqlserver_connection
from app.models import (
    ChatMessage,
    ConversationCreate,
    ConversationMessageResponse,
    ConversationResponse,
    ConversationDetail,
    QuestionResponse
)

logger = logging.getLogger(__name__)


class ConversationService:
    """Service para gerenciar conversas."""
    
    @staticmethod
    def create_conversation(user_id: str, title: Optional[str] = None) -> ConversationResponse:
        """
        Criar nova conversa.
        
        Args:
            user_id: ID do usuário
            title: Título opcional da conversa
            
        Returns:
            Dados da conversa criada
        """
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        try:
            sql = get_sqlserver_connection()
            
            query = """
            INSERT INTO conversations (conversation_id, user_id, title, created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            """
            
            sql.execute(query, [conversation_id, user_id, title, now, now])
            
            logger.info(f"Conversa criada: {conversation_id} para usuário {user_id}")
            
            return ConversationResponse(
                conversation_id=conversation_id,
                user_id=user_id,
                title=title,
                created_at=now,
                updated_at=now,
                is_active=True,
                message_count=0
            )
        except Exception as e:
            logger.error(f"Erro ao criar conversa: {e}")
            raise
    
    @staticmethod
    def add_message(
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        model: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        retrieval_time: Optional[float] = None,
        llm_time: Optional[float] = None,
        total_time: Optional[float] = None,
        document_categories_used: Optional[Dict[str, Any]] = None
    ) -> ConversationMessageResponse:
        """
        Adicionar mensagem à conversa.
        
        Args:
            conversation_id: ID da conversa
            user_id: ID do usuário
            role: 'user' ou 'assistant'
            content: Conteúdo da mensagem
            model: Modelo LLM usado (se assistant)
            prompt_tokens: Tokens de prompt (se assistant)
            completion_tokens: Tokens de conclusão (se assistant)
            retrieval_time: Tempo de recuperação de documentos (ms)
            llm_time: Tempo de resposta do LLM (ms)
            total_time: Tempo total de processamento (ms)
            document_categories_used: JSON com {"category_ids": [...], "category_names": [...]}
            
        Returns:
            Dados da mensagem criada
        """
        message_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        try:
            sql = get_sqlserver_connection()
            
            query = """
            INSERT INTO conversation_messages 
            (message_id, conversation_id, user_id, role, content, model, tokens_used, retrieval_time, llm_time, total_time, document_categories_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Total tokens = prompt + completion
            total_tokens = None
            if prompt_tokens is not None and completion_tokens is not None:
                total_tokens = prompt_tokens + completion_tokens
            
            # Converter dict para JSON string se fornecido
            categories_json = None
            if document_categories_used:
                categories_json = json.dumps(document_categories_used) if isinstance(document_categories_used, dict) else document_categories_used
            
            sql.execute(
                query,
                [message_id, conversation_id, user_id, role, content, model, total_tokens, retrieval_time, llm_time, total_time, categories_json, now]
            )
            
            # Atualizar updated_at da conversa
            update_query = "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?"
            sql.execute(update_query, [now, conversation_id])
            
            logger.info(f"Mensagem adicionada: {message_id} na conversa {conversation_id}")
            
            return ConversationMessageResponse(
                message_id=message_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                created_at=now
            )
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem: {e}")
            raise
    
    @staticmethod
    def save_question_and_answer(
        conversation_id: str,
        user_id: str,
        question: str,
        llm_response: Dict[str, Any],
        document_categories_used: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Salvar pergunta e resposta na conversa.
        
        Args:
            conversation_id: ID da conversa
            user_id: ID do usuário
            question: Pergunta do usuário
            llm_response: Resposta completa do LLM Server
            document_categories_used: JSON com {"category_ids": [...], "category_names": [...]}
            
        Returns:
            Dict com IDs das mensagens criadas
        """
        try:
            # Salvar pergunta do usuário
            user_msg = ConversationService.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content=question
            )
            
            # Se recebeu IDs de categoria, fazer lookup para pegar os nomes
            final_categories = None
            if document_categories_used and document_categories_used.get("category_ids"):
                try:
                    sql = get_sqlserver_connection()
                    category_ids = document_categories_used.get("category_ids", [])
                    
                    # Buscar nomes das categorias na tabela
                    placeholders = ",".join(["?" for _ in category_ids])
                    category_query = f"""
                    SELECT category_id, category_name
                    FROM dim_categories
                    WHERE category_id IN ({placeholders})
                    ORDER BY category_id
                    """
                    
                    category_results = sql.execute(category_query, category_ids)
                    category_names = []
                    
                    if category_results:
                        for row in category_results:
                            cat_name = row.get("category_name")
                            if cat_name:
                                category_names.append(cat_name)
                    
                    # Montar JSON completo com IDs e nomes
                    final_categories = {
                        "category_ids": category_ids,
                        "category_names": category_names if category_names else document_categories_used.get("category_names", [])
                    }
                    
                    logger.info(f"Categorias encontradas: {final_categories}")
                except Exception as e:
                    logger.warning(f"Erro ao buscar nomes de categorias: {e}")
                    final_categories = document_categories_used
            
            # Salvar resposta do assistente
            answer_text = llm_response.get("answer", "")
            model = llm_response.get("model", "gpt-4o-mini")
            prompt_tokens = llm_response.get("prompt_tokens", 0)
            completion_tokens = llm_response.get("completion_tokens", 0)
            retrieval_time = llm_response.get("retrieval_time")
            llm_time = llm_response.get("llm_time")
            total_time = llm_response.get("total_time")
            
            assistant_msg = ConversationService.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=answer_text,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                retrieval_time=retrieval_time,
                llm_time=llm_time,
                total_time=total_time,
                document_categories_used=final_categories
            )
            
            logger.info(f"Pergunta e resposta salvas na conversa {conversation_id}")
            
            return {
                "user_message_id": user_msg.message_id,
                "assistant_message_id": assistant_msg.message_id,
                "conversation_id": conversation_id
            }
        except Exception as e:
            logger.error(f"Erro ao salvar pergunta e resposta: {e}")
            raise
    
    @staticmethod
    def get_conversation(conversation_id: str) -> Optional[ConversationDetail]:
        """
        Obter conversa com todas as mensagens.
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            Detalhe da conversa com mensagens
        """
        try:
            sql = get_sqlserver_connection()
            
            # Buscar conversa
            conv_query = """
            SELECT conversation_id, user_id, title, created_at, updated_at, is_active, rating, rating_timestamp
            FROM conversations
            WHERE conversation_id = ?
            """
            conv_results = sql.execute(conv_query, [conversation_id])
            
            if not conv_results:
                logger.warning(f"Conversa não encontrada: {conversation_id}")
                return None
            
            conv_row = conv_results[0]
            
            # Buscar mensagens
            msg_query = """
            SELECT message_id, conversation_id, role, content, model, tokens_used, created_at
            FROM conversation_messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """
            msg_results = sql.execute(msg_query, [conversation_id])
            
            # Construir respostas de mensagens
            messages = []
            for row in msg_results:
                messages.append(ConversationMessageResponse(
                    message_id=row.get("message_id"),
                    conversation_id=row.get("conversation_id"),
                    role=row.get("role"),
                    content=row.get("content"),
                    model=row.get("model"),
                    prompt_tokens=None,  # Não temos breakdown individual
                    completion_tokens=None,
                    created_at=row.get("created_at")
                ))
            
            return ConversationDetail(
                conversation_id=conv_row.get("conversation_id"),
                user_id=conv_row.get("user_id"),
                title=conv_row.get("title"),
                created_at=conv_row.get("created_at"),
                updated_at=conv_row.get("updated_at"),
                is_active=conv_row.get("is_active"),
                rating=conv_row.get("rating"),
                rating_timestamp=conv_row.get("rating_timestamp"),
                messages=messages
            )
        except Exception as e:
            logger.error(f"Erro ao buscar conversa: {e}")
            raise
    
    @staticmethod
    def list_user_conversations(user_id: str, limit: int = 50) -> List[ConversationResponse]:
        """
        Listar conversas de um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Limite de conversas retornadas
            
        Returns:
            Lista de conversas do usuário
        """
        try:
            sql = get_sqlserver_connection()
            
            query = """
            SELECT TOP (?)
                c.conversation_id, c.user_id, c.title, c.created_at, c.updated_at, c.is_active,
                COUNT(m.message_id) as message_count
            FROM conversations c
            LEFT JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE c.user_id = ?
            GROUP BY c.conversation_id, c.user_id, c.title, c.created_at, c.updated_at, c.is_active
            ORDER BY c.updated_at DESC
            """
            
            rows = sql.execute(query, [limit, user_id])
            
            conversations = []
            for row in rows:
                conversations.append(ConversationResponse(
                    conversation_id=row.get("conversation_id"),
                    user_id=row.get("user_id"),
                    title=row.get("title"),
                    created_at=row.get("created_at"),
                    updated_at=row.get("updated_at"),
                    is_active=row.get("is_active"),
                    message_count=row.get("message_count", 0)
                ))
            
            logger.info(f"Listadas {len(conversations)} conversas para usuário {user_id}")
            return conversations
        except Exception as e:
            logger.error(f"Erro ao listar conversas: {e}")
            raise
    
    @staticmethod
    def delete_conversation(conversation_id: str) -> bool:
        """
        Deletar conversa (soft delete - apenas marcar como inativa).
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            True se deletado com sucesso
        """
        try:
            sql = get_sqlserver_connection()
            
            query = "UPDATE conversations SET is_active = 0 WHERE conversation_id = ?"
            sql.execute(query, [conversation_id])
            
            logger.info(f"Conversa deletada: {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar conversa: {e}")
            raise    
    @staticmethod
    def get_dashboard_summary(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obter resumo agregado de conversas para dashboard.
        
        Returns:
            Dict com métricas agregadas
        """
        try:
            sql = get_sqlserver_connection()
            
            # Construir filtros
            date_filter = ""
            params = []
            
            if start_date:
                date_filter += " AND c.created_at >= ?"
                params.append(start_date)
            if end_date:
                date_filter += " AND c.created_at <= ?"
                params.append(end_date)
            if user_id:
                date_filter += " AND c.user_id = ?"
                params.append(user_id)
            
            # Query de resumo
            query = f"""
            SELECT
                COUNT(DISTINCT c.conversation_id) as total_conversations,
                COUNT(DISTINCT c.user_id) as unique_users,
                COUNT(m.message_id) as total_messages,
                AVG(CAST(m.tokens_used AS FLOAT)) as avg_tokens_per_message,
                SUM(m.tokens_used) as total_tokens,
                MIN(c.created_at) as first_conversation,
                MAX(c.updated_at) as last_conversation
            FROM conversations c
            LEFT JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE c.is_active = 1
            {date_filter}
            """
            
            results = sql.execute(query, params)
            row = results[0] if results else {}
            
            # Query de tempos de resposta médios
            response_time_query = f"""
            SELECT
                AVG(CAST(retrieval_time AS FLOAT)) as avg_retrieval_time,
                AVG(CAST(llm_time AS FLOAT)) as avg_llm_time,
                AVG(CAST(total_time AS FLOAT)) as avg_total_time,
                MAX(CAST(total_time AS FLOAT)) as max_total_time,
                MIN(CAST(total_time AS FLOAT)) as min_total_time
            FROM conversation_messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE m.role = 'assistant' AND c.is_active = 1
            {date_filter}
            """
            
            response_times = {}
            try:
                time_results = sql.execute(response_time_query, params)
                if time_results:
                    time_row = time_results[0]
                    response_times = {
                        "avg_retrieval_time_ms": round((time_row.get("avg_retrieval_time") or 0) * 1000, 2),
                        "avg_llm_time_ms": round((time_row.get("avg_llm_time") or 0) * 1000, 2),
                        "avg_total_time_ms": round((time_row.get("avg_total_time") or 0) * 1000, 2),
                        "max_total_time_ms": round((time_row.get("max_total_time") or 0) * 1000, 2),
                        "min_total_time_ms": round((time_row.get("min_total_time") or 0) * 1000, 2)
                    }
            except Exception as e:
                logger.warning(f"Erro ao buscar tempos de resposta: {e}")
            
            # Query de modelos mais usados
            models_query = f"""
            SELECT TOP 10
                m.model,
                COUNT(m.message_id) as usage_count,
                AVG(CAST(m.tokens_used AS FLOAT)) as avg_tokens
            FROM conversation_messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE m.model IS NOT NULL AND m.role = 'assistant' AND c.is_active = 1
            {date_filter}
            GROUP BY m.model
            ORDER BY usage_count DESC
            """
            
            models = []
            try:
                model_results = sql.execute(models_query, params)
                for model_row in model_results:
                    avg_tokens = model_row.get("avg_tokens")
                    models.append({
                        "model": model_row.get("model"),
                        "usage_count": model_row.get("usage_count"),
                        "avg_tokens": round(avg_tokens, 2) if avg_tokens is not None else 0
                    })
            except Exception as e:
                logger.warning(f"Erro ao buscar modelos mais usados: {e}")
            
            # Query de usuários mais ativos
            users_query = f"""
            SELECT TOP 10
                c.user_id,
                COUNT(DISTINCT c.conversation_id) as conversation_count,
                COUNT(m.message_id) as message_count
            FROM conversations c
            LEFT JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE c.is_active = 1
            {date_filter}
            GROUP BY c.user_id
            ORDER BY conversation_count DESC
            """
            
            users = []
            try:
                user_results = sql.execute(users_query, params)
                for user_row in user_results:
                    users.append({
                        "user_id": user_row.get("user_id"),
                        "conversations": user_row.get("conversation_count"),
                        "messages": user_row.get("message_count")
                    })
            except Exception as e:
                logger.warning(f"Erro ao buscar usuários mais ativos: {e}")
            
            # Query de ratings/avaliações
            ratings_query = f"""
            SELECT
                COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) as total_rated,
                AVG(CAST(rating AS FLOAT)) as avg_rating,
                COUNT(CASE WHEN rating = 5.0 THEN 1 END) as five_stars,
                COUNT(CASE WHEN rating = 4.5 THEN 1 END) as four_and_half_stars,
                COUNT(CASE WHEN rating = 4.0 THEN 1 END) as four_stars,
                COUNT(CASE WHEN rating = 3.5 THEN 1 END) as three_and_half_stars,
                COUNT(CASE WHEN rating = 3.0 THEN 1 END) as three_stars,
                COUNT(CASE WHEN rating = 2.5 THEN 1 END) as two_and_half_stars,
                COUNT(CASE WHEN rating = 2.0 THEN 1 END) as two_stars,
                COUNT(CASE WHEN rating = 1.5 THEN 1 END) as one_and_half_stars,
                COUNT(CASE WHEN rating = 1.0 THEN 1 END) as one_star,
                COUNT(CASE WHEN rating = 0.5 THEN 1 END) as half_star,
                COUNT(CASE WHEN rating = 0.0 THEN 1 END) as zero_stars
            FROM conversations
            WHERE is_active = 1
            {date_filter}
            """
            
            ratings_info = {}
            try:
                ratings_results = sql.execute(ratings_query, params)
                if ratings_results:
                    rating_row = ratings_results[0]
                    total_rated = rating_row.get("total_rated", 0)
                    
                    # Calcular porcentagens
                    def calc_percentage(count):
                        return round((count / total_rated * 100) if total_rated > 0 else 0, 1)
                    
                    ratings_info = {
                        "total_rated": total_rated,
                        "avg_rating": round(rating_row.get("avg_rating") or 0, 2),
                        "distribution": {
                            "five_stars": {
                                "count": rating_row.get("five_stars", 0),
                                "percentage": calc_percentage(rating_row.get("five_stars", 0))
                            },
                            "four_and_half_stars": {
                                "count": rating_row.get("four_and_half_stars", 0),
                                "percentage": calc_percentage(rating_row.get("four_and_half_stars", 0))
                            },
                            "four_stars": {
                                "count": rating_row.get("four_stars", 0),
                                "percentage": calc_percentage(rating_row.get("four_stars", 0))
                            },
                            "three_and_half_stars": {
                                "count": rating_row.get("three_and_half_stars", 0),
                                "percentage": calc_percentage(rating_row.get("three_and_half_stars", 0))
                            },
                            "three_stars": {
                                "count": rating_row.get("three_stars", 0),
                                "percentage": calc_percentage(rating_row.get("three_stars", 0))
                            },
                            "two_and_half_stars": {
                                "count": rating_row.get("two_and_half_stars", 0),
                                "percentage": calc_percentage(rating_row.get("two_and_half_stars", 0))
                            },
                            "two_stars": {
                                "count": rating_row.get("two_stars", 0),
                                "percentage": calc_percentage(rating_row.get("two_stars", 0))
                            },
                            "one_and_half_stars": {
                                "count": rating_row.get("one_and_half_stars", 0),
                                "percentage": calc_percentage(rating_row.get("one_and_half_stars", 0))
                            },
                            "one_star": {
                                "count": rating_row.get("one_star", 0),
                                "percentage": calc_percentage(rating_row.get("one_star", 0))
                            },
                            "half_star": {
                                "count": rating_row.get("half_star", 0),
                                "percentage": calc_percentage(rating_row.get("half_star", 0))
                            },
                            "zero_stars": {
                                "count": rating_row.get("zero_stars", 0),
                                "percentage": calc_percentage(rating_row.get("zero_stars", 0))
                            }
                        }
                    }
            except Exception as e:
                logger.warning(f"Erro ao buscar ratings: {e}")
            
            # Query de mensagens do usuário
            user_messages_query = f"""
            SELECT COUNT(m.message_id) as total_user_messages
            FROM conversation_messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE m.role = 'user' AND c.is_active = 1
            {date_filter}
            """
            
            total_user_messages = 0
            try:
                user_msg_results = sql.execute(user_messages_query, params)
                if user_msg_results:
                    user_msg_row = user_msg_results[0]
                    total_user_messages = user_msg_row.get("total_user_messages", 0)
            except Exception as e:
                logger.warning(f"Erro ao buscar mensagens do usuário: {e}")
            
            # Query de volume de respostas por categoria (lê JSON de document_categories_used)
            # Usa OPENJSON para explodir o array e considerar TODAS as categorias em cada resposta
            # Filtra apenas JSONs válidos com ISJSON
            category_volume_query = f"""
            SELECT 
                TRIM(cat_value.value) as category_name,
                COUNT(DISTINCT m.message_id) as response_count,
                COUNT(DISTINCT CASE WHEN c.rating IS NOT NULL THEN c.conversation_id END) as rated_count,
                AVG(CAST(c.rating AS FLOAT)) as avg_category_rating
            FROM conversation_messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            CROSS APPLY OPENJSON(m.document_categories_used, '$.category_names') AS cat_value
            WHERE m.role = 'assistant' 
            AND m.document_categories_used IS NOT NULL
            AND ISJSON(m.document_categories_used) = 1
            AND c.is_active = 1
            AND cat_value.value IS NOT NULL
            {date_filter}
            GROUP BY TRIM(cat_value.value)
            ORDER BY response_count DESC
            """
            
            category_metrics = []
            try:
                logger.info("Executando query de category_metrics com OPENJSON...")
                category_results = sql.execute(category_volume_query, params)
                
                if category_results:
                    logger.info(f"Query de categorias retornou {len(category_results)} linhas")
                    for cat_row in category_results:
                        category_name = cat_row.get("category_name")
                        if category_name:
                            rated_count = cat_row.get("rated_count", 0)
                            total_count = cat_row.get("response_count", 0)
                            avg_rating = cat_row.get("avg_category_rating") or 0.0
                            
                            category_metrics.append({
                                "category_name": category_name,
                                "response_count": total_count,
                                "rated_count": rated_count,
                                "avg_rating": round(avg_rating, 2) if avg_rating > 0 else 0.0,
                                "rating_coverage": f"{round((rated_count/total_count)*100, 1)}%" if total_count > 0 else "0%"
                            })
                            logger.info(f"Categoria: {category_name} → Total: {total_count}, Avaliadas: {rated_count}, Média: {round(avg_rating, 2) if avg_rating > 0 else 0.0}")
                else:
                    logger.warning("Query de categorias retornou vazio")
                    
            except Exception as e:
                logger.error(f"Erro ao buscar métricas por categoria com OPENJSON: {e}")
                logger.error(f"Query: {category_volume_query}")
                # Fallback: versão simplificada sem OPENJSON (só primeira categoria)
                try:
                    logger.info("Tentando fallback com JSON_VALUE (apenas primeira categoria)...")
                    fallback_query = f"""
                    SELECT 
                        TRIM(JSON_VALUE(m.document_categories_used, '$.category_names[0]')) as category_name,
                        COUNT(DISTINCT m.message_id) as response_count,
                        COUNT(DISTINCT CASE WHEN c.rating IS NOT NULL THEN c.conversation_id END) as rated_count,
                        AVG(CAST(c.rating AS FLOAT)) as avg_category_rating
                    FROM conversation_messages m
                    JOIN conversations c ON m.conversation_id = c.conversation_id
                    WHERE m.role = 'assistant' 
                    AND m.document_categories_used IS NOT NULL
                    AND ISJSON(m.document_categories_used) = 1
                    AND c.is_active = 1
                    {date_filter}
                    GROUP BY TRIM(JSON_VALUE(m.document_categories_used, '$.category_names[0]'))
                    ORDER BY response_count DESC
                    """
                    category_results = sql.execute(fallback_query, params)
                    if category_results:
                        for cat_row in category_results:
                            category_name = cat_row.get("category_name")
                            if category_name:
                                rated_count = cat_row.get("rated_count", 0)
                                total_count = cat_row.get("response_count", 0)
                                avg_rating = cat_row.get("avg_category_rating") or 0.0
                                
                                category_metrics.append({
                                    "category_name": category_name,
                                    "response_count": total_count,
                                    "rated_count": rated_count,
                                    "avg_rating": round(avg_rating, 2) if avg_rating > 0 else 0.0,
                                    "rating_coverage": f"{round((rated_count/total_count)*100, 1)}%" if total_count > 0 else "0%"
                                })
                except Exception as fallback_e:
                    logger.error(f"Fallback também falhou: {fallback_e}")
            
            # Converter tempo de resposta de ms para segundos
            avg_response_time_seconds = (response_times.get("avg_total_time_ms", 0) or 0) / 1000
            
            return {
                "metrics": {
                    "total_conversations": row.get("total_conversations", 0),
                    "unique_users": row.get("unique_users", 0),
                    "total_messages": row.get("total_messages", 0),
                    "total_user_messages": total_user_messages,
                    "avg_response_time_seconds": round(avg_response_time_seconds, 2),
                    "avg_tokens_per_message": round(row.get("avg_tokens_per_message") or 0, 2),
                    "total_tokens": row.get("total_tokens", 0),
                    "first_conversation": row.get("first_conversation"),
                    "last_conversation": row.get("last_conversation")
                },
                "response_times_ms": response_times,
                "ratings": ratings_info,
                "category_metrics": category_metrics,
                "top_models": models,
                "top_users": users,
                "filters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "user_id": user_id
                }
            }
        except Exception as e:
            logger.error(f"Erro ao obter resumo do dashboard: {e}")
            raise
    
    @staticmethod
    def get_dashboard_detailed(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at"
    ) -> Dict[str, Any]:
        """
        Obter dados detalhados de conversas para análise.
        
        Returns:
            Dict com conversas e mensagens
        """
        try:
            sql = get_sqlserver_connection()
            
            # Validar order_by
            allowed_order_by = ["created_at", "message_count", "updated_at"]
            order_by = order_by if order_by in allowed_order_by else "created_at"
            
            # Construir filtros
            date_filter = ""
            params = []
            
            if start_date:
                date_filter += " AND c.created_at >= ?"
                params.append(start_date)
            if end_date:
                date_filter += " AND c.created_at <= ?"
                params.append(end_date)
            if user_id:
                date_filter += " AND c.user_id = ?"
                params.append(user_id)
            
            # Query de conversas
            query = f"""
            SELECT
                c.conversation_id,
                c.user_id,
                c.title,
                c.created_at,
                c.updated_at,
                c.is_active,
                c.rating,
                c.rating_timestamp,
                COUNT(m.message_id) as message_count,
                SUM(CAST(m.tokens_used AS INT)) as total_tokens
            FROM conversations c
            LEFT JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE c.is_active = 1
            {date_filter}
            GROUP BY c.conversation_id, c.user_id, c.title, c.created_at, c.updated_at, c.is_active, c.rating, c.rating_timestamp
            ORDER BY {order_by} DESC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
            """
            
            params_with_pagination = params + [offset, limit]
            conv_results = sql.execute(query, params_with_pagination)
            
            conversations = []
            for conv_row in conv_results:
                conv_id = conv_row.get("conversation_id")
                
                # Buscar mensagens da conversa
                msg_query = """
                SELECT message_id, role, content, model, tokens_used, created_at
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
                """
                msg_results = sql.execute(msg_query, [conv_id])
                
                messages = []
                for msg_row in msg_results:
                    messages.append({
                        "message_id": msg_row.get("message_id"),
                        "role": msg_row.get("role"),
                        "content": msg_row.get("content")[:200] + "..." if len(msg_row.get("content", "")) > 200 else msg_row.get("content"),
                        "model": msg_row.get("model"),
                        "tokens": msg_row.get("tokens_used"),
                        "created_at": msg_row.get("created_at")
                    })
                
                conversations.append({
                    "conversation_id": conv_id,
                    "user_id": conv_row.get("user_id"),
                    "title": conv_row.get("title"),
                    "message_count": conv_row.get("message_count", 0),
                    "total_tokens": conv_row.get("total_tokens", 0),
                    "created_at": conv_row.get("created_at"),
                    "updated_at": conv_row.get("updated_at"),
                    "rating": conv_row.get("rating"),
                    "rating_timestamp": conv_row.get("rating_timestamp"),
                    "messages": messages
                })
            
            # Contar total para paginação
            count_query = f"""
            SELECT COUNT(DISTINCT c.conversation_id) as total
            FROM conversations c
            WHERE c.is_active = 1
            {date_filter}
            """
            count_results = sql.execute(count_query, params)
            total = count_results[0].get("total", 0) if count_results else 0
            
            return {
                "conversations": conversations,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                },
                "filters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "user_id": user_id,
                    "order_by": order_by
                }
            }
        except Exception as e:
            logger.error(f"Erro ao obter dados detalhados do dashboard: {e}")
            raise
    
    @staticmethod
    def export_dashboard_data(
        format: str = "json",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exportar dados do dashboard em diferentes formatos.
        
        Args:
            format: 'json' ou 'csv'
            
        Returns:
            Dados formatados para export
        """
        try:
            # Buscar dados detalhados (sem paginação)
            data = ConversationService.get_dashboard_detailed(
                start_date=start_date,
                end_date=end_date,
                user_id=user_id,
                limit=10000,
                offset=0
            )
            
            if format == "csv":
                # Converter para CSV
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                
                # Header
                writer.writerow([
                    "Conversation ID", "User ID", "Title", "Message Count", 
                    "Total Tokens", "Created At", "Updated At",
                    "Message Role", "Message Content", "Model", "Message Tokens"
                ])
                
                # Rows
                for conv in data.get("conversations", []):
                    for msg in conv.get("messages", []):
                        writer.writerow([
                            conv["conversation_id"],
                            conv["user_id"],
                            conv["title"],
                            conv["message_count"],
                            conv["total_tokens"],
                            conv["created_at"],
                            conv["updated_at"],
                            msg["role"],
                            msg["content"],
                            msg["model"],
                            msg["tokens"]
                        ])
                
                return {
                    "format": "csv",
                    "data": output.getvalue(),
                    "filename": f"dashboard_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            else:
                # JSON (padrão)
                return {
                    "format": "json",
                    "data": data,
                    "filename": f"dashboard_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                }
        except Exception as e:
            logger.error(f"Erro ao exportar dados do dashboard: {e}")
            raise
    
    @staticmethod
    def save_conversation_rating(conversation_id: str, rating: float, comment: Optional[str] = None) -> bool:
        """
        Salvar avaliação de uma conversa com comentário opcional.
        
        Args:
            conversation_id: ID da conversa
            rating: Avaliação de 0.0 a 5.0
            comment: Comentário/feedback (obrigatório quando rating=1.0)
            
        Returns:
            True se salvo com sucesso
            
        Raises:
            ValueError: Se rating não estiver entre 0.0 e 5.0 ou comentário faltando para nota 1.0
        """
        # Validar rating
        if not (0.0 <= rating <= 5.0):
            raise ValueError(f"Rating deve estar entre 0.0 e 5.0, recebido: {rating}")
        
        # Validar que é múltiplo de 0.5
        if (rating * 2) % 1 != 0:
            raise ValueError(f"Rating deve ser múltiplo de 0.5, recebido: {rating}")
        
        # Validar comentário obrigatório para nota 1.0
        if rating == 1.0 and (not comment or not comment.strip()):
            raise ValueError("Comentário é obrigatório quando rating é 1.0")
        
        try:
            sql = get_sqlserver_connection()
            now = datetime.utcnow()
            
            query = """
            UPDATE conversations
            SET rating = ?, rating_timestamp = ?, rating_comment = ?
            WHERE conversation_id = ?
            """
            
            sql.execute(query, [rating, now, comment, conversation_id])
            logger.info(f"Avaliação {rating} salva para conversa {conversation_id}" + 
                       (f" com comentário" if comment else ""))
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar avaliação: {e}")
            raise


# Backward compatibility: expose selected functions at module level
def list_user_conversations(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Compatibility wrapper that returns plain dicts including first Q/A fields."""
    sql = get_sqlserver_connection()
    query = """
    SELECT TOP (?)
        c.conversation_id,
        c.user_id,
        c.title,
        c.document_id,
        c.created_at,
        c.updated_at,
        c.is_active,
        COUNT(m.message_id) as message_count,
        MIN(CASE WHEN m.role = 'user' THEN m.content END) as first_question,
        MIN(CASE WHEN m.role = 'assistant' THEN m.content END) as first_answer
    FROM conversations c
    LEFT JOIN conversation_messages m ON c.conversation_id = m.conversation_id
    WHERE c.user_id = ?
    GROUP BY c.conversation_id, c.user_id, c.title, c.document_id, c.created_at, c.updated_at, c.is_active
    ORDER BY c.updated_at DESC
    """

    rows = sql.execute(query, [limit, user_id])
    return [
        {
            "conversation_id": row.get("conversation_id"),
            "user_id": row.get("user_id") or user_id,
            "title": row.get("title"),
            "document_id": row.get("document_id"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
            "is_active": row.get("is_active"),
            "message_count": row.get("message_count", 0),
            "first_question": row.get("first_question"),
            "first_answer": row.get("first_answer"),
        }
        for row in rows
    ]