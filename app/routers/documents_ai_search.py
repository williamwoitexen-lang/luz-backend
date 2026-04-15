"""
Endpoints para ingestão e gerenciamento de documentos com LLM Server.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import logging
from app.services.document_service import DocumentService
from app.services.sqlserver_documents import get_document_versions, delete_document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/ingest", summary="Ingerir documento com LLM Server")
async def ingest_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    min_role_level: int = Form(default=1),
    allowed_roles: Optional[str] = Form(default=None),
    allowed_countries: Optional[str] = Form(default=None),
    allowed_cities: Optional[str] = Form(default=None),
    collar: Optional[str] = Form(default=None),
    plant_code: Optional[int] = Form(default=None),
    force_ingest: bool = Form(default=False)
):
    """
    Ingerir novo documento:
    1. Salva no Blob Storage
    2. Cria metadados no SQL Server
    3. Envia arquivo completo para LLM Server (texto, não chunks)
    """
    try:
        result = await DocumentService.ingest_document(
            file=file,
            user_id=user_id,
            min_role_level=min_role_level,
            allowed_roles=allowed_roles,
            allowed_countries=allowed_countries,
            allowed_cities=allowed_cities,
            collar=collar,
            plant_code=plant_code,
            force_ingest=force_ingest
        )
        return result
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", summary="Deletar documento inteiro")
async def delete_document_endpoint(document_id: str):
    """
    Deletar documento inteiro (todas as versões):
    1. Deleta do Blob Storage
    2. Marca como inativo no SQL Server
    3. Remove do Azure AI Search
    """
    try:
        # Deletar do Blob e SQL Server (todas as versões)
        delete_document(document_id)
        
        # Remover do AI Search
        from app.providers.llm_server import get_llm_client
        llm_client = get_llm_client()
        llm_client.delete_document(document_id)
        
        return {
            "status": "success",
            "document_id": document_id,
            "message": "Document completely deleted from Blob, SQL Server and AI Search"
        }
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}/versions/{version_number}", summary="Deletar versão específica")
async def delete_document_version_endpoint(document_id: str, version_number: int):
    """
    Deletar versão específica de documento:
    1. Deleta do Blob Storage
    2. Marca como inativa no SQL Server
    3. Se for última versão: remove do LLM Server
    4. Se houver versão anterior: re-ingera no LLM Server
    """
    try:
        result = await DocumentService.delete_version(document_id, version_number)
        return result
    except Exception as e:
        logger.error(f"Version delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/versions", summary="Listar versões do documento")
async def list_document_versions(document_id: str):
    """
    Listar todas as versões de um documento
    """
    try:
        versions = get_document_versions(document_id)
        return {
            "document_id": document_id,
            "versions": versions,
            "count": len(versions)
        }
    except Exception as e:
        logger.error(f"Failed to list versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
