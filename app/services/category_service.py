"""Category Service for managing benefit categories."""
import logging
import json
from typing import List, Dict
from app.core.sqlserver import get_sqlserver_connection

logger = logging.getLogger(__name__)

class CategoryService:
    """Service for managing benefit categories."""

    @staticmethod
    async def create_category(category_name: str, description: str = None) -> Dict:
        """Create a new benefit category."""
        try:
            sql = get_sqlserver_connection()
            query = "INSERT INTO dim_categories (category_name, description, is_active) VALUES (?, ?, 1)"
            sql.execute(query, [category_name, description])
            logger.info(f"Category created: {category_name}")
            return {"category_name": category_name, "description": description, "is_active": True}
        except Exception as e:
            logger.error(f"Error creating category: {e}")
            raise

    @staticmethod
    async def get_categories(active_only: bool = False, language: str = "pt") -> List[Dict]:
        """
        Get all benefit categories with optional language translation.
        
        Args:
            active_only: If True, return only active categories
            language: Language code ('pt', 'en', 'es'). Default is 'pt' (Portuguese)
        """
        try:
            sql = get_sqlserver_connection()
            query = "SELECT category_id, category_name, description, is_active, translations FROM dim_categories"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY category_name"
            results = sql.execute(query)
            
            output = []
            for r in results:
                category_name = r["category_name"]
                description = r["description"]
                
                # Se idioma é Portuguese ou não há traduções, usar o padrão
                if language != "pt":
                    translations_json = r.get("translations", "{}")
                    try:
                        if isinstance(translations_json, str):
                            translations = json.loads(translations_json) if translations_json else {}
                        else:
                            translations = translations_json
                        
                        # Buscar tradução no JSON
                        if language in translations:
                            if "category_name" in translations[language]:
                                category_name = translations[language]["category_name"]
                            if "description" in translations[language]:
                                description = translations[language]["description"]
                    except (json.JSONDecodeError, TypeError) as je:
                        logger.warning(f"Error parsing translations for category {r['category_id']}: {je}")
                
                output.append({
                    "category_id": r["category_id"],
                    "category_name": category_name,
                    "description": description,
                    "is_active": r["is_active"]
                })
            
            return output
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            raise

    @staticmethod
    async def update_category(category_id: int, category_name: str, description: str = None) -> Dict:
        """Update a benefit category."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_categories SET category_name = ?, description = ?, updated_at = GETDATE() WHERE category_id = ?"
            sql.execute(query, [category_name, description, category_id])
            logger.info(f"Category updated: {category_id}")
            return {"category_id": category_id, "category_name": category_name, "description": description}
        except Exception as e:
            logger.error(f"Error updating category: {e}")
            raise

    @staticmethod
    async def enable_category(category_id: int) -> Dict:
        """Enable a category."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_categories SET is_active = 1, updated_at = GETDATE() WHERE category_id = ?"
            sql.execute(query, [category_id])
            logger.info(f"Category enabled: {category_id}")
            return {"category_id": category_id, "is_active": True}
        except Exception as e:
            logger.error(f"Error enabling category: {e}")
            raise

    @staticmethod
    async def disable_category(category_id: int) -> Dict:
        """Disable a category."""
        try:
            sql = get_sqlserver_connection()
            query = "UPDATE dim_categories SET is_active = 0, updated_at = GETDATE() WHERE category_id = ?"
            sql.execute(query, [category_id])
            logger.info(f"Category disabled: {category_id}")
            return {"category_id": category_id, "is_active": False}
        except Exception as e:
            logger.error(f"Error disabling category: {e}")
            raise

    @staticmethod
    async def get_category_by_id(category_id: int) -> Dict:
        """Get a specific category by ID."""
        try:
            sql = get_sqlserver_connection()
            query = "SELECT category_id, category_name, description, is_active FROM dim_categories WHERE category_id = ?"
            result = sql.execute_single(query, [category_id])
            if result:
                return {"category_id": result["category_id"], "category_name": result["category_name"], "description": result["description"], "is_active": result["is_active"]}
            else:
                raise ValueError(f"Category {category_id} not found")
        except Exception as e:
            logger.error(f"Error fetching category: {e}")
            raise

    @staticmethod
    async def delete_category(category_id: int) -> Dict:
        """Delete a category."""
        try:
            sql = get_sqlserver_connection()
            query = "DELETE FROM dim_categories WHERE category_id = ?"
            sql.execute(query, [category_id])
            logger.info(f"Category deleted: {category_id}")
            return {"category_id": category_id, "deleted": True}
        except Exception as e:
            logger.error(f"Error deleting category: {e}")
            raise
