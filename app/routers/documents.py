"""
Endpoints para ingestão e gerenciamento de documentos com LLM Server.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Path
from fastapi.responses import StreamingResponse
from typing import Optional, List
import logging
from app.services.document_service import DocumentService
from app.services.sqlserver_documents import get_document_versions, delete_document
from app.services.graph_user_service import GraphUserService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/ingest", summary="Ingerir documento novo ou atualizar existente")
async def ingest_document(
    user_id: str = Form(...),
    user_name: Optional[str] = Form(default=None, description="Nome do usuário (mascarado ao salvar)"),
    document_id: Optional[str] = Form(
    default=None,
    description="ID do documento. Deixe vazio para criar novo, ou passe UUID existente para atualizar",
    example=None
    ),
    title: Optional[str] = Form(default=None, description="Título do documento (opcional, será extraído do arquivo se não fornecido)"),
    category_id: Optional[int] = Form(default=None),
    is_active: Optional[bool] = Form(default=None, description="Ativar/inativar documento (MODO 2 only). Se false, remove do LLM Server"),
    min_role_level: int = Form(default=0),
    allowed_roles: Optional[str] = Form(default=None),
    allowed_countries: Optional[List[str]] = Form(default=None, description="Lista de países permitidos (ex: ['Brazil', 'Argentina', 'Chile'])"),
    allowed_cities: Optional[str] = Form(default=None),
    allowed_location_ids: Optional[str] = Form(default=None, description="Lista de location_ids separados por vírgula (ex: 1,2,3)"),
    collar: Optional[str] = Form(default=None),
    plant_code: Optional[int] = Form(default=None),
    summary: Optional[str] = Form(default=None, description="Resumo do documento (será extraído do LLM se não fornecido)"),
    force_ingest: bool = Form(default=False),
    file: Optional[UploadFile] = File(default=None)
):
    """
    Ingerir novo documento OU atualizar metadados de existente:
    
    Modo 1 - Com arquivo (criar novo ou atualizar com nova versão):
    1. Envia arquivo + user_id
    2. Salva no Blob Storage
    3. Cria metadados no SQL Server
    
    Modo 2 - Sem arquivo (apenas atualizar metadados):
    1. Envia document_id + user_id + metadados (category_id, is_active, etc)
    2. NÃO cria nova versão
    3. Atualiza apenas os metadados do documento existente
    4. Se is_active=false, remove documento do LLM Server (vector search)
    
    ⚠️ IMPORTANTE: Esta requisição DEVE usar multipart/form-data, NÃO JSON!
    
    Exemplo 1 - Com arquivo (criar novo):
    ```
    curl -X POST /api/v1/documents/ingest \\
      -F "file=@documento.pdf" \\
      -F "user_id=user123" \\
      -F "category_id=1" \\
      -F "allowed_countries=Brazil" \\
      -F "allowed_countries=Argentina"
    ```
    
    Exemplo 2 - Sem arquivo (apenas atualizar metadados com múltiplos países):
    ```
    curl -X POST /api/v1/documents/ingest \\
      -F "user_id=user123" \\
      -F "document_id=550e8400-e29b-41d4-a716-446655440000" \\
      -F "category_id=2" \\
      -F "allowed_countries=Brazil" \\
      -F "allowed_countries=Chile" \\
      -F "allowed_countries=Argentina"
    ```
    
    Parâmetros:
    - file (opcional): Arquivo a ingerir. Se omitido, apenas atualiza metadados
    - user_id (obrigatório): ID do usuário
    - document_id (opcional): Se null + file = novo documento. Se passado + file = nova versão. Se passado sem file = atualizar metadados
    - category_id (opcional): ID da categoria (FK para dim_categories)
    - min_role_level (opcional): Nível de acesso mínimo
    - allowed_countries (opcional): Lista de países permitidos (repetir -F para cada país)
    - allowed_cities/collar/plant_code: Filtros de segurança
    - force_ingest: Force mesmo se arquivo foi processado antes
    """
    try:
        file_name = file.filename if file else "metadata_update"
        
        # Validar user_id
        if not user_id or (isinstance(user_id, str) and user_id.strip() == ""):
            logger.error(f"[/ingest] ERROR: user_id vazio ou inválido: '{user_id}'")
            raise HTTPException(status_code=400, detail="user_id é obrigatório e não pode estar vazio")
        
        logger.info(f"[/ingest] START: file={file_name}, user_id={user_id}, user_name={user_name}, document_id={document_id}, category_id={category_id}, is_active={is_active}, force_ingest={force_ingest}")
        result = await DocumentService.ingest_document(
            file=file,
            user_id=user_id,
            user_name=user_name,
            document_id=document_id,
            title=title,
            category_id=category_id,
            is_active=is_active,
            min_role_level=min_role_level,
            allowed_roles=allowed_roles,
            allowed_countries=allowed_countries,
            allowed_cities=allowed_cities,
            allowed_location_ids=allowed_location_ids,
            collar=collar,
            plant_code=plant_code,
            summary=summary,
            force_ingest=force_ingest
        )
        logger.info(f"[/ingest] SUCCESS: document_id={result.get('document_id')}, version={result.get('version', 'N/A')}")
        return result
    except Exception as e:
        logger.error(f"[/ingest] FAILED: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-preview", summary="Preview de ingestão com extração de metadados")
async def ingest_preview(
    file: UploadFile = File(...),
):
    """
    Preview de ingestão:
    1. Salva arquivo temporariamente
    2. Extrai texto
    3. Chama LLM Server para extrair metadados sugeridos
    4. Retorna temp_id + metadados para usuário confirmar
    """
    try:
        result = await DocumentService.ingest_preview(file)
        return result
    except Exception as e:
        logger.error(f"Ingest preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-confirm/{temp_id}", summary="Confirmar ingestão com metadados")
async def ingest_confirm(
    temp_id: str,
    user_id: str = Form(...),
    user_name: Optional[str] = Form(default=None, description="Nome do usuário (mascarado ao salvar)"),
    document_id: Optional[str] = Form(default=None),
    title: Optional[str] = Form(default=None, description="Título do documento (opcional)"),
    category_id: Optional[int] = Form(default=None),
    min_role_level: int = Form(default=0),
    allowed_roles: Optional[str] = Form(default=None),
    allowed_countries: Optional[str] = Form(default=None),
    allowed_cities: Optional[str] = Form(default=None),
    allowed_location_ids: Optional[str] = Form(default=None, description="Lista de location_ids separados por vírgula (ex: 1,2,3)"),
    collar: Optional[str] = Form(default=None),
    plant_code: Optional[int] = Form(default=None),
    summary: Optional[str] = Form(default=None, description="Resumo do documento (será extraído do LLM se não fornecido)"),
):
    """
    Confirmar ingestão após review de metadados:
    1. Recupera arquivo do temp storage
    2. Usa metadados fornecidos (que podem ter sido editados do preview)
    3. Salva em Blob Storage
    4. Cria metadados no SQL Server
    5. Envia para LLM Server
    
    Parâmetro document_id:
    - Se null → novo documento (auto-generate ID)
    - Se passado → atualizar documento existente (nova versão)
    
    Parâmetro category_id:
    - ID da categoria do documento (FK para dim_categories)
    
    Parâmetro summary:
    - Resumo do documento. Se não fornecido, será extraído do LLM
    """
    try:
        # Validar user_id
        if not user_id or (isinstance(user_id, str) and user_id.strip() == ""):
            logger.error(f"[/ingest-confirm] ERROR: user_id vazio ou inválido: '{user_id}'")
            raise HTTPException(status_code=400, detail="user_id é obrigatório e não pode estar vazio")
        
        result = await DocumentService.ingest_confirm(
            temp_id=temp_id,
            user_id=user_id,
            user_name=user_name,
            document_id=document_id,
            title=title,
            category_id=category_id,
            min_role_level=min_role_level,
            allowed_roles=allowed_roles,
            allowed_countries=allowed_countries,
            allowed_cities=allowed_cities,
            allowed_location_ids=allowed_location_ids,
            collar=collar,
            plant_code=plant_code,
            summary=summary
        )
        return result
    except Exception as e:
        logger.error(f"Ingest confirm failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("", summary="Listar todos os documentos")
async def list_documents(
    filename: Optional[str] = Query(None, description="Filtrar por título do documento"),
    user_id: Optional[str] = Query(None, description="Filtrar por ID do usuário"),
    category_id: Optional[int] = Query(None, description="Filtrar por ID da categoria"),
    location_id: Optional[int] = Query(None, description="Filtrar por ID de localidade (FK para dim_electrolux_locations)"),
    file_type: Optional[str] = Query(None, description="Filtrar por tipo de arquivo (pdf, docx, xlsx, csv, txt, etc)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status ativo (None = ambos, True = apenas ativos, False = apenas inativos)"),
    min_role_level: Optional[int] = Query(None, description="Nível de role mínimo"),
    allowed_countries: Optional[str] = Query(None, description="Países permitidos"),
    allowed_cities: Optional[str] = Query(None, description="Cidades permitidas"),
    collar: Optional[str] = Query(None, description="Filtrar por collar"),
    plant_code: Optional[int] = Query(None, description="Filtrar por código da planta"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação")
):
    """
    Listar documentos com filtros opcionais:
    - filename: busca parcial no nome do arquivo
    - user_id: filtrar por usuário proprietário
    - category_id: filtrar por categoria (FK para dim_categories)
    - location_id: filtrar por localidade (FK para dim_electrolux_locations)
    - file_type: filtrar por tipo de arquivo (pdf, docx, xlsx, csv, txt)
    - is_active: filtrar por status (None = ambos ativos e inativos, True = apenas ativos, False = apenas inativos)
    - min_role_level: retorna docs com role_level >= este valor
    - allowed_countries/cities/collar/plant_code: filtros de segurança
    """
    try:
        docs = await DocumentService.list_documents(
            filename=filename,
            user_id=user_id,
            category_id=category_id,
            location_id=location_id,
            file_type=file_type,
            is_active=is_active,
            min_role_level=min_role_level,
            allowed_countries=allowed_countries,
            allowed_cities=allowed_cities,
            collar=collar,
            plant_code=plant_code,
            limit=limit,
            offset=offset
        )
        return {
            "documents": docs,
            "count": len(docs),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"List documents failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", summary="Obter detalhes do documento")
async def get_document_endpoint(document_id: str = Path(..., description="ID do documento (UUID)")):
    """
    Obter detalhes completos de um documento:
    1. Retorna metadados do documento (filename, user_id, role_level, etc)
    2. Retorna lista de todas as versões com suas informações
    3. Retorna contagem de chunks processados por versão
    """
    try:
        doc = await DocumentService.get_document_details(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/with-user-info", summary="Obter documento com informações do usuário do Graph")
async def get_document_with_user_info(
    document_id: str = Path(..., description="ID do documento (UUID)"),
):
    """
    Obter detalhes do documento COM informações do usuário do Microsoft Graph.
    
    Retorna:
    - Dados do documento
    - Nome do usuário buscado do Azure AD via Graph API
    - Email do usuário
    - Outras informações
    
    Exemplo:
    ```
    GET /api/v1/documents/550e8400-e29b-41d4-a716-446655440000/with-user-info
    ```
    
    Response:
    ```json
    {
        "document_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Benefícios de Saúde",
        "created_by_id": "3a2bc284-f11c-4676-a9e1-6310eea60f26",
        "created_by_name": "Adele Vance",
        "created_by_email": "adele@company.com",
        "created_at": "2026-01-09T10:00:00",
        ...
    }
    ```
    """
    try:
        # Buscar documento base
        from app.services.sqlserver_documents import get_document
        doc = get_document(document_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        # Buscar informações do usuário no Graph
        user_id = doc.get("user_id")
        created_by_name = "Desconhecido"
        created_by_email = None
        
        if user_id:
            logger.info(f"[GET /with-user-info] Buscando user info para: {user_id}")
            
            # Se user_id é UUID, buscar do Graph pelo ID
            import uuid
            try:
                uuid.UUID(user_id)
                # É UUID válido, buscar do Graph
                user_info = GraphUserService.get_user_by_id(user_id)
                if user_info:
                    created_by_name = user_info.get("displayName", "Desconhecido")
                    created_by_email = user_info.get("mail")
                    logger.info(f"[GET /with-user-info] ✓ Encontrado: {created_by_name}")
            except ValueError:
                # Não é UUID, talvez seja nome - tentar buscar pelo nome
                logger.info(f"[GET /with-user-info] user_id não é UUID, tentando como nome: {user_id}")
                user_info = GraphUserService.search_user_by_name(user_id)
                if user_info:
                    created_by_name = user_info.get("displayName", user_id)
                    created_by_email = user_info.get("mail")
                    logger.info(f"[GET /with-user-info] ✓ Encontrado pelo nome: {created_by_name}")
                else:
                    created_by_name = user_id  # Fallback ao nome original
        
        # Adicionar informações do usuário ao documento
        doc["created_by_id"] = user_id
        doc["created_by_name"] = created_by_name
        doc["created_by_email"] = created_by_email
        
        # Normalizar campos do documento (allowed_countries, allowed_cities, allowed_roles, user_name)
        from app.services.document_service import DocumentService
        doc = DocumentService._normalize_document_fields(doc)
        
        return doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /with-user-info] Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/download", summary="Download do documento")
async def download_document(
    document_id: str = Path(..., description="ID do documento (UUID)"),
    version_number: Optional[int] = Query(None, description="Versão específica a baixar (opcional). Se não fornecido, baixa a versão mais recente.")
):
    """
    Download do documento em seu formato original:
    1. Se version_number fornecido: busca a versão específica
    2. Se não fornecido: busca a versão mais recente
    3. Recupera blob do Blob Storage
    4. Retorna como arquivo para download com nome e formato originais
    
    Parâmetros query:
    - version_number (int, opcional): Número da versão específica a baixar
    """
    try:
        from app.services.sqlserver_documents import get_version_by_number, get_latest_version
        from urllib.parse import quote
        
        # Recuperar informações da versão para obter o nome do arquivo
        version_info = None
        if version_number is not None:
            version_info = get_version_by_number(document_id, version_number)
        else:
            version_info = get_latest_version(document_id)
        
        if not version_info:
            raise HTTPException(status_code=404, detail="Versão do documento não encontrada")
        
        # Extrair nome do arquivo do blob_path
        # Format: azure://container/documents/{id}/{version}/{filename} ou documents/{id}/{version}/{filename}
        blob_path = version_info.get('blob_path', '')
        if blob_path:
            # Extrair filename (última parte do path)
            filename = blob_path.split('/')[-1]
        else:
            filename = f"document_{document_id}"
        
        logger.info(f"[download] Downloading: document_id={document_id}, version={version_number}, filename={filename}")
        
        file_data = await DocumentService.download_document(document_id, version_number)
        if not file_data:
            raise HTTPException(status_code=404, detail="Documento ou versão não encontrado")
        
        # RFC 5987 encoding para nomes com caracteres especiais/acentos
        # Primeiro tenta ASCII-safe, se falhar usa RFC 5987
        try:
            filename.encode('ascii')
            filename_header = f"attachment; filename={filename}"
        except UnicodeEncodeError:
            # Para nomes com caracteres especiais, usa RFC 5987
            filename_encoded = quote(filename.encode('utf-8'), safe='')
            filename_header = f"attachment; filename*=UTF-8''{filename_encoded}; filename=\"{filename}\""
        
        return StreamingResponse(
            iter([file_data]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": filename_header}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/{document_id}", summary="Deletar documento inteiro")
async def delete_document_endpoint(document_id: str):
    """
    Deletar documento inteiro (todas as versões):
    1. Deleta do Blob Storage
    2. Marca como inativo no SQL Server
    3. Remove do LLM Server
    """
    try:
        # Deletar do Blob e SQL Server (todas as versões)
        delete_document(document_id)
        
        # Remover do LLM Server
        from app.providers.llm_server import get_llm_client
        llm_client = get_llm_client()
        llm_client.delete_document(document_id)
        
        return {
            "status": "success",
            "document_id": document_id,
            "message": "Document marked as inactive (soft delete). All versions deactivated."
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

@router.post("/test-llm-only", summary="TEST ONLY: Enviar arquivo direto pro LLM Server (sem salvar em nada)")
async def test_llm_only(
    file: UploadFile = File(...),
    document_id: str = Form(default="test-doc-123"),
    user_id: str = Form(default="test-user"),
    min_role_level: int = Form(default=1),
    allowed_countries: Optional[str] = Form(default=None),
    allowed_cities: Optional[str] = Form(default=None),
    title: Optional[str] = Form(default=None)
):
    """
    ENDPOINT DE TESTE - Apenas para debugar integração com LLM Server.
    
    NÃO salva:
    - ❌ Não salva em Blob Storage
    - ❌ Não salva em SQL Server
    - ❌ Não cria versão
    - ❌ Não persiste nada
    
    SÓ faz:
    - ✅ Lê o arquivo
    - ✅ Converte para CSV (com header)
    - ✅ Envia para LLM Server
    - ✅ Retorna resposta do LLM Server
    
    Use este endpoint para testar se o LLM Server está recebendo e processando os documentos.
    
    Exemplo:
        curl -X POST "http://localhost:8000/api/v1/documents/test-llm-only" \
          -F "file=@documento.pdf" \
          -F "document_id=test-123" \
          -F "user_id=test-user"
    """
    try:
        from app.providers.format_converter import FormatConverter
        from app.providers.llm_server import get_llm_client
        import uuid
        
        logger.info(f"[TEST-LLM] Iniciando teste com arquivo: {file.filename}")
        
        # STEP 1: Ler arquivo
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8", errors="ignore")
        logger.info(f"[TEST-LLM] Arquivo lido: {len(content)} caracteres")
        
        # STEP 2: Converter para CSV (com header)
        csv_content, original_format = FormatConverter.convert_to_csv(content, file.filename)
        logger.info(f"[TEST-LLM] Convertido para CSV: {original_format} → csv ({len(csv_content)} chars)")
        
        # STEP 3: Enviar para LLM Server
        logger.info(f"[TEST-LLM] Enviando para LLM Server...")
        llm_client = get_llm_client()
        
        llm_response = llm_client.ingest_document(
            document_id=document_id,
            file_content=csv_content,
            filename=file.filename,
            user_id=user_id,
            title=title or file.filename,
            min_role_level=min_role_level,
            allowed_countries=allowed_countries.split(",") if allowed_countries else [],
            allowed_cities=allowed_cities.split(",") if allowed_cities else [],
            version_id=1
        )
        
        logger.info(f"[TEST-LLM] Resposta recebida do LLM Server")
        
        return {
            "status": "success",
            "test_type": "LLM-ONLY-NO-PERSISTENCE",
            "warning": "⚠️  Este é um TESTE - nada foi salvo em banco de dados ou blob storage",
            "file_info": {
                "filename": file.filename,
                "original_size": len(raw_bytes),
                "text_size": len(content),
                "csv_size": len(csv_content),
                "original_format": original_format,
                "converted_format": "csv"
            },
            "llm_request": {
                "document_id": document_id,
                "user_id": user_id,
                "min_role_level": min_role_level
            },
            "llm_response": llm_response,
            "next_steps": [
                "1. Verifique se 'chunks_created' > 0 no LLM Server",
                "2. Faça query no Azure AI Search do LLM para verificar se o documento foi indexado",
                "3. Se funcionou aqui, o problema pode estar em outro lugar (MODO 2 não chama LLM?)"
            ]
        }
        
    except Exception as e:
        logger.error(f"[TEST-LLM] Erro: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao testar LLM Server: {str(e)}")