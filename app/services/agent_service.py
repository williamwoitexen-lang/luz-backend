"""
Service para gerenciar agentes permitidos (guardrail).
"""
import logging
from typing import List, Optional, Dict, Any
from app.core.sqlserver import get_sqlserver_connection

logger = logging.getLogger(__name__)


class AgentService:
    """Service para validar e listar agentes permitidos."""
    
    @staticmethod
    def get_allowed_agents() -> List[Dict[str, Any]]:
        """
        Obter lista de agentes permitidos.
        
        Returns:
            Lista de dicts com dados dos agentes
        """
        try:
            sql = get_sqlserver_connection()
            query = """
            SELECT agent_id, code, name, description, is_active, created_at
            FROM allowed_agents
            WHERE is_active = 1
            ORDER BY code
            """
            rows = sql.execute(query, ())
            agents = [dict(r) for r in rows] if rows else []
            logger.debug(f"[AgentService] Agentes permitidos: {[a['code'] for a in agents]}")
            return agents
            
        except Exception as e:
            logger.error(f"[AgentService] Erro ao buscar agentes: {e}")
            raise
    
    @staticmethod
    def is_agent_valid(agente: str) -> bool:
        """
        Validar se agente é permitido.
        
        Args:
            agente: Código do agente (ex: 'LUZ', 'IGP', 'SMART')
            
        Returns:
            True se agente é válido, False caso contrário
        """
        try:
            sql = get_sqlserver_connection()
            query = """
            SELECT agent_id FROM allowed_agents
            WHERE code = ? AND is_active = 1
            """
            result = sql.execute_single(query, (agente,))
            is_valid = result is not None
            logger.debug(f"[AgentService] Agente '{agente}' válido: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"[AgentService] Erro ao validar agente: {e}")
            raise
    
    @staticmethod
    def validate_agent_or_raise(agente: str) -> None:
        """
        Validar agente e lançar exceção se inválido.
        
        Args:
            agente: Código do agente
            
        Raises:
            ValueError: Se agente não é permitido
        """
        if not AgentService.is_agent_valid(agente):
            allowed = AgentService.get_allowed_agents()
            allowed_codes = [a['code'] for a in allowed]
            raise ValueError(
                f"Agente '{agente}' não é permitido. Agentes válidos: {', '.join(allowed_codes)}"
            )
    
    @staticmethod
    def is_agent_valid_by_id(agent_id: int) -> bool:
        """
        Validar se agent_id é permitido.
        
        Args:
            agent_id: ID do agente (1, 2, 3)
            
        Returns:
            True se agent_id é válido, False caso contrário
        """
        try:
            sql = get_sqlserver_connection()
            query = """
            SELECT agent_id FROM allowed_agents
            WHERE agent_id = ? AND is_active = 1
            """
            result = sql.execute_single(query, (agent_id,))
            is_valid = result is not None
            logger.debug(f"[AgentService] Agent ID {agent_id} válido: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"[AgentService] Erro ao validar agent_id: {e}")
            raise
    
    @staticmethod
    def get_agent_by_id(agent_id: int) -> Optional[Dict[str, Any]]:
        """
        Obter agente por ID.
        
        Args:
            agent_id: ID do agente
            
        Returns:
            Dict com dados do agente ou None se não encontrado
        """
        try:
            sql = get_sqlserver_connection()
            query = """
            SELECT agent_id, code, name, description, is_active, created_at
            FROM allowed_agents
            WHERE agent_id = ? AND is_active = 1
            """
            result = sql.execute_single(query, (agent_id,))
            if result:
                return dict(result)
            logger.debug(f"[AgentService] Agent ID {agent_id} não encontrado")
            return None
            
        except Exception as e:
            logger.error(f"[AgentService] Erro ao buscar agent: {e}")
            raise
