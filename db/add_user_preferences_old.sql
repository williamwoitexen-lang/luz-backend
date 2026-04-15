-- Criar tabela de preferências do usuário com suporte a memória de longo prazo
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_preferences')
BEGIN
    CREATE TABLE user_preferences (
        user_id VARCHAR(255) PRIMARY KEY,
        preferred_language VARCHAR(10) DEFAULT 'pt-BR',
        memory_preferences NVARCHAR(MAX),  -- JSON com configurações de memória
        last_update DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX idx_user_preferences_last_update ON user_preferences(last_update);
END
ELSE
BEGIN
    -- Se a tabela já existe, adicionar coluna memory_preferences se não existir
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'user_preferences' AND COLUMN_NAME = 'memory_preferences'
    )
    BEGIN
        ALTER TABLE user_preferences ADD memory_preferences NVARCHAR(MAX);
    END
END
