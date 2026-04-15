import os
import json
import logging
from openai import AzureOpenAI, OpenAI

logger = logging.getLogger(__name__)

# Detect which provider to use - só tenta usar o que tiver credenciais
HAS_AZURE = os.getenv("AZURE_OPENAI_ENDPOINT") is not None and os.getenv("") is not None
HAS_OPENAI = os.getenv("OPENAI_API_KEY") is not None

client = None
DEPLOYMENT_NAME = None

try:
    if HAS_AZURE:
        client = AzureOpenAI(
            api_key=os.getenv(""),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
        DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-35-turbo")
        logger.info("Using Azure OpenAI for LLM")
    elif HAS_OPENAI:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        DEPLOYMENT_NAME = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        logger.info("Using OpenAI.com for LLM")
    else:
        logger.warning("No LLM provider configured (set OPENAI_API_KEY or AZURE_OPENAI_* variables)")
except Exception as e:
    logger.error(f"Failed to initialize LLM client: {e}")




def extract_document_fields(content: str, filename: str) -> dict:
    """
    Use LLM to extract/suggest document metadata fields from content.
    Returns a dict with extracted fields or empty if not found.
    
    Suggested fields:
    - user_id (creator/responsible person)
    - allowed_countries (list of country codes)
    - allowed_cities (list of city names)
    - min_role_level (access level, 0-5)
    - collar (w=white, b=blue, empty=no restriction)
    - plant_code (numeric code)
    """
    
    if not client:
        logger.warning("LLM client not initialized - returning empty metadata")
        return {}
    
    prompt = f"""Analyze the following document and extract/suggest the following metadata fields based on the content.
If a field cannot be inferred from the content, return null for that field.
Only return JSON, no other text.

Document filename: {filename}
Content (first 5000 chars):
{content[:5000]}

Return a JSON object with these fields:
{{
  "user_id": "person responsible/creator name or null",
  "allowed_countries": ["list of country codes (e.g., BR, US, AR) or empty list"],
  "allowed_cities": ["list of cities or empty list"],
  "min_role_level": "numeric 0-5 or null",
  "collar": "w for white-collar, b for blue-collar, or empty string",
  "plant_code": "numeric plant/facility code or null"
}}

Return ONLY the JSON object, no markdown, no extra text."""

    try:
        if USE_AZURE:
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500
            )
        else:
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500
            )
        
        # Parse response
        resp_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        try:
            extracted = json.loads(resp_text)
        except json.JSONDecodeError:
            # If response contains markdown code blocks, extract JSON
            if "```" in resp_text:
                start = resp_text.find("{")
                end = resp_text.rfind("}") + 1
                extracted = json.loads(resp_text[start:end])
            else:
                logger.warning(f"Failed to parse LLM response as JSON: {resp_text}")
                extracted = {}
        
        # Validate and clean extracted fields
        result = {
            "user_id": extracted.get("user_id") or None,
            "allowed_countries": extracted.get("allowed_countries") or [],
            "allowed_cities": extracted.get("allowed_cities") or [],
            "min_role_level": extracted.get("min_role_level"),
            "collar": extracted.get("collar") or "",
            "plant_code": extracted.get("plant_code"),
        }
        
        # Ensure types
        if isinstance(result["min_role_level"], str):
            try:
                result["min_role_level"] = int(result["min_role_level"])
            except ValueError:
                result["min_role_level"] = None
        
        if isinstance(result["plant_code"], str):
            try:
                result["plant_code"] = int(result["plant_code"])
            except ValueError:
                result["plant_code"] = None
        
        return result
    
    except Exception as e:
        logger.exception(f"Error extracting fields with LLM: {e}")
        return {}
