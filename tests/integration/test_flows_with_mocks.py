"""
Testes de fluxo completo com mocks funcionais
Testa lógica real dos serviços com BD em memória
"""

import pytest
from uuid import uuid4

from tests.fixtures.mocks import (
    create_mock_sqlserver,
    create_mock_llm_server,
    create_mock_storage,
)


class TestDocumentFlowWithMocks:
    """Testa fluxo completo de documento com mocks funcionais"""
    
    @pytest.fixture
    def mocks(self):
        """Setup dos mocks"""
        return {
            'db': create_mock_sqlserver(),
            'llm': create_mock_llm_server(),
            'storage': create_mock_storage(),
        }
    
    @pytest.mark.asyncio
    async def test_document_lifecycle_create_search_delete(self, mocks):
        """Testa ciclo completo: criar → buscar → deletar documento"""
        db = mocks['db']
        user_id = "test-user"
        
        # 1. Criar documento
        doc_id = await db.save_document_metadata(
            name="test_document.pdf",
            user_id=user_id,
            content="This is about embeddings and machine learning"
        )
        assert doc_id is not None
        
        # 2. Verificar que foi salvom
        doc = await db.get_document_metadata(doc_id)
        assert doc is not None
        assert doc['name'] == "test_document.pdf"
        assert doc['user_id'] == user_id
        
        # 3. Buscar documento
        search_results = await db.search_documents(user_id, "embeddings")
        assert len(search_results) > 0
        assert doc_id in [d['id'] for d in search_results]
        
        # 4. Listar documentos
        all_docs = await db.list_documents(user_id)
        assert len(all_docs) > 0
        assert doc_id in [d['id'] for d in all_docs]
        
        # 5. Deletar documento
        deleted = await db.delete_document(doc_id)
        assert deleted is True
        
        # 6. Verificar que desapareceu da lista
        all_docs_after = await db.list_documents(user_id)
        assert doc_id not in [d['id'] for d in all_docs_after]
    
    @pytest.mark.asyncio
    async def test_document_search_multiple_documents(self, mocks):
        """Testa busca com múltiplos documentos"""
        db = mocks['db']
        user_id = "test-user"
        
        # Criar vários documentos
        doc1_id = await db.save_document_metadata(
            name="embeddings.pdf",
            user_id=user_id,
            content="Embeddings are vector representations"
        )
        doc2_id = await db.save_document_metadata(
            name="ml_basics.pdf",
            user_id=user_id,
            content="Machine learning is about learning from data"
        )
        doc3_id = await db.save_document_metadata(
            name="capital_cities.pdf",
            user_id=user_id,
            content="Paris is the capital of France"
        )
        
        # Buscar por "embeddings"
        results = await db.search_documents(user_id, "embeddings")
        assert len(results) == 1
        assert results[0]['id'] == doc1_id
        
        # Buscar por "learning"
        results = await db.search_documents(user_id, "learning")
        assert len(results) == 1
        assert results[0]['id'] == doc2_id
        
        # Buscar por "Paris"
        results = await db.search_documents(user_id, "Paris")
        assert len(results) == 1
        assert results[0]['id'] == doc3_id


class TestChatFlowWithMocks:
    """Testa fluxo completo de chat com mocks funcionais"""
    
    @pytest.fixture
    def mocks(self):
        """Setup dos mocks"""
        return {
            'db': create_mock_sqlserver(),
            'llm': create_mock_llm_server(),
            'storage': create_mock_storage(),
        }
    
    @pytest.mark.asyncio
    async def test_conversation_lifecycle(self, mocks):
        """Testa ciclo: criar conversa → enviar mensagens → recuperar"""
        db = mocks['db']
        user_id = "test-user"
        
        # 1. Criar conversa
        conv_id = await db.create_conversation(user_id, title="Conversa de Teste")
        assert conv_id is not None
        
        # 2. Obter conversa
        conv = await db.get_conversation(user_id, conv_id)
        assert conv is not None
        assert conv['title'] == "Conversa de Teste"
        assert conv['user_id'] == user_id
        assert len(conv['messages']) == 0
        
        # 3. Adicionar mensagem do usuário
        msg1_id = await db.save_message(user_id, conv_id, "user", "What is embeddings?")
        assert msg1_id is not None
        
        # 4. Adicionar resposta do assistente
        msg2_id = await db.save_message(
            user_id, conv_id, "assistant", 
            "Embeddings são representações vetoriais de texto"
        )
        assert msg2_id is not None
        
        # 5. Verificar mensagens
        messages = await db.get_messages(user_id, conv_id)
        assert len(messages) == 2
        assert messages[0]['role'] == "user"
        assert messages[1]['role'] == "assistant"
        
        # 6. Listar conversas do usuário
        convs = await db.get_user_conversations(user_id)
        assert len(convs) > 0
        assert conv_id in [c['id'] for c in convs]
    
    @pytest.mark.asyncio
    async def test_llm_question_with_documents(self, mocks):
        """Testa fluxo: buscar documentos → chamar LLM → salvar resposta"""
        db = mocks['db']
        llm = mocks['llm']
        user_id = "test-user"
        
        # 1. Criar e salvar documento
        doc_id = await db.save_document_metadata(
            name="test.pdf",
            user_id=user_id,
            content="Embeddings are vector representations of text"
        )
        
        # 2. Buscar documento
        search_results = await db.search_documents(user_id, "embeddings")
        assert len(search_results) > 0
        
        # 3. Chamar LLM com documento
        question = "What are embeddings?"
        response = await llm.ask_question(
            question=question,
            documents=search_results,
            role_id=1,
            user_id=user_id,
            chat_id=None
        )
        
        assert response['answer'] is not None
        assert len(response['answer']) > 0
        assert response['confidence'] > 0
        assert len(response['sources']) > 0
    
    @pytest.mark.asyncio
    async def test_llm_validation_invalid_role(self, mocks):
        """Testa que LLM rejeita role_id inválido"""
        llm = mocks['llm']
        
        # role_id 0 deve ser rejeitado
        with pytest.raises(ValueError) as exc_info:
            await llm.ask_question(
                question="test",
                role_id=0,
                user_id="test"
            )
        
        assert "role_id" in str(exc_info.value)
        assert "must be 1-15 or 99" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_llm_validation_valid_roles(self, mocks):
        """Testa que LLM aceita roles válidos"""
        llm = mocks['llm']
        valid_roles = [1, 5, 10, 15, 99]
        
        for role_id in valid_roles:
            response = await llm.ask_question(
                question="test question",
                role_id=role_id,
                user_id="test"
            )
            assert response is not None
            assert response['answer'] is not None


