"""
Document service: unified CRUD operations for documents.
Orchestrates: Blob Storage, SQL Server metadata, and LLM Server communication.
"""
import uuid
import re
import json
import logging
import os
import io
import csv as csv_module
import unicodedata
from typing import Optional, Dict, Any, List
from app.providers.storage import get_storage_provider
from app.providers.llm_server import get_llm_client
from app.providers.format_converter import FormatConverter
from app.services.sqlserver_documents import (
    create_document,
    create_version,
    get_document,
    get_latest_version,
    get_version_by_number,
    delete_version as db_delete_version,
    list_documents as db_list_documents
)

logger = logging.getLogger(__name__)


class DocumentService:
    """Unified document management service."""
    
    @staticmethod
    def _derive_location_data(location_id: Optional[int]) -> Dict[str, Any]:
        """
        Derive location data (country, city, address, location_name) from location_id.
        
        Returns dict with location data, or empty dict if location_id is None/invalid.
        Does NOT raise error - logs warning instead for graceful fallback.
        """
        if not location_id:
            return {}
        
        try:
            from app.core.sqlserver import get_sqlserver_connection
            sql = get_sqlserver_connection()
            query = """
            SELECT location_id, country_name, state_name, city_name, location_name, address, region, continent, operation_type
            FROM dim_electrolux_locations
            WHERE location_id = ?
            """
            results = sql.execute(query, [location_id])
            
            if not results:
                logger.warning(f"⚠️  Location ID {location_id} not found - will use manual allowed_countries if provided")
                return {}
            
            loc = results[0]
            return {
                "location_id": loc["location_id"],
                "country_name": loc.get("country_name"),
                "city_name": loc.get("city_name"),
                "location_name": loc.get("location_name"),
                "address": loc.get("address") or "",
                "state_name": loc.get("state_name"),
                "region": loc.get("region"),
                "continent": loc.get("continent"),
                "operation_type": loc.get("operation_type")
            }
        except Exception as e:
            logger.warning(f"⚠️  Error deriving location data for location_id {location_id}: {e}")
            return {}
    
    @staticmethod
    def _normalize_input(value, expected_type='list', allow_json=True, convert_to_int=False) -> Optional[List]:
        """
        Normaliza input flexível para o tipo esperado.
        
        Suporta múltiplos formatos:
        - String com vírgulas: "item1,item2" → [item1, item2]
        - JSON string: '["item1"]' → [item1]
        - List: [item1] → [item1]
        - Single value: "item" → [item]
        
        Parâmetros:
        - value: Valor a normalizar
        - expected_type: 'list' ou 'single'
        - allow_json: Se True, tenta parse JSON antes de split
        - convert_to_int: Se True, tenta converter cada item para int
        
        Retorna:
        - List[] se expected_type='list' (vazio se value inválido)
        - Single value se expected_type='single'
        - None se value inválido e expected_type='single'
        """
        if not value:
            return [] if expected_type == 'list' else None
        
        # Se é list, normalizar cada item
        if isinstance(value, list):
            normalized = []
            for v in value:
                item = str(v).strip() if v else None
                if item:
                    if convert_to_int:
                        try:
                            normalized.append(int(item))
                        except (ValueError, TypeError):
                            normalized.append(item)
                    else:
                        normalized.append(item)
            return normalized
        
        # Se é string
        if isinstance(value, str):
            # Tentar JSON primeiro se permitido
            if allow_json:
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        normalized = []
                        for v in parsed:
                            item = str(v).strip() if v else None
                            if item:
                                if convert_to_int:
                                    try:
                                        normalized.append(int(item))
                                    except (ValueError, TypeError):
                                        normalized.append(item)
                                else:
                                    normalized.append(item)
                        return normalized
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
            
            # Fallback: comma-separated
            normalized = []
            for item in value.split(","):
                item = item.strip()
                if item:
                    if convert_to_int:
                        try:
                            normalized.append(int(item))
                        except (ValueError, TypeError):
                            normalized.append(item)
                    else:
                        normalized.append(item)
            return normalized
        
        # Se value é número/outro tipo
        if expected_type == 'list':
            return [value] if value else []
        return value
    
    @staticmethod
    def _normalize_allowed_cities(cities_input) -> List[str]:
        """
        Normalizar allowed_cities para array.
        
        Input pode ser:
        - String com vírgulas: "São Paulo,Rio de Janeiro"
        - String única: "São Paulo"
        - Array: ["São Paulo", "Rio de Janeiro"]
        - JSON string: '["São Paulo", "Rio de Janeiro"]'
        
        Output: Lista de cidades (sempre array)
        """
        return DocumentService._normalize_input(cities_input, expected_type='list', allow_json=True, convert_to_int=False)
    
    @staticmethod
    def _normalize_allowed_countries(countries_input) -> List[str]:
        """
        Normalizar allowed_countries para array.
        
        Input pode ser:
        - String com vírgulas: "Brazil,Argentina"
        - String única: "Brazil"
        - Array: ["Brazil", "Argentina"]
        - JSON string: '["Brazil", "Argentina"]'
        
        Output: Lista de países (sempre array)
        """
        return DocumentService._normalize_input(countries_input, expected_type='list', allow_json=True, convert_to_int=False)
    
    @staticmethod
    def _serialize_allowed_cities(cities_input) -> Optional[str]:
        """
        Converter allowed_cities para JSON string para salvar no banco.
        
        Input: qualquer formato aceito por _normalize_allowed_cities
        Output: JSON string como '["São Paulo"]' ou None se vazio
        """
        normalized = DocumentService._normalize_allowed_cities(cities_input)
        if not normalized:
            return None
        return json.dumps(normalized, ensure_ascii=False)
    
    @staticmethod
    def _serialize_allowed_countries(countries_input) -> Optional[str]:
        """
        Converter allowed_countries para string separada por vírgula para salvar no banco.
        Mantém compatibilidade com dados legados que estão como CSV strings.
        
        Input (List[str]): ["Brazil", "Chile", "Peru"]
        Output: "Brazil,Chile,Peru"
        
        Input (string): "Brazil,Chile,Peru"
        Output: "Brazil,Chile,Peru"
        
        Input (None): None
        """
        if not countries_input:
            return None
        
        # Se já é string, retorna como está
        if isinstance(countries_input, str):
            return countries_input.strip() if countries_input.strip() else None
        
        # Se é lista, junta com vírgula
        if isinstance(countries_input, list):
            # Filtra strings vazias e junta
            clean_items = [str(c).strip() for c in countries_input if c]
            return ",".join(clean_items) if clean_items else None
        
        return None
    
    @staticmethod
    def _serialize_roles(roles_input) -> Optional[str]:
        """
        Converter roles em JSON array.
        
        Input (lista de ints): [4, 5, 6]
        Output: '[4, 5, 6]'
        
        Input (string de números): "4,5,8,9,10" ou "4, 5, 8, 9, 10"
        Output: '[4, 5, 8, 9, 10]' (convertidos para inteiros)
        
        Input (string de nomes): "admin,manager,supervisor"
        Output: '["admin", "manager", "supervisor"]'
        
        Input (None): None
        Output: None
        """
        if not roles_input:
            return None
        
        try:
            # Usar helper que suporta convert_to_int
            normalized = DocumentService._normalize_input(roles_input, expected_type='list', allow_json=True, convert_to_int=True)
            
            if not normalized:
                return None
            
            return json.dumps(normalized)
            
        except Exception as e:
            logger.warning(f"Erro ao serializar roles: {e}")
            return None
    
    @staticmethod
    def _serialize_location_ids(location_ids_input) -> Optional[str]:
        """
        Converter location_ids em JSON array string.
        
        Input (lista de ints): [123, 456, 789]
        Output: '[123, 456, 789]'
        
        Input (string de números): "123,456,789" ou "123, 456, 789"
        Output: '[123, 456, 789]' (convertidos para inteiros)
        
        Input (None/empty): None
        Output: None
        """
        if not location_ids_input:
            return None
        
        try:
            # Usar helper que suporta convert_to_int
            normalized = DocumentService._normalize_input(location_ids_input, expected_type='list', allow_json=True, convert_to_int=True)
            
            if not normalized:
                return None
            
            return json.dumps(normalized)
            
        except Exception as e:
            logger.warning(f"Erro ao serializar location_ids: {e}")
            return None

    @staticmethod
    def _prepare_allowed_cities_for_llm(allowed_cities: Optional[str], location_data: Dict[str, Any]) -> List[str]:
        """
        Preparar allowed_cities para envio ao LLM.
        
        IMPORTANTE: O comportamento depende se location_id foi fornecido:
        
        Cenário 1 - COM location_id:
        - Ignora allowed_cities manual
        - Retorna apenas ["city_name, address"] do location
        - Motivo: evitar confusão com múltiplas cidades
        
        Cenário 2 - SEM location_id:
        - Retorna allowed_cities normalizado (sem mudanças)
        - Usuário pode fornecer múltiplas cidades livremente
        
        Exemplos:
        - location_data vazio: _prepare_allowed_cities_for_llm("São Paulo,Rio", {}) → ["São Paulo", "Rio"]
        - location_data com dados: _prepare_allowed_cities_for_llm("São Paulo,Rio", {city_name: "SP", address: "Rua X"}) → ["SP, Rua X"]
        """
        # Se NÃO houver location_data, apenas normalizar e retornar
        if not location_data:
            return DocumentService._normalize_allowed_cities(allowed_cities)
        
        # COM location_data (location_id foi fornecido)
        city_name = location_data.get("city_name")
        address = location_data.get("address")
        
        # Montar string com city + address
        if city_name and address:
            return [f"{city_name}, {address}"]
        elif city_name:
            return [city_name]
        elif address:
            return [address]
        
        # Se não conseguiu extrair nada, voltar para normalizado
        return DocumentService._normalize_allowed_cities(allowed_cities)
    
    # ===== JSON Utilities =====
    
    @staticmethod
    def _safe_json_loads(raw_json: str, default=None) -> Any:
        """
        Parse JSON com fallback seguro.
        
        Evita repetição de try/except em vários lugares.
        
        Args:
            raw_json: String com JSON
            default: Valor padrão se falhar o parse
            
        Returns:
            Dict/List parsed ou default se inválido
        """
        if not raw_json:
            return default
        
        try:
            return json.loads(raw_json)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(f"Failed to parse JSON: {e}")
            return default
    
    @staticmethod
    def _ensure_json_string(value) -> Optional[str]:
        """
        Garante que value é uma JSON string válida (ou None).
        
        Converts dict/list to JSON, validates strings, returns None if invalid.
        
        Args:
            value: Qualquer tipo (dict, list, string, None)
            
        Returns:
            Valid JSON string ou None
        """
        if value is None:
            return None
        
        if isinstance(value, str):
            # Validar se é JSON válido
            try:
                json.loads(value)
                return value
            except (json.JSONDecodeError, TypeError):
                return None
        
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except Exception:
                return None
        
        return None
    
    @staticmethod
    def _normalize_document_fields(doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza todos os campos de um documento para formato consistente.
        
        Faz:
        1. Parse de allowed_roles JSON → array de inteiros
        2. Parse de allowed_countries (JSON/CSV) → array de strings
        3. Parse de allowed_cities (JSON/CSV) → array de strings
        4. Desmascarar user_name_masked → user_name
        
        Args:
            doc: Dict com dados do documento (como vem do BD)
            
        Returns:
            Dict normalizado pronto para retornar na API
        """
        if not doc:
            return doc
        
        from app.utils.name_masking import unmask_user_name
        
        try:
            # Parse allowed_roles JSON
            allowed_roles_raw = doc.get("allowed_roles")
            if allowed_roles_raw:
                try:
                    doc["allowed_roles"] = json.loads(allowed_roles_raw)
                except:
                    pass  # Keep as is if not valid JSON
            
            # Parse allowed_countries (JSON ou CSV)
            allowed_countries_raw = doc.get("allowed_countries")
            if allowed_countries_raw:
                try:
                    doc["allowed_countries"] = json.loads(allowed_countries_raw)
                except:
                    # Se não for JSON válido, normalizar de CSV ou string simples
                    doc["allowed_countries"] = DocumentService._normalize_allowed_countries(allowed_countries_raw)
            else:
                doc["allowed_countries"] = None
            
            # Parse allowed_cities (JSON ou CSV)
            allowed_cities_raw = doc.get("allowed_cities")
            if allowed_cities_raw:
                try:
                    doc["allowed_cities"] = json.loads(allowed_cities_raw)
                except:
                    # Se não for JSON válido, normalizar para array
                    doc["allowed_cities"] = DocumentService._normalize_allowed_cities(allowed_cities_raw)
            else:
                doc["allowed_cities"] = None
            
            # Parse location_ids (JSON array de inteiros) → renomear para allowed_location_ids
            location_ids_raw = doc.get("location_ids")
            if location_ids_raw:
                try:
                    doc["allowed_location_ids"] = json.loads(location_ids_raw)
                except:
                    # Se não for JSON válido, tenta normalizar como CSV
                    doc["allowed_location_ids"] = DocumentService._normalize_input(location_ids_raw, expected_type='list', allow_json=False, convert_to_int=True)
            else:
                doc["allowed_location_ids"] = None
            
            # Remover o campo antigo location_ids (usar allowed_location_ids)
            doc.pop('location_ids', None)
            
            # Desmascarar nome do usuário (se present)
            user_name_masked = doc.get('user_name_masked')
            if user_name_masked:
                try:
                    doc['user_name'] = unmask_user_name(user_name_masked)
                except Exception as e:
                    logger.warning(f"[_normalize_document_fields] Erro ao desmascarar user_name: {e}")
                    doc['user_name'] = "Desconhecido"
                # Remover campo mascarado do retorno (é interno)
                doc.pop('user_name_masked', None)
            else:
                doc['user_name'] = doc.get('user_name', "Desconhecido")
                doc.pop('user_name_masked', None)
            
        except Exception as e:
            logger.warning(f"[_normalize_document_fields] Erro ao normalizar documento: {e}")
        
        return doc
    
    @staticmethod
    async def ingest_document(
        file: Optional[Any] = None,
        user_id: str = None,
        user_name: Optional[str] = None,
        document_id: Optional[str] = None,
        title: Optional[str] = None,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        min_role_level: int = 1,
        allowed_roles: Optional[str] = None,
        allowed_countries: Optional[List[str]] = None,
        allowed_cities: Optional[str] = None,
        allowed_location_ids: Optional[str] = None,
        collar: Optional[str] = None,
        plant_code: Optional[int] = None,
        summary: Optional[str] = None,
        force_ingest: bool = False
    ) -> Dict[str, Any]:
        """
        Ingest new document or update existing:
        
        MODO 1: Com arquivo (file não é None)
        1. Save to Blob Storage
        2. Create/update metadata in SQL Server
        3. Create new version
        
        MODO 2: Sem arquivo (file é None)
        1. document_id é obrigatório (documento existente)
        2. Apenas atualiza metadados (category_id, is_active, min_role_level, etc)
        3. NÃO cria nova versão
        4. Se is_active=false, remove do LLM Server
        
        Parâmetro document_id:
        - Com arquivo + None → novo documento (auto-generate UUID)
        - Com arquivo + passado → nova versão do documento existente
        - Sem arquivo + passado → atualizar apenas metadados
        
        Parâmetro category_id:
        - ID da categoria (FK para dim_categories)
        
        Parâmetro category_id:
        - ID da categoria (FK para dim_categories)
        """
        
        # Validação crítica: user_id é obrigatório
        if not user_id or (isinstance(user_id, str) and user_id.strip() == ""):
            logger.error(f"[ingest_document] CRITICAL: user_id vazio ou None: {repr(user_id)}")
            raise ValueError("user_id é obrigatório e não pode estar vazio")
        
        # Inicializar flag de duplicata
        was_duplicate = False
        
        # MODO 2: Apenas atualizar metadados (sem arquivo)
        if file is None:
            logger.info(f"[ingest_document] MODO 2: Atualizar apenas metadados")
            if not document_id:
                raise ValueError("document_id é obrigatório quando não enviando arquivo (metadata update)")
            
            # Apenas atualizar metadados do documento existente
            from app.services.sqlserver_documents import update_document_metadata
            
            logger.info(f"[ingest_document] Atualizando metadados do documento: {document_id}")
            
            # Serializar allowed_roles se fornecido
            allowed_roles_json = None
            if allowed_roles:
                allowed_roles_json = DocumentService._serialize_roles(allowed_roles)
                logger.info(f"[ingest_document] Serialized roles: {allowed_roles} → {allowed_roles_json}")
            
            updated_doc = update_document_metadata(
                document_id=document_id,
                title=title,
                category_id=category_id,
                is_active=is_active,
                min_role_level=min_role_level,
                allowed_roles=allowed_roles_json,
                allowed_countries=DocumentService._serialize_allowed_countries(allowed_countries),
                allowed_cities=DocumentService._serialize_allowed_cities(allowed_cities),
                location_ids=DocumentService._serialize_location_ids(allowed_location_ids),
                collar=collar,
                plant_code=plant_code,
                summary=summary
            )
            logger.info(f"[ingest_document] Metadados atualizados com sucesso")
            
            # Se is_active=false (inativar documento), remover do LLM Server
            if is_active is False:
                logger.info(f"[ingest_document] Inativando documento no LLM Server: {document_id}")
                try:
                    llm_client = get_llm_client()
                    llm_client.delete_document(document_id)
                    logger.info(f"[ingest_document] Documento removido do LLM Server com sucesso")
                except Exception as e:
                    logger.warning(f"[ingest_document] Erro ao remover do LLM Server: {e}")
            else:
                # Se is_active não foi setado para false, pode ter havido mudanças de metadados
                # (allowed_cities, allowed_countries, category_id, allowed_location_ids, etc)
                # Nesse caso, fazer re-ingest no LLM com os novos metadados
                if any([allowed_countries is not None, allowed_cities is not None, 
                        category_id is not None, min_role_level is not None, 
                        allowed_location_ids is not None]):
                    logger.info(f"[ingest_document] Mudanças de metadados detectadas (incluindo location_ids) - re-ingestando no LLM")
                    try:
                        # Buscar a versão mais recente do documento
                        latest_version = get_latest_version(str(document_id))
                        if latest_version:
                            logger.info(f"[ingest_document] Recuperando versão {latest_version['version_number']} do blob")
                            
                            # Recuperar arquivo do blob storage
                            storage = get_storage_provider()
                            blob_path = latest_version.get('blob_path')
                            if blob_path:
                                file_content = await storage.download_blob(blob_path)
                                # Usar o title se disponível (tem extensão), senão usar filename
                                filename = updated_doc.get('title') or latest_version.get('filename', 'document')
                                logger.info(f"[ingest_document] Usando filename para conversão: {filename}")
                                
                                # Re-ingestar no LLM com os novos metadados
                                llm_client = get_llm_client()
                                csv_content, _ = FormatConverter.convert_to_csv(file_content, filename)
                                
                                # Usar os novos valores ou manter os antigos
                                final_category_id = category_id if category_id is not None else updated_doc.get('category_id')
                                final_min_role_level = min_role_level if min_role_level is not None else updated_doc.get('min_role_level', 1)
                                final_allowed_roles = allowed_roles_json if allowed_roles_json is not None else updated_doc.get('allowed_roles')
                                final_allowed_countries = allowed_countries if allowed_countries is not None else (updated_doc.get('allowed_countries', '') or [])
                                final_allowed_cities = allowed_cities if allowed_cities is not None else updated_doc.get('allowed_cities', '')
                                
                                logger.info(f"[ingest_document] 🔄 Re-ingestando no LLM com:")
                                logger.info(f"[ingest_document]   - document_id: {document_id}")
                                logger.info(f"[ingest_document]   - filename: {filename}")
                                logger.info(f"[ingest_document]   - category_id: {final_category_id}")
                                logger.info(f"[ingest_document]   - allowed_cities (antes): {final_allowed_cities}")
                                logger.info(f"[ingest_document]   - allowed_cities (split): {final_allowed_cities.split(',') if final_allowed_cities else []}")
                                logger.info(f"[ingest_document]   - allowed_countries: {final_allowed_countries}")
                                logger.info(f"[ingest_document]   - csv_content tamanho: {len(csv_content)} chars")
                                
                                # Converter allowed_location_ids de string comma-separated para list de inteiros
                                final_allowed_location_ids = DocumentService._normalize_input(allowed_location_ids, expected_type='list', allow_json=False, convert_to_int=True) or []
                                
                                llm_response = llm_client.ingest_document(
                                    document_id=str(document_id),
                                    file_content=csv_content,
                                    filename=filename,
                                    user_id=updated_doc.get('user_id'),
                                    title=updated_doc.get('title'),
                                    category_id=final_category_id,
                                    min_role_level=final_min_role_level,
                                    allowed_roles=json.loads(final_allowed_roles) if final_allowed_roles else list(range(1, 16)),
                                    allowed_countries=final_allowed_countries if isinstance(final_allowed_countries, list) else (final_allowed_countries.split(",") if final_allowed_countries else []),
                                    allowed_cities=DocumentService._normalize_allowed_cities(final_allowed_cities),
                                    allowed_location_ids=final_allowed_location_ids,
                                    version_id=latest_version['version_number']
                                )
                                logger.info(f"[ingest_document] Document re-ingested in LLM with new metadata")
                                logger.info(f"[ingest_document] LLM Response Success: {llm_response.get('success') if llm_response else 'None'}")
                                logger.info(f"[ingest_document] LLM Response Chunks Created: {llm_response.get('chunks_created') if llm_response else 'None'}")
                                logger.info(f"[ingest_document] LLM Response Full: {json.dumps(llm_response, default=str)}")
                                
                                if llm_response.get('success') is not True:
                                    logger.error(f"[ingest_document] LLM returned error on re-ingest: {llm_response}")
                            else:
                                logger.warning(f"[ingest_document] Versão não tem blob_path, pulando re-ingest")
                        else:
                            logger.warning(f"[ingest_document] Nenhuma versão encontrada, pulando re-ingest")
                    except Exception as e:
                        logger.error(f"[ingest_document] Error re-ingesting metadata in LLM: {e}", exc_info=True)
            
            return {
                "status": "success",
                "message": "Metadados do documento atualizados" + (" e removido do LLM Server" if is_active is False else " e re-ingestado no LLM com novos metadados" if any([allowed_countries is not None, allowed_cities is not None, category_id is not None, min_role_level is not None]) else ""),
                "document_id": document_id,
                "title": updated_doc.get("title"),
                "type": "metadata_update",
                "is_active": is_active
            }
        
        # MODO 1: Com arquivo (criar novo ou atualizar com versão)
        logger.info(f"[ingest_document] MODO 1: Ingest com arquivo")
        
        # Validate file format (only accept formats that LLM Server supports)
        ACCEPTED_FORMATS = ["pdf", "docx", "doc", "xlsx", "xls", "csv", "txt"]
        file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
        
        if file_ext not in ACCEPTED_FORMATS:
            raise ValueError(
                f"Formato de arquivo '{file_ext.upper() if file_ext else 'unknown'}' não suportado. "
                f"Formatos aceitos: {', '.join([f.upper() for f in ACCEPTED_FORMATS])}"
            )
        
        logger.info(f"[ingest_document] Formato do arquivo validado: {file_ext.upper()}")
        
        # Read file
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8", errors="ignore")
        original_name = file.filename
        
        try:
            # STEP 1: Convert to CSV format FIRST - this extracts text properly from PDFs
            logger.info(f"[ingest] STEP 1: Convertendo para CSV (extrai texto de PDF corretamente)")
            csv_content, original_format = FormatConverter.convert_to_csv(raw_bytes, original_name)
            logger.info(f"Converted {original_name} ({original_format}) to CSV format")
            logger.info(f"CSV content size: {len(csv_content)} chars")
            
            # STEP 2: Clean the CSV content to remove metadata
            logger.info(f"[ingest] STEP 2: Limpando conteúdo de metadados")
            cleaned_content = DocumentService._clean_text_content(csv_content)
            size_reduction = 100 - (len(cleaned_content)*100//len(csv_content) if len(csv_content) > 0 else 0)
            logger.info(f"[ingest] Conteúdo limpo: {len(csv_content)} chars -> {len(cleaned_content)} chars (redução: {size_reduction}%)")
            
            # STEP 3: Check for duplicate documents with same or similar title across all users
            from app.services.sqlserver_documents import get_document_by_title
            logger.info(f"STEP 3: Checking for duplicate documents with title '{original_name}'")
            existing_doc = get_document_by_title(original_name)
            was_duplicate = False
            is_forced_new = False
            
            if existing_doc and document_id is None:
                if force_ingest:
                    # Force new document mesmo com titulo duplicado
                    logger.info(f"Found existing document with title '{original_name}' but force_ingest=True, creating NEW document")
                    is_forced_new = True
                else:
                    # Found existing document with same/similar title - this is an update (new version)
                    logger.info(f"Found existing document with similar title '{original_name}', treating as update (document_id={existing_doc.get('document_id')})")
                    document_id = existing_doc.get('document_id')
                    was_duplicate = True
            
            # STEP 4: Prepare document data (without saving yet)
            if document_id is None:
                # Novo documento: gerar UUID
                import uuid
                document_id = str(uuid.uuid4())
                version_number = 1
                logger.info(f"🆔 STEP 4: Generated NEW document ID (UUID): {document_id}")
                logger.info(f"🆔 IMPORTANTE: Este ID será usado para LLM Server E SQL Server")
            else:
                # Documento existente: next version
                logger.info(f"STEP 4: Using existing document with ID={document_id}")
                latest_version = get_latest_version(str(document_id))
                if latest_version:
                    version_number = latest_version.get('version_number', 0) + 1
                    logger.info(f"STEP 4: Latest active version is {latest_version.get('version_number')}, next version number={version_number}")
                else:
                    # Se não encontrou versão ativa, buscar a versão mais alta (mesmo que inativa)
                    from app.services.sqlserver_documents import get_all_document_versions
                    all_versions = get_all_document_versions(str(document_id))
                    if all_versions:
                        max_version = max([v.get('version_number', 0) for v in all_versions])
                        version_number = max_version + 1
                        logger.warning(f"STEP 4: No active version found. Highest version is {max_version}, next version number={version_number}")
                    else:
                        # Nenhuma versão encontrada (documento órfão) - começar do 1
                        version_number = 1
                        logger.warning(f"STEP 4: No versions found for document {document_id}, starting from version 1")
            
            # Serializar roles
            allowed_roles_json = DocumentService._serialize_roles(allowed_roles)
            logger.info(f"STEP 4a: Serialized roles: {allowed_roles} → {allowed_roles_json}")
            
            # IMPORTANTE: Call LLM FIRST before saving anything to SQL or Blob
            # If LLM fails, entire operation fails (no rollback needed, nothing was saved yet)
            logger.info(f"[ingest] STEP 5: Calling LLM Server FIRST for validation and embedding")
            llm_response = None
            llm_status = "skipped"
            final_summary = summary  # Inicializar com o summary passado pelo usuário
            
            if os.getenv("SKIP_LLM_SERVER") != "true" and is_active is not False:
                # Enviar para LLM apenas se não foi marcado como inativo
                llm_client = get_llm_client()
                logger.info(f"[ingest] STEP 5: Sending to LLM Server: doc_id={document_id}, version={version_number}")
                
                # Extrair doc_type do nome do arquivo
                if "." in original_name:
                    doc_type = original_name.rsplit(".", 1)[-1].lower()
                else:
                    doc_type = "txt"
                
                # Normalizar doc para docx (mesma lógica no LLM Server)
                doc_type_for_llm = "docx" if doc_type == "doc" else doc_type
                
                logger.info(f"[ingest] Extraindo metadata (doc_type={doc_type_for_llm}, include_summary=True)")
                metadata = llm_client.extract_metadata(
                    text=cleaned_content,
                    filename=original_name,
                    doc_type=doc_type_for_llm,
                    include_summary=True
                )
                extracted_summary = metadata.get("summary")
                logger.info(f"[ingest] Metadata extraído: summary={'presente' if extracted_summary else 'não encontrado'}")
                
                # Se o usuário já passou um summary, use o dele; caso contrário, use o extraído
                final_summary = summary if summary else extracted_summary
                
                # Converter allowed_location_ids de string comma-separated para list de inteiros
                final_allowed_location_ids = DocumentService._normalize_input(allowed_location_ids, expected_type='list', allow_json=False, convert_to_int=True) or []
                
                llm_response = llm_client.ingest_document(
                    document_id=str(document_id),
                    file_content=csv_content,
                    filename=original_name,
                    user_id=user_id,
                    title=original_name,
                    category_id=category_id,
                    min_role_level=min_role_level,
                    allowed_roles=json.loads(allowed_roles_json) if allowed_roles_json else list(range(1, 16)),
                    allowed_countries=allowed_countries if isinstance(allowed_countries, list) else (allowed_countries.split(",") if allowed_countries else []),
                    allowed_cities=DocumentService._normalize_allowed_cities(allowed_cities),
                    allowed_location_ids=final_allowed_location_ids,
                    version_id=version_number
                )
                llm_status = "success"
                logger.info(f"[ingest] LLM Server accepted document, now saving to SQL and Blob")
            else:
                if is_active is False:
                    logger.info(f"[ingest] STEP 5: Pulando LLM Server (documento marcado como inativo)")
                else:
                    logger.info(f"[ingest] LLM Server skipped (SKIP_LLM_SERVER=true)")
            
            # NOW that LLM succeeded, create document in SQL Server
            logger.info(f"STEP 6: Creating/updating document in SQL Server")
            if was_duplicate is False and document_id:
                # Check if this is actually a new document or existing
                existing = get_document(str(document_id))
                if not existing:
                    logger.info(f"STEP 6: Creating NEW document in SQL Server: {document_id}")
                    # Usar title fornecido pelo usuário, ou fallback para original_name
                    final_title = title if title else original_name
                    document_id = create_document(
                        title=final_title,
                        user_id=user_id,
                        user_name=user_name,
                        category_id=category_id,
                        min_role_level=min_role_level,
                        allowed_roles=allowed_roles_json,
                        allowed_countries=DocumentService._serialize_allowed_countries(allowed_countries),
                        allowed_cities=DocumentService._serialize_allowed_cities(allowed_cities),
                        location_ids=DocumentService._serialize_location_ids(allowed_location_ids),
                        collar=collar,
                        plant_code=plant_code,
                        summary=final_summary,
                        document_id=document_id
                    )
                    logger.info(f"STEP 6: Document created successfully with ID={document_id}")
                    logger.info(f"🆔 CRITICAL VERIFICATION: DB document_id = {document_id} (must match LLM Server ID from STEP 5)")
                else:
                    logger.info(f"STEP 6: Document already exists: {document_id}")
            
            # Save to Blob Storage
            logger.info(f"STEP 7: Saving document to Blob Storage")
            storage = get_storage_provider()
            blob_path = storage.save_file(str(document_id), version_number, original_name, raw_bytes)
            logger.info(f"Document saved to Blob: {blob_path}")
            
            # Create version in SQL Server
            logger.info(f"STEP 8: Creating version in SQL Server - document_id={document_id}, version={version_number}, blob_path={blob_path}, file_ext={file_ext}, updated_by={user_id}")
            logger.info(f"STEP 8: user_id validation: user_id={repr(user_id)}, type={type(user_id)}, is_empty={not user_id or (isinstance(user_id, str) and user_id.strip() == '')}")
            created_version = create_version(
                document_id=str(document_id),
                version_number=version_number,
                blob_path=blob_path,
                file_type=file_ext,
                filename=original_name,
                updated_by=user_id,
                updated_by_name=user_name
            )
            logger.info(f"Version {version_number} created in SQL Server with file_type={file_ext}, updated_by={user_id}")
            
            chunks_count = 0
            
            logger.info("Document ingested successfully and sent to LLM Server")
            
            response = {
                "status": "success",
                "document_id": document_id,
                "version": version_number,
                "chunks_count": chunks_count,
                "blob_path": blob_path,
                "title": original_name,
                "message": "Document ingested successfully and sent to LLM Server for embedding",
                "preview": {
                    "original_size_chars": len(csv_content),
                    "cleaned_size_chars": len(cleaned_content),
                    "size_reduction_percent": 100 - (len(cleaned_content)*100//len(csv_content) if len(csv_content) > 0 else 0),
                    "first_500_chars": cleaned_content[:500]
                }
            }
            
            # Adicionar aviso se foi uma versão nova de documento existente
            if was_duplicate:
                response["is_new_version"] = True
                response["message"] = f"VERSAO NOVA: Documento com titulo '{original_name}' ja existe. Criada versao {version_number}. Document ID permanece: {document_id}"
                response["duplicate_handling"] = "auto_updated_as_new_version"
                logger.info(f"Documento duplicado tratado como nova versao")
            elif is_forced_new:
                response["is_new_document"] = True
                response["message"] = f"NOVO DOCUMENTO (force_ingest=True): Documento com mesmo nome '{original_name}' criado como SEPARADO. Document ID novo: {document_id}"
                response["duplicate_handling"] = "force_created_as_separate"
                logger.info(f"Documento com titulo duplicado criado separadamente por force_ingest")
            
            return response
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            raise
    
    @staticmethod
    async def ingest_preview(file) -> Dict[str, Any]:
        """
        Preview de ingestão - extrai metadados do arquivo sem persistir.
        
        Steps:
        1. Salva arquivo em armazenamento temporário
        2. Salva metadados do upload temporário no banco de dados
        3. Extrai texto do arquivo (limitado a 15KB para preview)
        4. Chama LLM Server para extrair metadados sugeridos
        5. Retorna temp_id + metadados sugeridos
        
        Nota: O arquivo será expirado em 10 minutos se não for confirmado via /ingest-confirm
        """
        try:
            # STEP 1: Save to temp storage
            import uuid
            temp_id = str(uuid.uuid4())
            storage = get_storage_provider()
            raw_bytes = await file.read()
            file_size_bytes = len(raw_bytes)
            
            # Salvar em pasta temporária
            temp_path = storage.save_file("__temp__", 1, f"{temp_id}_{file.filename}", raw_bytes)
            logger.info(f"File saved to temp storage: {temp_path}")
            
            # STEP 2: Save temp upload metadata to database (for retrieval in ingest_confirm)
            from app.services.sqlserver_documents import save_temp_upload
            # user_id será preenchido no ingest_confirm
            save_temp_upload(
                temp_id=temp_id,
                filename=file.filename,
                blob_path=temp_path,
                file_size_bytes=file_size_bytes
            )
            logger.info(f"Temp upload metadata saved to database with 10min expiration")
            
            # STEP 3: Convert file to CSV format (handles PDF, Excel, DOCX, etc.)
            logger.info(f"Converting {file.filename} to CSV format...")
            csv_content, original_format = FormatConverter.convert_to_csv(raw_bytes, file.filename)
            logger.info(f"Converted {file.filename} ({original_format}) to CSV format: {len(csv_content)} chars")
            
            # Para preview, usar só os primeiros 15KB do texto (evita erro 422 em arquivos grandes)
            # PDFs e outros formatos já foram convertidos para CSV limpo
            MAX_PREVIEW_SIZE = 15 * 1024  # 15KB
            preview_content = csv_content[:MAX_PREVIEW_SIZE]
            
            if len(csv_content) > MAX_PREVIEW_SIZE:
                logger.info(f"CSV size {len(csv_content)} chars exceeds preview limit {MAX_PREVIEW_SIZE}. Using first {MAX_PREVIEW_SIZE} chars")
            
            # Clean the text: remove any remaining binary/metadata
            # This significantly reduces payload size for LLM Server
            cleaned_preview = DocumentService._clean_text_content(preview_content)
            logger.info(f"Cleaned preview: {len(preview_content)} chars -> {len(cleaned_preview)} chars")
            
            # NOTE: ingest_preview is temporary - LLM processing happens in /ingest or /ingest_confirm
            # This just shows cleaned text for user to review before confirming
            
            # STEP 4: Verificar se já existe documento com mesmo título (ANTES de chamar LLM)
            from app.services.sqlserver_documents import get_document_by_title
            existing_doc = None
            try:
                logger.info(f"[ingest_preview] STEP 4: Procurando documento duplicado com título: '{file.filename}'")
                existing_doc = get_document_by_title(file.filename)
                if existing_doc:
                    logger.warning(f"[ingest_preview] DUPLICATA DETECTADA - documento_id={existing_doc.get('document_id')}, title={existing_doc.get('title')}")
            except Exception as title_err:
                logger.warning(f"[ingest_preview] get_document_by_title failed, continuing without duplicate check: {title_err}")
                existing_doc = None
            
            # STEP 3b: Extract metadata from LLM Server with summary
            metadata = {}
            try:
                llm_client = get_llm_client()
                # Detect document type from filename extension (actual format)
                if "." in file.filename:
                    doc_type = file.filename.rsplit(".", 1)[-1].lower()
                else:
                    doc_type = "txt"
                
                # Normalizar doc para docx (mesma lógica no LLM Server)
                doc_type_for_llm = "docx" if doc_type == "doc" else doc_type
                
                metadata = llm_client.extract_metadata(
                    text=cleaned_preview,
                    filename=file.filename,
                    doc_type=doc_type_for_llm,
                    include_summary=True
                )
                logger.info(f"Metadata extracted from LLM with doc_type={doc_type_for_llm}, summary={'present' if metadata.get('summary') else 'not found'}")
            except Exception as e:
                logger.warning(f"Failed to extract metadata: {e}. Continuing with empty metadata")
                metadata = {}
            
            response = {
                "status": "success",
                "temp_id": temp_id,
                "filename": file.filename,
                "file_size_bytes": file_size_bytes,
                "csv_size_chars": len(csv_content),
                "preview_size_chars": len(preview_content),
                "cleaned_preview_chars": len(cleaned_preview),
                "size_reduction_percent": 100 - (len(cleaned_preview)*100//len(preview_content) if len(preview_content) > 0 else 0),
                "extracted_fields": metadata,
                "expires_in_minutes": 10,
                "next_step": f"POST /api/v1/documents/ingest-confirm/{temp_id} with metadata to confirm",
                "preview_sample": {
                    "summary": metadata.get("summary"),
                    "first_300_chars": cleaned_preview[:300],
                    "full_cleaned_preview": cleaned_preview if len(cleaned_preview) < 1000 else cleaned_preview[:1000] + "..."
                },
                "is_duplicate": existing_doc is not None,
                "document_type": "new" if not existing_doc else "version_update"
            }
            
            # CRÍTICO: Se encontrou duplicata, DEVE retornar o ID existente
            if existing_doc:
                response["warning"] = f"⚠️ DUPLICATA DETECTADA - Documento com título '{file.filename}' já existe"
                response["existing_document_id"] = existing_doc.get("document_id")
                response["existing_document_info"] = {
                    "document_id": existing_doc.get("document_id"),
                    "title": existing_doc.get("title"),
                    "user_id": existing_doc.get("user_id"),
                    "created_at": existing_doc.get("created_at"),
                    "version_count": existing_doc.get("version_count", "unknown"),
                    "is_active": existing_doc.get("is_active")
                }
                response["next_step"] = f"POST /api/v1/documents/ingest-confirm/{temp_id} com 'document_id={existing_doc.get('document_id')}' para criar NOVA VERSÃO"
                response["suggestion"] = "Para criar nova versão do documento existente, passe 'document_id' no confirm. Sem ele, um novo documento será criado!"
                logger.info(f"[ingest_preview] DUPLICATA - retornando existing_document_id={existing_doc.get('document_id')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Preview failed: {e}")
            raise

    @staticmethod
    def _clean_text_content(text: str) -> str:
        """
        Remove non-printable, binary, and metadata characters from PDF/document text.
        Keep ASCII printable characters + accented characters (Portuguese, Spanish, etc).
        
        Preserves: Letters (a-z, A-Z, áéíóúàâôãõç), numbers, spaces, punctuation, newlines.
        Removes: 
        - XML/RDF tags with content: <rdf:*, <xmp:*, <dc:*
        - Binary markers, control characters (0x00-0x1F, 0x7F-0x9F)
        - UUIDs, timestamps, document IDs, metadata prefixes (uuid:, id:, etc)
        - Creator/tool metadata (Microsoft Word, etc)
        - PDF noise and binary markers
        
        Example:
            "<xmp:CreatorTool>Microsoft Word</xmp:CreatorTool>" → "" (todo removido, é metadata)
            "uuid:2CD71D8B-11A5..." → "" (removido, é ID)
            "Benefícios de Saúde" → "Benefícios de Saúde" (preservado)
        """
        import re
        
        # Step 0: Remove carriage returns and weird PDF artifacts
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Step 1: Remove XML/RDF tags WITH their content (not just the tags)
        # Match opening and closing tags: <xmp:*>content</xmp:*>
        text = re.sub(r'<(?:xmp|rdf|dc|pdf):[^>]*>.*?</(?:xmp|rdf|dc|pdf):[^>]*>', '', text, flags=re.DOTALL)
        
        # Step 2: Remove remaining XML/RDF tags (just the tags themselves)
        # Match tags like <rdf:*, <xmp:*, <dc:*, xmlns:*, etc
        text = re.sub(r'<[^>]*>', '', text)
        
        # Step 3: Remove metadata prefixes AND their full values (everything until newline)
        # Remove patterns like "uuid:2CD71D8B-...", "id: some-document-id", "author: John Doe", etc
        # Captures prefix + everything until end of line (handles multi-word values)
        text = re.sub(r'\b(?:uuid|id|author|creator|tool|version|date|time):\s*[^\n]*', '', text, flags=re.IGNORECASE)
        
        # Step 4: (unused - kept for clarity) Originally was Step 4
        
        # Step 5: Remove standalone UUIDs (xxxx-xxxx-xxxx-xxxx pattern) without prefix
        text = re.sub(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', '', text)
        
        # Step 6: Remove ISO timestamps (2025-03-26T14:32:56 pattern)
        text = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\s]*', '', text)
        
        # Step 7: Remove common creator tools (Microsoft Word, Adobe, etc)
        text = re.sub(r'\b(?:Microsoft|Adobe|Word|Acrobat|Excel|PowerPoint|Office|365)\b', '', text, flags=re.IGNORECASE)
        
        # Step 8: Remove control characters and binary markers (0x00-0x1F, 0x7F-0x9F)
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        
        # Step 9: Keep alphanumerics, accented chars, common punctuation & symbols
        # INCLUDE: ~ (til) para São, § (parágrafo), ° (grau)
        # INCLUDE: @ for emails, $ for currency, / for dates, & for abbreviations
        text = re.sub(
            r'[^\w\s\.\,\!\?\;:\-\(\)\[\]\"\'\/@&$%~§°\u0100-\uFFFF]', 
            '', 
            text
        )
        
        # Step 10: Remove sequences of quotes/empty strings ("" or '')
        text = re.sub(r'["\'][\s]*["\']', ' ', text)
        
        # Step 11: Collapse multiple spaces/newlines into single space
        text = re.sub(r'[\s]+', ' ', text)
        
        # Step 12: Remove leading/trailing whitespace
        text = text.strip()
        
        return text

    @staticmethod
    async def ingest_confirm(
        temp_id: str,
        user_id: str,
        user_name: Optional[str] = None,
        document_id: Optional[str] = None,
        title: Optional[str] = None,
        category_id: Optional[int] = None,
        min_role_level: int = 1,
        allowed_roles: Optional[str] = None,
        allowed_countries: Optional[str] = None,
        allowed_cities: Optional[str] = None,
        allowed_location_ids: Optional[str] = None,
        collar: Optional[str] = None,
        plant_code: Optional[int] = None,
        summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Confirmar ingestão após revisão de metadados (fluxo preview + confirm).
        
        Workflow:
        1. /ingest-preview → salva em __temp__, extrai metadados
        2. Usuário revisa metadados
        3. /ingest-confirm → recupera de __temp__, salva permanentemente
        
        Steps:
        1. Recupera arquivo da pasta temporária (__temp__)
        2. Salva em Blob Storage permanente (documents/{document_id}/v{version}/)
        3. Cria documento no SQL Server
        4. Cria versão para rastrear histórico
        5. Deleta arquivo temporário
        
        Parâmetro document_id:
        - Se None → novo documento (auto-generate UUID)
        - Se passado → atualizar documento existente (nova versão)
        
        Parâmetro category_id:
        - ID da categoria (FK para dim_categories)
        
        Parâmetro allowed_location_ids:
        - String: separada por vírgula (ex: "1,2,3") ou JSON array (ex: "[1,2,3]")
        - Será convertida para List[int]
        """
        try:
            # Parse allowed_location_ids: string → List[int]
            location_ids_list: Optional[List[int]] = None
            if allowed_location_ids:
                try:
                    if isinstance(allowed_location_ids, str):
                        # Tentar JSON array primeiro (ex: "[1,2,3]")
                        if allowed_location_ids.startswith('['):
                            location_ids_list = json.loads(allowed_location_ids)
                        else:
                            # Separada por vírgula (ex: "1,2,3")
                            location_ids_list = [int(x.strip()) for x in allowed_location_ids.split(',') if x.strip()]
                    elif isinstance(allowed_location_ids, list):
                        # Já é lista
                        location_ids_list = [int(x) for x in allowed_location_ids]
                    logger.info(f"[ingest_confirm] allowed_location_ids parseado: {allowed_location_ids} → {location_ids_list}")
                except Exception as parse_err:
                    logger.warning(f"[ingest_confirm] Erro ao fazer parse de allowed_location_ids: {parse_err}. Ignorando.")
                    location_ids_list = None
            
            # Validação crítica: user_id é obrigatório
            if not user_id or (isinstance(user_id, str) and user_id.strip() == ""):
                logger.error(f"[ingest_confirm] CRITICAL: user_id vazio ou None: {repr(user_id)}")
                raise ValueError("user_id é obrigatório e não pode estar vazio")
            
            # AVISO CRÍTICO: document_id não foi passado
            if document_id is None:
                logger.warning(f"[ingest_confirm] ⚠️ IMPORTANTE: document_id=None - NOVO DOCUMENTO será criado")
                logger.warning(f"[ingest_confirm] Se havia duplicata no preview, o document_id dessa duplicata deveria ter sido passado aqui!")
                logger.warning(f"[ingest_confirm] Para criar VERSÃO de documento existente, passe 'document_id' como Form parameter no confirm")
            else:
                logger.info(f"[ingest_confirm] ✓ document_id fornecido - será criada NOVA VERSÃO: {document_id}")
            
            logger.info(f"[ingest_confirm] START: temp_id={temp_id}, user_id={user_id}, document_id={document_id}, category_id={category_id}")
            
            storage = get_storage_provider()
            from app.services.sqlserver_documents import (
                create_document, get_latest_version, create_version,
                get_temp_upload, mark_temp_upload_confirmed
            )
            
            # STEP 1: Recuperar metadados de upload temporário do banco de dados
            logger.info(f"[ingest_confirm] STEP 1: Recuperando temp_upload metadata do banco")
            
            temp_upload = get_temp_upload(temp_id)
            if not temp_upload:
                raise FileNotFoundError(
                    f"Upload temporário não encontrado ou expirou (temp_id={temp_id}). "
                    f"Use /ingest-preview para gerar um novo temp_id."
                )
            
            temp_blob_path = temp_upload.get('blob_path')
            original_filename = temp_upload.get('filename')
            logger.info(f"[ingest_confirm] Temp upload encontrado: path={temp_blob_path}, filename={original_filename}")
            
            # STEP 2: Recuperar arquivo do storage (funciona com Local e Azure)
            logger.info(f"[ingest_confirm] STEP 2: Recuperando arquivo do blob storage")
            try:
                file_content_bytes = storage.get_file(temp_blob_path)
                logger.info(f"[ingest_confirm] Arquivo recuperado: {len(file_content_bytes)} bytes")
            except Exception as e:
                logger.error(f"[ingest_confirm] Erro ao recuperar arquivo: {e}")
                raise FileNotFoundError(f"Não conseguiu recuperar arquivo temporário: {str(e)}")
            
            # Detectar formato do arquivo
            file_ext = ""
            if "." in original_filename:
                file_ext = original_filename.rsplit(".", 1)[-1].lower()
            
            # STEP 2b: Extract text based on format
            logger.info(f"[ingest_confirm] STEP 2b: Extraindo texto (formato: {file_ext})")
            
            # Para DOCX e XLSX: usar FormatConverter (extrai corretamente)
            # Para PDF e TXT: usar decode UTF-8 como antes (já funciona)
            if file_ext in ['docx', 'doc', 'xlsx', 'xls']:
                logger.info(f"[ingest_confirm] Formato {file_ext}: usando FormatConverter para extração correta")
                csv_content_for_text, _ = FormatConverter.convert_to_csv(file_content_bytes, original_filename)
                csv_reader = csv_module.reader(io.StringIO(csv_content_for_text))
                csv_rows = list(csv_reader)
                text_content = ""
                if len(csv_rows) > 1:
                    for row in csv_rows[1:]:
                        if row:
                            text_content += " ".join(row) + "\n"
                else:
                    text_content = csv_content_for_text
            else:
                logger.info(f"[ingest_confirm] Formato {file_ext}: usando decode UTF-8 (método original)")
                text_content = file_content_bytes.decode('utf-8', errors='ignore') if isinstance(file_content_bytes, bytes) else file_content_bytes
            
            cleaned_text_content = DocumentService._clean_text_content(text_content)
            
            # Validação: truncar para 50K chars se exceder (limite do LLM Server)
            MAX_CHARS_FOR_LLM = 50000
            original_size = len(cleaned_text_content)
            if len(cleaned_text_content) > MAX_CHARS_FOR_LLM:
                logger.warning(f"[ingest_confirm] Text exceeds {MAX_CHARS_FOR_LLM} chars ({original_size} chars). Truncating...")
                cleaned_text_content = cleaned_text_content[:MAX_CHARS_FOR_LLM]
                logger.info(f"[ingest_confirm] Texto truncado de {original_size} para {len(cleaned_text_content)} chars")
            
            logger.info(f"[ingest_confirm] Texto extraído e processado: {len(text_content)} chars -> {len(cleaned_text_content)} chars")
            
            # CRITICAL STEP: Send to LLM Server BEFORE saving to permanent storage
            # If LLM fails, we don't waste time/storage on document that can't be used
            logger.info(f"[ingest_confirm] STEP 2c: CHAMANDO LLM SERVER PRIMEIRO (antes de salvar permanentemente)")
            
            # Convert to CSV format - PASS ORIGINAL BYTES for proper extraction
            csv_content, _ = FormatConverter.convert_to_csv(file_content_bytes, original_filename)
            
            # Gerar document_id temporário se não foi fornecido
            temp_doc_id_for_llm = None
            llm_status = "skipped"
            llm_error = None
            llm_response = None
            final_summary = summary  # Inicializar com o summary passado pelo usuário
            
            if document_id is None:
                import uuid
                temp_doc_id_for_llm = str(uuid.uuid4())
            else:
                temp_doc_id_for_llm = str(document_id)
            
            # Serializar roles ANTES de usar (necessário para LLM Server)
            allowed_roles_json = DocumentService._serialize_roles(allowed_roles)
            logger.info(f"[ingest_confirm] Serialized roles: {allowed_roles} → {allowed_roles_json}")
            
            if os.getenv("SKIP_LLM_SERVER") != "true":
                try:
                    llm_client = get_llm_client()
                    
                    logger.info(f"[ingest_confirm] Preparando ingestão para LLM:")
                    logger.info(f"[ingest_confirm]   document_id: {temp_doc_id_for_llm}")
                    logger.info(f"[ingest_confirm]   filename: {original_filename}")
                    logger.info(f"[ingest_confirm]   user_id: {user_id}")
                    logger.info(f"[ingest_confirm]   min_role_level: {min_role_level}")
                    logger.info(f"[ingest_confirm]   allowed_roles: {json.loads(allowed_roles_json) if allowed_roles_json else []}")
                    logger.info(f"[ingest_confirm]   allowed_countries: {allowed_countries if isinstance(allowed_countries, list) else (allowed_countries.split(',') if allowed_countries else [])}")
                    logger.info(f"[ingest_confirm]   allowed_cities: {allowed_cities.split(',') if allowed_cities else []}")
                    logger.info(f"[ingest_confirm]   csv_content size: {len(csv_content)} chars")
                    
                    # Extract metadata including summary
                    if "." in original_filename:
                        doc_type = original_filename.rsplit(".", 1)[-1].lower()
                    else:
                        doc_type = "txt"
                    
                    # Normalizar doc para docx (mesma lógica no LLM Server)
                    doc_type_for_llm = "docx" if doc_type == "doc" else doc_type
                    
                    logger.info(f"[ingest_confirm] Extraindo metadata (doc_type={doc_type_for_llm}, include_summary=True)")
                    metadata = llm_client.extract_metadata(
                        text=cleaned_text_content,
                        filename=original_filename,
                        doc_type=doc_type_for_llm,
                        include_summary=True
                    )
                    extracted_summary = metadata.get("summary")
                    logger.info(f"[ingest_confirm] Metadata extraído: summary={'presente' if extracted_summary else 'não encontrado'}")
                    
                    # Se o usuário já passou um summary, use o dele; caso contrário, use o extraído
                    final_summary = summary if summary else extracted_summary
                    
                    llm_response = llm_client.ingest_document(
                        document_id=temp_doc_id_for_llm,
                        file_content=csv_content,
                        filename=original_filename,
                        user_id=user_id,
                        title=original_filename,
                        category_id=category_id,
                        min_role_level=min_role_level,
                        allowed_roles=json.loads(allowed_roles_json) if allowed_roles_json else list(range(1, 16)),
                        allowed_countries=allowed_countries if isinstance(allowed_countries, list) else (allowed_countries.split(",") if allowed_countries else []),
                        allowed_cities=DocumentService._normalize_allowed_cities(allowed_cities),
                        allowed_location_ids=location_ids_list,
                        version_id=1
                    )
                    llm_status = "success"
                    logger.info(f"[ingest_confirm] Document sent to LLM Server successfully")
                    logger.info(f"[ingest_confirm] LLM Response: {llm_response}")
                except Exception as llm_err:
                    llm_status = "failed"
                    llm_error = str(llm_err)
                    logger.error(f"[ingest_confirm] Failed to send to LLM Server: {llm_err}", exc_info=True)
                    raise  # Falha aqui - não continua
            else:
                logger.info(f"[ingest_confirm] LLM Server skipped (SKIP_LLM_SERVER=true)")
                final_summary = summary
            
            # STEP 3: Usar temp_doc_id_for_llm (já foi enviado ao LLM Server)
            # CRÍTICO: document_id deve ser o MESMO que foi enviado ao LLM Server!
            # Não gerar um novo UUID aqui - isso causa desalinhamento
            is_new_document = document_id is None
            if is_new_document:
                # Reutilizar o ID que foi enviado ao LLM Server
                document_id = temp_doc_id_for_llm
                logger.info(f"[ingest_confirm] STEP 3: Novo documento - reutilizando ID enviado ao LLM: {document_id}")
            else:
                # document_id foi fornecido (vem do ingest_preview)
                # Verificar que ele realmente existe na tabela (é_ativo=1)
                logger.info(f"[ingest_confirm] STEP 3: document_id fornecido - verificando se existe no banco: {document_id}")
                from app.services.sqlserver_documents import get_document as check_doc_exists
                existing_doc = check_doc_exists(document_id)
                if existing_doc:
                    if existing_doc.get('is_active') != 1:
                        raise ValueError(f"Documento existe mas está INATIVO (is_active={existing_doc.get('is_active')}). Não pode criar versão de documento inativo.")
                    logger.info(f"[ingest_confirm] STEP 3: ✓ Documento encontrado e ATIVO - será criada nova versão")
                else:
                    raise ValueError(f"Documento com ID '{document_id}' não encontrado no banco. Verifique o ID fornecido.")
            
            # STEP 4: Criar/atualizar documento no SQL Server
            logger.info(f"[ingest_confirm] STEP 4: Criando documento no SQL Server (is_new_document={is_new_document})")
            
            # Usar title fornecido pelo usuário, ou fallback para original_filename
            final_title = title if title else original_filename
            
            if is_new_document:
                # Criar novo documento
                logger.info(f"[ingest_confirm] STEP 4: Novo documento - chamando create_document")
                final_document_id = create_document(
                    title=final_title,
                    user_id=user_id,
                    user_name=user_name,
                    category_id=category_id,
                    min_role_level=min_role_level,
                    allowed_roles=allowed_roles_json,
                    allowed_countries=DocumentService._serialize_allowed_countries(allowed_countries),
                    allowed_cities=DocumentService._serialize_allowed_cities(allowed_cities),
                    location_ids=DocumentService._serialize_location_ids(location_ids_list),
                    collar=collar,
                    plant_code=plant_code,
                    summary=final_summary,
                    document_id=document_id
                )
            else:
                # Documento já existe (vem do preview via get_document_by_title)
                # Confiar no ID passado e criar nova versão
                final_document_id = document_id
                logger.info(f"[ingest_confirm] STEP 4: Documento já existe (document_id passado do preview) - reutilizando ID")
            
            logger.info(f"[ingest_confirm] STEP 4: Documento criado/reutilizado: {final_document_id}")
            
            # STEP 5: Determinar número da versão
            logger.info(f"[ingest_confirm] STEP 5: Determinando versão")
            # Verificar se é novo documento ou atualização
            if is_new_document:
                # Novo documento sempre inicia na versão 1.
                version_number = 1
                logger.info(f"[ingest_confirm] Novo documento, version_number=1")
            else:
                # Documento existente - obter próxima versão
                logger.info(f"[ingest_confirm] Documento existente: {final_document_id}")
                latest_version = get_latest_version(str(final_document_id))
                if latest_version:
                    version_number = latest_version.get('version_number', 0) + 1
                    logger.info(f"[ingest_confirm] Latest active version is {latest_version.get('version_number')}, next version_number={version_number}")
                else:
                    # Se não encontrou versão ativa, buscar a versão mais alta (mesmo que inativa)
                    from app.services.sqlserver_documents import get_all_document_versions
                    all_versions = get_all_document_versions(str(final_document_id))
                    if all_versions:
                        max_version = max([v.get('version_number', 0) for v in all_versions])
                        version_number = max_version + 1
                        logger.warning(f"[ingest_confirm] No active version found. Highest version is {max_version}, next version_number={version_number}")
                    else:
                        # Nenhuma versão encontrada (documento órfão) - começar do 1
                        version_number = 1
                        logger.warning(f"[ingest_confirm] No versions found for document {final_document_id}, starting from version 1")
            
            # STEP 6: Salvar arquivo permanentemente no Blob Storage
            logger.info(f"[ingest_confirm] STEP 6: Salvando arquivo permanentemente")
            permanent_blob_path = storage.save_file(final_document_id, version_number, original_filename, file_content_bytes)
            logger.info(f"[ingest_confirm] Arquivo salvo: {permanent_blob_path}")
            
            # STEP 7: Criar versão no SQL Server
            logger.info(f"[ingest_confirm] STEP 7: Criando registro de versão com file_ext={file_ext}, updated_by={user_id}")
            created_version = create_version(
                document_id=str(final_document_id),
                version_number=version_number,
                blob_path=permanent_blob_path,
                file_type=file_ext,
                filename=original_filename,
                updated_by=user_id,
                updated_by_name=user_name
            )
            logger.info(f"[ingest_confirm] Versão criada com sucesso (version_number={version_number}, file_type={file_ext}, updated_by={user_id})")
            
            # STEP 8: Marcar temp upload como confirmado (impede que seja deletado pelo cleanup)
            logger.info(f"[ingest_confirm] STEP 8: Marcando upload temporário como confirmado")
            mark_temp_upload_confirmed(temp_id)
            logger.info(f"[ingest_confirm] Upload temporário marcado como confirmado (não será deletado)")
            
            # STEP 9: Deletar arquivo temporário do storage (opcional - pode deixar cleanup fazer)
            logger.info(f"[ingest_confirm] STEP 9: Deletando arquivo temporário do blob storage")
            try:
                storage.delete_file(temp_blob_path)
                logger.info(f"[ingest_confirm] Arquivo temporário deletado do blob")
            except Exception as e:
                logger.warning(f"[ingest_confirm] Não foi possível deletar arquivo temporário do blob: {e}")
            
            logger.info(f"[ingest_confirm] SUCCESS: Ingestão confirmada e finalizada (LLM já foi chamado antes de salvar)")
            
            # Preparar preview visual do documento confirmado
            preview_text = cleaned_text_content[:500]  # Primeiros 500 chars do texto limpo
            size_reduction = 100 - (len(cleaned_text_content)*100//len(csv_content) if len(csv_content) > 0 else 0)
            
            response = {
                "status": "success",
                "message": "Ingestão confirmada e salva permanentemente (Azure/Local compatible). LLM embedding concluído.",
                "document_id": final_document_id,
                "version": version_number,
                "blob_path": permanent_blob_path,
                "temp_id": temp_id,
                "user_id": user_id,
                "filename": original_filename,
                "category_id": category_id,
                "metadata": {
                    "min_role_level": min_role_level,
                    "allowed_countries": allowed_countries,
                    "allowed_cities": allowed_cities,
                    "collar": collar,
                    "plant_code": plant_code
                },
                "llm_server": {
                    "status": llm_status,
                    "error": llm_error,
                    "response": llm_response
                },
                "preview": {
                    "original_size_chars": len(csv_content),
                    "cleaned_size_chars": len(cleaned_text_content),
                    "size_reduction_percent": size_reduction,
                    "first_500_chars": preview_text
                }
            }
            
            # ADIÇÃO CRÍTICA: Se document_id foi None, significa que criou novo documento
            # Isso é importante para alertar o frontend/usuário
            if is_new_document:
                response["document_type"] = "new"
                response["info"] = "✓ NOVO DOCUMENTO criado com sucesso"
            else:
                response["document_type"] = "version_update"
                response["info"] = f"✓ NOVA VERSÃO criada para documento existente (v{version_number})"
            
            return response
        except Exception as e:
            logger.error(f"[ingest_confirm] FAILED: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def delete_version(
        document_id: str,
        version_number: int
    ) -> Dict[str, Any]:
        """
        Delete a specific document version:
        1. Delete from Blob Storage
        2. Mark as inactive in SQL Server
        3. If last version: Delete from LLM Server
        4. If previous version exists: Re-ingest to LLM Server
        """
        
        try:
            # STEP 1: Get document metadata
            # Runtime import keeps compatibility with tests that patch sqlserver_documents.get_document.
            from app.services import sqlserver_documents as _sql_docs
            doc = _sql_docs.get_document(document_id)
            if not doc:
                return {"status": "error", "message": "Document not found"}
            
            # STEP 2: Delete from Blob Storage
            storage = get_storage_provider()
            blob_folder = f"documents/{document_id}/{version_number}"
            storage.delete_folder(blob_folder)
            logger.info(f"Deleted from Blob: {blob_folder}")
            
            # STEP 3: Mark version as inactive in SQL Server
            db_delete_version(document_id, version_number)
            logger.info(f"Version {version_number} marked as inactive in SQL Server")
            
            # STEP 4: Check for previous versions
            latest_version = get_latest_version(document_id)
            
            if not latest_version:
                # No active versions - delete entire document from LLM Server
                if os.getenv("SKIP_LLM_SERVER") != "true":
                    llm_client = get_llm_client()
                    llm_client.delete_document(document_id)
                logger.info(f"Document {document_id} deleted from LLM Server")
                
                return {
                    "status": "success",
                    "message": f"Version {version_number} deleted. No active versions remaining. Document removed from LLM Server."
                }
            else:
                # Previous version exists - re-ingest to LLM Server
                logger.info(f"Re-ingesting version {latest_version['version_number']} to LLM Server")
                
                # Read file from Blob
                prev_blob_path = latest_version['blob_path']
                prev_content = storage.get_file(prev_blob_path)
                content = prev_content.decode("utf-8", errors="ignore")
                filename = latest_version.get('original_filename', f"document-v{latest_version['version_number']}")
                
                # Convert to CSV format with header
                csv_content, _ = FormatConverter.convert_to_csv(content, filename)
                
                # Re-ingest to LLM Server with CSV format
                if os.getenv("SKIP_LLM_SERVER") != "true":
                    llm_client = get_llm_client()
                    
                    # Extrair location_ids do documento
                    location_ids_json = doc.get('location_ids')
                    location_ids_list = []
                    if location_ids_json:
                        try:
                            location_ids_list = json.loads(location_ids_json) if isinstance(location_ids_json, str) else (location_ids_json or [])
                        except json.JSONDecodeError:
                            logger.warning(f"[delete_version] Failed to parse location_ids JSON: {location_ids_json}")
                    
                    llm_response = llm_client.ingest_document(
                        document_id=str(document_id),
                        file_content=csv_content,  # Send as CSV with header
                        filename=filename,
                        user_id=doc.get('created_by', 'system'),
                        title=doc.get('title', filename),
                        category_id=doc.get('category_id'),
                        min_role_level=doc.get('min_role_level', 1),
                        allowed_roles=json.loads(doc.get('allowed_roles')) if doc.get('allowed_roles') else list(range(1, 16)),
                        allowed_countries=(doc.get('allowed_countries') if isinstance(doc.get('allowed_countries'), list) else (doc.get('allowed_countries', '').split(",") if doc.get('allowed_countries') else [])),
                        allowed_cities=DocumentService._normalize_allowed_cities(doc.get('allowed_cities', [])),
                        allowed_location_ids=location_ids_list,
                        version_id=latest_version['version_number']
                    )
                    logger.info(f"Version {latest_version['version_number']} re-ingested to LLM Server as CSV")
                
                return {
                    "status": "success",
                    "message": f"Version {version_number} deleted. Version {latest_version['version_number']} re-ingested to LLM Server."
                }
            
        except Exception as e:
            logger.error(f"Delete operation failed: {e}")
            raise
    @staticmethod
    async def list_documents(
        filename: Optional[str] = None,
        user_id: Optional[str] = None,
        category_id: Optional[int] = None,
        location_id: Optional[int] = None,
        file_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        min_role_level: Optional[int] = None,
        allowed_countries: Optional[str] = None,
        allowed_cities: Optional[str] = None,
        collar: Optional[str] = None,
        plant_code: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """
        Listar documentos com filtros opcionais.
        Busca informações do SQL Server (documento_id, user_id, version, timestamp, etc).
        
        Args:
            file_type: Filtrar por tipo de arquivo (pdf, docx, xlsx, csv, txt, etc)
            is_active: None = retorna ambos (ativo e inativo), True = apenas ativos, False = apenas inativos
            location_id: Filtrar por localidade (FK para dim_electrolux_locations)
        """
        try:
            # Buscar do SQL Server com filtros básicos
            documents = db_list_documents(
                user_id=user_id,
                skip=offset,
                limit=limit,
                is_active=None  # Buscar todos (filtrar em memória depois)
            )
            
            if not documents:
                return []
            
            # Aplicar filtros adicionais (filename -> title, min_role_level, etc) em memória
            filtered = []
            for doc in documents:
                # Normalizar campos do documento (allowed_countries, allowed_cities, allowed_roles, user_name)
                doc = DocumentService._normalize_document_fields(doc)
                
                # Filtro: is_active
                if is_active is not None and doc.get("is_active") != (1 if is_active else 0):
                    continue
                
                # Filtro: filename (busca em 'title')
                if filename and filename.lower() not in doc.get("title", "").lower():
                    continue
                
                # Filtro: file_type
                if file_type and doc.get("file_type", "").lower() != file_type.lower():
                    continue
                
                # Filtro: category_id
                if category_id and doc.get("category_id") != category_id:
                    continue
                
                # Filtro: location_id
                if location_id and doc.get("location_id") != location_id:
                    continue
                
                # Filtro: min_role_level
                if min_role_level and doc.get("min_role_level", 1) < min_role_level:
                    continue
                
                # Filtro: allowed_countries
                if allowed_countries:
                    # doc_countries já é array ou string (normalizar para array)
                    doc_countries = doc.get("allowed_countries", []) if isinstance(doc.get("allowed_countries"), list) else (DocumentService._normalize_allowed_countries(doc.get("allowed_countries", "")) if doc.get("allowed_countries") else [])
                    filter_countries = DocumentService._normalize_allowed_countries(allowed_countries)
                    if not any(c.strip().lower() == x.strip().lower() for c in filter_countries for x in doc_countries):
                        continue
                
                # Filtro: allowed_cities
                if allowed_cities:
                    # doc_cities agora já é array (graças ao parse acima)
                    doc_cities = doc.get("allowed_cities", []) if isinstance(doc.get("allowed_cities"), list) else []
                    filter_cities = DocumentService._normalize_allowed_cities(allowed_cities)
                    if not any(c.strip() in [x.strip() for x in doc_cities] for c in filter_cities):
                        continue
                
                # Filtro: collar
                if collar and doc.get("collar") != collar:
                    continue
                
                # Filtro: plant_code
                if plant_code and doc.get("plant_code") != plant_code:
                    continue
                
                filtered.append(doc)
            
            return filtered
            
        except Exception as e:
            logger.error(f"List documents failed: {e}")
            raise

    @staticmethod
    async def download_document(document_id: str, version_number: Optional[int] = None) -> bytes:
        """
        Download documento em formato original.
        
        Args:
            document_id: UUID do documento (string format)
            version_number: Número da versão específica a baixar (opcional).
                          Se não fornecido, baixa a versão mais recente.
        
        Returns:
            Bytes do arquivo
        """
        try:
            logger.info(f"[download] Starting download: doc_id={document_id}, version={version_number}")
            
            blob_path = None
            
            # Se version_number fornecido, verificar se existe
            if version_number is not None:
                logger.info(f"[download] Looking for specific version {version_number}")
                version = get_version_by_number(document_id, version_number)
                if not version:
                    logger.error(f"[download] Version {version_number} not found for document {document_id}")
                    return None
                # Backward compatibility: older payloads/tests may expose blob_id.
                blob_path = version.get("blob_path") or version.get("blob_id")
                logger.info(f"[download] Found version {version_number} with blob_path: {blob_path}")
            else:
                # Usar versão mais recente
                logger.info(f"[download] Looking for latest version of document {document_id}")
                latest = get_latest_version(document_id)
                if not latest:
                    logger.error(f"[download] No active version found for document {document_id}")
                    logger.info(f"[download] Document exists? {get_document(document_id) is not None}")
                    return None
                # Backward compatibility: older payloads/tests may expose blob_id.
                blob_path = latest.get("blob_path") or latest.get("blob_id")
                logger.info(f"[download] Found latest version with blob_path: {blob_path}")
            
            if not blob_path:
                logger.error(f"[download] blob_path is None or empty for document {document_id}")
                return None
            
            logger.info(f"[download] Downloading from blob: {blob_path}")
            storage = get_storage_provider()
            file_data = await storage.download_blob(blob_path)
            
            if not file_data:
                logger.error(f"[download] download_blob returned None for {blob_path}")
                return None
            
            logger.info(f"[download] Download successful, size: {len(file_data)} bytes")
            return file_data
            
        except Exception as e:
            logger.error(f"[download] Download failed: {e}", exc_info=True)
            return None

    
    @staticmethod
    async def get_document_details(document_id: str) -> Optional[Dict[str, Any]]:
        """
        Obter detalhes completos de um documento com todas as versões.
        
        Desmascarar nomes armazenados no BD (LGPD-compliant).
        document_id deve ser uma UUID (string format)
        """
        try:
            from app.core.sqlserver import get_sqlserver_connection
            from app.utils.name_masking import unmask_user_name, unmask_list
            from app.services import sqlserver_documents as _sql_docs
            
            # Buscar documento do SQL Server (runtime import for test compatibility)
            doc = _sql_docs.get_document(document_id)
            if not doc:
                return None
            
            # Buscar todas as versões
            versions_query = """
            SELECT version_id, document_id, version_number, blob_path, is_active, created_at,
                   filename, updated_by, updated_by_name_masked,
                   (SELECT title FROM documents WHERE document_id = versions.document_id) as document_title
            FROM versions
            WHERE document_id = ?
            ORDER BY version_number DESC
            """
            sql = get_sqlserver_connection()
            versions = sql.execute(versions_query, [document_id])
            
            # Resolver filename vazio para versões antigas
            if versions:
                for version in versions:
                    if not version.get('filename'):
                        # Usar title + extensão detectada do blob_path
                        doc_title = version.get('document_title', 'document').strip()
                        blob_path = version.get('blob_path', '')
                        
                        # Extrair extensão do blob_path
                        ext = '.docx'  # default
                        if blob_path and '.' in blob_path:
                            ext = '.' + blob_path.rsplit('.', 1)[-1]
                        
                        version['filename'] = f"{doc_title}{ext}"
                        logger.info(f"[get_document_details] Resolvido filename vazio de v{version['version_number']}: '{version['filename']}'")
                    
                    # Desmascarar nome do usuário que atualizou
                    updated_by_name_masked = version.get('updated_by_name_masked')
                    if updated_by_name_masked:
                        try:
                            version['updated_by_name'] = unmask_user_name(updated_by_name_masked)
                        except Exception as e:
                            logger.warning(f"[get_document_details] Erro ao desmascarar nome: {e}")
                            version['updated_by_name'] = version.get('updated_by', 'Desconhecido')
                    else:
                        version['updated_by_name'] = version.get('updated_by', 'Desconhecido')
            
            # Parse allowed_roles JSON
            allowed_roles_raw = doc.get("allowed_roles")
            allowed_roles_parsed = DocumentService._safe_json_loads(allowed_roles_raw) if allowed_roles_raw else None
            
            # Parse allowed_countries CSV/JSON
            allowed_countries_raw = doc.get("allowed_countries")
            if allowed_countries_raw:
                # Tentar parse como JSON primeiro (caso tenha sido armazenado como JSON)
                allowed_countries_parsed = DocumentService._safe_json_loads(allowed_countries_raw)
                if not allowed_countries_parsed:
                    # Se não for JSON válido, normalizar de CSV ou string simples
                    allowed_countries_parsed = DocumentService._normalize_allowed_countries(allowed_countries_raw)
            else:
                allowed_countries_parsed = None
            
            # Parse allowed_cities JSON
            allowed_cities_raw = doc.get("allowed_cities")
            allowed_cities_parsed = DocumentService._safe_json_loads(allowed_cities_raw) if allowed_cities_raw else None
            if not allowed_cities_parsed and allowed_cities_raw:
                # Se não for JSON válido, normalizar para array
                allowed_cities_parsed = DocumentService._normalize_allowed_cities(allowed_cities_raw)
            
            # Desmascarar nome do usuário criador
            user_name = "Desconhecido"
            user_name_masked = doc.get('user_name_masked')
            if user_name_masked:
                try:
                    user_name = unmask_user_name(user_name_masked)
                except Exception as e:
                    logger.warning(f"[get_document_details] Erro ao desmascarar nome criador: {e}")
            
            # Normalizar campos do documento
            doc = DocumentService._normalize_document_fields(doc)
            
            # Montar resposta completa
            response = {
                "document_id": doc.get("document_id"),
                "title": doc.get("title"),
                "user_id": doc.get("user_id"),
                "user_name": doc.get("user_name", "Desconhecido"),
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
                "is_active": doc.get("is_active"),
                "category_id": doc.get("category_id"),
                "category_name": doc.get("category_name"),
                "category_description": doc.get("category_description"),
                "min_role_level": doc.get("min_role_level"),
                "allowed_roles": doc.get("allowed_roles"),
                "allowed_countries": doc.get("allowed_countries"),
                "allowed_cities": doc.get("allowed_cities"),
                "allowed_location_ids": doc.get("allowed_location_ids"),
                "collar": doc.get("collar"),
                "plant_code": doc.get("plant_code"),
                "summary": doc.get("summary"),
                "file_type": doc.get("file_type"),
                "versions": versions or [],
                "version_count": len(versions) if versions else 0
            }
            
            # Se location_id estiver presente, adicionar dados completos da localidade
            if response.get("location_id"):
                try:
                    location_data = DocumentService._derive_location_data(response["location_id"])
                    response["location"] = location_data
                except Exception as e:
                    logger.warning(f"[get_document_details] Erro ao derivar dados de localidade: {e}")
                    response["location"] = None
            else:
                response["location"] = None
            
            return response
            
        except Exception as e:
            logger.error(f"Get document details failed: {e}")
            raise


# Backward compatibility: expose functions at module level
async def ingest_document_file(**kwargs) -> Dict[str, Any]:
    """Deprecated: Use DocumentService.ingest_document instead."""
    return await DocumentService.ingest_document(**kwargs)


async def delete_document_version(document_id: str, version_number: int) -> Dict[str, Any]:
    """Deprecated: Use DocumentService.delete_version instead."""
    return await DocumentService.delete_version(document_id, version_number)
