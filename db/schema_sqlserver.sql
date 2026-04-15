-- SQL Server Schema para PeopleChatBot

-- Tabela de documentos
CREATE TABLE documents (
    document_id NVARCHAR(36) PRIMARY KEY,
    title NVARCHAR(255) NOT NULL,
    user_id NVARCHAR(255) NOT NULL,
    category_id INT,  -- FK para dim_categories (opcional)
    min_role_level INT DEFAULT 0,
    allowed_roles NVARCHAR(MAX),        -- JSON array de roles específicos
    allowed_countries NVARCHAR(MAX),    -- JSON array (do formulário)
    allowed_cities NVARCHAR(MAX),       -- JSON array (do formulário)
    location_ids NVARCHAR(MAX) NULL,    -- JSON array dos location_ids: [123, 456]
    addresses NVARCHAR(MAX) NULL,       -- JSON array: ["Rua X", "Avenida Y"] (do formulário ou lookup)
    collar NVARCHAR(255),
    plant_code NVARCHAR(255),
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    INDEX idx_user_id (user_id),
    INDEX idx_category_id (category_id),
    INDEX idx_created_at (created_at)
);

-- Tabela de versões
CREATE TABLE versions (
    version_id NVARCHAR(36) PRIMARY KEY,
    document_id NVARCHAR(36) NOT NULL,
    version_number INT NOT NULL,
    blob_path NVARCHAR(MAX) NOT NULL,  -- Caminho no Blob Storage
    filename NVARCHAR(255),             -- Nome do arquivo que foi enviado nesta versão
    updated_by NVARCHAR(255),           -- Usuário que atualizou esta versão
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    UNIQUE (document_id, version_number),
    INDEX idx_document_id (document_id),
    INDEX idx_active (is_active)
);

-- Tabela de permissões (opcional, para controle fino)
CREATE TABLE permissions (
    permission_id NVARCHAR(36) PRIMARY KEY,
    document_id NVARCHAR(36) NOT NULL,
    user_id NVARCHAR(255) NOT NULL,
    can_read BIT DEFAULT 1,
    can_update BIT DEFAULT 0,
    can_delete BIT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    UNIQUE (document_id, user_id),
    INDEX idx_user_doc (user_id, document_id)
);

-- Índices para performance
CREATE INDEX idx_documents_user_active ON documents(user_id, is_active);
CREATE INDEX idx_versions_document_active ON versions(document_id, is_active);

-- Tabela de uploads temporários (para fluxo preview -> confirm)
CREATE TABLE temp_uploads (
    temp_id NVARCHAR(36) PRIMARY KEY,
    user_id NVARCHAR(255),  -- Nullable: preenchido apenas no ingest_confirm
    filename NVARCHAR(255) NOT NULL,
    blob_path NVARCHAR(MAX) NOT NULL,  -- Caminho no Blob Storage (__temp__/...)
    file_size_bytes INT,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    expires_at DATETIME2,  -- 10 minutos após criação
    is_confirmed BIT DEFAULT 0,  -- 1 se foi movido para documentos permanentes
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_created_at (created_at)
);

-- Tabela de conversas/histórico com LLM
CREATE TABLE conversations (
    conversation_id NVARCHAR(36) PRIMARY KEY,
    user_id NVARCHAR(255) NOT NULL,
    document_id INT,  -- Documento referenciado na conversa (opcional)
    title NVARCHAR(MAX),  -- Título da conversa
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    is_active BIT DEFAULT 1,
    rating DECIMAL(2,1) NULL,  -- Avaliação de 0.0 a 5.0 (com meia)
    rating_timestamp DATETIME2 NULL,  -- Quando foi avaliada
    INDEX idx_user_id (user_id),
    INDEX idx_document_id (document_id),
    INDEX idx_created_at (created_at)
);

-- Tabela de mensagens de conversa
CREATE TABLE conversation_messages (
    message_id NVARCHAR(36) PRIMARY KEY,
    conversation_id NVARCHAR(36) NOT NULL,
    user_id NVARCHAR(255) NOT NULL,
    role NVARCHAR(50) NOT NULL,  -- 'user' ou 'assistant'
    content NVARCHAR(MAX) NOT NULL,  -- Conteúdo da mensagem
    tokens_used INT,  -- Tokens gastos (se disponível)
    model NVARCHAR(100),  -- Modelo LLM usado (e.g., 'gpt-4', 'gpt-3.5-turbo')
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

```