"""
Rotas para gerenciar conversas e perguntas ao LLM Server.
"""
import json
import logging
import traceback
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from app.models import (
    QuestionRequest,
    QuestionResponse,
    ConversationResponse,
    ConversationDetail,
    RatingRequest,
    RatingResponse,
)
from app.services.conversation_service import ConversationService
from app.providers.llm_server import get_llm_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _convert_memory_preferences_for_llm(memory_prefs: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Converte memory_preferences do formato do banco para o formato esperado pelo LLM Server.
    
    Formato do banco:
    {
        "max_history_lines": 4,
        "summary_enabled": true,
        "context_window": "4_lines",
        "memory_type": "long_term",
        "custom_preferences": {...}
    }
    
    Formato esperado pelo LLM:
    {
        "memory": "User prefers concise answers...",
        "memory_version": 1
    }
    """
    if not memory_prefs:
        return None
    
    try:
        # Construir descrição textual das preferências
        memory_parts = []
        
        if memory_prefs.get("max_history_lines"):
            memory_parts.append(f"Manter histórico de {memory_prefs['max_history_lines']} linhas")
        
        if memory_prefs.get("memory_type"):
            memory_parts.append(f"Tipo de memória: {memory_prefs['memory_type']}")
        
        if memory_prefs.get("summary_enabled"):
            memory_parts.append("Resumos habilitados")
        
        custom = memory_prefs.get("custom_preferences", {})
        if custom.get("response_length"):
            memory_parts.append(f"Tamanho de resposta: {custom['response_length']}")
        
        if custom.get("tone"):
            memory_parts.append(f"Tom: {custom['tone']}")
        
        memory_description = ". ".join(memory_parts) if memory_parts else json.dumps(memory_prefs)
        
        return {
            "memory": memory_description,
            "memory_version": 1
        }
    except Exception as e:
        logger.warning(f"Erro ao converter memory_preferences: {e}")
        return None


@router.post("/question", response_model=QuestionResponse)
async def ask_question(req: QuestionRequest) -> QuestionResponse:
    """
    Fazer uma pergunta ao LLM Server e salvar no histórico de conversas.
    
    Frontend envia:
    - chat_id: ID da sessão de chat (pode ser a conversation_id)
    - question: Pergunta do usuário
    - user_id, name, email, country, city, roles, department, job_title, collar, unit
    - memory_preferences: (opcional) Preferências de memória do usuário
    
    Backend:
    1. Cria/obtém conversa
    2. Se for primeira mensagem E não tiver memory_preferences, busca do banco
    3. Chama LLM Server com memory_preferences
    4. Salva pergunta + resposta no banco
    5. Retorna resposta
    """
    try:
        # Usar chat_id como conversation_id
        conversation_id = req.chat_id
        user_id = req.user_id
        
        logger.info(f"Pergunta recebida: '{req.question[:100]}...' de {user_id}")
        
        # Obter conversa existente ou criar nova
        is_first_message = False
        try:
            conv = ConversationService.get_conversation(conversation_id)
            if not conv:
                # Criar nova conversa
                conv_create = ConversationService.create_conversation(user_id)
                conversation_id = conv_create.conversation_id
                is_first_message = True
                logger.info(f"Nova conversa criada: {conversation_id}")
            else:
                # Verificar se é primeira mensagem (conversa sem mensagens)
                is_first_message = len(conv.messages) == 0
        except Exception as e:
            logger.warning(f"Erro ao obter conversa, criando nova: {e}")
            conv_create = ConversationService.create_conversation(user_id)
            conversation_id = conv_create.conversation_id
            is_first_message = True
        
        # Se for primeira mensagem, buscar memory_preferences e preferred_language do banco
        memory_preferences = req.memory_preferences
        preferred_language = req.language or None  # Usar da request ou None para buscar no banco
        
        if is_first_message:
            try:
                from app.core.sqlserver import get_sqlserver_connection
                
                logger.info(f"[Preferences Load] Tentando carregar preferências para {user_id}")
                
                try:
                    sql = get_sqlserver_connection()
                    query = "SELECT memory_preferences, preferred_language FROM user_preferences WHERE user_id = ?"
                    results = sql.execute(query, [user_id])
                    
                    if results:
                        row = results[0]
                        
                        # Carregar memory_preferences se não fornecida no request
                        if not memory_preferences and row[0]:
                            try:
                                memory_preferences = json.loads(row[0])
                                logger.info(f"[Preferences Load] ✓ Memory carregada para {user_id}: {list(memory_preferences.keys())}")
                            except json.JSONDecodeError as json_err:
                                logger.warning(f"[Preferences Load] ✗ JSON inválido em memory_preferences: {json_err}")
                                memory_preferences = None
                        
                        # Carregar preferred_language se não fornecida no request
                        if not preferred_language and row[1]:
                            preferred_language = row[1]
                            logger.info(f"[Preferences Load] ✓ Preferred language carregado para {user_id}: {preferred_language}")
                        
                    else:
                        logger.info(f"[Preferences Load] ℹ Nenhuma preferência encontrada para {user_id}")
                        
                except Exception as db_err:
                    logger.error(f"[Preferences Load] ✗ Erro ao executar query: {db_err}")
                        
            except ImportError as import_err:
                logger.error(f"[Preferences Load] ✗ Erro ao importar get_sqlserver_connection: {import_err}")
            except Exception as outer_err:
                logger.warning(f"[Preferences Load] ✗ Erro ao buscar preferências (continuando sem): {outer_err}")
                logger.debug(f"[Preferences Load] Stack trace: {traceback.format_exc()}")
        
        # Chamar LLM Server
        llm_client = get_llm_client()
        try:
            # Converter street (address) para allowed_location_id (query na tabela dim_electrolux_locations)
            allowed_location_id = None
            if req.street:
                try:
                    from app.core.sqlserver import get_sqlserver_connection
                    sql = get_sqlserver_connection()
                    
                    # Buscar location_id baseado em address
                    query = """
                    SELECT TOP 1 location_id
                    FROM dim_electrolux_locations
                    WHERE address = ? AND is_active = 1
                    ORDER BY location_id
                    """
                    results = sql.execute(query, [req.street])
                    
                    if results:
                        allowed_location_id = results[0]["location_id"]
                        logger.info(f"[Location] Convertido '{req.street}' → allowed_location_id={allowed_location_id}")
                    else:
                        logger.warning(f"[Location] Nenhuma localização encontrada para: {req.street}")
                        
                except Exception as loc_err:
                    logger.warning(f"[Location] Erro ao converter street para allowed_location_id: {loc_err}")
                    allowed_location_id = None
            
            llm_request_params = {
                "question": req.question,
                "chat_id": conversation_id,
                "user_id": req.user_id,
                "name": req.name,
                "email": req.email,
                "country": req.country,
                "city": req.city,
                "role_id": req.role_id,
                "department": req.department,
                "job_title": req.job_title,
                "collar": req.collar,
                "unit": req.unit,
                "agent_id": req.agent_id,
                "language": preferred_language or req.language  # Usar preferred_language do banco ou da request
            }
            
            # Converter allowed_location_id para location_id (para LLM)
            # Se vem street, converter para um location_id int. Se não encontra na BD, passa null
            if allowed_location_id is not None:
                llm_request_params["location_id"] = allowed_location_id
                logger.info(f"[LLM Request] location_id (convertido de street): {allowed_location_id}")
            else:
                logger.info(f"[LLM Request] location_id não definido (street não fornecido ou não encontrado)")
                        
            # Usar memory do request ou converter memory_preferences do banco
            memory_for_llm = None
            if req.memory:
                # Se memory foi fornecido no request, montar o dict
                memory_for_llm = {
                    "memory": req.memory,
                    "memory_version": req.memory_version
                }
                logger.info(f"[LLM Request] Memory fornecido no request: {req.memory[:50]}...")
            elif memory_preferences:
                # Converter memory_preferences do banco
                memory_for_llm = _convert_memory_preferences_for_llm(memory_preferences)
            
            if memory_for_llm:
                llm_request_params["memory"] = memory_for_llm
                logger.info(
                    f"[LLM Request] Memory incluída: "
                    f"memory='{memory_for_llm.get('memory', '')[:50]}...', "
                    f"version={memory_for_llm.get('memory_version', 1)}"
                )
            else:
                logger.debug("[LLM Request] Memory não disponível")
            
            llm_response = llm_client.ask_question(**llm_request_params)
            
        except HTTPException as e:
            logger.error(f"[ask_question] LLM HTTP Error: {e.detail}")
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[ask_question] LLM Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"LLM Server retornou: {error_msg}")
        
        logger.info(f"Resposta recebida do LLM Server em {llm_response.get('total_time_ms', 'N/A')}ms")
        
        # Salvar pergunta e resposta no banco
        try:
            save_result = ConversationService.save_question_and_answer(
                conversation_id=conversation_id,
                user_id=user_id,
                question=req.question,
                llm_response=llm_response
            )
            logger.info(f"Pergunta e resposta salvas: {save_result}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar conversa: {e}")
            logger.error(traceback.format_exc())
            # Continuar mesmo se falhar ao salvar - retornar resposta do LLM
        
        # Retornar resposta
        # Converter total_time_ms para segundos se não tiver total_time
        total_time_ms = llm_response.get("total_time_ms", 0)
        total_time = llm_response.get("total_time") or (total_time_ms / 1000 if total_time_ms else 0.0)
        
        return QuestionResponse(
            conversation_id=conversation_id,
            answer=llm_response.get("answer", ""),
            source_documents=llm_response.get("source_documents", []),
            num_documents=llm_response.get("num_documents", 0),
            classification=llm_response.get("classification"),
            retrieval_time=llm_response.get("retrieval_time", 0.0),
            llm_time=llm_response.get("llm_time", 0.0),
            total_time=total_time,
            total_time_ms=total_time_ms,
            message_id=llm_response.get("message_id", ""),
            provider=llm_response.get("provider", "azure_openai"),
            model=llm_response.get("model", "gpt-4o-mini"),
            generated_at=llm_response.get("generated_at"),
            rbac_filter_applied=llm_response.get("rbac_filter_applied"),
            documents_returned=llm_response.get("documents_returned", 0),
            documents_filtered=llm_response.get("documents_filtered", 0),
            top_sources=llm_response.get("top_sources", []),
            agente=llm_response.get("agente", "general"),
            prompt_tokens=llm_response.get("prompt_tokens", 0),
            completion_tokens=llm_response.get("completion_tokens", 0),
            node_path=llm_response.get("node_path")
        )
    
    except Exception as e:
        logger.error(f"Erro ao processar pergunta: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")


@router.get("/conversations/{user_id}", response_model=List[ConversationResponse])
async def list_conversations(
    user_id: str,
    limit: int = Query(50, ge=1, le=100)
) -> List[ConversationResponse]:
    """
    Listar todas as conversas de um usuário.
    
    Args:
        user_id: ID do usuário
        limit: Número máximo de conversas (padrão 50, máx 100)
        
    Returns:
        Lista de conversas do usuário
    """
    try:
        conversations = ConversationService.list_user_conversations(user_id, limit)
        logger.info(f"Listadas {len(conversations)} conversas para usuário {user_id}")
        return conversations
    except Exception as e:
        logger.error(f"Erro ao listar conversas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar conversas: {str(e)}")


@router.get("/conversations/{conversation_id}/detail", response_model=ConversationDetail)
async def get_conversation_detail(conversation_id: str) -> ConversationDetail:
    """
    Obter detalhes completos de uma conversa com todas as mensagens.
    
    Args:
        conversation_id: ID da conversa
        
    Returns:
        Conversa com todas as mensagens
    """
    try:
        conversation = ConversationService.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversa não encontrada: {conversation_id}")
        
        logger.info(f"Detalhes da conversa {conversation_id} retornados ({len(conversation.messages)} mensagens)")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes da conversa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar conversa: {str(e)}")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict:
    """
    Deletar uma conversa (soft delete).
    
    Args:
        conversation_id: ID da conversa
        
    Returns:
        Confirmação de deleção
    """
    try:
        success = ConversationService.delete_conversation(conversation_id)
        if success:
            logger.info(f"Conversa deletada: {conversation_id}")
            return {"message": "Conversa deletada com sucesso", "conversation_id": conversation_id}
        else:
            raise HTTPException(status_code=404, detail=f"Conversa não encontrada: {conversation_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar conversa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao deletar conversa: {str(e)}")

@router.post("/question/stream")
async def ask_question_stream(req: QuestionRequest):
    """
    Fazer uma pergunta ao LLM Server com **streaming** (SSE - Server-Sent Events).
    
    Retorna a resposta em tempo real, aos poucos, conforme o LLM gera.
    
    **Frontend:**
    ```javascript
    const response = await fetch('/api/v1/chat/question/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        chat_id: '...', 
        question: 'Minha pergunta',
        user_id: '...',
        // ... outros campos
      })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while(true) {
      const {done, value} = await reader.read();
      if(done) break;
      const chunk = decoder.decode(value);
      console.log(chunk); // Mostra sendo digitado!
    }
    ```
    """
    try:
        logger.info(f"Stream: Pergunta recebida: '{req.question[:100]}...' de {req.user_id}")
        
        # Obter conversa existente ou criar nova
        conversation_id = None
        
        # Se chat_id foi fornecido, tentar usar
        if req.chat_id and req.chat_id.strip():
            try:
                # Tentar com retry em caso de delay na inserção (streaming)
                conv = ConversationService.get_conversation(req.chat_id)
                if conv:
                    conversation_id = req.chat_id
                    logger.info(f"Stream: Usando conversa existente: {conversation_id}")
                else:
                    # Retry com pequeno delay (em caso de INSERT ainda processando)
                    import time
                    time.sleep(0.1)
                    conv = ConversationService.get_conversation(req.chat_id)
                    if conv:
                        conversation_id = req.chat_id
                        logger.info(f"Stream: Usando conversa existente (após retry): {conversation_id}")
                    else:
                        logger.info(f"Stream: chat_id '{req.chat_id}' não encontrado após retry, criando nova conversa")
            except Exception as e:
                logger.warning(f"Stream: Erro ao obter conversa '{req.chat_id}': {e}, criando nova")
        
        # Se não temos conversa, criar uma nova
        if not conversation_id:
            conv_create = ConversationService.create_conversation(req.user_id)
            conversation_id = conv_create.conversation_id
            logger.info(f"Stream: Nova conversa criada: {conversation_id}")
        
        # Carregar preferências do banco (memory_preferences e preferred_language)
        memory_preferences = req.memory_preferences
        preferred_language = req.language or None  # Usar da request ou None para buscar no banco
        
        try:
            from app.core.sqlserver import get_sqlserver_connection
            
            logger.info(f"[Stream Preferences Load] Tentando carregar preferências para {req.user_id}")
            
            try:
                sql = get_sqlserver_connection()
                query = "SELECT memory_preferences, preferred_language FROM user_preferences WHERE user_id = ?"
                results = sql.execute(query, [req.user_id])
                
                if results:
                    row = results[0]
                    
                    # Carregar memory_preferences se não fornecida no request
                    if not memory_preferences and row[0]:
                        try:
                            memory_preferences = json.loads(row[0])
                            logger.info(f"[Stream Preferences Load] ✓ Memory carregada para {req.user_id}: {list(memory_preferences.keys())}")
                        except json.JSONDecodeError as json_err:
                            logger.warning(f"[Stream Preferences Load] ✗ JSON inválido em memory_preferences: {json_err}")
                            memory_preferences = None
                    
                    # Carregar preferred_language se não fornecida no request
                    if not preferred_language and row[1]:
                        preferred_language = row[1]
                        logger.info(f"[Stream Preferences Load] ✓ Preferred language carregado para {req.user_id}: {preferred_language}")
                    
                else:
                    logger.info(f"[Stream Preferences Load] ℹ Nenhuma preferência encontrada para {req.user_id}")
                    
            except Exception as db_err:
                logger.error(f"[Stream Preferences Load] ✗ Erro ao executar query: {db_err}")
                    
        except ImportError as import_err:
            logger.error(f"[Stream Preferences Load] ✗ Erro ao importar get_sqlserver_connection: {import_err}")
        except Exception as outer_err:
            logger.warning(f"[Stream Preferences Load] ✗ Erro ao buscar preferências (continuando sem): {outer_err}")
            logger.debug(f"[Stream Preferences Load] Stack trace: {traceback.format_exc()}")
        
        # Chamar LLM Server com stream
        llm_client = get_llm_client()
        
        # Converter street (address) para location_id int (query na tabela dim_electrolux_locations)
        # Chat é 1:1: um usuário tem apenas uma localização
        location_id_int = None
        logger.info(f"[Stream Location] [STEP 1] req.street={req.street} (type: {type(req.street).__name__})")
        
        if req.street:
            try:
                from app.core.sqlserver import get_sqlserver_connection
                sql = get_sqlserver_connection()
                
                # Buscar location_id baseado em address
                query = """
                SELECT TOP 1 location_id
                FROM dim_electrolux_locations
                WHERE address = ? AND is_active = 1
                ORDER BY location_id
                """
                logger.debug(f"[Stream Location] Executando query para '{req.street}'")
                results = sql.execute(query, [req.street])
                
                if results:
                    location_id_int = results[0]["location_id"]
                    logger.info(f"[Stream Location] [STEP 2] ✓ Convertido '{req.street}' → location_id={location_id_int} (type: {type(location_id_int).__name__})")
                else:
                    logger.warning(f"[Stream Location] [STEP 2] ✗ Nenhuma localização encontrada para: '{req.street}'")
                    
            except Exception as loc_err:
                logger.warning(f"[Stream Location] [STEP 2] ✗ Erro ao converter street para location_id: {loc_err}", exc_info=True)
                location_id_int = None
        else:
            logger.info(f"[Stream Location] [STEP 1] Street não fornecido, pulando conversão")
        
        # location_id_int pode ser None, e tudo bem
        logger.info(f"[Stream Location] [STEP 3] location_id_int={location_id_int} (type: {type(location_id_int).__name__ if location_id_int is not None else 'NoneType'})")
        
        # Preparar memory para LLM (usar do request ou converter do banco)
        memory_for_llm = None
        logger.info(f"[Stream Location] [STEP 3b] Preparando memory para LLM: req.memory={req.memory is not None}, memory_preferences={memory_preferences is not None}")
        
        if req.memory:
            # Se memory foi fornecido no request, montar o dict
            memory_for_llm = {
                "memory": req.memory,
                "memory_version": req.memory_version
            }
            logger.info(f"[Stream Memory] [STEP 3b.1] ✓ Memory montado do request: {memory_for_llm}")
        elif memory_preferences:
            # Converter memory_preferences do banco
            memory_for_llm = _convert_memory_preferences_for_llm(memory_preferences)
            logger.info(f"[Stream Memory] [STEP 3b.2] ✓ Memory convertido de preferences: {memory_for_llm}")
        else:
            logger.info(f"[Stream Memory] [STEP 3b.3] Memory = None (nenhuma preferência disponível)")
        
        # Variáveis para coletar a resposta real
        complete_response = None
        
        async def stream_generator():
            nonlocal complete_response
            try:
                import json
                buffer = ""
                
                # Enviar final_location_id como int singular pro LLM
                for chunk in llm_client.ask_question_stream(
                    question=req.question,
                    chat_id=conversation_id,
                    user_id=req.user_id,
                    name=req.name,
                    email=req.email,
                    country=req.country,
                    city=req.city,
                    role_id=req.role_id,
                    department=req.department,
                    job_title=req.job_title,
                    collar=req.collar,
                    unit=req.unit,
                    agent_id=req.agent_id,
                    language=preferred_language or req.language,
                    location_id=location_id_int,
                    memory=memory_for_llm  # Usar memory dict preparado
                ):
                    logger.debug(f"Stream: Chunk recebido: {len(chunk)} chars")
                    buffer += chunk
                    
                    # Processar eventos completos (delimitados por \n\n)
                    while "\n\n" in buffer:
                        event_block, buffer = buffer.split("\n\n", 1)
                        event_block = event_block.strip()
                        
                        if not event_block:
                            continue
                        
                        # Parsear evento SSE
                        event_type = None
                        event_data = None
                        
                        for line in event_block.split("\n"):
                            line = line.strip()
                            if line.startswith("event:"):
                                event_type = line.replace("event:", "").strip()
                            elif line.startswith("data:"):
                                event_data = line.replace("data:", "").strip()
                        
                        logger.debug(f"Stream: Evento SSE parseado - type={event_type}, data={event_data[:50] if event_data else 'empty'}...")
                        
                        # Capturar o evento "complete"
                        if event_type == "complete" and event_data:
                            try:
                                complete_response = json.loads(event_data)
                                logger.info(f"Stream: Evento 'complete' capturado com answer")
                            except json.JSONDecodeError as e:
                                logger.error(f"Stream: Erro ao parsear JSON do complete: {e}")
                        
                        # Reconstruir evento SSE corretamente antes de enviar
                        if event_type and event_data:
                            # Se for evento "complete", adicionar conversation_id
                            if event_type == "complete":
                                try:
                                    data_obj = json.loads(event_data)
                                    data_obj["conversation_id"] = conversation_id
                                    event_data = json.dumps(data_obj)
                                except json.JSONDecodeError:
                                    pass
                            
                            # Reconstrói no formato correto: "event: ...\ndata: ...\n\n"
                            reconstructed_event = f"event: {event_type}\ndata: {event_data}\n\n"
                            logger.debug(f"Stream: Enviando evento ao frontend: {reconstructed_event[:80]}...")
                            yield reconstructed_event
                            # Delay para melhor visualização do efeito de digitação
                            if event_type == "token":
                                import asyncio
                                await asyncio.sleep(0.08)
                        elif event_type:
                            # Se não tem data, ainda enviar o evento
                            reconstructed_event = f"event: {event_type}\n\n"
                            logger.debug(f"Stream: Enviando evento (sem data) ao frontend: {reconstructed_event}")
                            yield reconstructed_event
                
                # ✅ Salvar no banco DEPOIS que stream termina - SÓ A RESPOSTA REAL
                logger.info(f"Stream: Finalizado. Salvando resposta real no banco...")
                logger.info(f"Stream: complete_response = {complete_response is not None}")
                
                if complete_response:
                    try:
                        # Extrair dados do evento "complete"
                        answer = complete_response.get("answer", "")
                        metadata = complete_response.get("metadata", {})
                        
                        logger.info(f"Stream: Answer length: {len(answer)} chars")
                        logger.info(f"Stream: Metadata keys: {list(metadata.keys())}")
                        
                        # Montar resposta no formato esperado
                        total_time_ms = metadata.get("total_time_ms", 0)
                        total_time = metadata.get("total_time") or (total_time_ms / 1000 if total_time_ms else 0)
                        
                        llm_response_data = {
                            "answer": answer,
                            "source_documents": metadata.get("top_sources", []),
                            "num_documents": metadata.get("documents_returned", 0),
                            "retrieval_time": metadata.get("retrieval_time", 0),
                            "llm_time": metadata.get("llm_time", 0),
                            "total_time": total_time,
                            "total_time_ms": total_time_ms,
                            "message_id": metadata.get("message_id", ""),
                            "classification": metadata.get("classification", None)
                        }
                        
                        # Extrair categorias
                        # Pode vir em diferentes formas:
                        # 1. metadata["category_ids"] (array)
                        # 2. metadata["category_id"] (int único)
                        document_categories_used = None
                        
                        category_ids = None
                        if metadata.get("category_ids"):
                            category_ids = metadata.get("category_ids")
                        elif metadata.get("category_id"):
                            category_ids = [metadata.get("category_id")]
                        
                        if category_ids:
                            document_categories_used = {
                                "category_ids": category_ids,
                                "category_names": metadata.get("category_names", [])
                            }
                        
                        logger.info(f"Stream: Salvando - answer='{answer[:50]}...', num_docs={llm_response_data['num_documents']}")
                        
                        # ✅ Enfileirar salvamento (não bloqueia stream)
                        # Fila com ThreadPoolExecutor limita a 5 writers simultâneos
                        from app.services.task_queue import enqueue_task
                        from app.services.background_tasks import save_chat_message_worker
                        
                        enqueue_task(
                            save_chat_message_worker,
                            conversation_id=conversation_id,
                            user_id=req.user_id,
                            question=req.question,
                            llm_response=llm_response_data,
                            document_categories_used=document_categories_used
                        )
                        logger.info(f"[ask_question_stream] ✅ Task enfileirada (max 5 workers)")
                        
                    except Exception as e:
                        logger.error(f"Stream: Erro ao iniciar background task: {e}")
                        logger.error(traceback.format_exc())
                else:
                    logger.warning(f"[ask_question_stream] No 'complete' event received")
                    
            except Exception as e:
                logger.error(f"Stream: Erro ao gerar stream: {e}")
                logger.error(f"Stream: Tipo de erro: {type(e).__name__}")
                logger.error(traceback.format_exc())
                # Enviar erro específico ao frontend identificando que é do LLM
                error_message = str(e)
                if "LLM Server" in error_message:
                    yield f"event: error\ndata: {json.dumps({'error': 'LLM Server retornou: ' + error_message})}\n\n"
                else:
                    yield f"event: error\ndata: {json.dumps({'error': error_message})}\n\n"
        
        # Retornar como SSE streaming
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Stream: Erro geral: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao fazer stream: {str(e)}")


@router.post("/{chat_id}/rating", response_model=RatingResponse)
async def rate_conversation(chat_id: str, req: RatingRequest) -> RatingResponse:
    """
    Avaliar uma conversa com nota de 0.0 a 5.0 (permitindo meia estrela).
    
    **Comentário obrigatório:** Quando a nota for 1.0, o comentário é obrigatório.
    
    Args:
        chat_id: ID da conversa a avaliar
        req: RatingRequest com a nota (0.0 a 5.0) e comentário opcional
    
    Returns:
        RatingResponse com confirmação da avaliação
    
    Examples:
        POST /api/v1/chat/abc-123/rating
        {
            "rating": 4.5,
            "comment": "Resposta muito útil"
        }
        
        POST /api/v1/chat/abc-123/rating (nota baixa - comentário obrigatório)
        {
            "rating": 1.0,
            "comment": "A resposta não foi relevante para minha pergunta"
        }
    """
    try:
        logger.info(f"Avaliação recebida para conversa {chat_id}: {req.rating} ⭐")
        
        # Validar rating
        if not (0.0 <= req.rating <= 5.0):
            raise HTTPException(
                status_code=400, 
                detail=f"Rating deve estar entre 0.0 e 5.0, recebido: {req.rating}"
            )
        
        # Validar múltiplo de 0.5
        if (req.rating * 2) % 1 != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Rating deve ser múltiplo de 0.5 (ex: 4.5), recebido: {req.rating}"
            )
        
        # Validar comentário obrigatório para nota 1.0
        if req.rating == 1.0 and (not req.comment or not req.comment.strip()):
            raise HTTPException(
                status_code=400,
                detail="Comentário é obrigatório quando rating é 1.0 (muito insatisfeito)"
            )
        
        # Salvar avaliação com comentário
        ConversationService.save_conversation_rating(chat_id, req.rating, req.comment)
        
        if req.comment:
            logger.info(f"[rate_response] Rating {req.rating} saved with comment for conversation {chat_id}")
        else:
            logger.info(f"[rate_response] Rating {req.rating} saved for conversation {chat_id}")
        
        return RatingResponse(
            conversation_id=chat_id,
            rating=req.rating,
            comment=req.comment,
            message="Avaliação salva com sucesso"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao salvar avaliação: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao salvar avaliação: {str(e)}")


# =============================================================================
# TESTE ENDPOINT - Debug do Stream
# =============================================================================

@router.get("/test/stream", summary="Testar SSE Stream (Debug)")
async def test_stream():
    """
    Endpoint para testar se SSE stream está funcionando.
    
    Retorna eventos de teste simples:
    1. status: "iniciando"
    2. token: "Teste"
    3. token: " de"
    4. token: " stream"
    5. complete: dados finais
    
    Use no frontend:
    ```javascript
    const es = new EventSource('/api/v1/chat/test/stream');
    es.addEventListener('status', e => console.log('Status:', JSON.parse(e.data)));
    es.addEventListener('token', e => console.log('Token:', JSON.parse(e.data)));
    es.addEventListener('complete', e => console.log('Complete:', JSON.parse(e.data)));
    ```
    """
    async def test_generator():
        import asyncio
        
        # Evento 1: status
        yield "event: status\ndata: {\"message\": \"iniciando teste\"}\n\n"
        logger.info("[test_stream] Status sent")
        
        await asyncio.sleep(0.5)
        
        # Eventos 2-4: tokens
        for word in ["Teste", " de", " stream", " SSE"]:
            yield f"event: token\ndata: {{\"content\": \"{word}\"}}\n\n"
            logger.info(f"[test_stream] Token '{word}' sent")
            await asyncio.sleep(0.3)
        
        # Evento 5: complete
        complete_data = {
            "answer": "Teste de stream SSE",
            "metadata": {
                "message_id": "test-123",
                "total_time": 2.0
            }
        }
        import json
        yield f"event: complete\ndata: {json.dumps(complete_data)}\n\n"
        logger.info("[test_stream] Complete sent")
    
    return StreamingResponse(
        test_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )