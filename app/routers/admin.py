"""
Rotas para gerenciar admins e seus grupos de acesso.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from app.models import AdminCreate, AdminUpdate, AdminResponse, AdminListResponse, AdminAuditLogResponse
from app.services.admin_service import AdminService
from app.services.admin_audit_service import AdminAuditService
from app.services.agent_service import AgentService
from app.providers.dependencies import get_current_user
from app.services.graph_user_service import GraphUserService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admins", tags=["admins"])


@router.post("/init", response_model=AdminResponse, summary="Inicializar primeiro admin (sem auth)")
def init_first_admin(admin_data: AdminCreate):
    """
    Criar primeiro admin do sistema (sem autenticação).
    
    Só funciona se não houver nenhum admin no banco.
    Após criado o primeiro, use GET /admins para outros.
    """
    try:
        # Verificar se já existe algum admin ATIVO
        existing_list = AdminService.list_admins(active_only=True, limit=1, offset=0)
        if existing_list["total"] > 0:
            raise HTTPException(
                status_code=403,
                detail="Já existe admin ATIVO no sistema. Use as rotas normais."
            )
        
        agent_id = admin_data.agent_id or 1
        
        # Verificar se já existe admin ATIVO com este email E agent_id
        # (Admins deletados podem ser recriados)
        existing = AdminService.get_admin_by_email_and_agent_active(admin_data.email, agent_id)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Já existe um admin ATIVO com email {admin_data.email} para o agente {agent_id}. Se foi deletado, pode ser recriado."
            )
        
        admin = AdminService.create_admin(
            email=admin_data.email,
            agent_id=agent_id,
            feature_ids=admin_data.feature_ids or [],
            name=admin_data.name,
            job_title=admin_data.job_title,
            city=admin_data.city
        )
        
        logger.info(f"[Admin] ✅ Primeiro admin criado: {admin_data.email} ({admin_data.name or 'sem nome'})")
        return AdminResponse(**admin)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao inicializar admin: {e}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")



@router.get("/allowed-agents", summary="Listar agentes permitidos", tags=["admins"])
def get_allowed_agents(
    current_user: dict = Depends(get_current_user)
):
    """
    Listar todos os agentes permitidos para criar/atualizar admins.
    
    Requer autenticação básica (não precisa ser admin).
    
    **Response:**
    Retorna lista de agentes disponíveis:
    - agent_id: ID do agente
    - code: Código do agente (LUZ, IGP, SMART)
    - name: Nome descritivo
    - description: Descrição detalhada
    - is_active: Se está ativo
    - created_at: Data de criação
    """
    try:
        agents = AgentService.get_allowed_agents()
        logger.info(f"[Admin] Agentes permitidos solicitados")
        return {"agents": agents, "total": len(agents)}
        
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao listar agentes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar agentes: {str(e)}")


async def _require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency para validar se user é admin (verificando no banco)."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Log para debug
    logger.debug(f"[Admin] _require_admin - current_user keys: {current_user.keys() if current_user else 'None'}")
    logger.debug(f"[Admin] _require_admin - current_user: {current_user}")
    
    # Verificar se existe no banco de dados
    email = current_user.get("email")
    logger.info(f"[Admin] _require_admin - Email extraído do token: '{email}'")
    
    if not email:
        logger.error(f"[Admin] ❌ Email não encontrado. current_user: {current_user}")
        raise HTTPException(status_code=401, detail="Email não encontrado no token")
    
    admin = AdminService.get_admin_by_email(email)
    logger.info(f"[Admin] _require_admin - Admin lookup result: {admin}")
    
    if not admin or not admin.get("is_active"):
        logger.error(f"[Admin] ❌ Admin não encontrado ou inativo para email: {email}")
        raise HTTPException(status_code=403, detail="Acesso restrito a admins")
    
    return current_user


@router.post("", response_model=AdminResponse, summary="Criar novo admin", tags=["admins"])
def create_admin(
    admin_data: AdminCreate,
    current_user: dict = Depends(_require_admin)
):
    """
    Criar novo admin com features e dados do colaborador.
    
    **Request:**
    - email: Email único do admin por agente (obrigatório)
    - name: Nome completo do colaborador (opcional, para desambiguar)
    - job_title: Cargo do colaborador (opcional)
    - city: Cidade do colaborador (opcional, para desambiguar pessoas com mesmo nome)
    - agent_id: ID do agente (1=LUZ, 2=IGP, 3=SMART). Default: 1
    - feature_ids: Lista de IDs de features permitidas (ex: [1, 2, 3])
    
    **Regra de Unicidade:**
    - O mesmo email pode ser admin de múltiplos agentes
    - Mas não pode haver duplicatas de (email + agent_id)
    - Exemplo OK: usuario@example.com é admin do LUZ E do IGP
    - Exemplo ERRO: usuario@example.com é admin do LUZ duas vezes
    
    **Response:**
    Retorna admin com detalhes completos de todas as features associadas:
    - admin_id: ID único do admin
    - email, name, job_title, city: Dados do colaborador
    - agent_id: ID do agente
    - agent_name: Nome do agente (LUZ, IGP, SMART)
    - features: Array com detalhes completos de cada feature (id, code, name, description, agente)
    - is_active: Se admin está ativo
    - created_at, updated_at: Timestamps
    """
    try:
        agent_id = admin_data.agent_id or 1
        
        # Será validado no service (que tem informação mais completa)
        admin = AdminService.create_admin(
            email=admin_data.email,
            agent_id=agent_id,
            feature_ids=admin_data.feature_ids,
            name=admin_data.name,
            job_title=admin_data.job_title,
            city=admin_data.city,
            created_by=current_user.get("email")
        )
        
        logger.info(f"[Admin] ✅ Novo admin criado: {admin_data.email} ({admin_data.name or 'sem nome'}) - {admin_data.city or 'sem cidade'} (agent_id={agent_id}) por {current_user.get('email')}")
        return AdminResponse(**admin)
        
    except HTTPException:
        raise
    except ValueError as e:
        # Validação falhou (admin já existe, agent inválido, feature inválida, etc)
        logger.warning(f"[Admin] ⚠️ Validação falhou ao criar admin: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao criar admin: {str(e)}")
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao criar admin: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar admin: {str(e)}")


@router.get("", response_model=AdminListResponse, summary="Listar admins")
def list_admins(
    active_only: bool = Query(True, description="Filtro de status: True=apenas ativos, False=apenas inativos, None=ambos"),
    email: Optional[str] = Query(None, description="Filtrar por email (busca parcial, case-insensitive)"),
    name: Optional[str] = Query(None, description="Filtrar por nome (busca parcial, case-insensitive)"),
    skip: int = Query(0, ge=0, description="Skip de resultados"),
    limit: int = Query(50, ge=1, le=100, description="Limite de resultados"),
    current_user: dict = Depends(_require_admin)
):
    """
    Listar todos os admins com filtros opcionais.
    
    **Query Parameters:**
    - active_only: Filtro de status (default: True = apenas ativos)
      - True: apenas admins ATIVOS
      - False: apenas admins INATIVOS (deletados com soft delete)
      - null: ambos os estados
    - email: (Opcional) Buscar por email específico ou parcial (case-insensitive)
    - name: (Opcional) Buscar por nome específico ou parcial (case-insensitive)
    - skip: Número de registros a pular (default: 0)
    - limit: Limite de registros a retornar (default: 50, máximo: 100)
    
    **Response:**
    Retorna lista com admin.features detalhadas (id, code, name, description, agente, is_active)
    
    **Exemplos:**
    - GET /admins?active_only=true - apenas ativos
    - GET /admins?active_only=false - apenas inativos
    - GET /admins?email=rodrigo - busca por email contendo "rodrigo"
    - GET /admins?name=Silva - busca por nome contendo "Silva"
    - GET /admins?email=rodrigo@company.com&name=Silva&active_only=true - combinar filtros
    """
    try:
        result = AdminService.list_admins(
            active_only=active_only,
            email=email,
            name=name,
            limit=limit,
            offset=skip
        )
        
        return AdminListResponse(
            admins=[AdminResponse(**a) for a in result["admins"]],
            total=result["total"]
        )
        
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao listar admins: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar admins: {str(e)}")


@router.get("/search/email", summary="Buscar admin por email em todos os agentes")
def search_admin_by_email(
    email: str = Query(..., description="Email a buscar (case-insensitive, exact match)"),
    current_user: dict = Depends(_require_admin)
):
    """
    Buscar um usuário por email em TODOS os agentes.
    
    Útil para verificar se uma pessoa já é admin em algum agente.
    Retorna uma lista porque a mesma pessoa pode ser admin em múltiplos agentes.
    
    **Query Parameters:**
    - email: Email a buscar (case-insensitive, busca exata)
    
    **Response:**
    - Se encontrado: lista de registros (pode ter 1+ agentes)
    - Se não encontrado: lista vazia
    
    **Exemplos:**
    - GET /admins/search/email?email=rodrigo.souza@example.com
    - GET /admins/search/email?email=admin@company.com
    """
    try:
        if not email or email.strip() == "":
            raise HTTPException(status_code=400, detail="Email não pode estar vazio")
        
        admins = AdminService.search_admin_by_email_all_agents(email.strip())
        
        if not admins:
            logger.info(f"[Admin] ℹ️ Nenhum admin encontrado com email: {email}")
            return {
                "admins": [],
                "total": 0,
                "message": f"Nenhum admin encontrado com email: {email}"
            }
        
        logger.info(f"[Admin] ✅ Encontrado(s) {len(admins)} admin(ns) com email: {email}")
        
        return {
            "admins": [AdminResponse(**a) for a in admins],
            "total": len(admins),
            "message": f"Encontrado(s) {len(admins)} registro(s)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao buscar admin por email: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar admin: {str(e)}")


@router.get("/features", summary="Listar todas as features disponíveis", tags=["admins"])
def list_features(active_only: bool = False, current_user: dict = Depends(_require_admin)):
    """
    Listar todas as features disponíveis para associar aos admins.
    
    **Query Parameters:**
    - active_only: Retornar apenas features ativas (default: False)
    
    **Response:**
    Retorna lista de features com detalhes completos:
    - feature_id: ID da feature
    - name: Nome da feature
    - description: Descrição
    - agente: Agente associado (LUZ, IGP, SMART)
    - is_active: Se feature está ativa
    - created_at: Data de criação
    """
    try:
        features = AdminService.list_features(active_only=active_only)
        return {"features": features, "total": len(features)}
        
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao listar features: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar features: {str(e)}")


@router.get("/agent/{agent_id}", response_model=AdminListResponse, summary="Listar admins por agent_id")
def list_admins_by_agent_id(
    agent_id: int,
    active_only: bool = Query(True, description="Retornar apenas admins ativos"),
    skip: int = Query(0, ge=0, description="Skip de resultados"),
    limit: int = Query(50, ge=1, le=100, description="Limite de registros"),
    current_user: dict = Depends(_require_admin)
):
    """
    Listar todos os admins de um agent_id específico.
    
    **Path Parameter:**
    - agent_id: ID do agente (1=LUZ, 2=IGP, 3=SMART)
    
    **Query Parameters:**
    - active_only: Retornar apenas admins ativos (default: True)
    - skip: Número de registros a pular (default: 0)
    - limit: Limite de registros (default: 50, máximo: 100)
    
    **Response:**
    Retorna lista de admins do agent_id com features detalhadas para cada um
    """
    try:
        result = AdminService.list_admins_by_agent_id(
            agent_id=agent_id,
            active_only=active_only,
            limit=limit,
            offset=skip
        )
        
        return AdminListResponse(
            admins=[AdminResponse(**a) for a in result["admins"]],
            total=result["total"]
        )
        
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao listar admins por agente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar admins: {str(e)}")


@router.get("/graph/users")
def graph_users_by_prefix(prefix: str, account_enabled: bool = None, current_user: dict = Depends(_require_admin)):
    """
    Proxy para buscar usuarios no Graph por prefixo do displayName.
    
    Query params:
    - prefix: prefixo do displayName (obrigatório)
    - account_enabled: filtrar por status ativo/inativo (opcional, true/false)
    """    
    result = GraphUserService.search_users_by_display_name_prefix(prefix, account_enabled)
    if result is None:
        raise HTTPException(status_code=502, detail="Erro ao consultar Graph")
    return result


@router.get("/email/{email}", response_model=AdminResponse, summary="Obter admin por email")
def get_admin_by_email(
    email: str,
    current_user: dict = Depends(_require_admin)
):
    """
    Obter detalhes completos de um admin pelo email.
    
    **Path Parameter:**
    - email: Email do admin (ex: lucas.lorensi@electrolux.com)
    
    **Response:**
    Retorna admin com features detalhadas:
    - admin_id, email, agente, is_active
    - features: Array com detalhes de cada feature (id, code, name, description, agente, is_active, created_at)
    - created_at, updated_at: Timestamps
    
    **Errors:**
    - 404: Admin não encontrado com esse email
    - 401: Usuário não é admin
    """
    try:
        admin = AdminService.get_admin_by_email(email)
        if not admin:
            raise HTTPException(status_code=404, detail=f"Admin com email {email} não encontrado")
        
        logger.info(f"[Admin] 📋 Detalhes do admin solicitados: {email}")
        return AdminResponse(**admin)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao buscar admin por email: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar admin: {str(e)}")


@router.get("/{admin_id}", response_model=AdminResponse, summary="Obter admin por ID")
def get_admin(
    admin_id: str,
    current_user: dict = Depends(_require_admin)
):
    """
    Obter detalhes completos de um admin específico.
    
    **Path Parameter:**
    - admin_id: ID único do admin
    
    **Response:**
    Retorna admin com features detalhadas:
    - admin_id, email, agente, is_active
    - features: Array com detalhes de cada feature (id, code, name, description, agente, is_active, created_at)
    - created_at, updated_at: Timestamps
    """
    try:
        admin = AdminService.get_admin_by_id(admin_id)
        
        if not admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        
        return AdminResponse(**admin)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao obter admin: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter admin: {str(e)}")


@router.patch("/email/{email}", response_model=AdminResponse, summary="Atualizar admin por email")
def update_admin_by_email(
    email: str,
    data: AdminUpdate,
    current_user: dict = Depends(_require_admin)
):
    """
    Atualizar dados e/ou features de um admin por EMAIL.
    
    **Recomendado para o frontend** pois o email está sempre disponível.
    
    **Request:**
    - agent_id: Novo agent_id (opcional). Ex: 1 (LUZ), 2 (IGP), 3 (SMART)
    - feature_ids: Nova lista de features (opcional). Se fornecido, substitui TODAS as features anteriores
    
    **Response:**
    Retorna admin completo com detalhes das features atualizadas:
    - features: Array com detalhes de cada feature (id, code, name, description, agente, is_active)
    
    **Exemplo:**
    ```json
    PATCH /api/v1/admins/email/admin@example.com
    {
      "name": "João Silva",
      "job_title": "Gerente TI",
      "city": "São Paulo",
      "agent_id": 2,
      "feature_ids": [1, 3, 5]
    }
    ```
    """
    try:
        # Validação de agent_id já é feita em AdminService.update_admin_by_email()
        admin = AdminService.update_admin_by_email(
            email=email,
            name=data.name,
            job_title=data.job_title,
            city=data.city,
            agent_id=data.agent_id,
            feature_ids=data.feature_ids,
            updated_by=current_user.get("email")
        )
        
        if not admin:
            raise HTTPException(status_code=404, detail=f"Admin com email '{email}' não encontrado")
        
        logger.info(f"[Admin] ✅ Admin atualizado: {email} por {current_user.get('email')}")
        return AdminResponse(**admin)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao atualizar admin: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar admin: {str(e)}")


@router.patch("/{admin_id}", response_model=AdminResponse, summary="Atualizar admin")
def update_admin(
    admin_id: str,
    data: AdminUpdate,
    current_user: dict = Depends(_require_admin)
):
    """
    Atualizar dados e/ou features de um admin por ID.
    
    **Request:**
    - agent_id: Novo agent_id (opcional). Ex: 1 (LUZ), 2 (IGP), 3 (SMART)
    - feature_ids: Nova lista de features (opcional). Se fornecido, substitui TODAS as features anteriores
    
    **Response:**
    Retorna admin completo com detalhes das features atualizadas:
    - features: Array com detalhes de cada feature (id, code, name, description, agente, is_active)
    
    **Exemplo:**
    ```json
    PATCH /api/v1/admins/{admin_id}
    {
      "name": "Maria Santos",
      "job_title": "Admin Sistema",
      "city": "Rio de Janeiro",
      "agent_id": 3,
      "feature_ids": [1, 3, 5]
    }
    ```
    """
    try:
        # Validação de agent_id já é feita em AdminService.update_admin()
        admin = AdminService.update_admin(
            admin_id=admin_id,
            name=data.name,
            job_title=data.job_title,
            city=data.city,
            agent_id=data.agent_id,
            feature_ids=data.feature_ids,
            updated_by=current_user.get("email")
        )
        
        if not admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        
        logger.info(f"[Admin] ✅ Admin atualizado: {admin_id} por {current_user.get('email')}")
        return AdminResponse(**admin)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao atualizar admin: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar admin: {str(e)}")


@router.patch("/{admin_id}/deactivate", response_model=AdminResponse, summary="Inativar admin")
def deactivate_admin(
    admin_id: str,
    current_user: dict = Depends(_require_admin)
):
    """
    Inativar um admin (marca como is_active = 0).
    
    **Nota:**
    - Admin inativo não aparece em listagens normais
    - Pode ser reativado depois
    - Histórico e auditoria são preservados
    - Permite recriação com mesmo email/agent_id
    """
    try:
        logger.info(f"[DEACTIVATE ADMIN] 📥 Recebido request para inativar admin_id: {admin_id}")
        
        success = AdminService.deactivate_admin(admin_id, deactivated_by=current_user.get("email"))
        
        if not success:
            logger.warning(f"[DEACTIVATE ADMIN] ⚠️ Admin não encontrado: {admin_id}")
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        
        admin = AdminService.get_admin_by_id(admin_id)
        logger.info(f"[DEACTIVATE ADMIN] ✅ Admin inativado com sucesso: {admin_id}")
        return AdminResponse(**admin)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEACTIVATE ADMIN] ❌ Erro ao inativar admin: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao inativar admin: {str(e)}")


@router.delete("/{admin_id}", summary="Deletar admin permanentemente")
def delete_admin(
    admin_id: str,
    current_user: dict = Depends(_require_admin)
):
    """
    Deletar admin PERMANENTEMENTE do banco (hard delete).
    
    **CUIDADO:**
    - Remove o registro E todos seus dados (features, auditoria)
    - Não pode ser desfeito!
    - Use DELETE /{admin_id}/deactivate para apenas inativar
    
    **Quando usar:**
    - Admin criado por erro
    - Limpeza de dados de teste
    - GDPR/compliance (com autorização)
    
    **Alternativa recomendada:**
    - Use PATCH /{admin_id}/deactivate para apenas inativar
    - Permite reativar depois
    - Preserva histórico
    """
    try:
        logger.warning(f"[DELETE ADMIN] 🔴 PERMANENT DELETE solicitado para admin_id: {admin_id} por {current_user.get('email')}")
        
        success = AdminService.permanent_delete_admin(admin_id)
        
        if not success:
            logger.warning(f"[DELETE ADMIN] ⚠️ Admin não encontrado: {admin_id}")
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        
        logger.warning(f"[DELETE ADMIN] 🔴 PERMANENT DELETE executado: {admin_id}")
        return {"message": "Admin deletado permanentemente (não pode ser desfeito)", "admin_id": admin_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE ADMIN] ❌ Erro ao deletar permanentemente: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao deletar admin: {str(e)}")


@router.post("/{admin_id}/features/{feature_id}", response_model=AdminResponse, summary="Adicionar feature a um admin")
def add_feature(
    admin_id: str,
    feature_id: int,
    current_user: dict = Depends(_require_admin)
):
    """
    Adicionar feature a um admin.
    """
    try:
        updated_admin = AdminService.add_feature_to_admin(admin_id, feature_id)
        
        if not updated_admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        
        logger.info(f"[Admin] ✅ Feature {feature_id} adicionada ao admin {admin_id}")
        return AdminResponse(**updated_admin)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao adicionar feature: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar feature: {str(e)}")


@router.delete("/{admin_id}/features/{feature_id}", response_model=AdminResponse, summary="Remover feature de um admin")
def remove_feature(
    admin_id: str,
    feature_id: int,
    current_user: dict = Depends(_require_admin)
):
    """
    Remover feature de um admin.
    """
    try:
        updated_admin = AdminService.remove_feature_from_admin(admin_id, feature_id)
        
        if not updated_admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado")
        
        logger.info(f"[Admin] ✅ Feature {feature_id} removida do admin {admin_id}")
        return AdminResponse(**updated_admin)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao remover feature: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao remover feature: {str(e)}")


@router.get("/{admin_id}/audit", response_model=AdminAuditLogResponse, summary="Obter histórico de auditoria de um admin")
def get_admin_audit_history(
    admin_id: str,
    limit: int = Query(50, ge=1, le=500, description="Máximo de registros a retornar"),
    offset: int = Query(0, ge=0, description="Deslocamento para paginação"),
    current_user: dict = Depends(_require_admin)
):
    """
    Obter o histórico completo de auditoria de um admin.
    
    Retorna todos os registros de criação, atualização e exclusão.
    Cada alteração feita por diferentes usuários aparece como um registro separado,
    com data/hora, valores antigos e novos.
    
    Exemplo de resposta:
    ```json
    {
      "admin_id": "admin-123",
      "total": 3,
      "logs": [
        {
          "log_id": 1,
          "admin_id": "admin-123",
          "action": "CREATE",
          "changed_fields": ["email", "name", "job_title"],
          "old_values": {},
          "new_values": {
            "email": "admin@example.com",
            "name": "João Silva",
            "job_title": "Gerente"
          },
          "changed_by": "user@company.com",
          "changed_at": "2024-01-15T10:30:00",
          "ip_address": "192.168.1.1",
          "details": "Admin criado: admin@example.com"
        },
        {
          "log_id": 2,
          "admin_id": "admin-123",
          "action": "UPDATE",
          "changed_fields": ["job_title"],
          "old_values": {"job_title": "Gerente"},
          "new_values": {"job_title": "Diretor"},
          "changed_by": "user2@company.com",
          "changed_at": "2024-01-16T14:00:00",
          "ip_address": "192.168.1.2",
          "details": "Fields alterados: job_title"
        }
      ]
    }
    ```
    """
    try:
        # Verificar se admin existe
        admin = AdminService.get_admin_by_id(admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail=f"Admin {admin_id} não encontrado")
        
        # Obter histórico de auditoria
        history = AdminAuditService.get_admin_audit_history(admin_id, limit, offset)
        
        logger.info(f"[Admin] ✅ Histórico de auditoria obtido para admin {admin_id}")
        return AdminAuditLogResponse(
            admin_id=admin_id,
            logs=history.get("logs", []),
            total=history.get("total", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao obter histórico de auditoria: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter histórico de auditoria: {str(e)}")


@router.get("/deleted/list", response_model=AdminListResponse, summary="Listar admins deletados")
def list_deleted_admins(
    skip: int = Query(0, ge=0, description="Skip de resultados"),
    limit: int = Query(50, ge=1, le=100, description="Limite de resultados"),
    current_user: dict = Depends(_require_admin)
):
    """
    Listar todos os admins DELETADOS (soft delete - is_active=0).
    
    **Nota:**
    - Deletados não aparecem em GET /admins (que por padrão lista apenas ativos)
    - Permitem recriação com mesmo email/agent_id
    - Mantêm histórico de auditoria no admin_audit_log
    
    **Query Parameters:**
    - skip: Número de registros a pular (default: 0)
    - limit: Limite de registros a retornar (default: 50, máximo: 100)
    """
    try:
        result = AdminService.list_admins(
            active_only=False,  # Listar INATIVOS
            limit=limit,
            offset=skip
        )
        
        # Filtrar apenas inativos
        deleted_admins = [a for a in result["admins"] if not a.get("is_active", True)]
        
        return AdminListResponse(
            admins=[AdminResponse(**a) for a in deleted_admins],
            total=len(deleted_admins)
        )
        
    except Exception as e:
        logger.error(f"[Admin] ❌ Erro ao listar admins deletados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar admins deletados: {str(e)}")



