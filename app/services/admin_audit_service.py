"""
Service para registrar auditoria de alterações em admins.
Mantém histórico completo de todas as mudanças.
"""
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.core.sqlserver import get_sqlserver_connection

logger = logging.getLogger(__name__)


class AdminAuditService:
    """Serviço para registrar e consultar histórico de alterações de admins."""
    
    @staticmethod
    def log_create(admin_id: str, admin_data: Dict[str, Any], created_by: str, 
                   ip_address: Optional[str] = None) -> bool:
        """
        Registrar criação de admin.
        
        Args:
            admin_id: ID do admin criado
            admin_data: Dados do admin (name, email, job_title, etc)
            created_by: Nome do usuário que criou
            ip_address: IP do cliente (opcional)
        
        Returns:
            True se registrado com sucesso
        """
        try:
            sql = get_sqlserver_connection()
            now = datetime.utcnow()
            
            # Preparar dados para JSON
            new_values = {
                "email": admin_data.get("email"),
                "name": admin_data.get("name"),
                "job_title": admin_data.get("job_title"),
                "city": admin_data.get("city"),
                "agent_id": admin_data.get("agent_id"),
                "feature_ids": admin_data.get("feature_ids", []),
                "is_active": admin_data.get("is_active", True)
            }
            
            query = """
            INSERT INTO admin_audit_log (admin_id, action, changed_fields, old_values, new_values, changed_by, changed_at, ip_address, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            sql.execute(query, (
                admin_id,
                "CREATE",
                json.dumps(list(new_values.keys())),  # Todos os campos foram alterados (criação)
                json.dumps({}),  # Sem valores antigos na criação
                json.dumps(new_values),
                created_by,
                now,
                ip_address,
                f"Admin criado: {admin_data.get('email')}"
            ))
            
            logger.info(f"✅ Auditoria registrada - CREATE admin {admin_id} por {created_by}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar auditoria de CREATE: {e}")
            return False
    
    
    @staticmethod
    def log_update(admin_id: str, old_values: Dict[str, Any], new_values: Dict[str, Any],
                   updated_by: str, ip_address: Optional[str] = None) -> bool:
        """
        Registrar atualização de admin.
        
        Args:
            admin_id: ID do admin atualizado
            old_values: Valores antigos (antes da atualização)
            new_values: Valores novos (depois da atualização)
            updated_by: Nome do usuário que atualizou
            ip_address: IP do cliente (opcional)
        
        Returns:
            True se registrado com sucesso
        """
        try:
            sql = get_sqlserver_connection()
            now = datetime.utcnow()
            
            # Identificar quais campos foram alterados
            changed_fields = []
            for key in set(list(old_values.keys()) + list(new_values.keys())):
                old_val = old_values.get(key)
                new_val = new_values.get(key)
                if old_val != new_val:
                    changed_fields.append(key)
            
            if not changed_fields:
                logger.debug(f"Nenhum campo foi alterado para admin {admin_id}")
                return True
            
            query = """
            INSERT INTO admin_audit_log (admin_id, action, changed_fields, old_values, new_values, changed_by, changed_at, ip_address, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            sql.execute(query, (
                admin_id,
                "UPDATE",
                json.dumps(changed_fields),
                json.dumps({k: old_values.get(k) for k in changed_fields}),
                json.dumps({k: new_values.get(k) for k in changed_fields}),
                updated_by,
                now,
                ip_address,
                f"Campos alterados: {', '.join(changed_fields)}"
            ))
            
            logger.info(f"✅ Auditoria registrada - UPDATE admin {admin_id} por {updated_by} (campos: {', '.join(changed_fields)})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar auditoria de UPDATE: {e}")
            return False
    
    
    @staticmethod
    def log_delete(admin_id: str, admin_data: Dict[str, Any], deleted_by: str,
                   ip_address: Optional[str] = None) -> bool:
        """
        Registrar deleção (soft delete) de admin.
        
        Args:
            admin_id: ID do admin deletado
            admin_data: Dados do admin antes da deleção
            deleted_by: Nome do usuário que deletou
            ip_address: IP do cliente (opcional)
        
        Returns:
            True se registrado com sucesso
        """
        try:
            sql = get_sqlserver_connection()
            now = datetime.utcnow()
            
            # Preparar dados para JSON
            old_values = {
                "email": admin_data.get("email"),
                "name": admin_data.get("name"),
                "job_title": admin_data.get("job_title"),
                "city": admin_data.get("city"),
                "agent_id": admin_data.get("agent_id"),
                "is_active": admin_data.get("is_active", True)
            }
            
            new_values = {
                "is_active": False  # Admin desativado
            }
            
            query = """
            INSERT INTO admin_audit_log (admin_id, action, changed_fields, old_values, new_values, changed_by, changed_at, ip_address, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            sql.execute(query, (
                admin_id,
                "DELETE",
                json.dumps(["is_active"]),
                json.dumps(old_values),
                json.dumps(new_values),
                deleted_by,
                now,
                ip_address,
                f"Admin desativado: {admin_data.get('email')}"
            ))
            
            logger.info(f"✅ Auditoria registrada - DELETE admin {admin_id} por {deleted_by}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar auditoria de DELETE: {e}")
            return False
    
    
    @staticmethod
    def get_admin_audit_history(admin_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Obter histórico completo de alterações de um admin.
        
        Args:
            admin_id: ID do admin
            limit: Máximo de registros
            offset: Offset para paginação
        
        Returns:
            Dict com 'logs' (list) e 'total' (int)
        """
        try:
            sql = get_sqlserver_connection()
            
            # Contar total
            count_query = "SELECT COUNT(*) as total FROM admin_audit_log WHERE admin_id = ?"
            count_result = sql.execute_single(count_query, (admin_id,))
            total = count_result["total"] if count_result else 0
            
            # Buscar logs ordenados por data descendente (mais recentes primeiro)
            query = """
            SELECT 
                log_id,
                admin_id,
                action,
                changed_fields,
                old_values,
                new_values,
                changed_by,
                changed_at,
                ip_address,
                details
            FROM admin_audit_log
            WHERE admin_id = ?
            ORDER BY changed_at DESC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
            """
            
            results = sql.execute(query, (admin_id, offset, limit))
            
            logs = []
            for row in results:
                log_entry = {
                    "log_id": row["log_id"],
                    "admin_id": row["admin_id"],
                    "action": row["action"],
                    "changed_fields": json.loads(row["changed_fields"]) if row["changed_fields"] else [],
                    "old_values": json.loads(row["old_values"]) if row["old_values"] else {},
                    "new_values": json.loads(row["new_values"]) if row["new_values"] else {},
                    "changed_by": row["changed_by"],
                    "changed_at": row["changed_at"],
                    "ip_address": row["ip_address"],
                    "details": row["details"]
                }
                logs.append(log_entry)
            
            logger.info(f"📋 Histórico de auditoria para admin {admin_id}: {len(logs)} registros de {total} total")
            
            return {
                "logs": logs,
                "total": total,
                "admin_id": admin_id
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar histórico de auditoria: {e}")
            raise
    
    
    @staticmethod
    def get_recent_audit_logs(days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obter logs de auditoria dos últimos N dias.
        
        Args:
            days: Número de dias anteriores
            limit: Máximo de registros
        
        Returns:
            Lista de registros de audit
        """
        try:
            sql = get_sqlserver_connection()
            
            query = """
            SELECT TOP (?)
                log_id,
                admin_id,
                action,
                changed_fields,
                old_values,
                new_values,
                changed_by,
                changed_at,
                ip_address,
                details
            FROM admin_audit_log
            WHERE changed_at >= DATEADD(DAY, ?, CAST(GETUTCDATE() AS DATE))
            ORDER BY changed_at DESC
            """
            
            results = sql.execute(query, (limit, -days))
            
            logs = []
            for row in results:
                log_entry = {
                    "log_id": row["log_id"],
                    "admin_id": row["admin_id"],
                    "action": row["action"],
                    "changed_fields": json.loads(row["changed_fields"]) if row["changed_fields"] else [],
                    "old_values": json.loads(row["old_values"]) if row["old_values"] else {},
                    "new_values": json.loads(row["new_values"]) if row["new_values"] else {},
                    "changed_by": row["changed_by"],
                    "changed_at": row["changed_at"],
                    "ip_address": row["ip_address"],
                    "details": row["details"]
                }
                logs.append(log_entry)
            
            logger.info(f"📋 Logs recentes dos últimos {days} dias: {len(logs)} registros")
            
            return logs
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar logs recentes: {e}")
            raise
