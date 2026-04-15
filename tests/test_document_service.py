"""
Testes unitários para DocumentService.

Executa testes de:
- ingest_preview (salva temp, extrai metadados)
- ingest_confirm (recupera temp, salva permanente)
- get_document_details (recupera documento)
- list_documents (lista com filtros)
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from io import BytesIO
from app.services.document_service import DocumentService
from app.services.sqlserver_documents import (
    save_temp_upload,
    get_temp_upload,
    mark_temp_upload_confirmed,
    delete_expired_temp_uploads
)


class TestIngestPreview:
    """Testes para ingest_preview endpoint"""
    
    @pytest.mark.asyncio
    @patch('app.services.document_service.get_storage_provider')
    @patch('app.services.document_service.get_llm_client')
    @patch('app.services.sqlserver_documents.save_temp_upload')
    async def test_ingest_preview_success(self, mock_save_temp, mock_llm, mock_storage):
        """Test successful preview upload"""
        # Setup mocks
        mock_storage_inst = Mock()
        mock_storage_inst.save_file.return_value = "__temp__/1/uuid_file.pdf"
        mock_storage.return_value = mock_storage_inst
        
        mock_llm_inst = Mock()
        mock_llm_inst.extract_metadata.return_value = {
            "title": "Test Document",
            "category": "Finance"
        }
        mock_llm.return_value = mock_llm_inst
        
        # Create file mock
        file_mock = AsyncMock()
        file_mock.read = AsyncMock(return_value=b"PDF content here")
        file_mock.filename = "test.pdf"
        
        # Execute
        result = await DocumentService.ingest_preview(file_mock)
        
        # Assertions
        assert result["status"] == "success"
        assert "temp_id" in result
        assert result["filename"] == "test.pdf"
        assert result["file_size_bytes"] == len(b"PDF content here")
        assert "expires_in_minutes" in result
        assert result["expires_in_minutes"] == 10
        
        # Verify storage was called
        mock_storage_inst.save_file.assert_called_once()
        
        # Verify temp upload was saved to DB
        mock_save_temp.assert_called_once()


class TestIngestConfirm:
    """Testes para ingest_confirm endpoint"""
    
    @pytest.mark.asyncio
    @patch('app.services.document_service.get_storage_provider')
    @patch('app.services.sqlserver_documents.get_temp_upload')
    @patch('app.services.sqlserver_documents.create_document')
    @patch('app.services.sqlserver_documents.create_version')
    @patch('app.services.sqlserver_documents.mark_temp_upload_confirmed')
    async def test_ingest_confirm_success(self, mock_mark, mock_create_version, mock_create_doc, mock_get_temp, mock_storage):
        """Test successful confirm with temp file"""
        # Setup
        temp_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock temp upload retrieval
        temp_upload = {
            "temp_id": temp_id,
            "filename": "document.pdf",
            "blob_path": "__temp__/1/uuid_document.pdf"
        }
        mock_get_temp.return_value = temp_upload
        
        # Mock storage
        mock_storage_inst = Mock()
        mock_storage_inst.get_file.return_value = b"PDF content"
        mock_storage_inst.save_file.return_value = "documents/doc_id/v1/document.pdf"
        mock_storage.return_value = mock_storage_inst
        
        # Mock document creation
        mock_create_doc.return_value = "550e8400-e29b-41d4-a716-446655440001"
        mock_create_version.return_value = Mock(get=lambda x: "v1")
        
        # Execute
        result = await DocumentService.ingest_confirm(
            temp_id=temp_id,
            user_id="user123",
            document_id=None,
            category_id=1
        )
        
        # Assertions
        assert result["status"] == "success"
        assert result["document_id"] == "550e8400-e29b-41d4-a716-446655440001"
        assert result["version"] == 1
        assert result["temp_id"] == temp_id
        
        # Verify temp upload was retrieved
        mock_get_temp.assert_called_once_with(temp_id)
        
        # Verify document was created
        mock_create_doc.assert_called_once()
        
        # Verify file was saved
        mock_storage_inst.save_file.assert_called_once()
        
        # Verify marked as confirmed
        mock_mark.assert_called_once_with(temp_id)
    
    @pytest.mark.asyncio
    @patch('app.services.sqlserver_documents.get_temp_upload')
    async def test_ingest_confirm_temp_not_found(self, mock_get_temp):
        """Test confirm with expired/invalid temp_id"""
        mock_get_temp.return_value = None
        
        with pytest.raises(FileNotFoundError):
            await DocumentService.ingest_confirm(
                temp_id="invalid_id",
                user_id="user123"
            )
    
    @pytest.mark.asyncio
    @patch('app.services.document_service.get_llm_client')
    @patch('app.services.document_service.get_storage_provider')
    @patch('app.services.document_service.FormatConverter')
    @patch('app.services.sqlserver_documents.get_temp_upload')
    @patch('app.services.sqlserver_documents.create_document')
    @patch('app.services.sqlserver_documents.create_version')
    @patch('app.services.sqlserver_documents.mark_temp_upload_confirmed')
    async def test_ingest_confirm_uuid_sync_llm_and_sql(
        self,
        mock_mark,
        mock_create_version,
        mock_create_doc,
        mock_get_temp,
        mock_format_converter,
        mock_storage,
        mock_llm_client
    ):
        """
        CRITICAL: Test that the SAME UUID is used for both LLM Server and SQL Server.
        
        Bug fix validation: Previously, two different UUIDs were generated:
        - temp_doc_id_for_llm (sent to LLM Server)
        - document_id (saved to SQL Server)
        
        This test ensures they are now synchronized (same UUID).
        """
        # Setup
        temp_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock temp upload
        temp_upload = {
            "temp_id": temp_id,
            "filename": "document.pdf",
            "blob_path": "__temp__/1/uuid_document.pdf"
        }
        mock_get_temp.return_value = temp_upload
        
        # Mock storage
        mock_storage_inst = Mock()
        mock_storage_inst.get_file.return_value = b"PDF content"
        mock_storage_inst.save_file.return_value = "documents/doc_id/v1/document.pdf"
        mock_storage.return_value = mock_storage_inst
        
        # Mock FormatConverter
        mock_format_converter.convert_to_csv.return_value = ("CSV content", "pdf")
        
        # Mock LLM client - track what document_id was sent to LLM
        mock_llm_inst = Mock()
        llm_document_id = None
        
        def capture_llm_ingest(**kwargs):
            nonlocal llm_document_id
            llm_document_id = kwargs.get('document_id')
            return {
                "success": True,
                "chunks_created": 5
            }
        
        mock_llm_inst.ingest_document.side_effect = capture_llm_ingest
        mock_llm_inst.extract_metadata.return_value = {"summary": "Test summary"}
        mock_llm_client.return_value = mock_llm_inst
        
        # Mock document creation - track what document_id was saved to SQL
        sql_document_id = None
        
        def capture_create_doc(**kwargs):
            nonlocal sql_document_id
            sql_document_id = kwargs.get('document_id')
            return sql_document_id or "550e8400-e29b-41d4-a716-446655440001"
        
        mock_create_doc.side_effect = capture_create_doc
        mock_create_version.return_value = 1
        
        # Execute
        result = await DocumentService.ingest_confirm(
            temp_id=temp_id,
            user_id="user123",
            document_id=None,  # New document
            category_id=1
        )
        
        # ASSERTIONS - THE CRITICAL CHECK
        assert result["status"] == "success"
        
        # Verify LLM was called with a document_id
        assert llm_document_id is not None, "LLM Server should receive a document_id"
        
        # Verify SQL Server received the SAME document_id
        assert sql_document_id is not None, "SQL Server should receive a document_id"
        
        # THE CRITICAL FIX: Both must be EQUAL
        assert llm_document_id == sql_document_id, (
            f"BUG: document_id mismatch! "
            f"LLM Server: {llm_document_id}, "
            f"SQL Server: {sql_document_id}. "
            f"These MUST be equal to avoid desynchronization between systems."
        )
        
        # Additional verification
        assert result["document_id"] == sql_document_id
        assert mock_llm_inst.ingest_document.called
        assert mock_create_doc.called


class TestGetDocumentDetails:
    """Testes para recuperar detalhes do documento"""
    
    @pytest.mark.asyncio
    @patch('app.services.sqlserver_documents.get_document')
    @patch('app.core.sqlserver.get_sqlserver_connection')
    async def test_get_document_details_success(self, mock_sql_get, mock_get_doc):
        """Test get document with versions"""
        doc_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock document
        mock_get_doc.return_value = {
            "document_id": doc_id,
            "title": "Test Doc",
            "user_id": "user123",
            "category_id": 1,
            "is_active": 1
        }
        
        # Mock versions query
        mock_sql_inst = Mock()
        mock_sql_inst.execute.return_value = [
            {
                "version_id": "v1",
                "version_number": 1,
                "chunks_created": 10,
                "timestamp": "2025-01-08"
            }
        ]
        mock_sql_get.return_value = mock_sql_inst
        
        # Execute
        result = await DocumentService.get_document_details(doc_id)
        
        # Assertions
        assert result is not None
        assert result["document_id"] == doc_id
        assert result["title"] == "Test Doc"
        assert result["version_count"] == 1
        assert len(result["versions"]) == 1


class TestTempUploadDatabase:
    """Testes para funções de temp_uploads no banco"""
    
    @patch('app.services.sqlserver_documents.get_sqlserver_connection')
    def test_save_temp_upload(self, mock_sql):
        """Test save temp upload metadata"""
        mock_sql_inst = Mock()
        mock_sql.return_value = mock_sql_inst
        
        result = save_temp_upload(
            temp_id="550e8400-e29b-41d4-a716-446655440000",
            filename="test.pdf",
            blob_path="__temp__/1/uuid_test.pdf",
            file_size_bytes=1024
        )
        
        assert result["temp_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert result["filename"] == "test.pdf"
        assert "created_at" in result
        assert "expires_at" in result
        
        # Verify SQL execute was called
        mock_sql_inst.execute.assert_called_once()
    
    @patch('app.services.sqlserver_documents.get_sqlserver_connection')
    def test_get_temp_upload_found(self, mock_sql):
        """Test retrieve existing temp upload"""
        mock_sql_inst = Mock()
        mock_sql_inst.execute.return_value = [
            {
                "temp_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "test.pdf",
                "blob_path": "__temp__/1/uuid_test.pdf",
                "is_confirmed": 0
            }
        ]
        mock_sql.return_value = mock_sql_inst
        
        result = get_temp_upload("550e8400-e29b-41d4-a716-446655440000")
        
        assert result is not None
        assert result["filename"] == "test.pdf"
    
    @patch('app.services.sqlserver_documents.get_sqlserver_connection')
    def test_get_temp_upload_not_found(self, mock_sql):
        """Test retrieve non-existent temp upload"""
        mock_sql_inst = Mock()
        mock_sql_inst.execute.return_value = []
        mock_sql.return_value = mock_sql_inst
        
        result = get_temp_upload("invalid_id")
        
        assert result is None


class TestListDocuments:
    """Testes para listagem de documentos"""
    
    @pytest.mark.asyncio
    @patch('app.services.document_service.db_list_documents')
    async def test_list_documents_with_filters(self, mock_db_list):
        """Test list documents with category filter"""
        mock_db_list.return_value = [
            {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Finance Report",
                "category_id": 1,
                "is_active": 1,
                "min_role_level": 1
            },
            {
                "document_id": "550e8400-e29b-41d4-a716-446655440001",
                "title": "HR Policy",
                "category_id": 2,
                "is_active": 1,
                "min_role_level": 2
            }
        ]
        
        result = await DocumentService.list_documents(
            category_id=1,
            is_active=True
        )
        
        # Should return only category 1 documents
        assert len(result) == 1
        assert result[0]["category_id"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
