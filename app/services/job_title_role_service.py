"""
Service para gerenciar mapeamento de Job Title → Role
"""
import logging
from typing import Optional
from app.core.sqlserver import get_sqlserver_connection

logger = logging.getLogger(__name__)


class JobTitleRoleService:
    """Service para buscar role a partir de job_title"""
    
    @staticmethod
    def get_role_by_job_title(job_title: str) -> Optional[dict]:
        """
        Buscar role e role_id a partir de job_title.
        
        Args:
            job_title: Título do cargo (ex: "SVP Corporate Communications")
        
        Returns:
            Dict com 'role' e 'role_id' ou None se não encontrar
        """
        if not job_title:
            return None
        
        try:
            sql = get_sqlserver_connection()
            
            query = """
            SELECT role, role_id
            FROM dim_job_title_roles 
            WHERE job_title = ? AND is_active = 1
            """
            
            results = sql.execute(query, [job_title])
            
            if results and len(results) > 0:
                return {
                    'role': results[0].get('role'),
                    'role_id': results[0].get('role_id')
                }
            
            logger.debug(f"Job title não encontrado no mapeamento: {job_title}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar role para job_title '{job_title}': {e}")
            return None
    
    @staticmethod
    def list_all_mappings(limit: int = 100) -> list:
        """
        Listar todos os mapeamentos de job_title → role.
        
        Args:
            limit: Limite de resultados
        
        Returns:
            Lista de dicts com job_title e role
        """
        try:
            sql = get_sqlserver_connection()
            
            query = """
            SELECT TOP (?) job_title, role 
            FROM dim_job_title_roles 
            WHERE is_active = 1
            ORDER BY job_title
            """
            
            results = sql.execute(query, [limit])
            
            mappings = []
            for row in results:
                mappings.append({
                    'job_title': row.get('job_title'),
                    'role': row.get('role')
                })
            
            logger.info(f"Retornados {len(mappings)} mapeamentos de job_title")
            return mappings
            
        except Exception as e:
            logger.error(f"Erro ao listar mapeamentos: {e}")
            return []
    
    @staticmethod
    def add_mapping(job_title: str, role: str) -> bool:
        """
        Adicionar novo mapeamento de job_title → role.
        
        Args:
            job_title: Título do cargo
            role: Role mapeado
        
        Returns:
            True se adicionado com sucesso, False caso contrário
        """
        if not job_title or not role:
            logger.warning("job_title e role são obrigatórios")
            return False
        
        try:
            sql = get_sqlserver_connection()
            
            # Verificar se já existe
            check_query = "SELECT COUNT(*) as cnt FROM dim_job_title_roles WHERE job_title = ?"
            check_results = sql.execute(check_query, [job_title])
            if check_results and check_results[0].get('cnt', 0) > 0:
                logger.warning(f"Mapeamento para '{job_title}' já existe")
                return False
            
            # Inserir
            insert_query = """
            INSERT INTO dim_job_title_roles (job_title, role, is_active) 
            VALUES (?, ?, 1)
            """
            sql.execute(insert_query, [job_title, role])
            logger.info(f"Mapeamento adicionado: '{job_title}' → '{role}'")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar mapeamento: {e}")
            return False
