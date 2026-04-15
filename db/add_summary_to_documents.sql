-- Adicionar coluna summary à tabela documents
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('documents') AND name = 'summary')
BEGIN
    ALTER TABLE documents
    ADD summary NVARCHAR(MAX);
    
    PRINT 'Coluna summary adicionada com sucesso à tabela documents';
END
ELSE
BEGIN
    PRINT 'Coluna summary já existe na tabela documents';
END
GO
