-- ============================================================================
-- MIGRATION: Adicionar document_categories_used em conversation_messages
-- ============================================================================
-- Rastreia quais categorias de documentos foram utilizadas em cada resposta
-- Armazenado como JSON com category_ids e category_names

USE ca_peoplechatbot_db;

-- ============================================================================
-- 1. Adicionar coluna document_categories_used
-- ============================================================================

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'conversation_messages' AND COLUMN_NAME = 'document_categories_used'
)
BEGIN
    ALTER TABLE conversation_messages
    ADD document_categories_used NVARCHAR(MAX) NULL;  -- JSON com {"category_ids": [...], "category_names": [...]}
    
    PRINT 'OK: Coluna document_categories_used adicionada';
END
ELSE
BEGIN
    PRINT 'INFO: Coluna document_categories_used já existe';
END;

-- ============================================================================
-- 2. Criar índice para buscas por categoria
-- ============================================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IX_conversation_messages_categories'
)
BEGIN
    CREATE INDEX IX_conversation_messages_categories 
    ON conversation_messages(role, created_at)
    WHERE role = 'assistant' AND document_categories_used IS NOT NULL;
    
    PRINT 'OK: Índice criado para buscas de mensagens com categorias';
END
ELSE
BEGIN
    PRINT 'INFO: Índice já existe';
END;

-- ============================================================================
-- 3. Verificação final
-- ============================================================================

PRINT '';
PRINT '✅ Migration concluída!';
PRINT '';
PRINT 'Nova coluna:';
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'conversation_messages' AND COLUMN_NAME = 'document_categories_used';
