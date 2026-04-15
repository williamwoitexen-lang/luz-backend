-- ============================================================================
-- DASHBOARD MIGRATION - Adicionar colunas de tempo de resposta
-- ============================================================================
-- Execute este script no SQL Server Management Studio ou via sqlcmd
-- ============================================================================

USE ca_peoplechatbot_db;

-- ============================================================================
-- 1. Adicionar colunas de tempo de resposta na tabela conversation_messages
-- ============================================================================

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'conversation_messages' AND COLUMN_NAME = 'retrieval_time'
)
BEGIN
    ALTER TABLE conversation_messages
    ADD retrieval_time FLOAT NULL,  -- Tempo para recuperar documentos (milissegundos)
        llm_time FLOAT NULL,        -- Tempo que o LLM levou (milissegundos)
        total_time FLOAT NULL;      -- Tempo total da resposta (milissegundos)
    
    PRINT 'OK: Colunas de tempo adicionadas com sucesso';
END
ELSE
BEGIN
    PRINT 'INFO: Colunas de tempo já existem';
END;

-- ============================================================================
-- 2. Adicionar coluna para rastreamento de categorias
-- ============================================================================

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'conversation_messages' AND COLUMN_NAME = 'document_categories_used'
)
BEGIN
    ALTER TABLE conversation_messages
    ADD document_categories_used NVARCHAR(MAX) NULL;  -- JSON com {"category_ids": [...], "category_names": [...]}
    
    PRINT 'OK: Coluna document_categories_used adicionada com sucesso';
END
ELSE
BEGIN
    PRINT 'INFO: Coluna document_categories_used já existe';
END;

-- ============================================================================
-- 3. Criar índice para queries de categorias
-- ============================================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE object_id = OBJECT_ID('conversation_messages') 
    AND name = 'idx_assistant_messages_categories'
)
BEGIN
    CREATE NONCLUSTERED INDEX idx_assistant_messages_categories
    ON conversation_messages(role, created_at)
    WHERE role = 'assistant' AND document_categories_used IS NOT NULL;
    
    PRINT 'OK: Índice idx_assistant_messages_categories criado com sucesso';
END
ELSE
BEGIN
    PRINT 'INFO: Índice idx_assistant_messages_categories já existe';
END;

-- ============================================================================
-- 4. Verificar que as colunas foram criadas
-- ============================================================================

PRINT '';
PRINT 'Verificando colunas em conversation_messages:';
PRINT '---------------------------------------------';

SELECT 
    COLUMN_NAME AS 'Coluna',
    DATA_TYPE AS 'Tipo',
    IS_NULLABLE AS 'Nullable',
    ORDINAL_POSITION AS 'Posição'
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'conversation_messages' 
AND COLUMN_NAME IN ('retrieval_time', 'llm_time', 'total_time', 'document_categories_used')
ORDER BY ORDINAL_POSITION;

-- ============================================================================
-- 5. Popular dados históricos com categoria padrão
-- ============================================================================

PRINT '';
PRINT 'Populando dados históricos com categoria padrão...';

UPDATE conversation_messages
SET document_categories_used = N'{"category_ids": [14], "category_names": ["RH Geral"]}'
WHERE role = 'assistant' 
AND document_categories_used IS NULL;

DECLARE @updated INT = @@ROWCOUNT;
PRINT 'OK: ' + CAST(@updated AS VARCHAR(10)) + ' mensagens atualizadas com categoria padrão';

-- ============================================================================
-- 6. Resultado
-- ============================================================================

PRINT '';
PRINT '✅ Migration concluída com sucesso!';
PRINT '';
PRINT 'Colunas criadas:';
PRINT '  - retrieval_time (FLOAT): Tempo de recuperação de documentos';
PRINT '  - llm_time (FLOAT): Tempo de resposta do LLM';
PRINT '  - total_time (FLOAT): Tempo total de processamento';
PRINT '  - document_categories_used (NVARCHAR(MAX)): JSON com categorias usadas';
PRINT '';
PRINT 'Índice criado:';
PRINT '  - idx_assistant_messages_categories: Para queries de categorias otimizadas';
PRINT '';
PRINT 'Próximos passos:';
PRINT '  1. Novas mensagens salvas terão os tempos de resposta e categorias rastreados';
PRINT '  2. Endpoint /api/v1/chat/dashboard/summary retornará:';
PRINT '     - metrics.avg_response_time_seconds (em segundos)';
PRINT '     - metrics.total_user_messages (total de perguntas)';
PRINT '     - response_times_ms (detalhes em milissegundos)';
PRINT '     - category_metrics (uso de categorias com ratings agregados)';
PRINT '     - ratings (distribuição de avaliações com percentuais)';
