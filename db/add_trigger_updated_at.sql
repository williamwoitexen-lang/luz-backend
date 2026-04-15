-- Trigger para atualizar automaticamente updated_at da tabela documents
-- Executa sempre que um UPDATE é feito na tabela documents (exceto se apenas updated_at mudar)

-- Remover trigger anterior se existir
IF OBJECT_ID('tr_documents_updated_at', 'TR') IS NOT NULL
    DROP TRIGGER tr_documents_updated_at;
GO

CREATE TRIGGER tr_documents_updated_at
ON documents
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @RowUpdate INT;
    SET @RowUpdate = @@ROWCOUNT;
    
    IF @RowUpdate = 0
        RETURN;
    
    -- Se houver UPDATE em qualquer coluna exceto updated_at, atualizar updated_at
    IF UPDATE(document_id) OR UPDATE(title) OR UPDATE(user_id) OR UPDATE(category_id) 
       OR UPDATE(min_role_level) OR UPDATE(allowed_roles) OR UPDATE(allowed_countries) 
       OR UPDATE(allowed_cities) OR UPDATE(location_ids) OR UPDATE(collar) OR UPDATE(plant_code)
       OR UPDATE(is_active) OR UPDATE(summary)
    BEGIN
        UPDATE documents
        SET updated_at = GETUTCDATE()
        WHERE document_id IN (SELECT document_id FROM inserted);
    END
END;
GO



