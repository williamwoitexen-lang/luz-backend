"""
Serviço para buscar informações de usuários no Microsoft Graph.

Permite buscar por ID ou nome, com cache Redis (opcional).
"""

import logging
import os
try:
    import redis
    REDIS_AVAILABLE_IMPORT = True
except ImportError:
    REDIS_AVAILABLE_IMPORT = False

from typing import Optional, Dict, Any
import requests
from app.core.config import KeyVaultConfig

logger = logging.getLogger(__name__)

# Redis para cache (com fallback)
redis_client = None
REDIS_AVAILABLE = False

if REDIS_AVAILABLE_IMPORT:
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True,
            socket_connect_timeout=2
        )
        redis_client.ping()
        REDIS_AVAILABLE = True
        logger.info("[GraphService] ✅ Redis connected (shared cache enabled)")
    except Exception as e:
        logger.warning(f"[GraphService] ⚠️  Redis unavailable ({e}), queries will not be cached")
        redis_client = None
        REDIS_AVAILABLE = False
else:
    logger.warning("[GraphService] ⚠️  Redis package not installed, queries will not be cached")


class GraphUserService:
    """Serviço para buscar dados de usuários no Microsoft Graph."""
    
    GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
    CACHE_TTL = 86400  # 24 horas
    
    @staticmethod
    def get_graph_token() -> Optional[str]:
        """
        Obter token de acesso para Microsoft Graph.
        
        Usa credenciais de aplicação (não de usuário).
        """
        try:
            from msal import ConfidentialClientApplication
            
            app = ConfidentialClientApplication(
                client_id=KeyVaultConfig.get_azure_client_id(),
                client_credential=KeyVaultConfig.get_azure_client_secret(),
                authority=f"https://login.microsoftonline.com/{KeyVaultConfig.get_azure_tenant_id()}"
            )
            
            result = app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if "access_token" in result:
                return result["access_token"]
            else:
                logger.error(f"[Graph] Erro ao obter token: {result}")
                return None
                
        except Exception as e:
            logger.error(f"[Graph] Erro ao gerar token: {e}")
            return None
    
    @staticmethod
    def search_user_by_name(display_name: str) -> Optional[Dict[str, Any]]:
        """
        Buscar usuário pelo nome no Graph.
        
        Args:
            display_name: Nome completo do usuário (ex: "Adele Vance")
        
        Returns:
            Dict com informações do usuário ou None se não encontrar
        """
        cache_key = f"graph:user:name:{display_name.lower()}"
        
        # Tentar cache primeiro
        if REDIS_AVAILABLE:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    import json
                    logger.debug(f"[Graph] Cache HIT para nome: {display_name}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"[Graph] Erro ao acessar cache: {e}")
        
        try:
            token = GraphUserService.get_graph_token()
            if not token:
                logger.error("[Graph] Não conseguiu token de acesso")
                return None
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Buscar pelo displayName
            url = f"{GraphUserService.GRAPH_API_URL}/users"
            params = {
                "$filter": f"displayName eq '{display_name}'",
                "$select": "id,displayName,givenName,surname,mail,preferredLanguage,jobTitle"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("value", [])
                
                if users:
                    user = users[0]
                    logger.info(f"[Graph] Usuário encontrado pelo nome: {display_name} → {user.get('id')}")
                    
                    # Cachear resultado
                    if REDIS_AVAILABLE:
                        import json
                        redis_client.setex(cache_key, GraphUserService.CACHE_TTL, json.dumps(user))
                    
                    return user
                else:
                    logger.warning(f"[Graph] Nenhum usuário encontrado com nome: {display_name}")
                    return None
            else:
                logger.error(f"[Graph] Erro ao buscar usuário: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"[Graph] Erro na busca por nome: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Buscar usuário pelo ID (Object ID do Azure AD).
        
        Args:
            user_id: Object ID do usuário no Azure AD
        
        Returns:
            Dict com informações do usuário ou None
        """
        cache_key = f"graph:user:id:{user_id}"
        
        # Tentar cache primeiro
        if REDIS_AVAILABLE:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    import json
                    logger.debug(f"[Graph] Cache HIT para ID: {user_id}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"[Graph] Erro ao acessar cache: {e}")
        
        try:
            token = GraphUserService.get_graph_token()
            if not token:
                logger.error("[Graph] Não conseguiu token de acesso")
                return None
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            url = f"{GraphUserService.GRAPH_API_URL}/users/{user_id}"
            params = {
                "$select": "id,displayName,givenName,surname,mail,preferredLanguage,jobTitle"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                user = response.json()
                logger.info(f"[Graph] Usuário encontrado por ID: {user_id}")
                
                # Cachear resultado
                if REDIS_AVAILABLE:
                    import json
                    redis_client.setex(cache_key, GraphUserService.CACHE_TTL, json.dumps(user))
                
                return user
            else:
                logger.error(f"[Graph] Erro ao buscar usuário por ID: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"[Graph] Erro na busca por ID: {e}")
            return None
    
    @staticmethod
    def get_user_display_name(user_id: str) -> str:
        """
        Obter nome de exibição do usuário pelo ID.
        
        Útil para exibir quem criou um documento.
        
        Args:
            user_id: Object ID do usuário
        
        Returns:
            Nome de exibição ou "<Usuário Desconhecido>" se não encontrar
        """
        user = GraphUserService.get_user_by_id(user_id)
        
        if user:
            return user.get("displayName", "Desconhecido")
        else:
            logger.warning(f"[Graph] Não conseguiu nome para ID: {user_id}")
            return "Usuário Desconhecido"
    
    @staticmethod
    def get_user_email(user_id: str) -> Optional[str]:
        """
        Obter email do usuário pelo ID.
        
        Args:
            user_id: Object ID do usuário
        
        Returns:
            Email ou None
        """
        user = GraphUserService.get_user_by_id(user_id)
        return user.get("mail") if user else None
    
    @staticmethod
    def get_users_by_ids(user_ids: list) -> Dict[str, str]:
        """
        Buscar múltiplos usuários pelo ID em uma única chamada (batch).
        
        Muito mais rápido que fazer N chamadas individuais.
        Cacheia resultado em Redis por 24h.
        
        Args:
            user_ids: Lista de Object IDs dos usuários
        
        Returns:
            Dict {user_id: display_name} (desconsidera nomes legados)
            Exemplo: {
                "1ac770a2-eaa7-4200-97f8-043b83861c07": "Willian Woixtexen",
                "9d40e8a7-eaa7-4200-97f8-abcdef123456": "Maria Silva"
            }
        """
        if not user_ids:
            return {}
        
        import re
        import json
        
        result = {}
        
        # Filtrar apenas UUIDs válidos (pular nomes legados)
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        valid_uuids = [uid for uid in user_ids if re.match(uuid_pattern, str(uid).lower())]
        
        if not valid_uuids:
            logger.debug("[Graph] Nenhum UUID válido para batch lookup")
            return {}
        
        # Tentar recuperar do cache
        if REDIS_AVAILABLE:
            cache_key = f"graph:batch:{','.join(sorted(valid_uuids))}"
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"[Graph] Batch hit cache: {len(valid_uuids)} usuários")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"[Graph] Erro ao ler cache batch: {e}")
        
        try:
            token = GraphUserService.get_graph_token()
            if not token:
                logger.error("[Graph] Não conseguiu token de acesso para batch")
                return {}
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Fazer requisição batch: GET /users?$filter=id in ('id1','id2',...)
            ids_quoted = ",".join([f"'{uid}'" for uid in valid_uuids])
            ids_filter = f"id in ({ids_quoted})"
            url = f"{GraphUserService.GRAPH_API_URL}/users?$filter={ids_filter}&$select=id,displayName"
            
            logger.debug(f"[Graph] Batch lookup para {len(valid_uuids)} usuários")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("value", [])
                
                for user in users:
                    user_id = user.get("id")
                    display_name = user.get("displayName", "Desconhecido")
                    if user_id:
                        result[user_id] = display_name
                        logger.debug(f"[Graph] Resolvido batch: {user_id[:8]}... → {display_name}")
                
                logger.info(f"[Graph] Batch lookup completado: {len(result)}/{len(valid_uuids)} usuários encontrados")
                
                # Cachear resultado
                if REDIS_AVAILABLE and result:
                    try:
                        cache_key = f"graph:batch:{','.join(sorted(valid_uuids))}"
                        redis_client.setex(cache_key, GraphUserService.CACHE_TTL, json.dumps(result))
                    except Exception as e:
                        logger.warning(f"[Graph] Erro ao cachear batch: {e}")
            else:
                logger.error(f"[Graph] Erro no batch lookup: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[Graph] Erro ao fazer batch lookup: {e}")
        
        return result
    
    @staticmethod
    def invalidate_cache(user_id: str = None, display_name: str = None) -> None:
        """
        Invalidar cache Redis para um usuário.
        
        Args:
            user_id: ID do usuário (para invalidar por ID)
            display_name: Nome do usuário (para invalidar por nome)
        """
        if not REDIS_AVAILABLE:
            return
        
        try:
            if user_id:
                key = f"graph:user:id:{user_id}"
                redis_client.delete(key)
                logger.info(f"[Graph] Cache invalidado para ID: {user_id}")
            
            if display_name:
                key = f"graph:user:name:{display_name.lower()}"
                redis_client.delete(key)
                logger.info(f"[Graph] Cache invalidado para nome: {display_name}")
                
        except Exception as e:
            logger.warning(f"[Graph] Erro ao invalidar cache: {e}")


    @staticmethod
    def search_users_by_display_name_prefix(prefix: str, account_enabled: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """
        Buscar usuarios por prefixo do displayName no Graph.
        
        Args:
            prefix: prefixo do displayName
            account_enabled: filtrar por status (True/False/None para sem filtro)
        """
        try:
            token = GraphUserService.get_graph_token()
            if not token:
                return None

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            url = f"{GraphUserService.GRAPH_API_URL}/users"
            
            # Construir filtro dinamicamente
            filter_expr = f"startswith(displayName,'{prefix}')"
            if account_enabled is not None:
                enabled_str = "true" if account_enabled else "false"
                filter_expr += f" and accountEnabled eq {enabled_str}"
            
            params = {
                "$select": "displayName,mail,id,country,city,jobTitle,accountEnabled",
                "$filter": filter_expr
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            logger.error(f"[Graph] Erro ao buscar usuarios: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"[Graph] Erro na busca por prefixo: {e}")
            return None