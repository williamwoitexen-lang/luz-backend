"""
Rotas para gerenciar mapeamento de Job Title → Role
Suporta:
- Busca individual de role por job_title
- Listagem de todos os mapeamentos
- Adição de novo mapeamento
- Importação em massa (CSV, XLSX)
"""
import logging
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from typing import Optional
from pydantic import BaseModel
from app.services.job_title_role_service import JobTitleRoleService
from app.services.job_title_bulk_import import JobTitleBulkImport

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/master-data/job-title-roles", tags=["master-data"])


class JobTitleRoleMapping(BaseModel):
    """Modelo para criar mapeamento de job_title → role"""
    job_title: str
    role: str


@router.get("/mapping")
async def get_role_by_job_title(job_title: str = Query(..., description="Título do cargo")) -> dict:
    """
    Buscar role a partir do job_title.
    
    Exemplo: GET /api/v1/master-data/job-title-roles/mapping?job_title=SVP%20Corporate%20Communications
    
    Returns:
        {
            "job_title": "SVP Corporate Communications",
            "role": "Vice-Presidente"
        }
    """
    try:
        role = JobTitleRoleService.get_role_by_job_title(job_title)
        
        if not role:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum mapeamento encontrado para job_title: {job_title}"
            )
        
        return {
            "job_title": job_title,
            "role": role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar mapeamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar mapeamento: {str(e)}")


@router.get("/all")
async def list_all_mappings(limit: int = Query(100, ge=1, le=1000)) -> dict:
    """
    Listar todos os mapeamentos de job_title → role.
    
    Returns:
        {
            "count": 7,
            "mappings": [
                {"job_title": "SVP Corporate Communications", "role": "Vice-Presidente"},
                ...
            ]
        }
    """
    try:
        mappings = JobTitleRoleService.list_all_mappings(limit=limit)
        
        return {
            "count": len(mappings),
            "mappings": mappings
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar mapeamentos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar mapeamentos: {str(e)}")


@router.post("/add")
async def add_job_title_role_mapping(req: JobTitleRoleMapping) -> dict:
    """
    Adicionar novo mapeamento de job_title → role.
    
    Request body:
    {
        "job_title": "CFO",
        "role": "Executivo"
    }
    
    Returns:
        {
            "success": true,
            "message": "Mapeamento adicionado com sucesso"
        }
    """
    try:
        success = JobTitleRoleService.add_mapping(req.job_title, req.role)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Não foi possível adicionar mapeamento. Verifique se job_title '{req.job_title}' já existe"
            )
        
        return {
            "success": True,
            "message": f"Mapeamento adicionado: '{req.job_title}' → '{req.role}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar mapeamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar mapeamento: {str(e)}")


@router.post("/import/csv")
async def import_csv_file(file: UploadFile = File(..., description="Arquivo CSV com colunas: job_title, role")) -> dict:
    """
    Importar mapeamentos em massa a partir de arquivo CSV.
    
    **Formato esperado (CSV):**
    ```
    job_title,role
    SVP Corporate Communications,Vice-Presidente
    VP Brand & Consumer Insights,Vice-Presidente
    CFO,Executivo
    ...
    ```
    
    **Exemplo com curl:**
    ```bash
    curl -F "file=@mappings.csv" http://localhost:8000/api/v1/master-data/job-title-roles/import/csv
    ```
    
    **Response (Sucesso):**
    ```json
    {
        "success": true,
        "imported": 12000,
        "warnings": ["Aviso: 5 linhas não foram inseridas (pode ser duplicatas)"],
        "stats": {
            "total_mappings": 12005,
            "active_mappings": 12005,
            "unique_roles": 250
        }
    }
    ```
    """
    try:
        if not file.filename or not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Arquivo deve ter extensão .csv")
        
        # Ler conteúdo do arquivo
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        logger.info(f"Importando CSV: {file.filename}, tamanho: {len(csv_content)} bytes")
        
        # Importar
        success_count, errors = JobTitleBulkImport.import_csv_string(csv_content)
        
        # Obter estatísticas
        stats = JobTitleBulkImport.get_import_stats()
        
        return {
            "success": success_count > 0,
            "imported": success_count,
            "warnings": errors,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao importar CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao importar CSV: {str(e)}")


@router.post("/import/xlsx")
async def import_xlsx_file(
    file: UploadFile = File(..., description="Arquivo XLSX com colunas: job_title, role"),
    sheet_name: str = Form("Sheet1", description="Nome da aba (padrão: Sheet1)")
) -> dict:
    """
    Importar mapeamentos em massa a partir de arquivo XLSX/Excel.
    
    **Formato esperado (Excel):**
    - Coluna A: job_title
    - Coluna B: role
    
    **Exemplo com curl:**
    ```bash
    curl -F "file=@mappings.xlsx" -F "sheet_name=Mappings" "http://localhost:8000/api/v1/master-data/job-title-roles/import/xlsx"
    ```
    
    **Response (Sucesso):**
    ```json
    {
        "success": true,
        "imported": 12000,
        "warnings": [],
        "stats": {
            "total_mappings": 12007,
            "active_mappings": 12007,
            "unique_roles": 250
        }
    }
    ```
    """
    try:
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Arquivo deve ter extensão .xlsx ou .xls")
        
        # Salvar temporariamente
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            logger.info(f"Importando XLSX: {file.filename}, tamanho: {len(content)} bytes")
            
            # Importar
            success_count, errors = JobTitleBulkImport.import_from_excel(tmp_path, sheet_name)
            
            # Obter estatísticas
            stats = JobTitleBulkImport.get_import_stats()
            
            return {
                "success": success_count > 0,
                "imported": success_count,
                "warnings": errors,
                "stats": stats
            }
            
        finally:
            # Limpar arquivo temporário
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao importar XLSX: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao importar XLSX: {str(e)}")


@router.get("/stats")
async def get_import_statistics() -> dict:
    """
    Obter estatísticas da tabela de mapeamentos.
    
    **Response:**
    ```json
    {
        "total_mappings": 12007,
        "active_mappings": 12007,
        "inactive_mappings": 0,
        "unique_roles": 250,
        "first_import": "2026-01-15T10:30:00",
        "last_update": "2026-01-15T14:45:00"
    }
    ```
    """
    try:
        stats = JobTitleBulkImport.get_import_stats()
        return stats
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")
