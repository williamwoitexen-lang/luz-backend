"""
Microsoft Graph API client for making authenticated requests to Microsoft Graph.

This module provides helper functions to call Microsoft Graph APIs
using the graph_access_token obtained during authentication.

Official Graph API docs: https://learn.microsoft.com/en-us/graph/overview
"""

import logging
import aiohttp
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def call_graph_api(
    graph_token: str,
    endpoint: str,
    method: str = "GET",
    body: Optional[Dict] = None,
    headers_extra: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """
    Generic function to call Microsoft Graph API with your token.
    
    Args:
        graph_token: Access token for Microsoft Graph
        endpoint: Graph endpoint (e.g., "/me", "/me/manager")
        method: HTTP method (GET, POST, PATCH, DELETE)
        body: Request body for POST/PATCH
        headers_extra: Extra headers to add
    
    Returns:
        Response JSON or None if error
    
    Example:
        user_info = await call_graph_api(
            graph_token=graph_token,
            endpoint="/me",
            method="GET"
        )
    """
    headers = {
        "Authorization": f"Bearer {graph_token}",
        "Content-Type": "application/json"
    }
    
    if headers_extra:
        headers.update(headers_extra)
    
    url = f"https://graph.microsoft.com/v1.0{endpoint}"
    logger.info(f"[Graph API] Calling {method} {url}")
    logger.info(f"[Graph API] Token length: {len(graph_token) if graph_token else 0} chars, first 30: {graph_token[:30] if graph_token else 'None'}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                json=body
            ) as response:
                logger.info(f"[Graph API] Response status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"[Graph API] Success response received, keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
                    return result
                elif response.status == 204:
                    # No content (success)
                    logger.info(f"[Graph API] No content (204)")
                    return {"status": "success"}
                else:
                    error_text = await response.text()
                    logger.error(f"[Graph API] Error {response.status}: {error_text}")
                    return None
                    
    except Exception as e:
        logger.error(f"[Graph API] Exception calling {endpoint}: {type(e).__name__}: {e}")
        return None


async def get_user_profile(graph_token: str) -> Optional[Dict]:
    """
    Get current user's profile information.
    
    Returns:
        User profile with email, name, job title, etc.
    """
    return await call_graph_api(graph_token, "/me")


async def get_user_profile_extended(graph_token: str) -> Optional[Dict]:
    """
    Get current user's extended profile information from /beta/me.
    
    Includes: email, name, country, city, state, job title, office location, etc.
    
    Returns:
        Extended user profile with location and contact information
    """
    logger.info("[Graph] Calling GET /beta/me")
    
    # Usar URL beta diretamente (não v1.0)
    url = "https://graph.microsoft.com/beta/me"
    headers = {
        "Authorization": f"Bearer {graph_token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                logger.info(f"[Graph] /beta/me response status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"[Graph] /beta/me response: received {len(result)} fields")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"[Graph] /beta/me Error {response.status}: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"[Graph] /beta/me Exception: {type(e).__name__}: {e}", exc_info=True)
        return None


async def get_user_photo(graph_token: str) -> Optional[bytes]:
    """
    Get current user's profile photo.
    
    Returns:
        Photo bytes or None if not available
    """
    headers = {
        "Authorization": f"Bearer {graph_token}",
    }
    
    url = "https://graph.microsoft.com/v1.0/me/photo/$value"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    logger.info("[Graph API] User photo retrieved successfully")
                    return await response.read()
                else:
                    logger.warning(f"[Graph API] Could not retrieve photo (status {response.status})")
                    return None
    except Exception as e:
        logger.error(f"[Graph API] Error retrieving photo: {e}")
        return None


async def get_user_manager(graph_token: str) -> Optional[Dict]:
    """
    Get user's manager information.
    
    Returns:
        Manager details (id, email, displayName, etc.)
    """
    return await call_graph_api(graph_token, "/me/manager")


async def get_user_direct_reports(graph_token: str) -> Optional[list]:
    """
    Get list of user's direct reports.
    
    Returns:
        List of direct report users
    """
    result = await call_graph_api(graph_token, "/me/directReports")
    return result.get("value", []) if result else None


async def get_user_groups(graph_token: str) -> Optional[list]:
    """
    Get list of groups the user belongs to.
    
    Returns:
        List of groups
    """
    result = await call_graph_api(graph_token, "/me/memberOf")
    return result.get("value", []) if result else None


async def get_user_calendar_events(
    graph_token: str,
    skip: int = 0,
    limit: int = 10
) -> Optional[list]:
    """
    Get user's calendar events.
    
    Args:
        graph_token: Access token
        skip: Number of events to skip
        limit: Number of events to return
    
    Returns:
        List of calendar events
    """
    endpoint = f"/me/calendarview?$skip={skip}&$top={limit}"
    result = await call_graph_api(graph_token, endpoint)
    return result.get("value", []) if result else None


async def get_user_emails(
    graph_token: str,
    skip: int = 0,
    limit: int = 10
) -> Optional[list]:
    """
    Get user's recent emails.
    
    Args:
        graph_token: Access token
        skip: Number of emails to skip
        limit: Number of emails to return
    
    Returns:
        List of messages
    """
    endpoint = f"/me/messages?$skip={skip}&$top={limit}"
    result = await call_graph_api(graph_token, endpoint)
    return result.get("value", []) if result else None


async def get_user_by_id(graph_token: str, user_id: str) -> Optional[Dict]:
    """
    Get another user's information by their ID.
    
    Args:
        graph_token: Access token
        user_id: User's object ID (oid)
    
    Returns:
        User profile
    """
    return await call_graph_api(graph_token, f"/users/{user_id}")


async def get_user_by_email(graph_token: str, email: str) -> Optional[Dict]:
    """
    Get user information by their email.
    
    Args:
        graph_token: Access token
        email: User's email address
    
    Returns:
        User profile
    """
    endpoint = f"/users('{email}')"
    return await call_graph_api(graph_token, endpoint)


async def list_all_users(graph_token: str, skip: int = 0, limit: int = 10) -> Optional[list]:
    """
    List all users in the organization (requires admin consent).
    
    Args:
        graph_token: Access token
        skip: Number of users to skip
        limit: Number of users to return
    
    Returns:
        List of users
    """
    endpoint = f"/users?$skip={skip}&$top={limit}"
    result = await call_graph_api(graph_token, endpoint)
    return result.get("value", []) if result else None


async def get_organization_info(graph_token: str) -> Optional[Dict]:
    """
    Get organization information.
    
    Returns:
        Organization details
    """
    return await call_graph_api(graph_token, "/organization")


async def create_outlook_event(
    graph_token: str,
    subject: str,
    start_time: str,
    end_time: str,
    attendees: Optional[list] = None
) -> Optional[Dict]:
    """
    Create a new Outlook calendar event.
    
    Args:
        graph_token: Access token
        subject: Event title
        start_time: Start time (RFC3339 format, e.g., "2026-01-15T10:00:00")
        end_time: End time (RFC3339 format)
        attendees: List of attendee emails
    
    Returns:
        Created event
    
    Example:
        event = await create_outlook_event(
            graph_token=graph_token,
            subject="Team Meeting",
            start_time="2026-01-15T10:00:00",
            end_time="2026-01-15T11:00:00",
            attendees=["user1@company.com", "user2@company.com"]
        )
    """
    body = {
        "subject": subject,
        "start": {
            "dateTime": start_time,
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "UTC"
        }
    }
    
    if attendees:
        body["attendees"] = [
            {
                "emailAddress": {"address": email},
                "type": "required"
            }
            for email in attendees
        ]
    
    return await call_graph_api(
        graph_token,
        "/me/events",
        method="POST",
        body=body
    )


async def send_email(
    graph_token: str,
    to_recipients: list,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None
) -> bool:
    """
    Send an email from the user's account.
    
    Args:
        graph_token: Access token
        to_recipients: List of recipient emails
        subject: Email subject
        body_text: Plain text body
        body_html: HTML body (optional)
    
    Returns:
        True if successful
    
    Example:
        success = await send_email(
            graph_token=graph_token,
            to_recipients=["recipient@company.com"],
            subject="Hello",
            body_text="This is a test email",
            body_html="<p>This is a test email</p>"
        )
    """
    body = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML" if body_html else "text",
                "content": body_html or body_text
            },
            "toRecipients": [
                {"emailAddress": {"address": email}}
                for email in to_recipients
            ]
        }
    }
    
    result = await call_graph_api(
        graph_token,
        "/me/sendMail",
        method="POST",
        body=body
    )
    
    return result is not None


# Helper to check if a scope is available
async def check_graph_scopes(graph_token: str) -> Optional[Dict]:
    """
    Check which scopes the current token has access to.
    
    Returns:
        Token info with scopes
    """
    return await call_graph_api(graph_token, "/me")
