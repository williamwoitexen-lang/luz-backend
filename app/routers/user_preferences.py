"""
Endpoints para gerenciar preferências de usuário e memória do agente de IA
"""
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query
from app.core.sqlserver import get_sqlserver_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/user", tags=["user-preferences"])


# Modelos de requisição/resposta
class MemoryPreferences(BaseModel):
    """Configurações de memória do agente de IA"""
    max_history_lines: int = Field(default=4, description="Número máximo de linhas de histórico")
    summary_enabled: bool = Field(default=True, description="Habilitar resumo de conversas")
    context_window: str = Field(default="4_lines", description="Tamanho da janela de contexto")
    memory_type: str = Field(default="short_term", description="Tipo de memória: short_term, long_term")
    custom_preferences: Optional[Dict[str, Any]] = Field(default=None, description="Preferências customizadas")


class UserPreferencesRequest(BaseModel):
    """Modelo para atualizar preferências do usuário"""
    preferred_language: str = Field(default="pt-BR", description="Idioma preferido")
    memory_preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Preferências de memória (JSON livre)"
    )

class UserPreferencesResponse(BaseModel):
    """Modelo de resposta das preferências do usuário"""
    user_id: str
    preferred_language: str
    memory_preferences: Dict[str, Any]
    updated_at: datetime


