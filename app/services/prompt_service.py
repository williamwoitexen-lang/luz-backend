"""
Service para gerenciar prompts de agentes no banco de dados e no LLM Server.
"""
import logging
import requests
import os
import time
from typing import Dict, Any, Optional
from app.core.sqlserver import get_sqlserver_connection
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptService:
    """Service para gerenciar prompts de agentes."""
    
    def __init__(self):
        self.llm_server_url = os.getenv("LLM_SERVER_URL", "http://localhost:8001").rstrip("/")
        self.llm_server_timeout = int(os.getenv("LLM_SERVER_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("LLM_SERVER_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("LLM_SERVER_RETRY_DELAY", "1"))
    
    def _make_request_with_retry(self, method: str, url: str, json_data: Dict[str, Any], attempt: int = 1) -> requests.Response:
        """
        Faz requisição com retry em erros de conexão e 5xx.
        
        Args:
            method: GET, POST, PUT, DELETE, etc
            url: URL completa
            json_data: Payload JSON
            attempt: Tentativa atual (para logging)
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: Se falhar após todos os retries
        """
        try:
            if method == "PUT":
                response = requests.put(url, json=json_data, timeout=self.llm_server_timeout)
            else:
                raise ValueError(f"Método {method} não suportado")
            
            # Retry em 5xx server errors
            if response.status_code >= 500:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"[Retry] LLM Server retornou {response.status_code}. "
                        f"Tentar novamente em {wait_time}s... (tentativa {attempt}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                    return self._make_request_with_retry(method, url, json_data, attempt + 1)
            
            return response
            
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError) as e:
            if attempt < self.max_retries:
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.warning(
                    f"[Retry] Erro de conexão com LLM Server: {type(e).__name__}. "
                    f"Tentar novamente em {wait_time}s... (tentativa {attempt}/{self.max_retries})"
                )
                time.sleep(wait_time)
                return self._make_request_with_retry(method, url, json_data, attempt + 1)
            
            logger.error(f"[Erro] Falha após {self.max_retries} tentativas: {e}")
            raise
    
    def _sync_with_llm_server(self, agente: str, system_prompt: str) -> bool:
        """
        Sincroniza o prompt com o LLM Server.
        
        Args:
            agente: Nome do agente
            system_prompt: Texto do system prompt
            
        Returns:
            True se sucesso, False se falha
            
        Raises:
            RuntimeError: Se LLM Server falhar permanentemente
        """
        url = f"{self.llm_server_url}/api/v1/agents/{agente}/prompts"
        payload = {"system_prompt": system_prompt, "version": 1}
        
        logger.info(f"[Prompt Sync] Sincronizando prompt para agente '{agente}' com LLM Server: {url}")
        
        try:
            response = self._make_request_with_retry("PUT", url, payload)
            
            if response.status_code >= 400:
                error_msg = f"LLM Server retornou {response.status_code}: {response.text}"
                logger.error(f"[Prompt Sync] Erro: {error_msg}")
                raise RuntimeError(error_msg)
            
            logger.info(f"[Prompt Sync] Sucesso ao sincronizar prompt para agente '{agente}'")
            return True
            
        except Exception as e:
            logger.error(f"[Prompt Sync] Erro ao sincronizar com LLM Server: {e}")
            raise RuntimeError(f"Falha ao atualizar prompt no LLM Server: {str(e)}")
    
    def create_prompt(self, agente: str, system_prompt: str) -> Dict[str, Any]:
        """
        Cria um novo prompt para um agente.
        
        Args:
            agente: Nome do agente
            system_prompt: Texto do system prompt
            
        Returns:
            Dict com dados do prompt criado
            
        Raises:
            ValueError: Se agente já existe
            RuntimeError: Se falha ao sincronizar com LLM Server
        """
        try:
            sql = get_sqlserver_connection()
            
            # Verificar se agente já existe
            query = "SELECT prompt_id FROM prompts WHERE agente = ?"
            existing = sql.execute_single(query, (agente,))
            if existing:
                raise ValueError(f"Prompt para agente '{agente}' já existe")
            
            # Sincronizar com LLM Server PRIMEIRO (antes de salvar no DB)
            self._sync_with_llm_server(agente, system_prompt)
            
            # Salvar no DB
            now = datetime.utcnow()
            insert_query = """
                INSERT INTO prompts (agente, system_prompt, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """
            sql.execute(insert_query, (agente, system_prompt, now, now))
            
            # Buscar o prompt criado
            select_query = "SELECT prompt_id, agente, system_prompt, version, created_at, updated_at FROM prompts WHERE agente = ?"
            row = sql.execute_single(select_query, (agente,))
            
            logger.info(f"[Prompt] Criado novo prompt para agente '{agente}'")
            return dict(row)
            
        except Exception as e:
            logger.error(f"[Prompt] Erro ao criar prompt: {e}")
            raise
    
    def get_prompt_by_agente(self, agente: str) -> Optional[Dict[str, Any]]:
        """
        Busca prompt por agente.
        
        Args:
            agente: Nome do agente
            
        Returns:
            Dict com dados do prompt ou None se não encontrado
        """
        try:
            sql = get_sqlserver_connection()
            query = "SELECT prompt_id, agente, system_prompt, version, created_at, updated_at FROM prompts WHERE agente = ?"
            row = sql.execute_single(query, (agente,))
            
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"[Prompt] Erro ao buscar prompt para agente '{agente}': {e}")
            raise
    
    def list_prompts(self) -> list:
        """
        Lista todos os prompts.
        
        Returns:
            Lista de dicts com dados dos prompts
        """
        try:
            sql = get_sqlserver_connection()
            query = "SELECT prompt_id, agente, system_prompt, version, created_at, updated_at FROM prompts ORDER BY agente"
            rows = sql.execute(query, ())
            
            return [dict(row) for row in rows] if rows else []
            
        except Exception as e:
            logger.error(f"[Prompt] Erro ao listar prompts: {e}")
            raise
    
    def update_prompt(self, agente: str, system_prompt: str) -> Dict[str, Any]:
        """
        Atualiza um prompt existente.
        
        Sincroniza com LLM Server ANTES de atualizar o DB.
        Se LLM Server falhar, não atualiza o DB.
        
        Args:
            agente: Nome do agente
            system_prompt: Novo texto do system prompt
            
        Returns:
            Dict com dados do prompt atualizado
            
        Raises:
            ValueError: Se agente não existe
            RuntimeError: Se falha ao sincronizar com LLM Server
        """
        try:
            sql = get_sqlserver_connection()
            
            # Verificar se agente existe
            check_query = "SELECT prompt_id FROM prompts WHERE agente = ?"
            existing = sql.execute_single(check_query, (agente,))
            if not existing:
                raise ValueError(f"Prompt para agente '{agente}' não encontrado")
            
            # Buscar versão atual
            current = sql.execute_single("SELECT version FROM prompts WHERE agente = ?", (agente,))
            new_version = current["version"] + 1
            
            # Sincronizar com LLM Server PRIMEIRO (antes de atualizar no DB)
            self._sync_with_llm_server(agente, system_prompt, new_version)
            
            # Atualizar no DB (incrementando versão)
            now = datetime.utcnow()
            update_query = """
                UPDATE prompts 
                SET system_prompt = ?, version = ?, updated_at = ?
                WHERE agente = ?
            """
            sql.execute(update_query, (system_prompt, new_version, now, agente))
            
            # Buscar o prompt atualizado
            select_query = "SELECT prompt_id, agente, system_prompt, version, created_at, updated_at FROM prompts WHERE agente = ?"
            row = sql.execute_single(select_query, (agente,))
            
            logger.info(f"[Prompt] Atualizado prompt para agente '{agente}'")
            return dict(row)
            
        except Exception as e:
            logger.error(f"[Prompt] Erro ao atualizar prompt para agente '{agente}': {e}")
            raise
    
    def delete_prompt(self, agente: str) -> bool:
        """
        Deleta um prompt.
        
        Args:
            agente: Nome do agente
            
        Returns:
            True se deletado com sucesso
            
        Raises:
            ValueError: Se agente não existe
        """
        try:
            sql = get_sqlserver_connection()
            
            # Verificar se agente existe
            check_query = "SELECT prompt_id FROM prompts WHERE agente = ?"
            existing = sql.execute_single(check_query, (agente,))
            if not existing:
                raise ValueError(f"Prompt para agente '{agente}' não encontrado")
            
            # Deletar
            delete_query = "DELETE FROM prompts WHERE agente = ?"
            sql.execute(delete_query, (agente,))
            
            logger.info(f"[Prompt] Deletado prompt para agente '{agente}'")
            return True
            
        except Exception as e:
            logger.error(f"[Prompt] Erro ao deletar prompt para agente '{agente}': {e}")
            raise
