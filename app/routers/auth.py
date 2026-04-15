"""
Authentication routes for Entra ID OAuth2 flow

## Fluxo de Autenticação

1. **Usuário clica "Login"** → `/api/v1/login`
2. **Redirect para Azure AD** → Login no Azure
3. **Azure AD redireciona** → `/getAToken?code=...`
4. **Troca de código por token** → Token armazenado em HTTPOnly cookie
5. **Verificação de acesso** → `/api/v1/auth/status`
6. **Logout** → `/api/v1/logout`

## Endpoints

- `GET /api/v1/login` - Iniciar login
- `GET /getAToken?code=...` - Callback do Azure AD
- `GET /api/v1/logout` - Fazer logout
- `GET /api/v1/auth/status` - Verificar status
- `GET /api/v1/me/role` - Obter role do usuário

Handles:
- /api/v1/login - Redirect to Azure AD
- /getAToken - Token exchange callback
- /api/v1/logout - Logout
- /api/v1/auth/status - Check authentication status
"""

from fastapi import APIRouter, Cookie, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from app.providers.auth_msal import get_auth_msal
from app.providers.dependencies import get_current_user, get_current_user_with_graph
from app.providers.graph_client import get_user_profile_extended, get_user_photo
from app.services.job_title_role_service import JobTitleRoleService
from app.services.user_preference_service import UserPreferenceService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["auth"])


# ==================== Models ====================


# ==================== Endpoints ====================


@router.get("/login", summary="Iniciar login com Azure AD", description="Redireciona para Azure AD para autenticação")
def login():
    """
    Iniciar processo de login com Azure AD.
    
    **Fluxo:**
    1. Usuário é redirecionado para Azure AD
    2. Após login, Azure AD redireciona para `/getAToken?code=...`
    3. Token é armazenado em HTTPOnly cookie
    
    **Exemplo de Uso:**
    ```html
    <a href="/api/v1/login">Login com Azure AD</a>
    ```
    
    **Response:**
    - Redirect (302) para Azure AD login page
    """
    auth = get_auth_msal()
    authorize_url = auth.get_authorize_url()
    return RedirectResponse(url=authorize_url)


@router.get("/getatoken", summary="Callback do Azure AD", description="Troca código de autorização por token de acesso")
def get_a_token(code: Optional[str] = None):
    """Callback do Azure AD com código de autorização."""
    
    if not code:
        logger.error("getatoken: Missing ?code parameter")
        raise HTTPException(status_code=400, detail="Missing ?code parameter")

    logger.info("="*80)
    logger.info("[getatoken] STARTING TOKEN EXCHANGE")
    logger.info(f"[getatoken] Code received: {code[:50]}...")
    
    auth = get_auth_msal()
    token_data = auth.exchange_code_for_token(code)
    id_token = token_data.get("access_token")  # id_token para autenticação
    graph_access_token = token_data.get("graph_access_token")  # Token real para Graph
    user_id = token_data.get("user_id")  # User ID (oid)

    logger.info(f"[getatoken] Tokens received - id_token: {bool(id_token)}, graph_token: {bool(graph_access_token)}, user_id: {user_id}")
    if id_token:
        logger.info(f"[getatoken] id_token length: {len(id_token)}, first 50: {id_token[:50]}...")
    if graph_access_token:
        logger.info(f"[getatoken] graph_token length: {len(graph_access_token)}, first 50: {graph_access_token[:50]}...")

    # Salvar preferência do usuário (idioma) na primeira vez que entra
    try:
        if user_id:
            # Extrair idioma do token (se disponível)
            preferred_lang = token_data.get("preferred_language", "pt")
            UserPreferenceService.save_user_preference(user_id, preferred_lang)
            logger.info(f"[getatoken] Preferência do usuário salva: {user_id} → {preferred_lang}")
    except Exception as e:
        logger.warning(f"[getatoken] Erro ao salvar preferência do usuário: {e}")
        # Não interromper fluxo de login se algo der errado aqui

    # Criar response JSON com cookies ao invés de redirect imediato
    # Isso garante que os cookies sejam setados corretamente
    
    logger.info(f"[getatoken] Login successful for user {user_id}, redirecting to {auth.frontend_chat_url}")
    logger.info("="*80)
    
    # Fazer redirect automático (307) com cookies
    response = RedirectResponse(
        url=auth.frontend_chat_url,
        status_code=307
    )
    
    # Setar cookies na resposta
    response.set_cookie(
        "session",
        id_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/"
    )
    
    if graph_access_token:
        response.set_cookie(
            "graph_token",
            graph_access_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/"
        )
    
    if user_id:
        response.set_cookie(
            "user_id",
            user_id,
            httponly=True,
            secure=True,
            samesite="none",
            path="/"
        )
    
    return response


