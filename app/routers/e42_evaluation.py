"""
Rotas para integração com sistema 4x2 (Avaliação de Funcionários)
Integrá com Power Automate para buscar forças e fraquezas de colaboradores
"""
import logging
import json
import os
import httpx
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/e42", tags=["4x2-evaluation"])

# ============ Modelos Pydantic ============

class E42EvaluationRequest(BaseModel):
    """Request para buscar avaliação 4x2 de um funcionário"""
    user_email: str  # Email do colaborador (ex: email-teste@electrolux.com)
    identificator: str  # ID da avaliação (ex: "104")


class E42WeaknessItem(BaseModel):
    """Item de fraqueza extraído da avaliação"""
    comment: str  # Comentário/feedback da fraqueza
    selection: str  # Categoria da fraqueza (ex: "GR: Learning ability")
    evaluation_id: str  # ID único da avaliação


class E42StrengthItem(BaseModel):
    """Item de força extraído da avaliação"""
    comment: str  # Comentário/feedback da força
    selection: str  # Categoria da força (ex: "EN: Deliver Results")
    evaluation_id: str  # ID único da avaliação


class E42EvaluationResponse(BaseModel):
    """Resposta com informações processadas da avaliação"""
    user_email: str  # Email do colaborador
    user_id: Optional[str] = None  # ID interno do usuário (buscado no DB)
    weaknesses: List[E42WeaknessItem]  # Fraquezas (apenas Individual)
    strengths: List[E42StrengthItem]  # Forças (apenas Individual)
    total_evaluations: int  # Total de avaliações processadas
    evaluation_timestamp: Optional[str] = None  # Data da avaliação
    success: bool = True


# ============ Configuração ============

# URL e credenciais do Power Automate carregadas de variáveis de ambiente (Azure)
# POWER_AUTOMATE_URL é obrigatória e deve ser configurada em variáveis de ambiente
POWER_AUTOMATE_URL = os.getenv("POWER_AUTOMATE_URL")
POWER_AUTOMATE_PARAMS = {
    "api-version": "1",
    "sp": "/triggers/manual/run",
    "sv": "1.0",
    "sig": os.getenv("POWER_AUTOMATE_SIGNATURE", "your-signature-key-here")
}
POWER_AUTOMATE_HEADERS = {
    "Content-Type": "application/json",
    "secretkey": os.getenv("", "your-secret-key-here")
}


# ============ Funções Auxiliares ============

async def get_user_id_from_email(email: str) -> Optional[str]:
    """
    Busca o ID interno do usuário baseado no email
    Conecta ao banco de dados interno
    """
    try:
        from app.core.sqlserver import get_sqlserver_connection
        
        sql = get_sqlserver_connection()
        query = "SELECT user_id FROM users WHERE email = ? LIMIT 1"
        results = sql.execute(query, [email])
        
        if results:
            return results[0]["user_id"]
        
        logger.warning(f"Usuário não encontrado com email: {email}")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao buscar user_id para {email}: {str(e)}")
        return None


async def call_power_automate(user_email: str, identificator: str) -> Optional[List[Dict[str, Any]]]:
    """
    Faz chamada ao endpoint do Power Automate
    Retorna a lista de avaliações do CRM
    """
    try:
        payload = {
            "UserEmail": user_email,
            "Identificator": identificator
        }
        
        logger.info(f"Chamando Power Automate para {user_email} (ID: {identificator})")
        
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.post(
                POWER_AUTOMATE_URL,
                json=payload,
                headers=POWER_AUTOMATE_HEADERS,
                params=POWER_AUTOMATE_PARAMS
            )
            
            response.raise_for_status()
            
            # O Power Automate retorna a resposta do CRM
            data = response.json()
            
            logger.info(f"Resposta do Power Automate recebida: {len(data) if isinstance(data, list) else 'objeto único'} itens")
            
            return data if isinstance(data, list) else [data]
            
    except Exception as e:
        logger.error(f"Erro ao chamar Power Automate: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar dados do Power Automate: {str(e)}"
        )


