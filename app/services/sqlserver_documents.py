"""
Document management service using SQL Server.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.core.sqlserver import get_sqlserver_connection

logger = logging.getLogger(__name__)


def _enrich_user_id(user_id: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Enriquece user_id com nome do Graph.
    
    Suporta:
    - UUID (Object ID): faz lookup no Graph
    - Nome (string): retorna como está
    - None: retorna None
    
    Retorna dict com user_id e user_name.
    """
    if not user_id:
        return {"user_id": None, "user_name": None}
    
    # Verificar se é um UUID válido
    import re
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    is_uuid = bool(re.match(uuid_pattern, user_id.lower()))
    
    if not is_uuid:
        # Se não for UUID, é um nome (dado legado). Usar como está
        logger.debug(f"[Documents] {user_id} é um nome (não UUID), usando direto")
        return {"user_id": user_id, "user_name": user_id}
    
    # É UUID, tentar resolver no Graph
    try:
        from app.services.graph_user_service import GraphUserService
        display_name = GraphUserService.get_user_display_name(user_id)
        if display_name and display_name != "Usuário Desconhecido":
            logger.debug(f"[Documents] Resolvido UUID {user_id[:8]}... → {display_name}")
            return {
                "user_id": user_id,
                "user_name": display_name
            }
        else:
            logger.debug(f"[Documents] Graph retornou 'Desconhecido' para UUID {user_id[:8]}...")
            return {"user_id": user_id, "user_name": user_id}
    except Exception as e:
        logger.warning(f"[Documents] Erro ao resolver UUID {user_id}: {e}")
        return {"user_id": user_id, "user_name": user_id}


