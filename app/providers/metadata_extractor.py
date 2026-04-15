"""
Metadata Extraction Provider - integração com novo serviço de LLM para extração de metadados.
"""
import logging
import requests
from typing import Optional, Dict, Any, List
from app.core.config import get_config

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Cliente para chamar serviço de extração de metadados via LLM.
    
    Endpoint remoto: POST /api/v1/extract-metadata
    Request: {"text": "...", "filename": "..."}
    Response: {
        "min_role": "Manager" or null,
        "countries": ["Brazil"] or null,
        "cities": ["São Carlos"] or null,
        "collar": "blue" or null,
        "confidence": "high" or "medium" or "low"
    }
    """
    
    def __init__(self, metadata_server_url: str = None):
        """
        Inicializar extrator de metadados.
        
        Args:
            metadata_server_url: URL do servidor de metadados (ex: https://ca-peoplechatbot-dev-latam002.../api/v1)
        """
        # Se não passar URL, usar variável de ambiente
        self.metadata_server_url = metadata_server_url or self._get_metadata_server_url()
        self.timeout = 60  # segundos
        
        if not self.metadata_server_url:
            logger.warning("METADATA_SERVER_URL not configured")
    
    @staticmethod
    def _get_metadata_server_url() -> Optional[str]:
        """Obter URL do servidor de metadados da configuração."""
        import os
        return os.getenv("METADATA_SERVER_URL")
    
    def extract_metadata(
        self,
        text: str,
        filename: str = "document.txt"
    ) -> Dict[str, Any]:
        """
        Extrair metadados do texto usando serviço remoto.
        
        Args:
            text: Texto completo do documento
            filename: Nome do arquivo (opcional)
        
        Returns:
            {
                "min_role": "Manager" ou None,
                "countries": ["Brazil"] ou None,
                "cities": ["São Carlos"] ou None,
                "collar": "blue" ou None,
                "confidence": "high" ou "medium" ou "low"
            }
        
        Raises:
            RuntimeError: Se não conseguir conectar ao servidor
        """
        if not self.metadata_server_url:
            logger.warning("Metadata extraction skipped - server URL not configured")
            return self._empty_metadata()
        
        try:
            logger.info(f"Extracting metadata using {self.metadata_server_url}")
            
            # Chamar endpoint remoto
            response = requests.post(
                f"{self.metadata_server_url}/extract-metadata",
                json={
                    "text": text,
                    "filename": filename
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Metadata extracted: confidence={result.get('confidence', 'unknown')}")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Metadata extraction timeout after {self.timeout}s")
            raise RuntimeError("Metadata extraction server timeout")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to metadata server: {e}")
            raise RuntimeError(f"Metadata extraction server error: {e}")
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            raise RuntimeError(f"Failed to extract metadata: {e}")
    
    def map_to_document_fields(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mapear resposta do extrator para campos do documento.
        
        Args:
            metadata: Resposta do serviço de extração
        
        Returns:
            {
                "min_role_level": int,
                "allowed_countries": str ou None,
                "allowed_cities": str ou None,
                "collar": str ou None
            }
        """
        # Mapeamento de role strings para níveis numéricos
        role_mapping = {
            "executive": 3,
            "manager": 2,
            "employee": 1,
            "intern": 0
        }
        
        min_role_str = metadata.get("min_role", "").lower() if metadata.get("min_role") else None
        min_role_level = role_mapping.get(min_role_str, 0) if min_role_str else 0
        
        return {
            "min_role_level": min_role_level,
            "allowed_countries": ",".join(metadata.get("countries", [])) if metadata.get("countries") else None,
            "allowed_cities": ",".join(metadata.get("cities", [])) if metadata.get("cities") else None,
            "collar": metadata.get("collar")
        }
    
    @staticmethod
    def _empty_metadata() -> Dict[str, Any]:
        """Retornar metadados vazios (fallback)."""
        return {
            "min_role": None,
            "countries": None,
            "cities": None,
            "collar": None,
            "confidence": "low"
        }


# Cliente global (singleton)
_metadata_extractor_instance = None


def get_metadata_extractor() -> MetadataExtractor:
    """Obter instância global do extrator de metadados."""
    global _metadata_extractor_instance
    if _metadata_extractor_instance is None:
        _metadata_extractor_instance = MetadataExtractor()
    return _metadata_extractor_instance
