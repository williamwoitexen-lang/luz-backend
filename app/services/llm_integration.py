"""
LLM Server integration layer.
Handles all communication with LLM Server for document processing.
"""
from typing import Dict, Any, Optional
from app.providers.llm_server import get_llm_client
import logging

logger = logging.getLogger(__name__)


class LLMIntegration:
    """LLM Server communication wrapper."""
    
    @staticmethod
    def ingest_document(
        document_id: str,
        file_content: str,
        filename: str,
        user_id: str,
        title: Optional[str] = None,
        min_role_level: int = 1,
        allowed_roles: list = None,
        allowed_countries: list = None,
        allowed_cities: list = None,
        version_id: int = 1
    ) -> Dict[str, Any]:
        """
        Send document to LLM Server for processing.
        
        LLM Server responsibilities:
        - Detect file format from filename
        - Apply format-specific parsing (PDF, Excel, DOCX, etc)
        - Split text into chunks with context preservation
        - Generate embeddings
        - Index into search engine
        
        Args:
            document_id: Unique document identifier
            file_content: Complete file content as decoded text
            filename: Original filename (used for format detection)
            user_id: User who uploaded the document
            title: Display title (optional, defaults to filename)
            min_role_level: Minimum role level required
            allowed_roles: List of specific roles (e.g., ["admin", "manager"])
            allowed_countries: List of allowed countries
            allowed_cities: List of allowed cities
            version_id: Document version number
        
        Returns:
            Response from LLM Server containing chunk_count and other metadata
        """
        try:
            llm_client = get_llm_client()
            response = llm_client.ingest_document(
                document_id=document_id,
                file_content=file_content,
                filename=filename,
                user_id=user_id,
                title=title or filename,
                min_role_level=min_role_level,
                allowed_roles=allowed_roles or [],
                allowed_countries=allowed_countries or [],
                allowed_cities=allowed_cities or [],
                version_id=version_id
            )
            
            chunk_count = response.get("chunk_count", 0)
            logger.info(f"Document {document_id} ingested: {chunk_count} chunks created")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM Server ingestion failed for {document_id}: {e}")
            raise
    
    @staticmethod
    def delete_document(document_id: str) -> Dict[str, Any]:
        """
        Delete entire document from LLM Server (all versions, all chunks).
        
        Args:
            document_id: Unique document identifier
        
        Returns:
            Response from LLM Server
        """
        try:
            llm_client = get_llm_client()
            response = llm_client.delete_document(document_id)
            logger.info(f"Document {document_id} deleted from LLM Server")
            return response
            
        except Exception as e:
            logger.error(f"LLM Server deletion failed for {document_id}: {e}")
            raise
    
    @staticmethod
    def delete_document_version(
        document_id: str,
        version_number: int
    ) -> Dict[str, Any]:
        """
        Delete specific version's chunks from LLM Server.
        
        Args:
            document_id: Unique document identifier
            version_number: Version number to delete
        
        Returns:
            Response from LLM Server
        """
        try:
            llm_client = get_llm_client()
            # Note: This assumes LLM Server has a delete_document_version endpoint
            # If not available, fall back to delete_document and re-ingest latest
            response = llm_client.delete_document_version(document_id, version_number)
            logger.info(f"Version {version_number} of document {document_id} deleted from LLM Server")
            return response
            
        except Exception as e:
            logger.warning(f"LLM Server version deletion not available, will handle in deletion logic: {e}")
            raise