class TestStorageFlowWithMocks:
    """Testa fluxo de armazenamento com mocks"""
    
    @pytest.fixture
    def mocks(self):
        """Setup dos mocks"""
        return {
            'db': create_mock_sqlserver(),
            'llm': create_mock_llm_server(),
            'storage': create_mock_storage(),
        }
    
    @pytest.mark.asyncio
    async def test_file_upload_download(self, mocks):
        """Testa ciclo: fazer upload → download arquivo"""
        storage = mocks['storage']
        
        # 1. Upload arquivo
        content = b"PDF content here"
        path = "documents/test_doc_v1.pdf"
        url = await storage.upload_file(content, path)
        
        assert url is not None
        assert "test_doc_v1" in url
        
        # 2. Download arquivo
        downloaded = await storage.download_file(path)
        assert downloaded == content
    
    @pytest.mark.asyncio
    async def test_file_delete(self, mocks):
        """Testa deleção de arquivo"""
        storage = mocks['storage']
        
        # 1. Upload
        content = b"test content"
        path = "documents/delete_test.pdf"
        await storage.upload_file(content, path)
        
        # 2. Verificar que existe
        exists = await storage.download_file(path)
        assert exists == content
        
        # 3. Deletar
        deleted = await storage.delete_file(path)
        assert deleted is True
        
        # 4. Verificar que foi deletado
        gone = await storage.download_file(path)
        assert gone == b""


class TestCompleteUserJourney:
    """Testa jornada completa do usuário"""
    
    @pytest.fixture
    def mocks(self):
        """Setup dos mocks"""
        return {
            'db': create_mock_sqlserver(),
            'llm': create_mock_llm_server(),
            'storage': create_mock_storage(),
        }
    
    @pytest.mark.asyncio
    async def test_full_journey_ingest_query_chat(self, mocks):
        """
        Jornada completa:
        1. Upload documento
        2. Buscar documento
        3. Criar conversa
        4. Fazer pergunta com LLM
        5. Salvar resposta
        """
        db = mocks['db']
        llm = mocks['llm']
        storage = mocks['storage']
        
        user_id = "journey-user"
        
        # ETAPA 1: Ingerir documento
        doc_content = b"The capital of France is Paris. Paris is located in the north-central part of the country."
        storage_path = f"documents/{user_id}/document_v1.pdf"
        
        storage_url = await storage.upload_file(doc_content, storage_path)
        assert storage_url is not None
        
        # ETAPA 2: Salvar metadados
        doc_id = await db.save_document_metadata(
            name="facts_about_france.pdf",
            user_id=user_id,
            content=doc_content.decode('utf-8')
        )
        assert doc_id is not None
        
        # ETAPA 3: Criar conversa
        conv_id = await db.create_conversation(user_id, title="Questions about France")
        assert conv_id is not None
        
        # ETAPA 4: Usuário faz pergunta
        question = "What is the capital of France?"
        msg_id = await db.save_message(user_id, conv_id, "user", question)
        assert msg_id is not None
        
        # ETAPA 5: Buscar documentos relacionados
        search_results = await db.search_documents(user_id, "capital")
        assert len(search_results) > 0
        
        # ETAPA 6: LLM responde
        llm_response = await llm.ask_question(
            question=question,
            documents=search_results,
            role_id=1,
            user_id=user_id
        )
        assert llm_response['answer'] is not None
        
        # ETAPA 7: Salvar resposta na conversa
        response_msg_id = await db.save_message(
            user_id, conv_id, "assistant", llm_response['answer']
        )
        assert response_msg_id is not None
        
        # ETAPA 8: Verificar conversa completa
        messages = await db.get_messages(user_id, conv_id)
        assert len(messages) == 2
        assert messages[0]['content'] == question
        assert "Paris" in messages[1]['content']
    
    @pytest.mark.asyncio
    async def test_journey_with_invalid_role_error_handling(self, mocks):
        """Testa jornada com erro de validação de role_id"""
        db = mocks['db']
        llm = mocks['llm']
        user_id = "error-user"
        
        # 1. Criar conversa
        conv_id = await db.create_conversation(user_id)
        
        # 2. Usuário faz pergunta
        question = "Test question"
        msg_id = await db.save_message(user_id, conv_id, "user", question)
        assert msg_id is not None
        
        # 3. Tentar chamar LLM com role_id inválido
        with pytest.raises(ValueError) as exc_info:
            await llm.ask_question(
                question=question,
                role_id=0,  # INVÁLIDO
                user_id=user_id
            )
        
        # 4. Verificar que erro contém informação útil
        error_msg = str(exc_info.value)
        assert "role_id" in error_msg
        assert "must be" in error_msg
        
        # 5. Conversa ainda existe (não foi afetada pelo erro)
        conv = await db.get_conversation(user_id, conv_id)
        assert conv is not None
        assert len(conv['messages']) == 1  # Pergunta continua lá
