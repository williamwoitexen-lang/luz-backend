"""
Testes unitários para as novas funcionalidades implementadas:
1. Download com version_number parameter
2. List conversations com first_question e first_answer
3. Title nos responses de ingest
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.document_service import DocumentService
from app.services.sqlserver_documents import get_version_by_number, update_document_metadata
from app.services.conversation_service import list_user_conversations


class TestDownloadWithVersionNumber:
    """Testes para download com version_number parameter"""
    
    @pytest.mark.asyncio
    @patch('app.services.document_service.get_version_by_number')
    @patch('app.services.document_service.get_storage_provider')
    async def test_download_specific_version(self, mock_storage, mock_get_version):
        """Test download de versão específica"""
        # Setup
        doc_id = "550e8400-e29b-41d4-a716-446655440000"
        version_num = 2
        blob_id = "doc-uuid-v2"
        
        mock_get_version.return_value = {
            "document_id": doc_id,
            "version_number": version_num,
            "blob_id": blob_id
        }
        
        mock_storage_inst = Mock()
        mock_storage_inst.download_blob = AsyncMock(return_value=b"PDF content v2")
        mock_storage.return_value = mock_storage_inst
        
        # Execute
        result = await DocumentService.download_document(doc_id, version_number=version_num)
        
        # Verify
        assert result == b"PDF content v2"
        mock_get_version.assert_called_once_with(doc_id, version_num)
        mock_storage_inst.download_blob.assert_called_once_with(blob_id)
    
    @pytest.mark.asyncio
    @patch('app.services.document_service.get_latest_version')
    @patch('app.services.document_service.get_storage_provider')
    async def test_download_latest_version_default(self, mock_storage, mock_get_latest):
        """Test download de versão mais recente (padrão)"""
        # Setup
        doc_id = "550e8400-e29b-41d4-a716-446655440000"
        blob_id = "doc-uuid-latest"
        
        mock_get_latest.return_value = {
            "document_id": doc_id,
            "version_number": 3,
            "blob_id": blob_id
        }
        
        mock_storage_inst = Mock()
        mock_storage_inst.download_blob = AsyncMock(return_value=b"PDF content latest")
        mock_storage.return_value = mock_storage_inst
        
        # Execute (sem version_number)
        result = await DocumentService.download_document(doc_id)
        
        # Verify
        assert result == b"PDF content latest"
        mock_get_latest.assert_called_once_with(doc_id)
        mock_storage_inst.download_blob.assert_called_once_with(blob_id)
    
    @pytest.mark.asyncio
    @patch('app.services.document_service.get_version_by_number')
    async def test_download_version_not_found(self, mock_get_version):
        """Test download falha quando versão não existe"""
        # Setup
        doc_id = "550e8400-e29b-41d4-a716-446655440000"
        version_num = 99
        
        mock_get_version.return_value = None
        
        # Execute
        result = await DocumentService.download_document(doc_id, version_number=version_num)
        
        # Verify
        assert result is None
        mock_get_version.assert_called_once_with(doc_id, version_num)


class TestIngestWithTitle:
    """Testes para ingest responses com title field"""
    
    @pytest.mark.asyncio
    async def test_ingest_modo2_has_title(self):
        """Test MODO 2 (sem arquivo) retorna title"""
        # Setup
        doc_id = "550e8400-e29b-41d4-a716-446655440000"
        title = "Document Title"
        user_id = "user123"
        
        with patch('app.services.sqlserver_documents.update_document_metadata') as mock_update_doc:
            mock_update_doc.return_value = {
                "document_id": doc_id,
                "title": title,
                "category_id": 1,
                "is_active": 1
            }
            
            # Execute
            result = await DocumentService.ingest_document(
                file=None,
                user_id=user_id,
                document_id=doc_id,
                category_id=1
            )
            
            # Verify
            assert result["status"] == "success"
            assert result["document_id"] == doc_id
            assert result["title"] == title
            assert result["type"] == "metadata_update"


class TestListConversationsWithFirstQA:
    """Testes para list_user_conversations com first_question e first_answer"""
    
    @patch('app.services.conversation_service.get_sqlserver_connection')
    def test_list_conversations_structure(self, mock_get_sql):
        """Test que list_conversations retorna estrutura com first_question e first_answer"""
        # Setup
        user_id = "user123"
        mock_sql = Mock()
        mock_sql.execute.return_value = [
            {
                "conversation_id": "conv-1",
                "title": "First Conversation",
                "document_id": "doc-1",
                "created_at": "2026-01-08T10:00:00",
                "updated_at": "2026-01-08T10:30:00",
                "is_active": 1,
                "message_count": 5,
                "first_question": "Como fazer X?",
                "first_answer": "Para fazer X, você deve..."
            },
            {
                "conversation_id": "conv-2",
                "title": "Second Conversation",
                "document_id": "doc-2",
                "created_at": "2026-01-08T09:00:00",
                "updated_at": "2026-01-08T09:45:00",
                "is_active": 1,
                "message_count": 3,
                "first_question": "Qual é Y?",
                "first_answer": "Y é..."
            }
        ]
        mock_get_sql.return_value = mock_sql
        
        # Execute
        result = list_user_conversations(user_id)
        
        # Verify
        assert len(result) == 2
        assert result[0]["conversation_id"] == "conv-1"
        assert result[0]["first_question"] == "Como fazer X?"
        assert result[0]["first_answer"] == "Para fazer X, você deve..."
        assert result[1]["first_question"] == "Qual é Y?"
        assert result[1]["first_answer"] == "Y é..."


class TestGetVersionByNumber:
    """Testes para nova função get_version_by_number"""
    
    @patch('app.services.sqlserver_documents.get_sqlserver_connection')
    def test_get_version_by_number_found(self, mock_get_sql):
        """Test get_version_by_number encontra versão"""
        # Setup
        doc_id = "550e8400-e29b-41d4-a716-446655440000"
        version_num = 2
        
        mock_sql = Mock()
        mock_sql.execute_single.return_value = {
            "document_id": doc_id,
            "version_number": version_num,
            "blob_id": f"{doc_id}-v{version_num}",
            "is_active": 1
        }
        mock_get_sql.return_value = mock_sql
        
        # Execute
        result = get_version_by_number(doc_id, version_num)
        
        # Verify
        assert result is not None
        assert result["version_number"] == version_num
        assert result["is_active"] == 1
    
    @patch('app.services.sqlserver_documents.get_sqlserver_connection')
    def test_get_version_by_number_not_found(self, mock_get_sql):
        """Test get_version_by_number retorna None quando versão não existe"""
        # Setup
        doc_id = "550e8400-e29b-41d4-a716-446655440000"
        version_num = 99
        
        mock_sql = Mock()
        mock_sql.execute_single.return_value = None
        mock_get_sql.return_value = mock_sql
        
        # Execute
        result = get_version_by_number(doc_id, version_num)
        
        # Verify
        assert result is None
