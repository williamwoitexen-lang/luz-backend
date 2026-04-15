-- ============================================================================
-- MIGRATION: Adicionar coluna de comentário de avaliação
-- ============================================================================
-- Permite que usuários deixem feedback quando dão nota baixa

USE ca_peoplechatbot_db;

-- ============================================================================
-- 1. Adicionar coluna de comentário na tabela conversations
-- ============================================================================

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'conversations' AND COLUMN_NAME = 'rating_comment'
)
BEGIN
    ALTER TABLE conversations
    ADD rating_comment NVARCHAR(MAX) NULL;  -- Comentário/feedback da avaliação
    
    PRINT 'OK: Coluna rating_comment adicionada';
END
ELSE
BEGIN
    PRINT 'INFO: Coluna rating_comment já existe';
END;

-- ============================================================================
-- 2. Criar índice para buscas de comentários
-- ============================================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IX_conversations_rating_comment'
)
BEGIN
    CREATE INDEX IX_conversations_rating_comment 
    ON conversations(rating, is_active)
    WHERE rating IS NOT NULL AND rating_comment IS NOT NULL;
    
    PRINT 'OK: Índice criado para buscas de avaliações com comentário';
END;

-- ============================================================================
-- 3. Verificação final
-- ============================================================================

PRINT '';
PRINT '✅ Migration concluída!';
PRINT '';
PRINT 'Nova coluna:';
PRINT '  • rating_comment (NVARCHAR(MAX)) - Comentário/feedback obrigatório quando rating=1.0';
