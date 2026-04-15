import os
import logging
from pathlib import Path
import numpy as np
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# tenta localizar o .env em possíveis caminhos
CANDIDATES = [
    Path("/workspaces/Embeddings/.env"),
    Path("/workspace/.env"),
    Path(".env")
]

for p in CANDIDATES:
    if p.exists():
        load_dotenv(p, override=True)
        break

# Detect which provider to use - só tenta usar o que tiver credenciais
HAS_AZURE = os.getenv("AZURE_OPENAI_ENDPOINT") is not None and os.getenv("") is not None
HAS_OPENAI = os.getenv("OPENAI_API_KEY") is not None

client = None
EMBEDDING_MODEL = None

try:
    if HAS_AZURE:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=os.getenv(""),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
        logger.info("Using Azure OpenAI for embeddings")
    elif HAS_OPENAI:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        EMBEDDING_MODEL = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
        logger.info("Using OpenAI.com for embeddings")
    else:
        logger.warning("No embeddings provider configured (set OPENAI_API_KEY or AZURE_OPENAI_* variables)")
except Exception as e:
    logger.error(f"Failed to initialize embeddings client: {e}")




def embed_text(text: str):
    """Generate embeddings using either OpenAI.com or Azure OpenAI."""
    if not client:
        raise RuntimeError("Embeddings client not initialized. Set OPENAI_API_KEY or AZURE_OPENAI_* variables.")
    
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding
