"""
LLM Server Endpoints Documentation
Estes endpoints devem ser implementados no LLM Server para comunicação com o Backend.
"""

# Endpoints esperados no LLM Server:

"""
1. POST /llm/ingest
   Ingerir chunks no Azure AI Search
   
   Request:
   {
       "document_id": "550e8400-e29b-41d4-a716-446655440000",
       "chunks": [
           {
               "text": "Conteúdo do chunk 1",
               "chunk_index": 0,
               "metadata": {
                   "document_id": "550e8400-e29b-41d4-a716-446655440000",
                   "title": "Documento.pdf",
                   "user_id": "user123",
                   "version": 1,
                   "source": "documents/550e8400-e29b-41d4-a716-446655440000/1/Documento.pdf"
               }
           },
           ...
       ]
   }
   
   Response (200):
   {
       "status": "success",
       "document_id": "550e8400-e29b-41d4-a716-446655440000",
       "chunks_indexed": 5,
       "message": "Chunks ingested successfully"
   }


2. POST /llm/delete
   Deletar documento do Azure AI Search
   
   Request:
   {
       "document_id": "550e8400-e29b-41d4-a716-446655440000"
   }
   
   Response (200):
   {
       "status": "success",
       "document_id": "550e8400-e29b-41d4-a716-446655440000",
       "chunks_deleted": 5,
       "message": "Document deleted from AI Search"
   }


3. GET /health
   Health check
   
   Response (200):
   {
       "status": "ok",
       "service": "llm-server"
   }
"""

# Responsabilidades do LLM Server:
# 1. Receber chunks com metadata
# 2. Gerar embeddings (usando Azure OpenAI)
# 3. Indexar no Azure AI Search com document_id como filtro
# 4. Manter apenas a última versão de cada documento
# 5. Deletar todos os chunks de um documento quando solicitado

# Fluxo:
# Backend (FastAPI)
#     ↓
# Salva no Blob Storage
# Cria metadados no SQL Server
# Divide em chunks
#     ↓
# LLM Server
#     ↓
# Gera embeddings
# Indexa no Azure AI Search
#     ↓
# Retorna confirmação ao Backend