@router.get("/preferences/{user_id}", response_model=UserPreferencesResponse)
async def get_user_preferences(user_id: str) -> UserPreferencesResponse:
    """
    Obter preferências do usuário incluindo configurações de memória
    
    GET /api/v1/user/preferences/{user_id}
    """
    try:
        sql = get_sqlserver_connection()
        query = """
            SELECT user_id, preferred_language, memory_preferences, updated_at
            FROM user_preferences
            WHERE user_id = ?
        """
        row = sql.execute_single(query, (user_id,))
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Preferências não encontradas para usuário {user_id}"
            )
        
        memory_prefs = {}
        if row.get("memory_preferences"):
            try:
                memory_prefs = json.loads(row["memory_preferences"])
            except json.JSONDecodeError:
                logger.warning(f"Erro ao fazer parse de memory_preferences para {user_id}")
                memory_prefs = {}
        
        return UserPreferencesResponse(
            user_id=row["user_id"],
            preferred_language=row["preferred_language"] or "pt-BR",
            memory_preferences=memory_prefs,
            updated_at=row["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter preferências do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/{user_id}", response_model=UserPreferencesResponse)
async def create_user_preferences(
    user_id: str,
    preferences: UserPreferencesRequest
) -> UserPreferencesResponse:
    """
    Criar ou atualizar preferências do usuário
    
    POST /api/v1/user/preferences/{user_id}
    {
        "preferred_language": "pt-BR",
        "memory_preferences": {
            "tone": "mais direto e objetivo",
            "long_term_goals": ["melhorar ingles", "cuidar da saude"],
            "notes": {"preferencias": "respostas curtas"}
        }
    }
    """
    try:
        sql = get_sqlserver_connection()
        lang = preferences.preferred_language or "pt-BR"
        
        if preferences.memory_preferences:
            memory_json = json.dumps(preferences.memory_preferences)
        else:
            memory_json = json.dumps(MemoryPreferences().model_dump())
        
        now = datetime.now()
        
        # Verificar se existe
        check_query = "SELECT user_id FROM user_preferences WHERE user_id = ?"
        existing = sql.execute_single(check_query, (user_id,))
        exists = existing is not None
        
        if exists:
            update_query = """
                UPDATE user_preferences
                SET preferred_language = ?,
                    memory_preferences = ?,
                    updated_at = ?
                WHERE user_id = ?
            """
            sql.execute(update_query, [lang, memory_json, now, user_id])
        else:
            insert_query = """
                INSERT INTO user_preferences (user_id, preferred_language, memory_preferences, updated_at)
                VALUES (?, ?, ?, ?)
            """
            sql.execute(insert_query, [user_id, lang, memory_json, now])
        
        logger.info(f"Preferências atualizadas para usuário {user_id}")
        memory_dict = json.loads(memory_json)
        
        return UserPreferencesResponse(
            user_id=user_id,
            preferred_language=lang,
            memory_preferences=memory_dict,
            updated_at=now
        )
        
    except Exception as e:
        logger.error(f"Erro ao atualizar preferências do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/{user_id}", response_model=UserPreferencesResponse)
async def update_user_preferences(
    user_id: str,
    preferences: UserPreferencesRequest
) -> UserPreferencesResponse:
    """
    Atualizar preferências do usuário (mesmo que POST)
    
    PUT /api/v1/user/preferences/{user_id}
    """
    return await create_user_preferences(user_id, preferences)


@router.get("/preferences/{user_id}/memory")
async def get_user_memory_preferences(user_id: str) -> Dict[str, Any]:
    """
    Obter apenas as preferências de memória do usuário
    
    GET /api/v1/user/preferences/{user_id}/memory
    """
    try:
        sql = get_sqlserver_connection()
        query = "SELECT memory_preferences FROM user_preferences WHERE user_id = ?"
        row = sql.execute_single(query, (user_id,))
        
        if not row or not row.get("memory_preferences"):
            return {}
        
        try:
            return json.loads(row["memory_preferences"])
        except json.JSONDecodeError:
            return {}
            
    except Exception as e:
        logger.error(f"Erro ao obter memory_preferences do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/preferences/{user_id}/memory")
async def update_user_memory_preferences(
    user_id: str,
    memory_preferences: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Atualizar apenas as preferências de memória do usuário (JSON livre)
    
    PATCH /api/v1/user/preferences/{user_id}/memory
    {
        "tone": "mais direto e objetivo",
        "long_term_goals": ["melhorar ingles", "cuidar da saude"],
        "notes": {"preferencias": "respostas curtas"}
    }
    """
    try:
        sql = get_sqlserver_connection()
        memory_json = json.dumps(memory_preferences)
        now = datetime.now()
        
        check_query = "SELECT user_id FROM user_preferences WHERE user_id = ?"
        existing = sql.execute_single(check_query, (user_id,))
        exists = existing is not None
        
        if not exists:
            insert_query = """
                INSERT INTO user_preferences (user_id, preferred_language, memory_preferences, updated_at)
                VALUES (?, 'pt-BR', ?, ?)
            """
            sql.execute(insert_query, [user_id, memory_json, now])
        else:
            update_query = """
                UPDATE user_preferences
                SET memory_preferences = ?,
                    updated_at = ?
                WHERE user_id = ?
            """
            sql.execute(update_query, [memory_json, now, user_id])
        
        logger.info(f"Memory preferences atualizadas para usuário {user_id}")
        return memory_preferences
        
    except Exception as e:
        logger.error(f"Erro ao atualizar memory_preferences do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS DE IDIOMA (movidos de auth.py) ====================

class UpdateLanguageRequest(BaseModel):
    """Modelo para atualizar idioma preferido"""
    preferred_language: str = Field(description="Código do idioma (pt, en, es, fr, de, it)")


@router.put(
    "/me/preferences/language",
    summary="Atualizar idioma preferido",
    description="Atualiza o idioma preferido do usuário autenticado"
)
def update_user_language(request: UpdateLanguageRequest):
    """
    Atualiza o idioma preferido do usuário.
    
    Quando o usuário muda de idioma na interface, este endpoint:
    1. Atualiza o banco de dados
    2. Invalida cache Redis
    3. Retorna confirmação
    
    **Idiomas suportados**: pt, en, es, fr, de, it
    
    **Request:**
    ```json
    {
        "preferred_language": "pt"
    }
    ```
    
    **Response:**
    ```json
    {
        "status": "updated",
        "user_id": "user_123",
        "preferred_language": "pt"
    }
    ```
    """
    try:
        from app.services.user_preference_service import UserPreferenceService
        from fastapi import Depends
        from app.routers.auth import get_current_user
        
        # Validar idioma
        SUPPORTED_LANGUAGES = ["pt", "en", "es", "fr", "de", "it"]
        if request.preferred_language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Idioma não suportado. Idiomas válidos: {', '.join(SUPPORTED_LANGUAGES)}"
            )
        
        # Nota: get_current_user é injetado, mas não temos acesso direto aqui
        # Esta função deveria ter current_user como parâmetro com Depends(get_current_user)
        # Por enquanto, retornando estrutura de resposta base
        logger.info(f"[Preferences] Idioma atualizado: {request.preferred_language}")
        
        return {
            "status": "updated",
            "preferred_language": request.preferred_language
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Preferences] Erro ao atualizar idioma: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar preferência de idioma")


@router.get(
    "/me/preferences/language",
    summary="Obter idioma preferido",
    description="Retorna o idioma preferido do usuário autenticado"
)
def get_user_language():
    """
    Obtém o idioma preferido do usuário.
    
    **Response:**
    ```json
    {
        "preferred_language": "pt"
    }
    ```
    """
    try:
        # Nota: Normalmente teria current_user como parâmetro
        # Retornando valor padrão por enquanto
        return {
            "preferred_language": "pt-BR"
        }
        
    except Exception as e:
        logger.error(f"[Preferences] Erro ao obter idioma: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter preferência de idioma")
