"""
LLM Server communication for Azure AI Search operations.
"""
import os
import logging
import json
import requests
import time
from typing import List, Dict, Any, Tuple, Optional, Callable, Union
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

load_dotenv()

logger = logging.getLogger(__name__)

class LLMServerClient:
    """Client for communicating with LLM Server."""
    
    def __init__(self):
        self.base_url = os.getenv("LLM_SERVER_URL", "http://localhost:8001").rstrip("/")
        self.timeout = int(os.getenv("LLM_SERVER_TIMEOUT", "300"))  # 5 minutes for large files
        self.max_retries = int(os.getenv("LLM_SERVER_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("LLM_SERVER_RETRY_DELAY", "1"))  # seconds
        logger.info(f"[LLMServerClient] URL: {self.base_url}")
        logger.info(f"[LLMServerClient] Timeout: {self.timeout}s")
        logger.info(f"[LLMServerClient] Max retries: {self.max_retries}")
        print(f"🔗 LLM Server URL: {self.base_url}")  # Print também pra debug
        
    def _with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with exponential backoff retry logic.
        
        Retries on connection errors and 5xx server errors.
        Does NOT retry on 4xx client errors (invalid input).
        
        Args:
            func: Callable function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func
            
        Raises:
            requests.exceptions.RequestException: After all retries exhausted
        """
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # Retry on 5xx server errors but not 4xx client errors
                if hasattr(result, 'status_code') and result.status_code >= 500:
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                        logger.warning(
                            f"[Retry] LLM Server returned {result.status_code}. "
                            f"Retrying in {wait_time}s... (attempt {attempt}/{self.max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                
                # Success or client error (4xx) - don't retry 4xx
                return result
                
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.warning(
                        f"[Retry] Connection error to LLM Server: {type(e).__name__}. "
                        f"Retrying in {wait_time}s... (attempt {attempt}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"[Retry] Failed after {self.max_retries} attempts: {e}"
                    )
                    raise
            except Exception as e:
                # Other exceptions - don't retry
                raise
        
        if last_exception:
            raise last_exception
    
    def _get_file_format(self, filename: str) -> str:
        """
        Extract file format from filename.
        Returns the original file extension as the doc_type.
        
        Args:
            filename: Original filename
            
        Returns:
            File format (pdf, docx, doc, xlsx, xls, csv, txt, etc)
        """
        if not filename:
            return "txt"  # Default to txt for unknown
        
        ext = filename.rsplit(".", 1)[-1].lower()
        
        # Validate against accepted formats, otherwise default to txt
        accepted_formats = ["txt", "pdf", "docx", "doc", "xlsx", "xls", "csv"]
        
        return ext if ext in accepted_formats else "txt"
    
    @staticmethod
    def _handle_llm_error(response) -> str:
        """
        Parse de erro do LLM standardizado.
        
        Extrai e loga mensagens de erro de forma consistente.
        Evita repetição de try/except em vários métodos.
        
        Args:
            response: Response object do requests
            
        Returns:
            Mensagem de erro formatada: "LLM Server XXX: detailed error message"
        """
        error_detail = response.text
        error_message = error_detail
        
        try:
            error_json = response.json()
            if "detail" in error_json:
                # Parse estruturado de validação
                if isinstance(error_json["detail"], list):
                    errors_info = []
                    for err in error_json["detail"]:
                        msg = err.get('msg', 'Validation error')
                        loc = err.get('loc', [])
                        errors_info.append(f"{msg} (field: {loc})")
                        
                        # Log específico para campos importantes
                        if "role_id" in str(loc):
                            logger.error(f"[LLM role_id validation] {msg}")
                    
                    error_message = " | ".join(errors_info)
                else:
                    error_message = str(error_json["detail"])
        except (json.JSONDecodeError, ValueError):
            pass
        
        logger.error(f"[LLM Error] LLM Server {response.status_code}: {error_message}")
        return f"LLM Server {response.status_code}: {error_message}"
    
    def ingest_document(
        self, 
        document_id: str,  # ID do documento (UUID string)
        file_content: str,  # Conteúdo do arquivo como texto
        filename: str,
        category_id: int,  # ID da categoria (obrigatório)
        user_id: str = "",
        title: str = "",
        min_role_level: int = 1,
        allowed_roles: list = None,
        allowed_countries: list = None,
        allowed_cities: list = None,
        allowed_location_ids: list = None,
        version_id: int = 1
    ) -> Dict[str, Any]:
        """
        Send complete document text to LLM Server for ingestion.
        
        LLM Server handles:
        - Format-specific processing (Excel, PDF, etc)
        - Chunking (if needed)
        - Indexing into Azure AI Search
        
        Args:
            document_id: Document ID (UUID string)
            file_content: Complete file content as decoded text
            filename: Original filename (used to detect format)
            category_id: Category ID (FK para dim_categories) - OBRIGATÓRIO
            user_id: User ID (for metadata)
            title: Document title (for metadata)
            min_role_level: Minimum role level required
            allowed_roles: List of specific roles (e.g., ["admin", "manager"])
            allowed_countries: List of allowed countries
            allowed_cities: List of allowed cities
            allowed_location_ids: List of location IDs from dim_electrolux_locations
            version_id: Document version number
            
        Returns:
            Response from LLM Server with chunk info
            
        Raises:
            requests.exceptions.RequestException: If LLM Server call fails
        """
        try:
            file_format = self._get_file_format(filename)
            
            # Validar tamanho do conteudo
            MAX_CONTENT_SIZE = 1000000  # 1MB limite para LLM Server
            if len(file_content) > MAX_CONTENT_SIZE:
                logger.warning(f"Content size {len(file_content)} exceeds MAX_CONTENT_SIZE {MAX_CONTENT_SIZE}, truncating")
                file_content_to_send = file_content[:MAX_CONTENT_SIZE]
                logger.warning(f"Original size: {len(file_content)}, truncated to: {len(file_content_to_send)}")
            else:
                file_content_to_send = file_content
            
            # Validar que conteudo nao esta vazio
            if not file_content_to_send or len(file_content_to_send.strip()) == 0:
                raise ValueError(f"Document content is empty after processing (original size: {len(file_content)})")
            
            payload = {
                'document_id': document_id,
                'source_file': filename,
                'title': title or filename,
                'user_id': user_id,
                'doc_type': file_format,
                'content': file_content_to_send,
                'category_id': category_id,
                'min_role_level': min_role_level,
                'allowed_roles': allowed_roles or [],
                'allowed_countries': allowed_countries or [],
                'allowed_cities': allowed_cities or [],
                'allowed_location_ids': allowed_location_ids or [],
                'document_type': 'policy',  # Required by LLM Server
                'language': 'pt',
                'version_id': str(version_id)  # Convert to string as LLM Server expects
            }
            
            logger.info(f"[LLM Ingest] Sending document to LLM Server")
            logger.info(f"[LLM Ingest] Filename: {filename}")
            logger.info(f"[LLM Ingest] Document ID: {document_id}")
            logger.info(f"[LLM Ingest] Title: {title}")
            logger.info(f"[LLM Ingest] User ID: {user_id}")
            logger.info(f"[LLM Ingest] Format: {file_format}")
            logger.info(f"[LLM Ingest] Min Role Level: {min_role_level}")
            logger.info(f"[LLM Ingest] Content size: {len(file_content_to_send)} chars")
            logger.info(f"[LLM Ingest] Content type: {type(file_content_to_send).__name__}")
            logger.info(f"[LLM Ingest] Content has null bytes: {chr(0) in file_content_to_send if isinstance(file_content_to_send, str) else 'N/A'}")
            logger.info(f"[LLM Ingest] Allowed roles: {payload['allowed_roles']} (type: {type(payload['allowed_roles']).__name__})")
            logger.info(f"[LLM Ingest] Allowed countries: {payload['allowed_countries']}")
            logger.info(f"[LLM Ingest] Allowed cities: {payload['allowed_cities']}")
            logger.info(f"[LLM Ingest] Allowed location IDs: {payload['allowed_location_ids']}")
            logger.info(f"[LLM Ingest] Payload keys: {list(payload.keys())}")
            logger.info(f"[LLM Ingest] Content preview (first 300 chars): {file_content_to_send[:300]}")
            logger.debug(f"[LLM Ingest] Full payload: {json.dumps(payload, default=str)}")
            
            def _make_request():
                return requests.post(
                    f"{self.base_url}/api/v1/documents",
                    json=payload,
                    timeout=self.timeout
                )
            
            response = self._with_retry(_make_request)
            
            # Log response details for debugging
            logger.info(f"[LLM Response] Status: {response.status_code}")
            logger.info(f"[LLM Response] Headers: {dict(response.headers)}")
            
            if response.status_code >= 400:
                logger.error(f"[LLM Error] HTTP {response.status_code}")
                logger.error(f"[LLM Error] URL: {response.url}")
                logger.error(f"[LLM Error] Full response text: {response.text[:2000]}")
                logger.error(f"[LLM Error] Response headers: {dict(response.headers)}")
                logger.error(f"[LLM Error] Content-Type: {response.headers.get('content-type')}")
                
                # Tentar parsear como JSON
                try:
                    error_json = response.json()
                    logger.error(f"[LLM Error] Response JSON: {json.dumps(error_json, indent=2)}")
                    if isinstance(error_json, dict):
                        if 'detail' in error_json:
                            logger.error(f"[LLM Error] Detail: {error_json['detail']}")
                        if 'error' in error_json:
                            logger.error(f"[LLM Error] Error: {error_json['error']}")
                        if 'message' in error_json:
                            logger.error(f"[LLM Error] Message: {error_json['message']}")
                except Exception as json_err:
                    logger.error(f"[LLM Error] Could not parse response as JSON: {json_err}")
            else:
                logger.info(f"[LLM Response] Success {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[LLM Success] Response keys: {list(result.keys())}")
            logger.info(f"[LLM Success] Full response: {result}")
            
            chunks_created = result.get('chunks_created', 0)
            logger.info(f"[LLM Success] Successfully ingested document {document_id} with {chunks_created} chunks")
            
            return result
        except requests.exceptions.Timeout as e:
            logger.error(f"LLM Server timeout (>{ self.timeout}s) for document {document_id}: {e}")
            logger.error("Large files may exceed timeout. Consider contacting LLM team for optimization.")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to ingest document to LLM Server: {e}")
            raise
    
    def ingest_chunks(self, document_id: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send pre-processed chunks to LLM Server for ingestion into Azure AI Search.
        
        (Legacy method - LLM Server now handles chunking)
        
        Args:
            document_id: Document ID
            chunks: List of chunks with text and metadata
            
        Returns:
            Response from LLM Server
        """
        try:
            payload = {
                "document_id": document_id,
                "chunks": chunks
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/documents",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Successfully ingested {len(chunks)} chunks for document {document_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to ingest chunks to LLM Server: {e}")
            raise
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete document from Azure AI Search via LLM Server.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            Response from LLM Server
        """
        try:
            logger.info(f"Deletando documento {document_id} do LLM Server...")
            
            # Tentar com DELETE primeiro (padrão REST)
            try:
                response = requests.delete(
                    f"{self.base_url}/api/v1/documents/{document_id}",
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.info(f"Documento {document_id} deletado com sucesso via DELETE {self.base_url}/api/v1/documents/{document_id}")
                return response.json() if response.text else {"success": True, "message": "Document deleted"}
            except requests.exceptions.RequestException as e:
                logger.warning(f"DELETE falhou, tentando POST: {e}")
                
                # Fallback: tentar com POST
                payload = {"document_id": document_id}
                response = requests.post(
                    f"{self.base_url}/api/v1/documents/delete",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.info(f"Documento {document_id} deletado com sucesso via POST")
                return response.json()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Falha ao deletar documento {document_id} do LLM Server: {e}")
            raise
    
    
    def ask_question(
        self,
        question: str,
        chat_id: str,
        user_id: str = "",
        name: str = "",
        email: str = "",
        country: str = "Brazil",
        city: str = "",
        role_id: int = 1,
        department: str = "",
        job_title: str = "",
        collar: str = "",
        unit: str = "",
        agent_id: int = 1,
        language: str = "",
        location_id: Optional[int] = None,
        memory: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ask a question to the LLM Server and get an answer.
        
        Args:
            question: User's question
            chat_id: Chat session ID (conversation ID)
            user_id: User ID
            name: User's full name
            email: User's email
            country: User's country
            city: User's city
            role_id: User's role ID (integer)
            department: User's department
            job_title: User's job title
            collar: Collar type (e.g., "white", "blue")
            unit: User's unit
            agent_id: Agent ID (1=LUZ, 2=IGP, 3=SMART)
            language: Language code (e.g., "pt", "en", "es"). Empty string if not specified.
            location_id: Location ID (int) para filtrar documentos (convertido do street)
            
        Returns:
            Response from LLM Server with answer, sources, metadata
        """
        # Converter location_id (int) - chat é 1:1, um usuário tem apenas uma localização
        location_id_int = None
        logger.info(f"[ask_question] [STEP 4] location_id={location_id} (type: {type(location_id).__name__})")
        
        if location_id is not None:
            try:
                location_id_int = int(location_id) if isinstance(location_id, str) else location_id
                logger.info(f"[ask_question] [STEP 5] ✓ location_id convertido para int: {location_id_int} (type: {type(location_id_int).__name__})")
            except (ValueError, TypeError) as conv_err:
                logger.warning(f"[ask_question] [STEP 5] ✗ Falha ao converter location_id: {location_id} - Erro: {conv_err}")
                location_id_int = None
        else:
            logger.info(f"[ask_question] [STEP 5] location_id é None, pulando conversão")
        
        payload = {
            "chat_id": chat_id,
            "question": question,
            "user_id": user_id,
            "name": name,
            "email": email,
            "country": country,
            "city": city,
            "role_id": role_id,
            "department": department,
            "job_title": job_title,
            "collar": collar,
            "unit": unit,
            "agent_id": agent_id,
            "language": language
        }
        
        if location_id_int is not None:
            payload["location_id"] = location_id_int
            logger.info(f"[ask_question] [STEP 6] Payload incluindo location_id={payload['location_id']} (int)")
        else:
            logger.info(f"[ask_question] [STEP 6] Payload SEM location_id (location_id_int foi {location_id_int})")
        
        if memory is not None:
            payload["memory"] = memory
        
        logger.info(f"Asking LLM Server: '{question[:100]}...' (chat_id: {chat_id}, user: {user_id})")
        
        def _make_request():
            return requests.post(
                f"{self.base_url}/api/v1/question",
                json=payload,
                timeout=self.timeout
            )
        
        try:
            response = self._with_retry(_make_request)
            
            if response.status_code != 200:
                logger.debug(f"[ask_question] Payload sent: {payload}")
                error_message = self._handle_llm_error(response)
                raise requests.exceptions.HTTPError(error_message)
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[ask_question] Answer received (total_time_ms: {result.get('total_time_ms', 'N/A')})")
            
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"[ask_question] Failed to get answer: {e}")
            print(f"❌ Failed to get answer from LLM Server: {e}")
            raise

    def health_check(self) -> bool:
        """Check if LLM Server is available."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LLM Server health check failed: {e}")
            return False

    def extract_metadata(
        self,
        text: str,
        filename: str = "document.txt",
        doc_type: str = "document",
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Extrair metadados do documento usando o novo endpoint do LLM Server.
        
        Args:
            text: Texto completo do documento
            filename: Nome do arquivo (opcional)
        
        Returns:
            {
                "min_role": "Manager" ou null,
                "countries": ["Brazil"] ou null,
                "cities": ["São Carlos"] ou null,
                "collar": "blue" ou null,
                "confidence": "high/medium/low"
            }
        
        Se LLM Server indisponível e SKIP_LLM_METADATA_EXTRACTION=true, retorna vazio.
        """
        # Check if metadata extraction should be skipped
        skip_extraction = os.getenv("SKIP_LLM_METADATA_EXTRACTION", "false").lower() == "true"
        if skip_extraction:
            logger.info("Metadata extraction skipped (SKIP_LLM_METADATA_EXTRACTION=true)")
            return {
                "min_role": None,
                "countries": None,
                "cities": None,
                "collar": None,
                "confidence": "low"
            }
        
        try:
            logger.info(f"Extracting metadata from {filename} (text length: {len(text)})")
            
            payload = {
                "text": text,
                "filename": filename,
                "doc_type": doc_type,
                "include_summary": include_summary
            }
            logger.info(f"Metadata extraction request URL: {self.base_url}/api/v1/extract-metadata")
            logger.info(f"Metadata extraction payload keys: {list(payload.keys())}")
            
            response = requests.post(
                f"{self.base_url}/api/v1/extract-metadata",
                json=payload,
                timeout=self.timeout
            )
            
            logger.info(f"Metadata extraction response status: {response.status_code}")
            logger.info(f"Metadata extraction response text: {response.text[:500]}")
            
            # Log response even if error
            if response.status_code >= 400:
                logger.error(f"LLM Server metadata error: {response.status_code} - {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Metadata extraction successful: {result}")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Metadata extraction timeout after {self.timeout}s")
            raise RuntimeError(f"LLM Server metadata extraction timeout (>{self.timeout}s)")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to LLM Server for metadata: {e}")
            raise RuntimeError(f"LLM Server connection error: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"LLM Server HTTP error in metadata extraction: {e}")
            raise RuntimeError(f"LLM Server HTTP error: {e}")
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from LLM Server: {e}")
            logger.error(f"Response text: {response.text}")
            raise RuntimeError(f"Invalid response from LLM Server: {e}")
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise RuntimeError(f"Failed to extract metadata: {e}")
    
    def ask_question_stream(
        self,
        question: str,
        chat_id: str,
        user_id: str = "",
        name: str = "",
        email: str = "",
        country: str = "Brazil",
        city: str = "",
        role_id: int = 1,
        department: str = "",
        job_title: str = "",
        collar: str = "",
        unit: str = "",
        agent_id: int = 1,
        language: str = "",
        location_id: Optional[int] = None,
        memory: Optional[Dict[str, Any]] = None
    ):
        """
        Ask a question to the LLM Server and get streaming response.
        
        Returns an iterator of response chunks for SSE (Server-Sent Events) streaming.
        
        Args:
            question: User's question
            chat_id: Chat session ID (conversation ID)
            user_id: User ID
            name: User's full name
            email: User's email
            country: User's country
            city: User's city
            role_id: User's role ID (integer)
            department: User's department
            job_title: User's job title
            collar: Collar type
            unit: User's unit
            agent_id: Agent ID (1=LUZ, 2=IGP, 3=SMART)
            language: Language code (e.g., "pt", "en", "es"). Empty string if not specified.
            location_id: Location ID (int) para filtrar documentos (convertido do street)
            
        Yields:
            Response chunks from LLM Server
        """
        try:
            # Converter location_id (int) - chat é 1:1, um usuário tem apenas uma localização
            location_id_int = None
            logger.info(f"[ask_question_stream] [STEP 4] location_id={location_id} (type: {type(location_id).__name__})")
            
            if location_id is not None:
                try:
                    location_id_int = int(location_id) if isinstance(location_id, str) else location_id
                    logger.info(f"[ask_question_stream] [STEP 5] ✓ location_id convertido para int: {location_id_int} (type: {type(location_id_int).__name__})")
                except (ValueError, TypeError) as conv_err:
                    logger.warning(f"[ask_question_stream] [STEP 5] ✗ Falha ao converter location_id: {location_id} - Erro: {conv_err}")
                    location_id_int = None
            else:
                logger.info(f"[ask_question_stream] [STEP 5] location_id é None, pulando conversão")
            
            payload = {
                "chat_id": chat_id,
                "question": question,
                "user_id": user_id,
                "name": name,
                "email": email,
                "country": country,
                "city": city,
                "role_id": role_id,
                "department": department,
                "job_title": job_title,
                "collar": collar,
                "unit": unit,
                "agent_id": agent_id,
                "language": language
            }
            
            if location_id_int is not None:
                payload["location_id"] = location_id_int
                logger.info(f"[ask_question_stream] [STEP 6] Payload incluindo location_id={payload['location_id']} (int)")
            else:
                logger.info(f"[ask_question_stream] [STEP 6] Payload SEM location_id (location_id_int foi {location_id_int})")
            
            if memory is not None:
                payload["memory"] = memory
            
            logger.info(f"[Stream] Asking LLM Server: '{question[:100]}...' (chat_id: {chat_id}, user: {user_id})")
            logger.debug(f"[ask_question_stream] [STEP 7] Payload final enviado: {json.dumps(payload, default=str)}")
            
            response = requests.post(
                f"{self.base_url}/api/v1/question/stream",
                json=payload,
                timeout=self.timeout,
                stream=True  # ← Enable streaming
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"[ask_question_stream] Stream error {response.status_code}: {error_detail}")
                logger.debug(f"[ask_question_stream] Payload sent: {payload}")
                print(f"❌ LLM Server Stream Error {response.status_code}: {error_detail}")
                
                # Parse estruturado de erro (mesmo do ask_question)
                error_message = error_detail
                try:
                    error_json = response.json()
                    if "detail" in error_json:
                        if isinstance(error_json["detail"], list):
                            errors_info = []
                            for err in error_json["detail"]:
                                msg = err.get('msg', 'Validation error')
                                loc = err.get('loc', [])
                                errors_info.append(f"{msg} (field: {loc})")
                                if "role_id" in str(loc):
                                    logger.error(f"[LLM role_id validation] {msg}")
                                    print(f"⚠️  [LLM role_id validation] {msg}")
                            error_message = " | ".join(errors_info)
                        else:
                            error_message = str(error_json["detail"])
                except:
                    pass
                
                # Lançar exceção prefixada
                raise requests.exceptions.HTTPError(f"LLM Server {response.status_code}: {error_message}")
            
            response.raise_for_status()
            
            logger.info(f"[Stream] Stream started from LLM Server")
            
            # Yield chunks as they come
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk:
                    logger.debug(f"[Stream] Chunk received: {len(chunk)} chars")
                    yield chunk
                    
        except requests.exceptions.Timeout as e:
            logger.error(f"[Stream] LLM Server timeout (>{self.timeout}s): {e}")
            yield f"ERROR: Request timeout after {self.timeout} seconds\n"
        except requests.exceptions.RequestException as e:
            logger.error(f"[Stream] Failed to get stream from LLM Server: {e}")
            yield f"ERROR: {str(e)}\n"
        except Exception as e:
            logger.error(f"[Stream] Unexpected error: {e}")
            yield f"ERROR: {str(e)}\n"


_llm_client = None

def get_llm_client() -> LLMServerClient:
    """Get or create LLM Server client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMServerClient()
    return _llm_client

