"""
Migration script para adicionar tabela temp_uploads ao SQL Server.

Executa a query de criação da tabela temp_uploads se não existir.
"""
import logging
from app.core.sqlserver import get_sqlserver_connection

logger = logging.getLogger(__name__)


def migrate_create_temp_uploads_table():
    """
    Criar tabela temp_uploads se não existir.
    
    Executa:
    - CREATE TABLE temp_uploads com colunas para rastrear uploads temporários
    - Índices para performance em queries de cleanup
    """
    sql = get_sqlserver_connection()
    
    # Check if table exists
    check_table_query = """
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'temp_uploads')
    BEGIN
        SELECT 'Table temp_uploads does not exist'
    END
    ELSE
    BEGIN
        SELECT 'Table temp_uploads already exists'
    END
    """
    
    try:
        result = sql.execute(check_table_query)
        logger.info(f"Table check result: {result}")
        
        if result and 'does not exist' in str(result[0]):
            logger.info("Creating temp_uploads table...")
            
            create_table_query = """
            CREATE TABLE temp_uploads (
                temp_id NVARCHAR(36) PRIMARY KEY,
                user_id NVARCHAR(255) NOT NULL,
                filename NVARCHAR(255) NOT NULL,
                blob_path NVARCHAR(MAX) NOT NULL,
                file_size_bytes INT,
                created_at DATETIME2 DEFAULT GETUTCDATE(),
                expires_at DATETIME2,
                is_confirmed BIT DEFAULT 0,
                INDEX idx_user_id (user_id),
                INDEX idx_expires_at (expires_at),
                INDEX idx_created_at (created_at)
            )
            """
            
            sql.execute(create_table_query)
            logger.info("✅ Table temp_uploads created successfully")
            return True
        else:
            logger.info("✅ Table temp_uploads already exists")
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_create_temp_uploads_table()
