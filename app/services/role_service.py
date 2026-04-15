"""Role Service for managing job roles/levels."""
import logging
import json
from typing import List, Dict
from app.core.sqlserver import get_sqlserver_connection

logger = logging.getLogger(__name__)

class RoleService:
    """Service for managing job roles/levels."""

    @staticmethod
    async def create_role(role_name: str) -> Dict:
        """Create a new job role."""
        try:
            sql = get_sqlserver_connection()
            query = "INSERT INTO dim_roles (role_name, is_active) VALUES (?, 1)"
            sql.execute(query, [role_name])
            logger.info(f"Role created: {role_name}")
            return {"role_name": role_name, "is_active": True}
        except Exception as e:
            logger.error(f"Error creating role: {e}")
            raise

    @staticmethod
    async def get_roles(active_only: bool = False, language: str = "pt") -> List[Dict]:
        """
        Get all job roles with optional language translation.
        
        Args:
            active_only: If True, return only active roles
            language: Language code ('pt', 'en', 'es'). Default is 'pt' (Portuguese)
        """
        try:
            sql = get_sqlserver_connection()
            query = "SELECT role_id, role_name, is_active, translations FROM dim_roles"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY role_name"
            results = sql.execute(query)
            
            output = []
            for r in results:
                role_name = r["role_name"]
                
                # Se idioma é Portuguese ou não há traduções, usar o padrão
                if language != "pt":
                    translations_json = r.get("translations", "{}")
                    try:
                        if isinstance(translations_json, str):
                            translations = json.loads(translations_json) if translations_json else {}
                        else:
                            translations = translations_json
                        
                        # Buscar tradução no JSON
                        if language in translations and "role_name" in translations[language]:
                            role_name = translations[language]["role_name"]
                    except (json.JSONDecodeError, TypeError) as je:
                        logger.warning(f"Error parsing translations for role {r['role_id']}: {je}")
                
                output.append({
                    "role_id": r["role_id"],
                    "role_name": role_name,
                    "is_active": r["is_active"]
                })
            
            return output
        except Exception as e:
            logger.error(f"Error fetching roles: {e}")
            raise

    @staticmethod
    async def update_role(role_id: int, role_name: str) -> Dict:
        """Update a job role."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_roles SET role_name = ? WHERE role_id = ?"
            sql.execute(query, [role_name, role_id])
            logger.info(f"Role updated: {role_id}")
            return {"role_id": role_id, "role_name": role_name}
        except Exception as e:
            logger.error(f"Error updating role: {e}")
            raise

    @staticmethod
    async def enable_role(role_id: int) -> Dict:
        """Enable a job role."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_roles SET is_active = 1 WHERE role_id = ?"
            sql.execute(query, [role_id])
            logger.info(f"Role enabled: {role_id}")
            return {"role_id": role_id, "is_active": True}
        except Exception as e:
            logger.error(f"Error enabling role: {e}")
            raise

    @staticmethod
    async def disable_role(role_id: int) -> Dict:
        """Disable a job role."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_roles SET is_active = 0 WHERE role_id = ?"
            sql.execute(query, [role_id])
            logger.info(f"Role disabled: {role_id}")
            return {"role_id": role_id, "is_active": False}
        except Exception as e:
            logger.error(f"Error disabling role: {e}")
            raise

    @staticmethod
    async def get_role_by_id(role_id: int) -> Dict:
        """Get a specific role by ID."""
        try:
            sql = get_sqlserver_connection()
            query = "SELECT role_id, role_name, is_active FROM dim_roles WHERE role_id = ?"
            result = sql.execute_single(query, [role_id])
            if result:
                return {"role_id": result["role_id"], "role_name": result["role_name"], "is_active": result["is_active"]}
            else:
                raise ValueError(f"Role {role_id} not found")
        except Exception as e:
            logger.error(f"Error fetching role: {e}")
            raise

    @staticmethod
    async def delete_role(role_id: int) -> Dict:
        """Delete a job role."""
        try:
            sql = get_sqlserver_connection()
            query = "DELETE FROM dim_roles WHERE role_id = ?"
            sql.execute(query, [role_id])
            logger.info(f"Role deleted: {role_id}")
            return {"role_id": role_id, "deleted": True}
        except Exception as e:
            logger.error(f"Error deleting role: {e}")
            raise
