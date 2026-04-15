"""
Configuration management - Todas as credenciais vêm de variáveis de ambiente.
As variáveis sensíveis (com API) são injetadas a cada deployment.
"""

import os
import logging

logger = logging.getLogger(__name__)


class KeyVaultConfig:
    """
    Gerencia leitura de configurações via variáveis de ambiente.
    
    Variáveis obrigatórias:
    - AZURE_TENANT_ID
    - AZURE_CLIENT_ID
    - 
    - 
    - AZURE_SEARCH_API_KEY
    - AZURE_CONTENT_SAFETY_API_KEY
    - AZURE_STORAGE_CONNECTION_STRING
    - AZURE_STORAGE_ACCOUNT_NAME
    - AZURE_STORAGE_CONTAINER_NAME
    - LLM_SERVER_URL
    - LANGCHAIN_BASE_URL
    """
    
    def __init__(self):
        """Inicializa a configuração"""
        logger.info("Configuração carregada via variáveis de ambiente")
    
    @staticmethod
    def get_azure_tenant_id() -> str:
        """Retorna AZURE_TENANT_ID"""
        return os.environ.get("AZURE_TENANT_ID", "")
    
    @staticmethod
    def get_azure_client_id() -> str:
        """Retorna AZURE_CLIENT_ID"""
        return os.environ.get("AZURE_CLIENT_ID", "")
    
    @staticmethod
    def get_azure_client_secret() -> str:
        """Retorna  (sensível)"""
        value = os.environ.get("")
        if not value:
            raise ValueError(" não definida")
        return value
    
    @staticmethod
    def get_azure_openai_key() -> str:
        """Retorna  (sensível)"""
        value = os.environ.get("")
        if not value:
            raise ValueError(" não definida")
        return value
    
    @staticmethod
    def get_azure_search_api_key() -> str:
        """Retorna AZURE_SEARCH_API_KEY (sensível)"""
        value = os.environ.get("AZURE_SEARCH_API_KEY")
        if not value:
            raise ValueError("AZURE_SEARCH_API_KEY não definida")
        return value
    
    @staticmethod
    def get_azure_content_safety_api_key() -> str:
        """Retorna AZURE_CONTENT_SAFETY_API_KEY (sensível)"""
        value = os.environ.get("AZURE_CONTENT_SAFETY_API_KEY")
        if not value:
            raise ValueError("AZURE_CONTENT_SAFETY_API_KEY não definida")
        return value
    
    @staticmethod
    def get_azure_storage_connection_string() -> str:
        """Retorna AZURE_STORAGE_CONNECTION_STRING"""
        value = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        if not value:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING não definida")
        return value
    
    @staticmethod
    def get_azure_storage_account_name() -> str:
        """Retorna AZURE_STORAGE_ACCOUNT_NAME"""
        return os.environ.get("AZURE_STORAGE_ACCOUNT_NAME", "")
    
    @staticmethod
    def get_azure_storage_container_name() -> str:
        """Retorna AZURE_STORAGE_CONTAINER_NAME"""
        return os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "chat-rh")
    
    @staticmethod
    def get_llm_server_url() -> str:
        """Retorna LLM_SERVER_URL, caindo para LANGCHAIN_BASE_URL se não vier."""
        value = os.environ.get("LLM_SERVER_URL") or os.environ.get("LANGCHAIN_BASE_URL")
        if not value:
            raise ValueError("LLM_SERVER_URL não definida")
        return value
    
    @staticmethod
    def get_langchain_base_url() -> str:
        """Retorna LANGCHAIN_BASE_URL"""
        value = os.environ.get("LANGCHAIN_BASE_URL")
        if not value:
            raise ValueError("LANGCHAIN_BASE_URL não definida")
        return value
    
    @staticmethod
    def get_sqlserver_connection_string() -> str:
        """Retorna SQLSERVER_CONNECTION_STRING sem credenciais (usa Managed Identity)"""
        return os.getenv(
            "SQLSERVER_CONNECTION_STRING",
            "Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=data;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;Authentication=ActiveDirectoryMsi;"
        )
    
    @staticmethod
    def get_llm_server_timeout() -> int:
        """Retorna LLM_SERVER_TIMEOUT"""
        return int(os.environ.get("LLM_SERVER_TIMEOUT", "30"))
    
    @staticmethod
    def get_metadata_server_url() -> str:
        """Retorna METADATA_SERVER_URL (mesmo que LLM_SERVER_URL por enquanto)"""
        return os.environ.get("METADATA_SERVER_URL") or os.environ.get("LLM_SERVER_URL", "")
    
    @staticmethod
    def skip_llm_metadata_extraction() -> bool:
        """Retorna se deve pular extração de metadados do LLM"""
        return os.environ.get("SKIP_LLM_METADATA_EXTRACTION", "false").lower() == "true"


# Instância global para uso em toda a aplicação
_config_instance = None


def get_config() -> KeyVaultConfig:
    """Retorna a instância global de configuração"""
    global _config_instance
    if _config_instance is None:
        _config_instance = KeyVaultConfig()
    return _config_instance
