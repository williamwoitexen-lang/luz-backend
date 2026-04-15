-- SQL para adicionar coluna category_id na tabela documents
-- (Se nao existir) e adicionar Foreign Key para dim_categories

USE data;
GO

-- 1. Verificar se dim_categories existe
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'dim_categories')
BEGIN
    RAISERROR('Tabela dim_categories nao existe! Execute schema_dimensions.sql primeiro.', 16, 1);
END
GO

-- 2. Adicionar coluna category_id em documents (se nao existir)
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'documents' 
    AND COLUMN_NAME = 'category_id'
)
BEGIN
    ALTER TABLE documents
    ADD category_id INT NULL;
    PRINT 'Coluna category_id adicionada em documents.';
END
ELSE
BEGIN
    PRINT 'Coluna category_id ja existe em documents.';
END
GO

-- 3. Adicionar Foreign Key em documents (se nao existir)
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS 
    WHERE CONSTRAINT_NAME = 'FK_documents_category'
)
BEGIN
    ALTER TABLE documents
    ADD CONSTRAINT FK_documents_category
    FOREIGN KEY (category_id) REFERENCES dim_categories(category_id);
    PRINT 'Foreign Key FK_documents_category adicionada.';
END
ELSE
BEGIN
    PRINT 'Foreign Key FK_documents_category ja existe.';
END
GO

-- 4. Adicionar indice para performance
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'idx_documents_category' 
    AND object_id = OBJECT_ID('documents')
)
BEGIN
    CREATE INDEX idx_documents_category ON documents(category_id);
    PRINT 'Indice idx_documents_category criado.';
END
ELSE
BEGIN
    PRINT 'Indice idx_documents_category ja existe.';
END
GO

-- 5. Verificacao final
PRINT '';
PRINT '========== VERIFICACAO ==========';

-- Mostrar coluna
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'documents' 
AND COLUMN_NAME = 'category_id';

-- Mostrar Foreign Key
SELECT 
    OBJECT_NAME(fk.parent_object_id) AS [TABLE_NAME],
    fk.name AS [CONSTRAINT_NAME],
    OBJECT_NAME(referenced_object_id) AS [REFERENCED_TABLE]
FROM sys.foreign_keys fk
WHERE OBJECT_NAME(fk.parent_object_id) = 'documents'
AND fk.name = 'FK_documents_category';

-- Mostrar categorias disponiveis
PRINT '';
PRINT '=== Categorias Disponiveis ===';
SELECT 
    category_id, 
    category_name
FROM dim_categories 
WHERE is_active = 1
ORDER BY category_id;

PRINT '';
PRINT 'Setup categoria concluido!';
GO


