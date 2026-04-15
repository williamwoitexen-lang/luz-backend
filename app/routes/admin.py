from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import logging
from app.services.admin_service import AdminService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admins", tags=["admins"])


class AdminCreate(BaseModel):
    email: EmailStr
    agente: str = "luz"
    feature_ids: Optional[List[int]] = None


class AdminUpdate(BaseModel):
    agente: Optional[str] = None
    feature_ids: Optional[List[int]] = None


class AdminResponse(BaseModel):
    admin_id: str
    email: str
    agente: str
    is_active: bool
    feature_ids: List[int]
    created_at: Any
    updated_at: Any


@router.post("/", response_model=Dict[str, Any])
def create_admin(data: AdminCreate):
    """Criar novo admin."""
    try:
        admin = AdminService.create_admin(
            email=data.email,
            agente=data.agente,
            feature_ids=data.feature_ids
        )
        return {"success": True, "data": admin}
    except Exception as e:
        logger.error(f"Erro ao criar admin: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{admin_id}", response_model=Dict[str, Any])
def get_admin(admin_id: str):
    """Obter admin por ID."""
    try:
        admin = AdminService.get_admin_by_id(admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        return {"success": True, "data": admin}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar admin: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/email/{email}", response_model=Dict[str, Any])
def get_admin_by_email(email: str):
    """Obter admin por email."""
    try:
        admin = AdminService.get_admin_by_email(email)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        return {"success": True, "data": admin}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar admin por email: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=Dict[str, Any])
def list_admins(
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Listar todos os admins com paginação."""
    try:
        result = AdminService.list_admins(
            active_only=active_only,
            limit=limit,
            offset=offset
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Erro ao listar admins: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agente/{agente}", response_model=Dict[str, Any])
def list_admins_by_agente(
    agente: str,
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Listar admins de um agente específico."""
    try:
        result = AdminService.list_admins_by_agente(
            agente=agente,
            active_only=active_only,
            limit=limit,
            offset=offset
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Erro ao listar admins do agente: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{admin_id}", response_model=Dict[str, Any])
def update_admin(admin_id: str, data: AdminUpdate):
    """Atualizar admin."""
    try:
        admin = AdminService.update_admin(
            admin_id=admin_id,
            name=data.name,
            job_title=data.job_title,
            city=data.city,
            agent_id=data.agent_id,
            feature_ids=data.feature_ids
        )
        if not admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        return {"success": True, "data": admin}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar admin: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{admin_id}", response_model=Dict[str, Any])
def delete_admin(admin_id: str):
    """Deletar admin (soft delete)."""
    try:
        deleted = AdminService.delete_admin(admin_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        return {"success": True, "message": "Admin deletado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar admin: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{admin_id}/features/{feature_id}", response_model=Dict[str, Any])
def add_feature_to_admin(admin_id: str, feature_id: int):
    """Adicionar feature a um admin."""
    try:
        admin = AdminService.add_feature_to_admin(admin_id, feature_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        return {"success": True, "data": admin}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar feature: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{admin_id}/features/{feature_id}", response_model=Dict[str, Any])
def remove_feature_from_admin(admin_id: str, feature_id: int):
    """Remover feature de um admin."""
    try:
        admin = AdminService.remove_feature_from_admin(admin_id, feature_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        return {"success": True, "data": admin}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover feature: {e}")
        raise HTTPException(status_code=400, detail=str(e))
