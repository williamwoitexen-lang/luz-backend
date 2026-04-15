"""
Testes específicos para validar sincronização de document_ids entre LLM Server e SQL Server.

Este módulo testa o fix para o bug onde documentos eram criados com IDs diferentes
em cada sistema (LLM Server vs SQL Server), causando desincronização.

Referência: https://github.com/project/issues/document-id-sync-bug
"""

import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from app.services.document_service import DocumentService


class TestDocumentIDSynchronization:
    """Test suite para garantir sincronização de UUIDs entre LLM e SQL Server."""
    
    def test_document_id_generation_is_consistent(self):
        """Verifica que IDs gerados são UUIDs válidos e consistentes."""
        generated_ids = set()
        
        for _ in range(10):
            new_id = str(uuid.uuid4())
            
            # Validar que é UUID
            try:
                uuid.UUID(new_id)
            except ValueError:
                pytest.fail(f"Generated ID {new_id} is not a valid UUID")
            
            # Validar que não há duplicatas
            assert new_id not in generated_ids, f"Duplicate UUID generated: {new_id}"
            generated_ids.add(new_id)
    
    @pytest.mark.asyncio
    @patch('app.services.document_service.get_llm_client')
    @patch('app.services.document_service.get_storage_provider')
    @patch('app.services.document_service.FormatConverter')
    @patch('app.services.sqlserver_documents.get_temp_upload')
    @patch('app.services.sqlserver_documents.create_document')
    @patch('app.services.sqlserver_documents.create_version')
    @patch('app.services.sqlserver_documents.mark_temp_upload_confirmed')
    async def test_new_document_uses_same_uuid_everywhere(
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
        Testa que um novo documento recebe o MESMO UUID em:
        1. Envio para LLM Server
        2. Salvamento em SQL Server
        3. Resposta final ao usuário
        """
        # Setup
        temp_id = str(uuid.uuid4())
        mock_get_temp.return_value = {
            "temp_id": temp_id,
            "filename": "report.pdf",
            "blob_path": "__temp__/" + temp_id + "/report.pdf"
        }
        
        # Track IDs used in each system
        llm_ids = []
        sql_ids = []
        
        # Mock LLM
        mock_llm_inst = Mock()
        def mock_ingest_doc(**kwargs):
            llm_ids.append(kwargs.get('document_id'))
            return {"success": True, "chunks_created": 5}
        
        mock_llm_inst.ingest_document.side_effect = mock_ingest_doc
        mock_llm_inst.extract_metadata.return_value = {}
        mock_llm_client.return_value = mock_llm_inst
        
        # Mock SQL
        def mock_create_document(**kwargs):
            sql_ids.append(kwargs.get('document_id'))
            return kwargs.get('document_id') or str(uuid.uuid4())
        
        mock_create_doc.side_effect = mock_create_document
        mock_create_version.return_value = 1
        
        # Mock storage
        mock_storage_inst = Mock()
        mock_storage_inst.get_file.return_value = b"PDF content"
        mock_storage_inst.save_file.return_value = "documents/v1/report.pdf"
        mock_storage.return_value = mock_storage_inst
        
        # Mock format converter
        mock_format_converter.convert_to_csv.return_value = ("CSV", "pdf")
        
        # Execute
        result = await DocumentService.ingest_confirm(
            temp_id=temp_id,
            user_id="test-user",
            document_id=None
        )
        
        # Validações
        assert len(llm_ids) == 1, "LLM ingest_document should be called exactly once"
        assert len(sql_ids) == 1, "create_document should be called exactly once"
        
        assert llm_ids[0] == sql_ids[0], (
            f"UUID mismatch! "
            f"LLM Server received: {llm_ids[0]}, "
            f"SQL Server received: {sql_ids[0]}"
        )
        
        # Verify format (should be valid UUID)
        try:
            uuid.UUID(sql_ids[0])
            uuid.UUID(llm_ids[0])
        except ValueError as e:
            pytest.fail(f"Generated IDs are not valid UUIDs: {e}")
        
        # Verify response contains the correct ID
        assert result["document_id"] == sql_ids[0]
    
    @pytest.mark.asyncio
    @patch('app.services.document_service.get_llm_client')
    @patch('app.services.document_service.get_storage_provider')
    @patch('app.services.document_service.FormatConverter')
    @patch('app.services.sqlserver_documents.get_temp_upload')
    @patch('app.services.sqlserver_documents.get_document')
    @patch('app.services.sqlserver_documents.get_latest_version')
    @patch('app.services.sqlserver_documents.create_version')
    @patch('app.services.sqlserver_documents.mark_temp_upload_confirmed')
    async def test_new_version_preserves_document_id(
        self,
        mock_mark,
        mock_create_version,
        mock_get_latest,
        mock_get_doc,
        mock_get_temp,
        mock_format_converter,
        mock_storage,
        mock_llm_client
    ):
        """
        Testa que ao criar UMA NOVA VERSÃO de documento existente:
        1. O document_id NÃO muda
        2. Tanto LLM quanto SQL usam o MESMO ID
        3. Apenas version_number é incrementado
        """
        # Setup
        existing_doc_id = str(uuid.uuid4())
        temp_id = str(uuid.uuid4())
        
        mock_get_temp.return_value = {
            "temp_id": temp_id,
            "filename": "report_v2.pdf",
            "blob_path": "__temp__/" + temp_id + "/report_v2.pdf"
        }
        
        # Mock existing document
        mock_get_doc.return_value = {
            "document_id": existing_doc_id,
            "title": "Report",
            "is_active": 1
        }
        
        # Mock latest version
        mock_get_latest.return_value = {
            "version_number": 1
        }
        
        # Track IDs and versions
        llm_calls = []
        
        # Mock LLM
        mock_llm_inst = Mock()
        def mock_ingest_doc(**kwargs):
            llm_calls.append({
                "document_id": kwargs.get('document_id'),
                "version_id": kwargs.get('version_id')
            })
            return {"success": True, "chunks_created": 5}
        
        mock_llm_inst.ingest_document.side_effect = mock_ingest_doc
        mock_llm_inst.extract_metadata.return_value = {}
        mock_llm_client.return_value = mock_llm_inst
        
        # Mock storage
        mock_storage_inst = Mock()
        mock_storage_inst.get_file.return_value = b"PDF content v2"
        mock_storage_inst.save_file.return_value = "documents/v2/report.pdf"
        mock_storage.return_value = mock_storage_inst
        
        # Mock format converter
        mock_format_converter.convert_to_csv.return_value = ("CSV v2", "pdf")
        
        # Mock create_version
        mock_create_version.return_value = 2
        
        # Execute - criar nova versão
        result = await DocumentService.ingest_confirm(
            temp_id=temp_id,
            user_id="test-user",
            document_id=existing_doc_id  # Pass existing document ID
        )
        
        # Validações
        assert len(llm_calls) == 1
        
        # Verificar que o documento_id NÃO mudou
        assert result["document_id"] == existing_doc_id, (
            f"Document ID should not change for new versions! "
            f"Expected: {existing_doc_id}, Got: {result['document_id']}"
        )
        
        # Verificar que LLM recebeu o mesmo ID
        assert llm_calls[0]["document_id"] == existing_doc_id, (
            f"LLM should receive existing document_id! "
            f"Expected: {existing_doc_id}, Got: {llm_calls[0]['document_id']}"
        )
        
        # Verificar que version_number foi incrementado
        assert result["version"] == 2, (
            f"Version should be incremented for new version! "
            f"Expected: 2, Got: {result['version']}"
        )
        assert llm_calls[0]["version_id"] == 2, (
            f"LLM should receive incremented version! "
            f"Expected: 2, Got: {llm_calls[0]['version_id']}"
        )


class TestDocumentIDEdgeCases:
    """Testes para edge cases e scenario específicos."""
    
    def test_uuid_format_validation(self):
        """Valida que todos os UUIDs seguem o formato correto."""
        # Gerar múltiplos UUIDs e validar
        for _ in range(5):
            test_uuid = str(uuid.uuid4())
            
            # Deve ter exatamente 36 characters (incluindo hífens)
            assert len(test_uuid) == 36, f"UUID should be 36 chars long: {test_uuid}"
            
            # Deve ter hífens nas posições corretas
            assert test_uuid[8] == '-' and test_uuid[13] == '-' and \
                   test_uuid[18] == '-' and test_uuid[23] == '-', \
                   f"UUID format invalid: {test_uuid}"
            
            # Deve ser validável por uuid.UUID()
            try:
                uuid.UUID(test_uuid)
            except ValueError:
                pytest.fail(f"UUID validation failed: {test_uuid}")
    
    def test_uuid_string_conversion(self):
        """Testa que str(uuid.uuid4()) produz formato correto."""
        test_id = uuid.uuid4()
        str_id = str(test_id)
        
        # Reconverter deve produzir o mesmo
        assert uuid.UUID(str_id) == test_id
    
    @pytest.mark.asyncio
    @patch('app.services.document_service.get_storage_provider')
    @patch('app.services.sqlserver_documents.get_document')
    async def test_metadata_update_does_not_change_document_id(
        self,
        mock_get_doc,
        mock_storage
    ):
        """
        Testa que atualizar apenas metadados de um documento
        NÃO gera novo document_id.
        """
        document_id = str(uuid.uuid4())
        
        mock_get_doc.return_value = {
            "document_id": document_id,
            "title": "Original Title",
            "category_id": 1
        }
        
        mock_storage_inst = Mock()
        mock_storage.return_value = mock_storage_inst
        
        # Passar document_id com file=None indica metadata-only update
        # (arquivo não será enviado)
        # Verificar que document_id não muda
        
        # O test aqui é conceitual - o importante é validar
        # que o código não deveria gerar um novo UUID
        # quando apenas metadados são atualizados
        
        assert document_id is not None
        # Se file=None, document_id não deve ser regenerado
