# 📊 Diagramas de Arquitetura - Fluxos Visuais

**Diagramas dos fluxos principais do backend em Mermaid.js**

---

## Índice

1. [Fluxo de Autenticação](#fluxo-de-autenticação)
2. [Fluxo de Ingestão de Documentos](#fluxo-de-ingestão-de-documentos)
3. [Fluxo de Chat com LLM](#fluxo-de-chat-com-llm)
4. [Integrações: Request → Serviços → Resposta](#integrações-request--serviços--resposta)

---

## Fluxo de Autenticação

Quando um usuário faz login pela primeira vez:

```mermaid
sequenceDiagram
    participant User as Usuário<br/>(Frontend)
    participant API as Backend<br/>(FastAPI)
    participant AzureAD as Azure Entra ID<br/>(MSAL)
    participant DB as SQL Server<br/>(Banco)
    
    User->>API: 1. GET /api/v1/login
    
    API->>AzureAD: 2. Redireciona para Azure
    AzureAD-->>User: 3. Página de login Azure
    
    User->>AzureAD: 4. Digita credenciais
    AzureAD-->>User: 5. Redireciona com código
    
    User->>API: 6. GET /api/v1/getatoken?code=...
    
    API->>AzureAD: 7. Valida código<br/>(MSAL)
    AzureAD-->>API: 8. Retorna Access Token +<br/>User Info
    
    API->>DB: 9. Busca/Cria usuário
    DB-->>API: 10. Usuário carregado
    
    API->>API: 11. Gera JWT interno
    
    API-->>User: 12. Set Cookie (JWT)<br/>Redireciona para /app/chat
    
    Note over User,API: ✅ Autenticado!<br/>Próximas requisições: Cookie HTTPOnly
```

**Detalhes**:
- ✅ Token do Azure → Valida identidade
- ✅ JWT interno → Sessão do backend
- ✅ Cookie HTTPOnly → Seguro contra XSS
- ✅ Cada request valida JWT no middleware

---

## Fluxo de Ingestão de Documentos

Vou documentar o fluxo **2-step** (preview → confirm):

### Etapa 1: Preview

```mermaid
sequenceDiagram
    participant User as Usuário<br/>(Frontend)
    participant API as Backend<br/>document_service
    participant Storage as Blob Storage<br/>(Temp)
    participant LLM as LLM Server<br/>(IA)
    
    User->>+API: 1. POST /ingest-preview<br/>file=documento.pdf
    
    API->>+Storage: 2. Cria pasta temp<br/>storage/temp/{temp_id}/
    Storage-->>-API: 3. Pasta criada
    
    API->>+API: 4. Detecta formato<br/>(PDF/DOCX/XLSX)
    API->>API: 5. Extrai texto<br/>(converter para string)
    API->>API: 6. Limpa texto<br/>(remove binário, metadados)
    API->>API: 7. Trunca se > 50KB
    API-->>-API: 8. Texto pronto
    
    API->>+LLM: 9. POST /api/v1/preview<br/>text=documento.pdf<br/>user_info=xxx
    
    LLM->>+LLM: 10. Parse com LLM<br/>(GPT-4o)
    LLM-->>-API: 11. Metadados sugeridos:<br/>- allowed_countries: [BR, US]<br/>- allowed_cities: [SP, RJ]<br/>- min_role_level: 2
    
    API-->>-User: 12. Retorna:<br/>temp_id<br/>suggested_metadata<br/>expires_in_seconds
    
    Note over Storage: ⏰ Auto-delete<br/>após 10 min
```

**O Que Acontece**:
- ✅ Arquivo salvo temporariamente
- ✅ Texto extraído e limpo
- ✅ LLM sugere metadados
- ✅ Usuário revisa em frontend
- ✅ Arquivo expira em 10 min se não confirmar

---

### Etapa 2: Confirm

```mermaid
sequenceDiagram
    participant User as Usuário
    participant API as Backend<br/>document_service
    participant Blob as Blob Storage<br/>(Permanente)
    participant DB as SQL Server<br/>(Metadados)
    participant LLM as LLM Server<br/>(Indexação)
    
    User->>+API: 1. POST /ingest-confirm/{temp_id}<br/>user_id=alice<br/>allowed_countries=[BR]<br/>category_id=5
    
    API->>+Blob: 2. Recupera arquivo temp
    Blob-->>-API: 3. Retorna conteúdo
    
    API->>API: 4. Valida metadados
    
    API->>+LLM: 5. POST /api/v1/ingest<br/>document_id=xxx<br/>text=...<br/>chunks=...
    
    LLM->>+LLM: 6. Divide em chunks
    LLM->>LLM: 7. Gera embeddings<br/>(Azure OpenAI)
    LLM->>LLM: 8. Indexa em Azure AI Search
    LLM-->>-API: 9. ✅ Success<br/>chunks_indexed: 42<br/>embedding_model: text-embedding-3-large
    
    API->>+DB: 10. INSERT documento<br/>id, title, user_id, allowed_countries,<br/>category_id, created_at, ...
    DB-->>-API: 11. document_id=550e8400-...
    
    API->>+DB: 12. INSERT versão<br/>document_id, version=1,<br/>filename, created_by, ...
    DB-->>-API: 13. version_id=...
    
    API->>+Blob: 14. Move arquivo<br/>temp/{temp_id}/ → permanent/{doc_id}/1/
    Blob-->>-API: 15. ✅ Movido
    
    API->>+Blob: 16. Delete temp folder
    Blob-->>-API: 17. ✅ Deletado
    
    API-->>-User: 18. Retorna:<br/>document_id<br/>status: "ingested"<br/>version: 1
    
    Note over LLM: 📍 Documento agora<br/>está indexado<br/>e pronto para busca
```

**O Que Acontece**:
- ✅ Arquivo recuperado do temp
- ✅ LLM Server indexa + gera embeddings
- ✅ Metadados salvos no SQL Server
- ✅ Arquivo movido para permanent
- ✅ Arquivo temp deletado
- ✅ **Pronto para chat!**

---

## Fluxo de Chat com LLM

Quando usuário faz pergunta:

```mermaid
sequenceDiagram
    participant User as Usuário<br/>(Frontend)
    participant API as Backend<br/>chat_service
    participant DB as SQL Server<br/>(Histórico)
    participant LLM as LLM Server<br/>(Busca + IA)
    participant Search as Azure AI Search<br/>(Índice)
    participant OpenAI as Azure OpenAI<br/>(GPT-4o)
    
    User->>+API: 1. POST /api/v1/chat/question<br/>user_id=alice<br/>country=Brazil<br/>role=Manager<br/>question=Quais benefícios?
    
    API->>+DB: 2. GET conversa<br/>(ou cria nova)
    DB-->>-API: 3. Retorna conversation_id
    
    API->>+DB: 4. INSERT mensagem user
    DB-->>-API: 5. message_id=xxx
    
    API->>+LLM: 6. POST /api/v1/question<br/>user_id=alice<br/>country=Brazil<br/>role=Manager<br/>question=Quais benefícios?<br/>conversation_id=yyy
    
    LLM->>+Search: 7. Busca semântica<br/>query: "benefícios"<br/>filtro: role >= Manager<br/>filtro: country IN [Brazil]
    
    Search->>+OpenAI: 8. Gera embedding da pergunta
    OpenAI-->>-Search: 9. Embedding vector
    
    Search->>Search: 10. Vector search<br/>(cosine similarity)
    Search-->>-LLM: 11. Top 5 documentos<br/>relevantes + score
    
    LLM->>+OpenAI: 12. POST chat.completions<br/>system_prompt + docs contexto<br/>user_question
    
    OpenAI->>+OpenAI: 13. Processa com GPT-4o<br/>(streaming possível)
    OpenAI-->>-LLM: 14. Resposta + tokens used
    
    LLM-->>-API: 15. Retorna:<br/>answer: "Os benefícios são..."<br/>source_documents: [doc1.pdf, doc2.pdf]<br/>num_documents: 5<br/>total_time_ms: 2345
    
    API->>+DB: 16. INSERT mensagem assistant
    DB-->>-API: 17. message_id=zzz
    
    API-->>-User: 18. Retorna resposta<br/>+ documentos relevantes<br/>+ tempo de resposta<br/>+ tokens utilizados
    
    Note over User,OpenAI: ✅ Response completa!<br/>Historiado automaticamente
```

**Detalhes Importantes**:
- ✅ Busca semântica (não por keyword)
- ✅ Filtros de RBAC (role, país, cidade)
- ✅ Contexto dos documentos incluído
- ✅ Histórico salvo para reference
- ✅ Tempos rastreados

---

## Integrações: Request → Serviços → Resposta

Visão geral de como um request flui pela aplicação:

```mermaid
graph TB
    User["👤 Usuário<br/>(Frontend)"]
    
    User -->|HTTP Request| Router["🔗 Router<br/>(FastAPI endpoint)"]
    
    Router -->|Valida| Pydantic["✓ Pydantic<br/>(Schema validation)"]
    Pydantic -->|Passa| Middleware["🔒 Middleware<br/>(JWT validation)"]
    
    Middleware -->|Autoriza| Service["⚙️ Service<br/>(Lógica de negócio)"]
    
    Service -->|Lê dados| DB["🗄️ SQL Server<br/>(Azure SQL)"]
    Service -->|Upload/Download| Blob["📦 Blob Storage<br/>(Azure)"]
    Service -->|Busca/Indexa| LLM["🤖 LLM Server<br/>(IA)"]
    
    DB -.->|Retorna dados| Service
    Blob -.->|Retorna arquivo| Service
    LLM -.->|Retorna resultado| Service
    
    Service -->|Formata resposta| ResponseModel["📄 Response Model<br/>(Pydantic)"]
    ResponseModel -->|JSON| Router
    
    Router -->|HTTP 200/4xx/5xx| User
    
    style User fill:#e1f5ff
    style Router fill:#fff3e0
    style Service fill:#f3e5f5
    style DB fill:#e8f5e9
    style Blob fill:#fce4ec
    style LLM fill:#fff9c4
```

**Fluxo Resumido**:
```
Request → Router → Validação → Middleware Auth → Service → Providers (DB/Blob/LLM) → Response
```

---

## Arquitetura de 5 Camadas

Visão estática da organização do código:

```mermaid
graph TD
    A["🌐 HTTP Layer<br/>(FastAPI)"]
    
    A --> B["🔗 Routers (14)<br/>- auth.py<br/>- documents.py<br/>- chat.py<br/>- master_data.py<br/>- etc"]
    
    B --> C["⚙️ Services (16)<br/>- document_service.py<br/>- conversation_service.py<br/>- llm_integration.py<br/>- etc"]
    
    C --> D["🔌 Providers<br/>1. auth_msal.py<br/>2. storage.py<br/>3. llm_server.py<br/>4. metadata_extractor.py"]
    
    D --> E["🗂️ External Services<br/>- Azure SQL Server<br/>- Azure Blob Storage<br/>- Azure Entra ID<br/>- Azure OpenAI<br/>- Azure AI Search<br/>- LLM Server"]
    
    C --> F["📋 Core<br/>- config.py (KeyVaultConfig)<br/>- sqlserver.py (DB Connection)<br/>- logging"]
    
    style A fill:#1976d2,color:#fff
    style B fill:#388e3c,color:#fff
    style C fill:#d32f2f,color:#fff
    style D fill:#f57c00,color:#fff
    style E fill:#7b1fa2,color:#fff
    style F fill:#0097a7,color:#fff
```

**Responsabilidades**:
- **Routers**: HTTP → Parse → Call Service
- **Services**: Lógica de negócio → Orquestra providers
- **Providers**: Interface com externos (Azure, LLM)
- **Core**: Config, DB, logging compartilhado

---

## Fluxo de Erro (Error Handling)

O que acontece quando dá erro:

```mermaid
sequenceDiagram
    participant User as Usuário
    participant API as Backend
    participant Provider as Provider<br/>(BD/Storage/LLM)
    
    User->>+API: Request
    API->>+Provider: Operação
    
    alt ✅ Sucesso
        Provider-->>-API: Success
        API-->>-User: 200 + data
    else ❌ Erro Provider
        Provider->>-API: Exception
        API->>API: Catch + Log
        
        alt Erro de Validação
            API-->>User: 400 Bad Request
        else Erro de Auth
            API-->>User: 401 Unauthorized
        else Erro de Negócio
            API-->>User: 422 Unprocessable Entity
        else Erro Servidor
            API-->>User: 500 Internal Server Error
        end
    end
    
    Note over API: 🔍 Sempre logga erro<br/>User ID, request ID, timestamp
```

---

## Ciclo de Vida de um Documento

Desde upload até aparecer em buscas:

```mermaid
graph LR
    A["📄 Frontend<br/>Seleciona arquivo"]
    B["📤 Preview<br/>Arquivo em TEMP"]
    C["🔍 LLM Extrai<br/>Metadados"]
    D["👤 Usuário<br/>Revisa"]
    E["✅ Confirm<br/>Pronto"]
    F["📦 Permanente<br/>Blob Storage"]
    G["🗄️ SQL<br/>Metadados"]
    H["🤖 LLM Indexa<br/>Embeddings"]
    I["🔎 Pronto Para<br/>Busca"]
    
    A -->|POST preview| B
    B -->|Extract| C
    C -->|Sugere| D
    D -->|Accept| E
    E -->|Move| F
    E -->|INSERT| G
    E -->|Ingest| H
    H -->|Indexed| I
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style C fill:#fff9c4
    style D fill:#f3e5f5
    style E fill:#c8e6c9
    style F fill:#fce4ec
    style G fill:#b2dfdb
    style H fill:#ffe0b2
    style I fill:#c8e6c9
```

---

## Filtros de Segurança (RBAC)

Como os documentos são filtrados em buscas:

```mermaid
graph TD
    A["📝 Documento<br/>Indexado"]
    
    A -->|Metadata| B["allowed_countries: [BR, US]"]
    A -->|Metadata| C["allowed_cities: [SP, RJ]<br/>ou null"]
    A -->|Metadata| D["min_role_level: 2"]
    A -->|Metadata| E["created_by: user_id"]
    
    B -->|Validar| F["User Country<br/>= Brazil ✓"]
    C -->|Validar| G["User City<br/>= SP ✓"]
    D -->|Validar| H["User Role Level<br/>= 3 ✓ >= 2"]
    
    F & G & H -->|All Pass| I["✅ Documento<br/>Retornado"]
    
    F -->|Fail| J["❌ Documento<br/>Filtrado"]
    G -->|Fail| J
    H -->|Fail| J
    
    style I fill:#c8e6c9
    style J fill:#ffcdd2
```

---

## Deployment: Request → Container → Produção

Visão de como request chega em produção:

```mermaid
graph LR
    User["👤 User<br/>(Frontend)"]
    CDN["🌐 CDN<br/>(Frontend)"]
    AppGW["🚪 Application<br/>Gateway<br/>(Routing)"]
    
    LB["⚖️ Load Balancer<br/>(Azure)"]
    
    Container1["🐳 Container 1<br/>API:8000"]
    Container2["🐳 Container 2<br/>API:8000"]
    Container3["🐳 Container 3<br/>API:8000"]
    
    DB[(🗄️ Azure SQL<br/>Managed)]
    Cache["💾 Redis<br/>Cache"]
    
    User -->|HTTPS| CDN
    CDN -->|Static Assets| User
    
    User -->|API Request<br/>HTTPS| AppGW
    AppGW -->|Route| LB
    
    LB -->|Distribute| Container1 & Container2 & Container3
    
    Container1 & Container2 & Container3 -->|Query| DB
    Container1 & Container2 & Container3 -->|Cache| Cache
    
    style User fill:#e1f5ff
    style AppGW fill:#fff3e0
    style LB fill:#f3e5f5
    style Container1 fill:#c8e6c9
    style Container2 fill:#c8e6c9
    style Container3 fill:#c8e6c9
    style DB fill:#ffcdd2
    style Cache fill:#fff9c4
```

---

## Referências & Termos

### Componentes

| Termo | O Quê |
|-------|--------|
| **Router** | Endpoint HTTP (POST /api/v1/documents) |
| **Service** | Lógica (document_service.py) |
| **Provider** | Interface com externos (storage.py) |
| **Middleware** | Filtro aplicado a TODAS as requisições |
| **Pydantic Model** | Validação de schema JSON |

### Protocolos

| Tipo | Descrição |
|------|-----------|
| **HTTP/HTTPS** | Comunicação Frontend ↔ Backend |
| **Azure MSAL** | Protocolo de autenticação Azure AD |
| **JWT** | Token de sessão |
| **REST** | Estilo de API (GET, POST, PUT, DELETE) |

### Azure Services

| Serviço | Função |
|---------|--------|
| **Azure SQL Server** | Banco de dados relacional |
| **Azure Blob Storage** | Armazenamento de arquivos |
| **Azure Entra ID** | Autenticação corporativa |
| **Azure OpenAI** | Modelos de IA (GPT-4o) |
| **Azure AI Search** | Busca semântica com embeddings |

---

## 🎯 Resumo Visual

```
┌──────────────────────────────────────────────────────────────┐
│                  SECURE DOCUMENT PLATFORM                     │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  👤 User → [Auth] → JWT → [Router] → [Service] → [Provider] │
│                                            ↓                  │
│                              ┌─────────────────────┬───────┐ │
│                              ↓                     ↓       ↓ │
│                          SQL Server         Blob Storage  LLM│
│                                                                │
│  [Upload] → [Preview - Temp] → [Confirm - Permanent]  [Chat]│
│               ↓                      ↓                   ↓    │
│          LLM Extracts          Insert Metadata      Search DB│
│          Metadatos             Index in LLM         + LLM AI │
│                                                                │
│                     ✅ Seguro ✅ Rápido ✅ Escalável        │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 📚 Próximas Leituras

Para entender cada parte:
- [RUN_LOCAL_COMPLETE_GUIDE.md](RUN_LOCAL_COMPLETE_GUIDE.md) - Como rodar
- [CONFIG_KEYS.md](CONFIG_KEYS.md) - Variáveis
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - Arquitetura textual
- [DOCUMENT_INGESTION.md](DOCUMENT_INGESTION.md) - Detalhes de ingestão
- [CHAT_API.md](CHAT_API.md) - API de chat

---

**Última atualização**: 20/03/2026  
**Criado em**: Mermaid.js  
**Visualizador**: GitHub Markdown ou https://mermaid.live
