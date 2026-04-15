-- Criar tabela de auditoria para rastrear todas as alterações de admins
-- Cada alteração gera um novo registro (nunca sobrescreve)

-- Primeiro, remover as colunas created_by e updated_by se existirem (opcional, pois usaremos o audit log)
-- IF EXISTS (
--     SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
--     WHERE TABLE_NAME = 'admins' AND COLUMN_NAME = 'created_by'
-- )
-- BEGIN
--     ALTER TABLE admins DROP COLUMN created_by;
-- END

-- IF EXISTS (
--     SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
--     WHERE TABLE_NAME = 'admins' AND COLUMN_NAME = 'updated_by'
-- )
-- BEGIN
--     ALTER TABLE admins DROP COLUMN updated_by;
-- END

-- Criar tabela de auditoria se não existir
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'admin_audit_log')
BEGIN
    CREATE TABLE admin_audit_log (
        log_id BIGINT PRIMARY KEY IDENTITY(1,1),
        admin_id NVARCHAR(36) NOT NULL,
        action NVARCHAR(50) NOT NULL,  -- CREATE, UPDATE, DELETE
        changed_fields NVARCHAR(MAX) NULL,  -- JSON array dos campos alterados
        old_values NVARCHAR(MAX) NULL,  -- JSON com valores antigos
        new_values NVARCHAR(MAX) NOT NULL,  -- JSON com valores novos
        changed_by NVARCHAR(255) NOT NULL,  -- Nome do usuário que fez a alteração
        changed_at DATETIME2 DEFAULT GETUTCDATE(),
        ip_address NVARCHAR(45) NULL,  -- IP do cliente (opcional)
        details NVARCHAR(MAX) NULL,  -- Descrição adicional
        INDEX idx_admin_id (admin_id),
        INDEX idx_changed_at (changed_at),
        INDEX idx_action (action),
        FOREIGN KEY (admin_id) REFERENCES admins(admin_id)
    );
    PRINT 'Tabela admin_audit_log criada com sucesso';
END
ELSE
BEGIN
    PRINT 'Tabela admin_audit_log já existe';
END

-- Criar índice composto para consultas comuns
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_admin_audit_log_composite')
BEGIN
    CREATE INDEX idx_admin_audit_log_composite ON admin_audit_log(admin_id, changed_at DESC);
    PRINT 'Índice idx_admin_audit_log_composite criado com sucesso';
END