def create_document(
    title: str,
    user_id: str,
    user_name: Optional[str] = None,
    min_role_level: int = 1,
    allowed_roles: Optional[str] = None,
    allowed_countries: Optional[str] = None,
    allowed_cities: Optional[str] = None,
    location_ids: Optional[str] = None,
    addresses: Optional[str] = None,
    collar: Optional[str] = None,
    plant_code: Optional[str] = None,
    category_id: Optional[int] = None,
    document_id: Optional[str] = None,
    file_type: Optional[str] = None,
    summary: Optional[str] = None
) -> str:
    """
    Create a new document record in SQL Server.
    
    Args:
        file_type: File extension (pdf, docx, xlsx, csv, txt, etc). Auto-extracted from title if not provided.
        summary: Resumo do documento extraído pelo LLM
        user_name: Nome do usuário criador (será mascarado para LGPD compliance)
        location_ids: JSON array de location_ids: [123, 456] (códigos das ruas)
        addresses: JSON array de addresses: ["Rua X", "Avenida Y"] (strings descritivas)
    
    Returns:
        document_id (str - UUID)
    """
    from app.utils.name_masking import mask_user_name
    
    # Auto-extract file_type from title if not provided
    if file_type is None:
        file_type = title.rsplit(".", 1)[-1].lower() if "." in title else "txt"
    
    # Validar document_id se fornecido
    if document_id is not None:
        # Rejeitar strings inválidas
        if document_id.lower() == "string" or document_id.lower() == "none":
            raise ValueError(f"Invalid document_id: '{document_id}'. Use a valid UUID or leave empty to auto-generate.")
        
        # Validar se é UUID válido
        try:
            uuid.UUID(document_id)
            logger.debug(f"[create_document] document_id passed: {document_id}")
        except ValueError:
            raise ValueError(f"Invalid document_id: '{document_id}' is not a valid UUID. Use a valid UUID or leave empty to auto-generate.")
    
    # Se não fornecido, gera UUID
    if document_id is None:
        document_id = str(uuid.uuid4())
        logger.warning(f"[create_document] ⚠️  GERADO NOVO UUID: {document_id}. Certifique-se que LLM Server foi chamado ANTES com o mesmo ID!")
    
    
    # Mascarar user_name se fornecido
    user_name_masked = None
    if user_name:
        try:
            user_name_masked = mask_user_name(user_name)
        except Exception as e:
            logger.warning(f"Erro ao mascarar user_name: {e}")
    
    sql = get_sqlserver_connection()
    
    query = """
    INSERT INTO documents (
        document_id, title, user_id, user_name_masked, category_id, min_role_level, allowed_roles,
        allowed_countries, allowed_cities, location_ids, addresses, collar, plant_code, file_type, summary,
        created_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    now = datetime.utcnow()
    
    try:
        logger.debug(f"Creating document with ID: {document_id}, title: {title}, user_id: {user_id}, file_type: {file_type}, summary: {'present' if summary else 'none'}")
        sql.execute(query, [
            str(document_id), title, user_id, user_name_masked, category_id, min_role_level, allowed_roles,
            allowed_countries, allowed_cities, location_ids, addresses, collar, plant_code, file_type, summary,
            now, now
        ])
        logger.info(f"✓ Document created successfully: {document_id} (title='{title}', type={file_type}, is_active will be DEFAULT=1)")
        
        # Verificar que foi criado com is_active=1
        doc = sql.execute_single("SELECT document_id, title, is_active FROM documents WHERE document_id = ?", [document_id])
        if doc:
            logger.info(f"✓ Verification: Document in DB - document_id={doc.get('document_id')}, is_active={doc.get('is_active')}")
        else:
            logger.error(f"✗ CRITICAL: Document NOT FOUND in DB immediately after creation! {document_id}")
        
        return document_id
    except Exception as e:
        logger.error(f"Failed to create document: {e}", exc_info=True)
        raise


def create_version(
    document_id: str,
    version_number: int,
    blob_path: str,
    file_type: Optional[str] = None,
    filename: Optional[str] = None,
    updated_by: Optional[str] = None,
    updated_by_name: Optional[str] = None
) -> int:
    """
    Create a new version record for a document.
    
    Args:
        file_type: File extension. Auto-extracted from document if not provided.
        filename: Nome do arquivo enviado (ex: "relatorio.pdf")
        updated_by: ID do usuário que fez o upload/atualização
        updated_by_name: Nome do usuário (será mascarado para LGPD compliance)
    
    Returns:
        version_number
    
    Note: This function assumes document_id already exists in the documents table.
    If FK constraint fails, it means the document_id doesn't exist in documents table.
    """
    from app.utils.name_masking import mask_user_name
    
    # Validação crítica: updated_by não deve ser None/vazio
    if not updated_by or (isinstance(updated_by, str) and updated_by.strip() == ""):
        logger.error(f"[create_version] CRITICAL: updated_by vazio ou None: {repr(updated_by)}")
        raise ValueError("updated_by é obrigatório e não pode estar vazio")
    
    logger.info(f"[create_version] updated_by validado: {repr(updated_by)}")
    
    # Mascarar updated_by_name se fornecido
    updated_by_name_masked = None
    if updated_by_name:
        try:
            updated_by_name_masked = mask_user_name(updated_by_name)
        except Exception as e:
            logger.warning(f"Erro ao mascarar updated_by_name: {e}")
    
    sql = get_sqlserver_connection()
    
    version_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Usar filename passado, ou extrair do blob_path
    if filename is None or filename.strip() == "":
        filename = blob_path.split('/')[-1] if blob_path else None
    
    # Se ainda não tem filename, pegar do título do documento
    if not filename:
        doc_query = "SELECT title FROM documents WHERE document_id = ?"
        doc = sql.execute_single(doc_query, [document_id])
        filename = doc.get('title') if doc else 'documento'
        logger.info(f"[create_version] filename não fornecido, usando document title: {filename}")
    
    # Auto-extract file_type from filename (prioritária) ou document title
    if file_type is None:
        # Tentar extrair do filename primeiro (mais confiável)
        if filename and "." in filename:
            file_type = filename.rsplit(".", 1)[-1].lower()
            logger.info(f"[create_version] file_type extraído do filename: {file_type}")
        else:
            # Fallback para title do documento
            doc_query = "SELECT title FROM documents WHERE document_id = ?"
            doc = sql.execute_single(doc_query, [document_id])
            if doc:
                file_type = doc.get('title', '').rsplit(".", 1)[-1].lower() if "." in doc.get('title', '') else "txt"
                logger.info(f"[create_version] file_type extraído do title: {file_type}")
            else:
                file_type = "txt"
                logger.warning(f"[create_version] Nenhuma extensão encontrada, usando padrão: txt")
    
    query = """
    INSERT INTO versions (
        version_id, document_id, version_number, blob_path, file_type,
        created_at, is_active, filename, updated_by, updated_by_name_masked
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        logger.info(f"[create_version] Starting: document_id={document_id}, version_number={version_number}, file_type={file_type}")
        
        # Verify document exists before insert
        check_query = "SELECT document_id FROM documents WHERE document_id = ?"
        existing_doc = sql.execute_single(check_query, [document_id])
        if not existing_doc:
            logger.error(f"[create_version] FATAL: document_id={document_id} does NOT exist in documents table. FK constraint will fail!")
            raise ValueError(f"Document with ID {document_id} does not exist in documents table. Cannot create version.")
        else:
            logger.info(f"[create_version] Verified: document_id exists in documents table")
        
        logger.info(f"[create_version] Executing INSERT: version_id={version_id}, document_id={document_id}, version={version_number}, filename={filename}, updated_by={updated_by}")
        sql.execute(query, [
            version_id, document_id, version_number, blob_path, file_type, now, 1, filename, updated_by, updated_by_name_masked
        ])
        
        # Atualizar updated_at do documento para refletir a nova versão
        update_doc_query = "UPDATE documents SET updated_at = ? WHERE document_id = ?"
        sql.execute(update_doc_query, [now, document_id])
        logger.info(f"[create_version] Updated document.updated_at = {now}")
        
        logger.info(f"[create_version] SUCCESS: Version {version_number} created for document {document_id} (type: {file_type}, updated_by={updated_by})")
        return version_number
    except ValueError as ve:
        logger.error(f"[create_version] Validation error: {ve}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"[create_version] Failed to create version: {e}", exc_info=True)
        raise


def get_document(document_id: str) -> Optional[Dict[str, Any]]:
    """Get document metadata with category name and description, including allowed_roles, summary and file_type."""
    from app.utils.name_masking import unmask_user_name
    
    sql = get_sqlserver_connection()
    
    query = """
    SELECT d.document_id, d.title, d.user_id, d.user_name_masked, d.category_id, d.min_role_level, d.allowed_roles,
           d.allowed_countries, d.allowed_cities, d.location_ids, d.addresses, d.collar, d.plant_code, d.summary, d.file_type,
           d.is_active, d.created_at, d.updated_at,
           c.category_name as category_name, c.description as category_description
    FROM documents d
    LEFT JOIN dim_categories c ON d.category_id = c.category_id
    WHERE d.document_id = ?
    """
    doc = sql.execute_single(query, [document_id])
    
    if doc:
        # Desmascarar nome do usuário criador
        user_name_masked = doc.get('user_name_masked')
        if user_name_masked:
            try:
                doc['user_name'] = unmask_user_name(user_name_masked)
            except Exception as e:
                logger.warning(f"Erro ao desmascarar nome do criador: {e}")
                doc['user_name'] = "Desconhecido"
        else:
            doc['user_name'] = "Desconhecido"
        
        # Remover campo mascarado do retorno (é interno, não enviar para front)
        doc.pop('user_name_masked', None)
    
    return doc


def get_document_by_title(title: str) -> Optional[Dict[str, Any]]:
    """Get document by title (check for duplicates across all users).
    Searches for exact match first, then fuzzy match using LIKE.
    """
    sql = get_sqlserver_connection()
    
    logger.info(f"[get_document_by_title] Searching for title: '{title}' (length={len(title)} chars)")
    
    # First try exact match
    logger.debug(f"[get_document_by_title] Trying exact match...")
    query = "SELECT TOP 1 * FROM documents WHERE title = ? AND is_active = 1 ORDER BY created_at DESC"
    result = sql.execute_single(query, [title])
    if result:
        logger.info(f"[get_document_by_title] ✓ EXACT MATCH FOUND: document_id={result.get('document_id')}, title='{result.get('title')}', is_active={result.get('is_active')}")
        return result
    
    logger.info(f"[get_document_by_title] ✗ No exact match found. Checking if document exists but is INACTIVE...")
    # Check if document exists but is inactive (for debugging)
    query_inactive = "SELECT TOP 1 document_id, title, is_active FROM documents WHERE title = ? ORDER BY created_at DESC"
    result_inactive = sql.execute_single(query_inactive, [title])
    if result_inactive:
        logger.warning(f"[get_document_by_title] ⚠️ Document exists with same title but IS_ACTIVE={result_inactive.get('is_active')} (INACTIVE). Not returning it.")
    
    logger.debug(f"[get_document_by_title] Trying fuzzy match...")
    
    # If no exact match, try fuzzy match with LIKE (80% similarity)
    # Use LIKE to find titles that contain most of the key words
    query = """
    SELECT TOP 1 * FROM documents 
    WHERE LOWER(title) LIKE LOWER(?) AND is_active = 1
    ORDER BY created_at DESC
    """
    # Create LIKE pattern - search for ~80% match
    like_pattern = f"%{title[:int(len(title)*0.8)]}%"
    logger.debug(f"[get_document_by_title] Fuzzy pattern: '{like_pattern}' (80% of '{title}')")
    result = sql.execute_single(query, [like_pattern])
    
    if result:
        logger.info(f"[get_document_by_title] ✓ FUZZY MATCH FOUND: document_id={result.get('document_id')}, title='{result.get('title')}'")
        return result
    
    logger.info(f"[get_document_by_title] ✗ NO MATCH FOUND for title: '{title}'")
    return None


def get_document_versions(document_id: str) -> List[Dict[str, Any]]:
    """Get all versions of a document with document title and category info."""
    from app.utils.name_masking import unmask_user_name
    
    sql = get_sqlserver_connection()
    
    query = """
    SELECT v.*, d.title, c.category_name, c.description as category_description
    FROM versions v
    LEFT JOIN documents d ON v.document_id = d.document_id
    LEFT JOIN dim_categories c ON d.category_id = c.category_id
    WHERE v.document_id = ? 
    ORDER BY v.version_number DESC
    """
    versions = sql.execute(query, [document_id])
    
    # Resolver filename vazio para versões antigas
    if versions:
        for version in versions:
            if not version.get('filename'):
                # Usar title + extensão detectada do blob_path
                doc_title = version.get('title', 'document').strip()
                blob_path = version.get('blob_path', '')
                
                # Extrair extensão do blob_path
                ext = '.docx'  # default
                if blob_path and '.' in blob_path:
                    ext = '.' + blob_path.rsplit('.', 1)[-1]
                
                version['filename'] = f"{doc_title}{ext}"
            
            # Desmascarar nome do usuário que atualizou
            updated_by_name_masked = version.get('updated_by_name_masked')
            if updated_by_name_masked:
                try:
                    version['updated_by_name'] = unmask_user_name(updated_by_name_masked)
                except Exception as e:
                    logger.warning(f"Erro ao desmascarar nome: {e}")
                    version['updated_by_name'] = version.get('updated_by', 'Desconhecido')
            else:
                version['updated_by_name'] = version.get('updated_by', 'Desconhecido')
            
            # Remover campo mascarado do retorno
            version.pop('updated_by_name_masked', None)
    
    return versions


def get_latest_version(document_id: str) -> Optional[Dict[str, Any]]:
    """Get latest version of a document."""
    sql = get_sqlserver_connection()
    
    query = """
    SELECT TOP 1 v.* FROM versions v
    JOIN documents d ON v.document_id = d.document_id
    WHERE v.document_id = ? AND v.is_active = 1 AND d.is_active = 1
    ORDER BY v.version_number DESC
    """
    return sql.execute_single(query, [document_id])


def get_all_document_versions(document_id: str) -> List[Dict[str, Any]]:
    """Get ALL versions of a document (including inactive), sorted by version_number descending."""
    from app.utils.name_masking import unmask_user_name
    
    sql = get_sqlserver_connection()
    
    query = """
    SELECT v.* FROM versions v
    WHERE v.document_id = ?
    ORDER BY v.version_number DESC
    """
    try:
        results = sql.execute(query, [document_id])
        if results:
            for version in results:
                # Desmascarar nome do usuário que atualizou
                updated_by_name_masked = version.get('updated_by_name_masked')
                if updated_by_name_masked:
                    try:
                        version['updated_by_name'] = unmask_user_name(updated_by_name_masked)
                    except Exception as e:
                        logger.warning(f"Erro ao desmascarar nome: {e}")
                        version['updated_by_name'] = version.get('updated_by', 'Desconhecido')
                else:
                    version['updated_by_name'] = version.get('updated_by', 'Desconhecido')
                
                # Remover campo mascarado do retorno
                version.pop('updated_by_name_masked', None)
        return results if results else []
    except Exception as e:
        logger.error(f"[get_all_document_versions] Error fetching all versions: {e}")
        return []


def get_version_by_number(document_id: str, version_number: int) -> Optional[Dict[str, Any]]:
    """Get specific version of a document by version_number."""
    from app.utils.name_masking import unmask_user_name
    
    sql = get_sqlserver_connection()
    
    query = """
    SELECT v.* FROM versions v
    JOIN documents d ON v.document_id = d.document_id
    WHERE v.document_id = ? AND v.version_number = ? AND v.is_active = 1 AND d.is_active = 1
    """
    version = sql.execute_single(query, [document_id, version_number])
    
    if version:
        # Desmascarar nome do usuário que atualizou
        updated_by_name_masked = version.get('updated_by_name_masked')
        if updated_by_name_masked:
            try:
                version['updated_by_name'] = unmask_user_name(updated_by_name_masked)
            except Exception as e:
                logger.warning(f"Erro ao desmascarar nome: {e}")
                version['updated_by_name'] = version.get('updated_by', 'Desconhecido')
        else:
            version['updated_by_name'] = version.get('updated_by', 'Desconhecido')
        
        # Remover campo mascarado do retorno
        version.pop('updated_by_name_masked', None)
    
    return version


def delete_version(document_id: str, version_number: int) -> bool:
    """Hard delete de uma versão específica (remove da tabela versions)."""
    sql = get_sqlserver_connection()
    
    try:
        logger.info(f"[delete_version] Deletando versão {version_number} do documento {document_id}")
        
        # DELETE real (hard delete) - remove a linha da tabela
        query = """
        DELETE FROM versions 
        WHERE document_id = ? AND version_number = ?
        """
        
        sql.execute(query, [document_id, version_number])
        logger.info(f"[delete_version] Versão {version_number} deletada permanentemente para documento {document_id}")
        return True
    except Exception as e:
        logger.error(f"[delete_version] Falha ao deletar versão {version_number}: {e}")
        raise


def delete_document(document_id: str) -> bool:
    """Mark all versions of a document as inactive (soft delete)."""
    sql = get_sqlserver_connection()
    
    query = """
    UPDATE versions 
    SET is_active = 0 
    WHERE document_id = ?
    """
    
    try:
        sql.execute(query, [document_id])
        logger.info(f"All versions marked as inactive for document {document_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to mark versions inactive for document {document_id}: {e}")
        raise


def update_document_metadata(
    document_id: str,
    title: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    min_role_level: Optional[int] = None,
    allowed_roles: Optional[str] = None,
    allowed_countries: Optional[str] = None,
    allowed_cities: Optional[str] = None,
    location_ids: Optional[str] = None,
    collar: Optional[str] = None,
    plant_code: Optional[int] = None,
    summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update metadata of existing document without creating new version.
    Used when user wants to just update category, is_active, min_role_level, etc.
    
    Se is_active=false, o documento será marcado como inativo no banco.
    O delete no LLM Server é feito no document_service.py (após chamar esta função)
    
    Aceita is_active em múltiplos formatos:
    - True/False (Python bool)
    - true/false (strings JSON)
    - 1/0 (int)
    """
    sql = get_sqlserver_connection()
    
    logger.info(f"[update_document_metadata] START: document_id={document_id}, is_active={is_active} (type: {type(is_active).__name__}), category_id={category_id}")
    
    # Verificar se documento existe
    query_check = "SELECT * FROM documents WHERE document_id = ?"
    existing_doc = sql.execute_single(query_check, [document_id])
    if not existing_doc:
        logger.error(f"[update_document_metadata] Documento {document_id} não encontrado no banco")
        raise ValueError(f"Documento com ID {document_id} não encontrado")
    
    logger.info(f"[update_document_metadata] Documento encontrado. Status atual: is_active={existing_doc.get('is_active')}")
    
    # Validar category_id (FK constraint check)
    if category_id is not None:
        query_category = "SELECT category_id FROM dim_categories WHERE category_id = ?"
        category_exists = sql.execute_single(query_category, [category_id])
        if not category_exists:
            raise ValueError(f"Categoria com ID {category_id} não existe em dim_categories. Use uma categoria válida.")
    
    # Normalizar is_active para aceitar múltiplos formatos
    is_active_normalized = None
    if is_active is not None:
        # Converter string "false"/"true" para bool
        if isinstance(is_active, str):
            is_active_str = is_active.lower().strip()
            if is_active_str in ("false", "0", "no"):
                is_active_normalized = False
                logger.info(f"[update_document_metadata] is_active string convertido: '{is_active}' → False")
            elif is_active_str in ("true", "1", "yes"):
                is_active_normalized = True
                logger.info(f"[update_document_metadata] is_active string convertido: '{is_active}' → True")
            else:
                raise ValueError(f"is_active inválido: '{is_active}'. Use: true/false, True/False, 1/0, 'yes'/'no'")
        # Converter int para bool
        elif isinstance(is_active, int):
            is_active_normalized = bool(is_active)
            logger.info(f"[update_document_metadata] is_active int convertido: {is_active} → {is_active_normalized}")
        # Já é bool
        else:
            is_active_normalized = bool(is_active)
            logger.info(f"[update_document_metadata] is_active já é bool: {is_active_normalized}")
    
    # Construir UPDATE dinâmico (atualizar apenas campos fornecidos)
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
        logger.info(f"[update_document_metadata] Atualizando title → {title}")
    
    if category_id is not None:
        updates.append("category_id = ?")
        params.append(category_id)
        logger.info(f"[update_document_metadata] Atualizando category_id → {category_id}")
    
    if is_active_normalized is not None:
        updates.append("is_active = ?")
        is_active_int = 1 if is_active_normalized else 0
        params.append(is_active_int)
        logger.info(f"[update_document_metadata] Updating is_active -> {is_active_normalized} (int: {is_active_int})")
        logger.info(f"[update_document_metadata] Status: INATIVAR = {not is_active_normalized}")
    
    if min_role_level is not None:
        updates.append("min_role_level = ?")
        params.append(min_role_level)
        logger.info(f"[update_document_metadata] Atualizando min_role_level → {min_role_level}")
    
    if allowed_roles is not None:
        updates.append("allowed_roles = ?")
        params.append(allowed_roles)
        logger.info(f"[update_document_metadata] Atualizando allowed_roles")
    
    if allowed_countries is not None:
        updates.append("allowed_countries = ?")
        params.append(allowed_countries)
        logger.info(f"[update_document_metadata] Atualizando allowed_countries")
    
    if allowed_cities is not None:
        updates.append("allowed_cities = ?")
        params.append(allowed_cities)
        logger.info(f"[update_document_metadata] Atualizando allowed_cities")
    
    if location_ids is not None:
        updates.append("location_ids = ?")
        params.append(location_ids)
        logger.info(f"[update_document_metadata] Atualizando location_ids")
    
    if collar is not None:
        updates.append("collar = ?")
        params.append(collar)
        logger.info(f"[update_document_metadata] Atualizando collar")
    
    if plant_code is not None:
        updates.append("plant_code = ?")
        params.append(plant_code)
        logger.info(f"[update_document_metadata] Atualizando plant_code")
    
    if summary is not None:
        updates.append("summary = ?")
        params.append(summary)
        logger.info(f"[update_document_metadata] Atualizando summary")
    
    # Sempre atualizar updated_at
    updates.append("updated_at = ?")
    params.append(datetime.utcnow())
    logger.info(f"[update_document_metadata] Atualizando updated_at")
    
    if len(updates) <= 1:  # Apenas updated_at foi adicionado
        logger.warning(f"[update_document_metadata] Nenhum campo fornecido para atualização (além de updated_at)")
        return existing_doc
    
    # Adicionar document_id no final dos params
    params.append(document_id)
    
    update_clause = ", ".join(updates)
    query = f"UPDATE documents SET {update_clause} WHERE document_id = ?"
    
    logger.info(f"[update_document_metadata] Query: {query}")
    logger.info(f"[update_document_metadata] Params (valores sem PII): updates={len(updates)} campos")
    
    try:
        logger.info(f"[update_document_metadata] ⏳ Executando UPDATE...")
        sql.execute(query, params)
        logger.info(f"[update_document_metadata] UPDATE executed successfully")
        
        # Retornar documento atualizado
        updated_doc = sql.execute_single(query_check, [document_id])
        logger.info(f"[update_document_metadata] Document after update:")
        logger.info(f"  - document_id: {updated_doc.get('document_id')}")
        logger.info(f"  - is_active: {updated_doc.get('is_active')} (esperado: {0 if is_active_normalized is False else '1 ou anterior'})")
        logger.info(f"  - updated_at: {updated_doc.get('updated_at')}")
        
        # Verificar se update foi bem-sucedido
        if is_active_normalized is not None:
            is_active_result = updated_doc.get('is_active')
            is_active_expected = 1 if is_active_normalized else 0
            if is_active_result == is_active_expected:
                logger.info(f"[update_document_metadata] is_active updated correctly to {is_active_result}")
            else:
                logger.error(f"[update_document_metadata] is_active NOT updated correctly! Expected: {is_active_expected}, Got: {is_active_result}")
        
        return updated_doc
    except Exception as e:
        logger.error(f"[update_document_metadata] Failed to update: {e}", exc_info=True)
        raise


def list_documents(user_id: Optional[str] = None, skip: int = 0, limit: int = 50, is_active: Optional[bool] = True) -> List[Dict[str, Any]]:
    """List documents with optional user filter and category description.
    
    Args:
        user_id: Filter by user ID (optional)
        skip: Number of rows to skip for pagination
        limit: Max rows to return
        is_active: Filter by active status. None=all, True=only active, False=only inactive
    """
    sql = get_sqlserver_connection()
    
    # Construir cláusula WHERE dinamicamente
    where_clauses = []
    params = []
    
    if user_id:
        where_clauses.append("d.user_id = ?")
        params.append(user_id)
    
    if is_active is not None:
        is_active_int = 1 if is_active else 0
        where_clauses.append(f"d.is_active = ?")
        params.append(is_active_int)
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    query = f"""
    SELECT d.document_id, d.title, d.user_id, d.user_name_masked, d.category_id, d.created_at, d.updated_at,
           d.is_active, d.min_role_level, d.allowed_roles, d.allowed_countries, d.allowed_cities,
           d.collar, d.plant_code, d.summary, d.file_type,
           c.category_name as category_name,
           c.description as category_description,
           COUNT(v.version_id) as version_count
    FROM documents d
    LEFT JOIN versions v ON d.document_id = v.document_id
    LEFT JOIN dim_categories c ON d.category_id = c.category_id
    WHERE {where_clause}
    GROUP BY d.document_id, d.title, d.user_id, d.user_name_masked, d.category_id, d.created_at, d.updated_at,
             d.is_active, d.min_role_level, d.allowed_roles, d.allowed_countries, d.allowed_cities,
             d.collar, d.plant_code, d.summary, d.file_type, c.category_name, c.description
    ORDER BY d.created_at DESC
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    
    params.extend([skip, limit])
    return sql.execute(query, params)

def save_temp_upload(
    temp_id: str,
    filename: str,
    blob_path: str,
    file_size_bytes: int,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Salvar metadados de upload temporário no banco.
    
    O arquivo será expirado após 10 minutos se não for confirmado.
    
    Parâmetros:
    - temp_id: UUID único para este upload
    - filename: nome original do arquivo
    - blob_path: caminho no blob storage (__temp__/1/temp_id_filename)
    - file_size_bytes: tamanho do arquivo
    - user_id: ID do usuário (opcional, será preenchido no ingest_confirm)
    
    Retorna:
    - temp_id, filename, blob_path, created_at, expires_at
    """
    sql = get_sqlserver_connection()
    
    now = datetime.utcnow()
    # Expira em 10 minutos
    from datetime import timedelta
    expires_at = now + timedelta(minutes=10)
    
    query = """
    INSERT INTO temp_uploads (temp_id, user_id, filename, blob_path, file_size_bytes, created_at, expires_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        logger.info(f"Saving temp upload: temp_id={temp_id}, filename={filename}, blob_path={blob_path}")
        sql.execute(query, [temp_id, user_id, filename, blob_path, file_size_bytes, now, expires_at])
        logger.info(f"Temp upload saved successfully. Expires at: {expires_at}")
        return {
            "temp_id": temp_id,
            "filename": filename,
            "blob_path": blob_path,
            "created_at": now,
            "expires_at": expires_at
        }
    except Exception as e:
        logger.error(f"Failed to save temp upload: {e}")
        raise


def get_temp_upload(temp_id: str) -> Optional[Dict[str, Any]]:
    """
    Recuperar metadados de upload temporário.
    
    Retorna None se:
    - temp_id não existe
    - já foi confirmado
    - expirou (created_at + 10min < now)
    """
    sql = get_sqlserver_connection()
    
    query = """
    SELECT temp_id, user_id, filename, blob_path, file_size_bytes, created_at, expires_at, is_confirmed
    FROM temp_uploads
    WHERE temp_id = ? AND is_confirmed = 0 AND expires_at > GETUTCDATE()
    """
    
    try:
        result = sql.execute(query, [temp_id])
        if result and len(result) > 0:
            return result[0]
        return None
    except Exception as e:
        logger.error(f"Failed to get temp upload: {e}")
        return None


def mark_temp_upload_confirmed(temp_id: str) -> bool:
    """
    Marcar upload temporário como confirmado.
    Isso impede que seja deletado pelo cleanup job.
    """
    sql = get_sqlserver_connection()
    
    query = """
    UPDATE temp_uploads
    SET is_confirmed = 1
    WHERE temp_id = ?
    """
    
    try:
        logger.info(f"Marking temp upload as confirmed: {temp_id}")
        sql.execute(query, [temp_id])
        logger.info(f"Temp upload marked as confirmed")
        return True
    except Exception as e:
        logger.error(f"Failed to mark temp upload as confirmed: {e}")
        return False


def delete_expired_temp_uploads() -> int:
    """
    Deletar uploads temporários expirados (mais de 10 minutos).
    Usado pelo background cleanup job.
    
    Retorna:
    - Número de registros deletados
    """
    sql = get_sqlserver_connection()
    
    query = """
    DELETE FROM temp_uploads
    WHERE expires_at < GETUTCDATE()
    """
    
    try:
        logger.info("Cleaning expired temp uploads...")
        result = sql.execute(query, [])
        deleted_count = sql.rowcount if hasattr(sql, 'rowcount') else 0
        logger.info(f"Deleted {deleted_count} expired temp uploads")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to delete expired temp uploads: {e}")
        return 0