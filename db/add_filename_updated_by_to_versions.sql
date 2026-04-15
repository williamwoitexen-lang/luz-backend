-- Migration: Add filename and updated_by columns to versions table

-- Adicionar coluna filename (nome do arquivo enviado nesta versão)
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'versions' AND COLUMN_NAME = 'filename')
BEGIN
    ALTER TABLE versions ADD filename NVARCHAR(255) NULL;
    PRINT 'Column filename added to versions table';
END
ELSE
BEGIN
    PRINT 'Column filename already exists in versions table';
END

-- Adicionar coluna updated_by (usuário que atualizou esta versão)
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'versions' AND COLUMN_NAME = 'updated_by')
BEGIN
    ALTER TABLE versions ADD updated_by NVARCHAR(255) NULL;
    PRINT 'Column updated_by added to versions table';
END
ELSE
BEGIN
    PRINT 'Column updated_by already exists in versions table';
END
