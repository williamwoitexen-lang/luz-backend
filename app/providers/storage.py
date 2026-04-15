"""
Abstract storage layer: can swap between local filesystem and Azure ADLS Gen2.
"""
import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class StorageProvider:
    """Base storage interface."""
    
    def save_file(self, document_id: str, version_number: int, filename: str, content: bytes) -> str:
        """Save file and return path/URI for retrieval."""
        raise NotImplementedError
    
    def get_file(self, path: str) -> bytes:
        """Retrieve file by path/URI."""
        raise NotImplementedError
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        raise NotImplementedError
    
    def delete_file(self, path: str) -> bool:
        """Delete file."""
        raise NotImplementedError
    
    def delete_folder(self, path: str) -> bool:
        """Delete folder recursively."""
        raise NotImplementedError

    async def list_documents(self, filename=None, user_id=None, min_role_level=None,
                            allowed_countries=None, allowed_cities=None, collar=None, 
                            plant_code=None, limit=100, offset=0) -> list:
        """List documents with filters."""
        raise NotImplementedError

    async def download_blob(self, document_id: str) -> bytes:
        """Download blob by document ID."""
        raise NotImplementedError


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage."""
    
    def __init__(self, base_path: str = "storage/documents"):
        self.base_path = Path(base_path)
    
    def save_file(self, document_id: str, version_number: int, filename: str, content: bytes) -> str:
        """Save file locally and return path."""
        folder = self.base_path / document_id / str(version_number)
        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / filename
        file_path.write_bytes(content)
        return str(file_path)
    
    def get_file(self, path: str) -> bytes:
        """Read file from local filesystem."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return file_path.read_bytes()
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists locally."""
        return Path(path).exists()
    
    def delete_file(self, path: str) -> bool:
        """Delete file locally."""
        file_path = Path(path)
        if file_path.exists():
            file_path.unlink()
        return True
    
    def delete_folder(self, path: str) -> bool:
        """Delete folder recursively."""
        folder = Path(path)
        if folder.exists():
            import shutil
            shutil.rmtree(folder)
        return True

    async def list_documents(self, filename=None, user_id=None, min_role_level=None,
                            allowed_countries=None, allowed_cities=None, collar=None, 
                            plant_code=None, limit=100, offset=0) -> list:
        """List documents from local storage."""
        # Implementação básica - lista pasta de documentos
        documents = []
        if self.base_path.exists():
            for doc_folder in self.base_path.iterdir():
                if doc_folder.is_dir():
                    documents.append({
                        "document_id": doc_folder.name,
                        "path": str(doc_folder)
                    })
        return documents[offset:offset+limit]

    async def download_blob(self, document_id: str) -> bytes:
        """Download blob by document ID."""
        # Procura arquivo mais recente na pasta do documento
        doc_folder = self.base_path / document_id
        if doc_folder.exists():
            # Retorna o arquivo mais recente
            files = list(doc_folder.glob("**/*.*"))
            if files:
                return files[0].read_bytes()
        return None


class AzureStorageProvider(StorageProvider):
    """Azure ADLS Gen2 storage using azure-storage-blob."""
    
    def __init__(self, account_name: str, container_name: str, account_key: str = None, connection_string: str = None):
        """
        Initialize Azure storage.
        
        Args:
            account_name: Azure Storage account name
            container_name: Container name for documents
            account_key: Account key (alternative to connection_string)
            connection_string: Connection string (alternative to account_key)
        """
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError:
            raise ImportError("azure-storage-blob not installed. Install with: pip install azure-storage-blob")
        
        self.account_name = account_name
        self.container_name = container_name
        
        # Initialize BlobServiceClient
        if connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        elif account_key:
            self.blob_service_client = BlobServiceClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                credential=account_key
            )
        else:
            # Try credential chain: DefaultAzureCredential (Managed Identity) → AzureCliCredential (dev)
            try:
                from azure.identity import DefaultAzureCredential, ChainedTokenCredential, AzureCliCredential
                
                # Order matters: DefaultAzureCredential is primary (Managed Identity in production)
                credentials = ChainedTokenCredential(
                    DefaultAzureCredential(),  # Managed Identity (PRODUCTION PRIMARY)
                    AzureCliCredential()       # Azure CLI (DEVELOPMENT)
                )
                
                self.blob_service_client = BlobServiceClient(
                    account_url=f"https://{account_name}.blob.core.windows.net",
                    credential=credentials
                )
            except Exception as e:
                raise ValueError(
                    f"Failed to authenticate with Azure Blob Storage.\n"
                    f"Error: {str(e)}\n"
                    f"\nAuthentication priority:\n"
                    f"  1. Managed Identity (DefaultAzureCredential) - Production\n"
                    f"  2. Azure CLI credentials - Development (run 'az login')\n"
                    f"  3. Connection String from Key Vault - Fallback\n"
                    f"\nTo fix:\n"
                    f"  - In production: Configure Managed Identity on your Azure resource\n"
                    f"  - In development: Run 'az login' or set AZURE-STORAGE-CONNECTION-STRING in Key Vault"
                )
        
        self.container_client = self.blob_service_client.get_container_client(container_name)
    
    def save_file(self, document_id: str, version_number: int, filename: str, content: bytes) -> str:
        """Upload file to Azure ADLS and return blob path."""
        # Create blob path: documents/{document_id}/{version_number}/{filename}
        blob_path = f"documents/{document_id}/{version_number}/{filename}"
        
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.upload_blob(content, overwrite=True)
            
            # Return URI for retrieval
            return f"azure://{self.container_name}/{blob_path}"
        except Exception as e:
            raise RuntimeError(f"Failed to upload to Azure: {str(e)}")
    
    def get_file(self, path: str) -> bytes:
        """Download file from Azure ADLS."""
        # Extract blob path from URI: azure://container/path -> path
        if path.startswith("azure://"):
            # Format: azure://container/documents/...
            parts = path.replace("azure://", "").split("/", 1)
            blob_path = parts[1] if len(parts) > 1 else path
        else:
            blob_path = path
        
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            return blob_client.download_blob().readall()
        except Exception as e:
            raise FileNotFoundError(f"File not found in Azure: {path} ({str(e)})")
    
    def file_exists(self, path: str) -> bool:
        """Check if blob exists in Azure."""
        if path.startswith("azure://"):
            parts = path.replace("azure://", "").split("/", 1)
            blob_path = parts[1] if len(parts) > 1 else path
        else:
            blob_path = path
        
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.get_blob_properties()
            return True
        except:
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete blob from Azure."""
        if path.startswith("azure://"):
            parts = path.replace("azure://", "").split("/", 1)
            blob_path = parts[1] if len(parts) > 1 else path
        else:
            blob_path = path
        
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.delete_blob()
            return True
        except:
            return False
    
    def delete_folder(self, path: str) -> bool:
        """Delete all blobs with prefix (folder-like)."""
        if path.startswith("azure://"):
            parts = path.replace("azure://", "").split("/", 1)
            prefix = parts[1] if len(parts) > 1 else path
        else:
            prefix = path
        
        try:
            # Ensure prefix ends with / to match folder structure
            if not prefix.endswith("/"):
                prefix += "/"
            
            blobs = self.container_client.list_blobs(name_starts_with=prefix)
            for blob in blobs:
                self.container_client.delete_blob(blob.name)
            return True
        except:
            return False

    async def list_documents(self, filename=None, user_id=None, min_role_level=None,
                            allowed_countries=None, allowed_cities=None, collar=None, 
                            plant_code=None, limit=100, offset=0) -> list:
        """List documents from Azure Blob Storage."""
        # Implementação básica - lista blobs no container
        documents = []
        try:
            blobs = self.container_client.list_blobs()
            for blob in blobs:
                documents.append({
                    "name": blob.name,
                    "size": blob.size,
                    "created": blob.creation_time
                })
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
        return documents[offset:offset+limit]

    async def download_blob(self, blob_path: str) -> bytes:
        """Download blob by full path from Azure."""
        try:
            # Extract path from URI if needed: azure://container/documents/... -> documents/...
            if blob_path.startswith("azure://"):
                parts = blob_path.replace("azure://", "").split("/", 1)
                path = parts[1] if len(parts) > 1 else blob_path
            else:
                path = blob_path
            
            logger.info(f"[download_blob] Downloading from Azure: {path}")
            blob_client = self.container_client.get_blob_client(path)
            data = blob_client.download_blob().readall()
            logger.info(f"[download_blob] Downloaded successfully, size: {len(data)} bytes")
            return data
        except Exception as e:
            logger.error(f"[download_blob] Error downloading blob {blob_path}: {e}")
            return None


def get_storage_provider() -> StorageProvider:
    """Factory function to get the appropriate storage provider based on env vars."""
    storage_type = os.getenv("STORAGE_TYPE", "azure").lower()

    # Aceitar vários aliases para Azure Blob / ADLS
    if storage_type in ("azure", "azure_blob_storage", "blob", "azure-blob", "adls"):
        from app.core.config import get_config
        
        account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "documents")
        
        # Priority: Connection string (from Key Vault) → Account Key → Managed Identity
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        
        # If no connection string or key, Managed Identity will be tried in AzureStorageProvider
        return AzureStorageProvider(
            account_name=account_name,
            container_name=container_name,
            connection_string=connection_string,
            account_key=account_key
        )
    else:
        base_path = os.getenv("LOCAL_STORAGE_PATH", "storage/documents")
        return LocalStorageProvider(base_path=base_path)
