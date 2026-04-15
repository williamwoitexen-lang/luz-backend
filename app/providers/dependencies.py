"""
FastAPI Dependency functions for authentication with MSAL

These dependencies extract user information and tokens from cookies.
Use them in your endpoints to get:
- user_id (oid from Azure AD)
- graph_access_token (for calling Microsoft Graph APIs)
- decoded_token (complete token information)
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Cookie, HTTPException
from app.providers.auth_msal import get_auth_msal
from app.providers.graph_client import get_user_profile_extended

logger = logging.getLogger(__name__)


async def get_current_user_id(
    session: Optional[str] = Cookie(None)
) -> str:
    """
    Dependency to extract user_id from session token.
    
    Usage:
        @router.post("/ingest")
        async def ingest_document(
            user_id: str = Depends(get_current_user_id),
        ):
            ...
    """
    auth = get_auth_msal()
    decoded = auth.validate_token(session)
    
    if decoded is None:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing token")
    
    user_id = decoded.get("oid")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    return user_id


async def get_graph_token(
    graph_token: Optional[str] = Cookie(None)
) -> str:
    """
    Dependency to extract graph_access_token from cookie.
    
    Usage:
        @router.get("/me/profile")
        async def get_profile(
            graph_token: str = Depends(get_graph_token),
        ):
            # Use graph_token to call Microsoft Graph APIs
            ...
    """
    if not graph_token:
        raise HTTPException(status_code=401, detail="Graph token not available")
    
    return graph_token


async def get_current_user_with_graph(
    session: Optional[str] = Cookie(None),
    graph_token: Optional[str] = Cookie(None)
) -> Dict[str, Any]:
    """
    Dependency that combines user_id and graph_access_token (RECOMMENDED).
    
    Returns everything you need in one call:
        {
            "user_id": "oid-from-token",
            "graph_access_token": "access-token-for-graph",
            "email": "user@company.com",
            "name": "User Name",
            "roles": ["admin", "user"],
            "country": "Brazil",  # From Graph API if available
            "city": "São Paulo",   # From Graph API if available
            "department": "Engineering",  # From Graph API if available
            "jobTitle": "Senior Developer",  # From Graph API if available
            "decoded_token": {...}  # Complete token
        }
    
    Usage:
        @router.post("/ingest")
        async def ingest_document(
            file: UploadFile = File(None),
            current_user: Dict = Depends(get_current_user_with_graph),
        ):
            user_id = current_user["user_id"]
            graph_token = current_user["graph_access_token"]
            email = current_user["email"]
            country = current_user.get("country")  # Optional, from Graph
            ...
    """
    auth = get_auth_msal()
    decoded = auth.validate_token(session)
    
    if decoded is None:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing token")
    
    user_id = decoded.get("oid")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    if not graph_token:
        raise HTTPException(status_code=401, detail="Graph token not available")
    
    # Try to get email from multiple fields, with upn as fallback
    email = decoded.get("email") or decoded.get("upn") or decoded.get("preferred_username")
    if not email:
        raise HTTPException(status_code=401, detail="Email não encontrado no token")
    
    # Start with basic user info from token
    user_info = {
        "user_id": user_id,
        "graph_access_token": graph_token,
        "email": email,
        "name": decoded.get("name"),
        "roles": decoded.get("roles", []),
        "given_name": decoded.get("given_name"),
        "family_name": decoded.get("family_name"),
        "oid": user_id,
        "decoded_token": decoded,
    }
    
    # Try to enrich with Graph API data
    try:
        logger.info(f"[get_current_user_with_graph] Fetching extended profile from Graph for {email}")
        graph_profile = await get_user_profile_extended(graph_token)
        if graph_profile:
            logger.info(f"[get_current_user_with_graph] ✓ Graph profile retrieved, merging data")
            # Merge Graph profile data (country, city, jobTitle, etc)
            user_info.update(graph_profile)
            # Keep our essentials from token (they might be missing in Graph)
            user_info["email"] = email
            user_info["user_id"] = user_id
            user_info["oid"] = user_id
            user_info["roles"] = decoded.get("roles", [])
        else:
            logger.warning(f"[get_current_user_with_graph] Graph API returned empty response")
    except Exception as e:
        logger.warning(f"[get_current_user_with_graph] Could not fetch Graph profile: {type(e).__name__}: {e}")
        # Continue with token-only info, don't fail
    
    return user_info


async def get_current_user(
    session: Optional[str] = Cookie(None),
    graph_token: Optional[str] = Cookie(None)
) -> Dict[str, Any]:
    """
    Dependency to get current user information (backward compatible).
    
    Returns user information extracted from decoded token:
        {
            "user_id": "oid",
            "email": "user@company.com",
            "name": "User Name",
            "roles": ["admin"],
            "decoded_token": {...}
        }
    
    If email not found in token, fetches from Graph API.
    
    Usage:
        @router.get("/me")
        async def get_me(
            current_user: Dict = Depends(get_current_user),
        ):
            return current_user
    """
    auth = get_auth_msal()
    decoded = auth.validate_token(session)
    
    if decoded is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Try to get email from token
    email = decoded.get("email") or decoded.get("upn") or decoded.get("preferred_username")
    
    # If not in token, fetch from Graph API
    if not email and graph_token:
        try:
            graph_profile = await get_user_profile_extended(graph_token)
            if graph_profile:
                email = graph_profile.get("mail")
        except Exception as e:
            logger.warning(f"[get_current_user] Could not fetch from Graph: {e}")
    
    if not email:
        raise HTTPException(status_code=401, detail="Email não encontrado no token")
    
    user_info = auth.get_user_info_from_token(decoded)
    
    return {
        **(user_info or {}),
        "user_id": decoded.get("oid"),
        "email": email,  # Garantir que email não seja sobrescrito
        "name": decoded.get("name"),
        "roles": decoded.get("roles", []),
        "decoded_token": decoded,
    }
