"""
Rotas para dashboard de análise de conversas e chat.
"""
import logging
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.conversation_service import ConversationService
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    start_date: Optional[str] = Query(None, description="Data início (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data fim (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="Filtrar por usuário específico")
):
    """
    Obter resumo agregado de conversas e chat para dashboard.
    
    **Retorna:**
    - Total de conversas
    - Total de mensagens
    - Tokens gastos (total e média)
    - Modelos mais usados
    - Usuários mais ativos
    - Métricas de tempo
    - Taxa de conclusão
    """
    try:
        logger.info(f"Dashboard summary requested: start={start_date}, end={end_date}, user={user_id}")
        
        summary = ConversationService.get_dashboard_summary(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        logger.info(f"Dashboard summary retrieved successfully")
        return summary
        
    except Exception as e:
        logger.error(f"Erro ao buscar resumo do dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar resumo: {str(e)}")


@router.get("/detailed")
async def get_dashboard_detailed(
    start_date: Optional[str] = Query(None, description="Data início (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data fim (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="Filtrar por usuário"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    order_by: str = Query("created_at", description="Ordenar por: created_at, message_count, updated_at")
):
    """
    Obter dados detalhados de conversas e mensagens para análise.
    
    **Retorna:**
    - Lista de todas as conversas com:
      - ID, usuário, título
      - Data de criação/atualização
      - Total de mensagens
      - Tokens gastos
      - Modelos usados
      - Conteúdo das mensagens (resumido)
    
    **Filtros disponíveis:**
    - start_date: Data mínima (YYYY-MM-DD)
    - end_date: Data máxima (YYYY-MM-DD)
    - user_id: Usuário específico
    - limit: Pagination limit
    - offset: Pagination offset
    - order_by: Coluna para ordenação
    """
    try:
        logger.info(f"Dashboard detailed requested: start={start_date}, end={end_date}, user={user_id}, limit={limit}, offset={offset}")
        
        detailed = ConversationService.get_dashboard_detailed(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            limit=limit,
            offset=offset,
            order_by=order_by
        )
        
        logger.info(f"Dashboard detailed retrieved successfully: {len(detailed.get('conversations', []))} conversations")
        return detailed
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados detalhados do dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {str(e)}")


@router.get("/export")
async def export_dashboard_data(
    format: str = Query("json", description="Formato: json, csv"),
    start_date: Optional[str] = Query(None, description="Data início (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data fim (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="Filtrar por usuário")
):
    """
    Exportar dados do dashboard em diferentes formatos.
    
    **Formatos suportados:**
    - json: JSON estruturado
    - csv: CSV para Excel/análise
    """
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail=f"Formato não suportado: {format}")
        
        logger.info(f"Dashboard export requested: format={format}, start={start_date}, end={end_date}, user={user_id}")
        
        data = ConversationService.export_dashboard_data(
            format=format,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        logger.info(f"Dashboard data exported successfully in {format} format")
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao exportar dados do dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao exportar dados: {str(e)}")
