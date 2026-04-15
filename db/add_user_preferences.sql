-- Criar tabela de preferências do usuário com suporte a memória de longo prazo
-- Migration corrigida para usar updated_at e created_at
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_preferences')
BEGIN
    CREATE TABLE user_preferences (
        user_id VARCHAR(255) PRIMARY KEY,
        preferred_language VARCHAR(10) DEFAULT 'pt-BR',
        memory_preferences NVARCHAR(MAX),  -- JSON com configurações de memória
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX idx_user_preferences_updated_at ON user_preferences(updated_at);
END
ELSE
BEGIN
    -- Se a tabela já existe, adicionar colunas que faltam
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'user_preferences' AND COLUMN_NAME = 'memory_preferences'
    )
    BEGIN
        ALTER TABLE user_preferences ADD memory_preferences NVARCHAR(MAX);
    END
    
    -- Adicionar coluna updated_at se não existir
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'user_preferences' AND COLUMN_NAME = 'updated_at'
    )
    BEGIN
        ALTER TABLE user_preferences ADD updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;
        CREATE INDEX idx_user_preferences_updated_at ON user_preferences(updated_at);
    END
    
    -- Adicionar coluna created_at se não existir
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'user_preferences' AND COLUMN_NAME = 'created_at'
    )
    BEGIN
        ALTER TABLE user_preferences ADD created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
    END
    
    -- Remover coluna last_update se existir (migração de schema)
    IF EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'user_preferences' AND COLUMN_NAME = 'last_update'
    )
    BEGIN
        -- Copiar dados para updated_at se não tiver valores
        UPDATE user_preferences 
        SET updated_at = last_update 
        WHERE updated_at IS NULL OR updated_at = CURRENT_TIMESTAMP;
        
        -- Remover índice antigo se existir
        IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_user_preferences_last_update')
            DROP INDEX idx_user_preferences_last_update ON user_preferences;
        
        ALTER TABLE user_preferences DROP COLUMN last_update;
    END
END
