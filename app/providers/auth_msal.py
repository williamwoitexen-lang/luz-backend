"""
Azure Entra ID (OAuth2) Authentication Provider with MSAL

Handles OAuth2 flow with Azure Entra ID using Microsoft Authentication Library (MSAL):
- Login redirect to Azure AD (authorization URL)
- Token exchange via MSAL
- Token validation
- Token refresh
- Graph API access
- Logout

MSAL benefits:
- Official Microsoft library
- Secure token caching
- Automatic token refresh
- Better security practices
"""

import os
import jwt
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException
from jwt import PyJWKClient
from dotenv import load_dotenv
from msal import ConfidentialClientApplication

logger = logging.getLogger(__name__)

load_dotenv()


class EntraIDAuthMSAL:
    """Azure Entra ID Authentication Handler using MSAL"""

    def __init__(self):
        self.tenant_id = os.environ.get("AZURE_TENANT_ID", "")
        self.client_id = os.environ.get("AZURE_CLIENT_ID", "")
        self.client_secret = os.environ.get("", "")
        
        # Detectar ambiente de APP_ENV (sempre em maiúsculas)
        app_env = os.environ.get("APP_ENV", "dev").upper()
        is_production = app_env == "PROD"
        
        # Base URLs
        backend_base_url = os.environ.get("APP_BASE_URL_BACKEND", "http://localhost:8000").rstrip("/")
        frontend_base_url = os.environ.get("APP_BASE_URL_FRONTEND", "http://localhost:4200").rstrip("/")
        
        # Redirect URI condicional por ambiente
        if is_production:
            # PROD: usa frontend proxy
            self.redirect_uri = f"{frontend_base_url}/api/getatoken"
            logger.info(f"[AUTH] PRODUCTION mode (APP_ENV={app_env}): redirect_uri = {frontend_base_url}/api/getatoken")
        else:
            # DEV: usa backend direto
            self.redirect_uri = f"{backend_base_url}/api/v1/getatoken"
            logger.info(f"[AUTH] DEVELOPMENT mode (APP_ENV={app_env}): redirect_uri = {backend_base_url}/api/v1/getatoken")
        
        self.frontend_dashboard_url = f"{frontend_base_url}/app/dashboard"
        self.frontend_chat_url = f"{frontend_base_url}/app/chat"
        self.frontend_logout_redirect_url = f"{frontend_base_url}/login"

        # MSAL Client Application - ConfidentialClientApplication para backend seguro
        # Requer client_secret para token acquisition
        self.msal_app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            token_cache=None  # Token cache pode ser implementado depois
        )

        # JWT validation
        if self.tenant_id and self.client_id:
            self.jwks_url = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
            self.jwks_client = PyJWKClient(self.jwks_url)
        else:
            self.jwks_client = None

    def get_authorize_url(self) -> str:
        """Get Azure AD authorization URL for login redirect using MSAL"""
        if not self.tenant_id or not self.client_id:
            raise ValueError("AZURE_TENANT_ID and AZURE_CLIENT_ID must be configured")

        # MSAL gera a URL de autorização
        # Nota: MSAL adiciona automaticamente openid, profile, offline_access
        # Não usar scopes reservados aqui, apenas o Graph scope
        auth_url = self.msal_app.get_authorization_request_url(
            scopes=[
                "https://graph.microsoft.com/User.Read"
            ],
            redirect_uri=self.redirect_uri
        )
        
        logger.info(f"[MSAL] Authorization URL generated for tenant {self.tenant_id}")
        return auth_url

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens using MSAL
        
        Returns:
            {
                "user_id": "oid-from-token",
                "access_token": "id_token-for-app-auth",
                "graph_access_token": "access_token-for-graph",
                "token_type": "Bearer",
                "expires_in": seconds,
                "refresh_token": "refresh-token"
            }
        """
        if not self.tenant_id or not self.client_id:
            raise ValueError("Azure credentials not configured")

        try:
            logger.info(f"[MSAL] Exchanging authorization code for tokens...")
            
            # MSAL adquire token via código de autorização
            # Nota: MSAL adiciona automaticamente openid, profile, offline_access
            # Não usar scopes reservados aqui, apenas o Graph scope
            result = self.msal_app.acquire_token_by_authorization_code(
                code=code,
                scopes=[
                    "https://graph.microsoft.com/User.Read"
                ],
                redirect_uri=self.redirect_uri
            )
            
            if "error" in result:
                error_msg = result.get("error_description", result.get("error"))
                logger.error(f"[MSAL] Token acquisition failed: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "token_acquisition_failed",
                        "details": error_msg
                    }
                )
            
            id_token = result.get("id_token")
            graph_access_token = result.get("access_token")  # Token real para Graph
            refresh_token = result.get("refresh_token")
            expires_in = result.get("expires_in")
            
            if not id_token:
                logger.error("[MSAL] No id_token in result")
                raise HTTPException(
                    status_code=500,
                    detail="No id_token received from Azure"
                )
            
            # Decodificar id_token para extrair user_id (oid)
            try:
                decoded_id_token = jwt.decode(
                    id_token,
                    options={"verify_signature": False}  # Já foi verificado pelo MSAL
                )
                user_id = decoded_id_token.get("oid")
            except Exception as e:
                logger.error(f"[MSAL] Error decoding id_token: {e}")
                user_id = None
            
            logger.info(f"[MSAL] Token exchange successful for user {user_id}")
            
            return {
                "user_id": user_id,
                "access_token": id_token,  # Para autenticação na app
                "graph_access_token": graph_access_token,  # Para chamar Graph
                "token_type": result.get("token_type", "Bearer"),
                "expires_in": expires_in,
                "refresh_token": refresh_token
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[MSAL] Exception during token exchange: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "msal_exchange_error",
                    "details": str(e)
                }
            )

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token using MSAL
        
        Args:
            refresh_token: Refresh token from previous login
            
        Returns:
            New token response or None if refresh fails
        """
        try:
            logger.info("[MSAL] Attempting to refresh token...")
            
            result = self.msal_app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=[
                    "https://graph.microsoft.com/User.Read"
                ]
            )
            
            if "error" in result:
                logger.warning(f"[MSAL] Token refresh failed: {result.get('error_description')}")
                return None
            
            logger.info("[MSAL] Token successfully refreshed")
            return result
            
        except Exception as e:
            logger.error(f"[MSAL] Error refreshing token: {e}")
            return None

    def validate_token(self, token: Optional[str]) -> Optional[Dict]:
        """Validate JWT token from Azure AD"""
        if not token:
            logger.warning("validate_token: token is None or empty")
            return None
        
        if not self.jwks_client:
            logger.error(f"validate_token: jwks_client is None")
            return None

        try:
            logger.info(f"validate_token: Validating token...")
            signing_key = self.jwks_client.get_signing_key_from_jwt(token).key

            # Aceitar ambas as versões (v1.0 e v2.0) do issuer do Azure AD
            valid_issuers = [
                f"https://sts.windows.net/{self.tenant_id}/",
                f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
            ]
            
            decoded = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=valid_issuers
            )
            logger.info(f"validate_token: SUCCESS - email={decoded.get('email')}")
            return decoded

        except Exception as e:
            logger.error(f"Token validation failed: {type(e).__name__}: {e}")
            return None

    def get_logout_url(self) -> str:
        """Get Azure AD logout URL"""
        if not self.tenant_id:
            raise ValueError("AZURE_TENANT_ID must be configured")

        return (
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/logout"
            f"?post_logout_redirect_uri={self.frontend_logout_redirect_url}"
        )

    def get_user_info_from_token(self, decoded_token: Dict) -> Optional[Dict]:
        """
        Extract user information from decoded token
        """
        if not decoded_token:
            logger.warning("get_user_info_from_token: decoded_token is None")
            return None
        
        try:
            user_info = {
                "email": decoded_token.get("email") or decoded_token.get("upn"),
                "displayName": decoded_token.get("name"),
                "oid": decoded_token.get("oid"),
                "user_id": decoded_token.get("oid"),
                "roles": decoded_token.get("roles", []),
                "given_name": decoded_token.get("given_name"),
                "family_name": decoded_token.get("family_name"),
                "country": decoded_token.get("country") or decoded_token.get("ctry"),
                "city": decoded_token.get("city"),
                "postalCode": decoded_token.get("postalCode"),
                "streetAddress": decoded_token.get("streetAddress"),
                "state": decoded_token.get("state"),
            }
            
            logger.info(f"get_user_info_from_token: User info for {user_info.get('email')}")
            return user_info

        except Exception as e:
            logger.error(f"get_user_info_from_token: Error: {e}")
            return None


# Global instance
_auth_instance_msal = None


def get_auth_msal() -> EntraIDAuthMSAL:
    """Get or create auth instance with MSAL"""
    global _auth_instance_msal
    if _auth_instance_msal is None:
        _auth_instance_msal = EntraIDAuthMSAL()
    return _auth_instance_msal