def process_crm_response(crm_data: List[Dict[str, Any]], user_email: str) -> Dict[str, Any]:
    """
    Processa a resposta do CRM e extrai fraquezas e forças
    Filtra apenas avaliações do tipo "Individual"
    """
    weaknesses: List[E42WeaknessItem] = []
    strengths: List[E42StrengthItem] = []
    
    if not crm_data:
        return {
            "weaknesses": weaknesses,
            "strengths": strengths,
            "total_evaluations": 0
        }
    
    for item in crm_data:
        # Verificar se é avaliação individual
        evaluation_type = item.get("kietec_type", "").strip()
        
        if evaluation_type != "Individual":
            logger.debug(f"Ignorando avaliação do tipo: {evaluation_type}")
            continue
        
        # Verificar email (segurança)
        item_email = item.get("kietec_employeeemail", "").strip()
        if item_email.lower() != user_email.lower():
            logger.warning(f"Email não corresponde: {item_email} vs {user_email}")
            continue
        
        factor = item.get("kietec_factor", "").strip()
        comment = item.get("kietec_comment", "").strip()
        selection = item.get("kietec_selection", "").strip()
        evaluation_id = item.get("kietec_e42_answerid", "").strip()
        
        # Ignorar se não tem comentário
        if not comment:
            logger.debug("Ignorando item sem comentário")
            continue
        
        # Extrair fraquezas
        if factor == "Weakness":
            weaknesses.append(E42WeaknessItem(
                comment=comment,
                selection=selection,
                evaluation_id=evaluation_id
            ))
            logger.debug(f"Fraqueza extraída: {comment} ({selection})")
        
        # Extrair forças
        elif factor == "Strength":
            strengths.append(E42StrengthItem(
                comment=comment,
                selection=selection,
                evaluation_id=evaluation_id
            ))
            logger.debug(f"Força extraída: {comment} ({selection})")
        
        else:
            logger.warning(f"Fator desconhecido: {factor}")
    
    return {
        "weaknesses": weaknesses,
        "strengths": strengths,
        "total_evaluations": len(crm_data)
    }





# ============ Endpoints ============

@router.post("/evaluation", response_model=E42EvaluationResponse)
async def get_employee_evaluation(req: E42EvaluationRequest) -> E42EvaluationResponse:
    """
    Busca avaliação 4x2 de um funcionário
    
    Fluxo:
    1. Chama Power Automate com email e ID da avaliação
    2. Processa resposta do CRM
    3. Extrai fraquezas (Weakness) e forças (Strength) do tipo Individual
    4. Retorna dados formatados com ID do usuário interno
    
    Exemplo de uso:
    ```json
    {
        "user_email": "email-teste@electrolux.com",
        "identificator": "104"
    }
    ```
    
    Resposta:
    ```json
    {
        "user_email": "email-teste@electrolux.com",
        "user_id": "user123",
        "weaknesses": [
            {
                "comment": "teste8",
                "selection": "GR: Learning ability",
                "evaluation_id": "ad3cad96-06ca-f011-8544-002248379316"
            }
        ],
        "strengths": [
            {
                "comment": "teste2",
                "selection": "EN: Leading others and Self",
                "evaluation_id": "e7b85c8a-06ca-f011-8544-002248379316"
            }
        ],
        "total_evaluations": 6,
        "evaluation_timestamp": "2026-02-26T10:30:00Z",
        "success": true
    }
    ```
    """
    logger.info(f"GET /e42/evaluation - Email: {req.user_email}, ID: {req.identificator}")
    
    try:
        # 1. Buscar dados do Power Automate
        crm_data = await call_power_automate(req.user_email, req.identificator)
        
        # 2. Processar resposta
        processed = process_crm_response(crm_data, req.user_email)
        
        # 3. Buscar ID do usuário interno
        user_id = await get_user_id_from_email(req.user_email)
        
        # 4. Montar resposta
        response = E42EvaluationResponse(
            user_email=req.user_email,
            user_id=user_id,
            weaknesses=processed["weaknesses"],
            strengths=processed["strengths"],
            total_evaluations=processed["total_evaluations"],
            evaluation_timestamp=datetime.utcnow().isoformat() + "Z",
            success=True
        )
        
        logger.info(
            f"Avaliação processada com sucesso: "
            f"{len(response.weaknesses)} fraquezas, "
            f"{len(response.strengths)} forças"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar avaliação: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar avaliação: {str(e)}"
        )


@router.post("/evaluation/weaknesses-only")
async def get_employee_weaknesses(req: E42EvaluationRequest) -> Dict[str, Any]:
    """
    Versão simplificada: busca APENAS as fraquezas do funcionário
    
    Retorna:
    ```json
    {
        "user_email": "email-teste@electrolux.com",
        "user_id": "user123",
        "weaknesses": ["sempre atrasado", "ganancioso"]
    }
    ```
    """
    try:
        # Chamar endpoint completo
        full_evaluation = await get_employee_evaluation(req)
        
        # Extrair apenas comentários das fraquezas
        weakness_comments = [w.comment for w in full_evaluation.weaknesses]
        
        return {
            "user_email": full_evaluation.user_email,
            "user_id": full_evaluation.user_id,
            "weaknesses": weakness_comments
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar fraquezas: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar fraquezas: {str(e)}"
        )
