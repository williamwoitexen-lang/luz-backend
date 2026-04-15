"""
Router para gerenciar prompts de agentes.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from app.models import PromptResponse, PromptCreate, PromptUpdate
from app.services.prompt_service import PromptService
from app.services.agent_service import AgentService
from app.routers.auth import get_current_user
from app.routers.admin import _require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/prompts", tags=["Prompts"])


def get_prompt_service() -> PromptService:
    """Dependency para PromptService."""
    return PromptService()


@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    request: PromptCreate,
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(_require_admin),
    prompt_service: PromptService = Depends(get_prompt_service)
):
    """
    Cria um novo prompt para um agente.
    
    Sincroniza com o LLM Server antes de salvar no banco.
    Requer permissão de admin.
    
    **Request:**
    - agente: Um dos agentes permitidos ('LUZ', 'IGP', 'SMART')
    - system_prompt: Texto do prompt para o LLM
    
    Args:
        request: PromptCreate com agente e system_prompt
        
    Returns:
        PromptResponse com dados do prompt criado
        
    Raises:
        400: Agente inválido ou já existe
        500: Erro ao sincronizar com LLM Server ou DB
    """
    try:
        # Validar agente
        try:
            AgentService.validate_agent_or_raise(request.agente)
        except ValueError as e:
            logger.warning(f"[Prompt] Agente inválido: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        logger.info(f"[Prompt] Criando novo prompt para agente '{request.agente}'")
        
        prompt = prompt_service.create_prompt(
            agente=request.agente,
            system_prompt=request.system_prompt
        )
        
        return PromptResponse(**prompt)
        
    except ValueError as e:
        logger.warning(f"[Prompt] Erro de validação: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except RuntimeError as e:
        logger.error(f"[Prompt] Erro ao sincronizar com LLM Server: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao atualizar prompt no LLM Server: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"[Prompt] Erro ao criar prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agente}", response_model=PromptResponse)
async def get_prompt(
    agente: str,
    current_user: dict = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service)
):
    """
    Busca um prompt de um agente específico.
    
    Args:
        agente: Nome do agente (luz, agua, energia, etc)
        
    Returns:
        PromptResponse com dados do prompt
        
    Raises:
        404: Prompt não encontrado
        500: Erro ao buscar no DB
    """
    try:
        logger.info(f"[Prompt] Buscando prompt para agente '{agente}'")
        
        prompt = prompt_service.get_prompt_by_agente(agente)
        if not prompt:
            raise HTTPException(
                status_code=404,
                detail=f"Prompt para agente '{agente}' não encontrado"
            )
        
        return PromptResponse(**prompt)
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"[Prompt] Erro ao buscar prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[PromptResponse])
async def list_prompts(
    current_user: dict = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service)
):
    """
    Lista todos os prompts de todos os agentes.
    
    Returns:
        Lista de PromptResponse
        
    Raises:
        500: Erro ao buscar no DB
    """
    try:
        logger.info("[Prompt] Listando todos os prompts")
        
        prompts = prompt_service.list_prompts()
        return [PromptResponse(**prompt) for prompt in prompts]
        
    except Exception as e:
        logger.error(f"[Prompt] Erro ao listar prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agente}", response_model=PromptResponse)
async def update_prompt(
    agente: str,
    request: PromptUpdate,
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(_require_admin),
    prompt_service: PromptService = Depends(get_prompt_service)
):
    """
    Atualiza um prompt existente.
    
    Sincroniza com o LLM Server ANTES de atualizar no banco.
    Se o LLM Server falhar, não atualiza o DB.
    Requer permissão de admin.
    
    **Request:**
    - system_prompt: Novo texto do prompt
    
    Args:
        agente: Nome do agente ('LUZ', 'IGP', 'SMART')
        request: PromptUpdate com novo system_prompt
        
    Returns:
        PromptResponse com dados do prompt atualizado
        
    Raises:
        400: Agente inválido
        404: Prompt não encontrado
        500: Erro ao sincronizar com LLM Server ou DB
    """
    try:
        # Validar agente
        try:
            AgentService.validate_agent_or_raise(agente)
        except ValueError as e:
            logger.warning(f"[Prompt] Agente inválido: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        logger.info(f"[Prompt] Atualizando prompt para agente '{agente}'")
        
        prompt = prompt_service.update_prompt(
            agente=agente,
            system_prompt=request.system_prompt
        )
        
        return PromptResponse(**prompt)
        
    except ValueError as e:
        logger.warning(f"[Prompt] Erro de validação: {e}")
        raise HTTPException(status_code=404, detail=str(e))
        
    except RuntimeError as e:
        logger.error(f"[Prompt] Erro ao sincronizar com LLM Server: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao atualizar prompt no LLM Server: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"[Prompt] Erro ao atualizar prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agente}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    agente: str,
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(_require_admin),
    prompt_service: PromptService = Depends(get_prompt_service)
):
    """
    Deleta um prompt.
    
    Requer permissão de admin.
    
    Args:
        agente: Nome do agente
        
    Raises:
        404: Prompt não encontrado
        500: Erro ao deletar
    """
    try:
        logger.info(f"[Prompt] Deletando prompt para agente '{agente}'")
        
        prompt_service.delete_prompt(agente)
        
    except ValueError as e:
        logger.warning(f"[Prompt] Erro de validação: {e}")
        raise HTTPException(status_code=404, detail=str(e))
        
    except Exception as e:
        logger.error(f"[Prompt] Erro ao deletar prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))