@router.get("/auth/status", summary="Verificar status de autenticação", description="Valida se o usuário está autenticado")
def auth_status(session: Optional[str] = Cookie(None)):
    """
    Verificar se usuário está autenticado.
    
    **Cookie:**
    - `session`: Token JWT no cookie (HTTPOnly)
    
    **Response (200 - Autenticado):**
    ```json
    {
      "authenticated": true,
      "claims": {
        "email": "user@example.com",
        "oid": "user-object-id",
        "roles": ["admin", "user"],
        "name": "User Name"
      }
    }
    ```
    
    **Response (401 - Não Autenticado):**
    ```json
    {
      "detail": "Unauthorized"
    }
    ```
    
    **Exemplo de Uso:**
    ```javascript
    const response = await fetch('/api/v1/auth/status');
    if (response.status === 200) {
      const data = await response.json();
      console.log('Usuário:', data.claims.email);
    } else {
      console.log('Não autenticado');
    }
    ```
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"auth_status: session_cookie={bool(session)}, cookie_length={len(session) if session else 0}")
    if session:
        logger.info(f"auth_status: session first 30 chars: {session[:30]}...")
    
    auth = get_auth_msal()
    decoded = auth.validate_token(session)

    if decoded is None:
        logger.warning(f"auth_status: Token validation failed, returning 401")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f"auth_status: Token validated successfully")
    return {
        "authenticated": True,
        "claims": decoded
    }


@router.get("/logout", summary="Fazer logout", description="Remove sessão e redireciona para logout do Azure AD")
def logout():
    """
    Fazer logout:
    1. Deleta cookie "session"
    2. Redireciona para logout do Azure AD
    
    **Response:**
    - Redirect (302) para Azure AD logout
    - Cookie "session" deletado
    
    **Exemplo de Uso:**
    ```html
    <a href="/api/v1/logout">Logout</a>
    ```
    """
    auth = get_auth_msal()
    logout_url = auth.get_logout_url()

    response = RedirectResponse(url=logout_url)
    response.delete_cookie(
        "session",
        httponly=True,
        secure=True,
        samesite="none",
        path="/"  # Match the path used in set_cookie
    )

    return response


@router.get("/me/role", summary="Obter role do usuário", description="Busca role e informações do usuário via Azure AD")
def get_user_role(session: Optional[str] = Cookie(None)):
    """
    Obter role e informações do usuário autenticado.
    
    **Response (200 - Com Role no Token):**
    ```json
    {
      "authenticated": true,
      "email": "user@example.com",
      "roles": ["admin", "user"],
      "source": "token"
    }
    ```
    
    **Response (200 - Sem Role no Token):**
    ```json
    {
      "authenticated": true,
      "email": "user@example.com",
      "oid": "user-object-id",
      "message": "Para obter role completo, use o Microsoft Graph com o access token"
    }
    ```
    
    **Response (401 - Não Autenticado):**
    ```json
    {
      "detail": "Unauthorized"
    }
    ```
    
    **Campos Retornados:**
    - `email`: Email do usuário
    - `roles`: Array de roles atribuídas no Azure AD
    - `oid`: Object ID do usuário no Azure AD
    
    **Exemplo de Uso:**
    ```javascript
    const response = await fetch('/api/v1/me/role');
    const data = await response.json();
    if (data.authenticated) {
      console.log('Roles:', data.roles);
      if (data.roles.includes('admin')) {
        // Mostrar opções de admin
      }
    }
    ```
    """
    auth = get_auth_msal()
    decoded = auth.validate_token(session)

    if decoded is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Se o token tem role claim, retornar
    if "roles" in decoded:
        return {
            "authenticated": True,
            "email": decoded.get("email"),
            "roles": decoded.get("roles", []),
            "source": "token"
        }

    # Se não, retornar 200 mas sem informações de role
    # (role virá do Microsoft Graph no frontend)
    return {
        "authenticated": True,
        "email": decoded.get("email"),
        "oid": decoded.get("oid"),
        "message": "Para obter role completo, use o Microsoft Graph com o access token"
    }

@router.get("/me/info", summary="Obter informações completas do usuário", description="Busca país, cidade, role e informações do usuário via Azure AD")
async def get_user_info(
    session: Optional[str] = Cookie(None),
    graph_token: Optional[str] = Cookie(None),
    token: Optional[str] = Query(None, description="JWT token (query parameter alternative to cookie)")
):
    """
    Obter informações **completas** do usuário autenticado via Microsoft Graph /beta/me (país, cidade, role, etc).
    
    **Response (200 - Sucesso):**
    ```json
    {
      "authenticated": true,
      "email": "user@company.com",
      "displayName": "João Silva",
      "country": "Brazil",
      "city": "São Paulo",
      "state": "SP",
      "jobTitle": "Senior Developer",
      "department": "Engineering",
      "companyName": "ACME Corp",
      "mobilePhone": "+55 11 9999-9999",
      "role": "admin",
      "role_id": 1,
      "roles": ["admin", "user"]
    }
    ```
    
    **Formas de enviar o token:**
    
    1. **Via Cookie (preferido):**
       ```javascript
       const response = await fetch('/api/v1/me/info', {
         credentials: 'include'  // Envia cookies automaticamente
       });
       ```
    
    2. **Via Query Parameter:**
       ```
       GET /api/v1/me/info?token=eyJ0eXAi...
       ```
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log início do endpoint
    logger.info("="*80)
    logger.info("GET /me/info - ENDPOINT START")
    logger.info(f"GET /me/info - session_cookie: {bool(session)}, graph_token: {bool(graph_token)}, token_param: {bool(token)}")
    if session:
        logger.info(f"GET /me/info - session length: {len(session)}, first 30: {session[:30]}...")
    if graph_token:
        logger.info(f"GET /me/info - graph_token length: {len(graph_token)}, first 30: {graph_token[:30]}...")
    
    # Validar que temos token
    jwt_token = session or token
    logger.info(f"GET /me/info - Using JWT token: {bool(jwt_token)}")
    
    auth = get_auth_msal()
    decoded = auth.validate_token(jwt_token)

    if decoded is None:
        logger.warning(f"GET /me/info - Token validation failed, returning 401")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f"GET /me/info - Token validated successfully for user: {decoded.get('email')}")
    
    # Se temos graph_token, usar Graph API para dados completos
    if graph_token:
        logger.info("[Graph] ATTEMPTING TO FETCH EXTENDED PROFILE FROM /beta/me")
        logger.info(f"[Graph] graph_token available: True, length: {len(graph_token)}, first 30: {graph_token[:30]}...")
        try:
            logger.info("[Graph] Calling get_user_profile_extended()...")
            user_info = await get_user_profile_extended(graph_token)
            logger.info(f"[Graph] Response received: {user_info}")
            if user_info:
                logger.info(f"[Graph] Received {len(user_info)} fields from Graph API")
                user_info["authenticated"] = True
                user_info["oid"] = decoded.get("oid")
                user_info["user_id"] = decoded.get("oid")
                user_info["roles"] = decoded.get("roles", [])
                
                # Enriquecer com role e role_id baseado em job_title
                job_title = user_info.get("jobTitle")
                if job_title:
                    logger.info(f"[JobTitle] Searching for role mapping: jobTitle='{job_title}'")
                    mapped_role_info = JobTitleRoleService.get_role_by_job_title(job_title)
                    if mapped_role_info:
                        logger.info(f"[JobTitle] FOUND role mapping: '{job_title}' → role='{mapped_role_info.get('role')}', role_id={mapped_role_info.get('role_id')}")
                        user_info["role"] = mapped_role_info.get("role")
                        user_info["role_id"] = mapped_role_info.get("role_id")
                    else:
                        logger.debug(f"[JobTitle] No role mapping found for jobTitle='{job_title}'")
                else:
                    logger.debug("[JobTitle] User has no jobTitle in Graph profile")
                
                # ✨ NOVO: Adicionar foto do usuário
                try:
                    logger.info("[Graph] Tentando obter foto do usuário...")
                    photo_bytes = await get_user_photo(graph_token)
                    if photo_bytes:
                        import base64
                        b64_photo = base64.b64encode(photo_bytes).decode()
                        user_info["photoUrl"] = f"data:image/jpeg;base64,{b64_photo}"
                        user_info["photoBase64"] = b64_photo
                        logger.info(f"[Graph] Foto adicionada com sucesso ({len(photo_bytes)} bytes)")
                    else:
                        user_info["photoUrl"] = None
                        user_info["photoBase64"] = None
                        logger.info("[Graph] Foto não disponível para este usuário")
                except Exception as e:
                    logger.warning(f"[Graph] Erro ao obter foto: {e}")
                    user_info["photoUrl"] = None
                    user_info["photoBase64"] = None
                
                logger.info(f"[Graph] SUCCESS - Returning complete profile for {user_info.get('email')}")
                logger.info("="*80)
                return user_info
            else:
                logger.warning("[Graph] WARNING - Graph API returned None/empty")
        except Exception as e:
            logger.error(f"[Graph] EXCEPTION during Graph API call: {type(e).__name__}: {e}", exc_info=True)
    else:
        logger.warning("[Graph] NO graph_token in cookies - cannot call Graph API")
    
    # Fallback: usar informações do token
    logger.warning(f"GET /me/info - Retornando informações do token (Graph não disponível)")
    user_info = auth.get_user_info_from_token(decoded)
    if user_info:
        user_info["authenticated"] = True
        return user_info
    
    return {
        "authenticated": True,
        "email": decoded.get("email"),
        "displayName": decoded.get("name"),
        "oid": decoded.get("oid"),
        "roles": decoded.get("roles", [])
    }


# Dependency for protected routes
async def get_current_user(session: Optional[str] = Cookie(None)):
    """Dependency to check if user is authenticated"""
    auth = get_auth_msal()
    decoded = auth.validate_token(session)

    if decoded is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return decoded