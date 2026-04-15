"""
Migração para criar tabela conversations e conversation_messages em produção
"""

from app.core.sqlserver import get_sqlserver_connection
import logging

logger = logging.getLogger(__name__)

def migrate_create_conversations_table():
    """Criar tabelas conversations e conversation_messages se não existirem"""
    
    sql = get_sqlserver_connection()
    
    # Verificar se tabela já existe
    check_query = """
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME = 'conversations'
    """
    
    try:
        result = sql.execute_single(check_query, [])
        if result:
            logger.info("Tabela 'conversations' já existe. Skip migration.")
            return True
    except Exception as e:
        logger.warning(f"Erro ao verificar tabela: {e}")
    
    # Criar tabela conversations
    conversations_table = """
    CREATE TABLE conversations (
        conversation_id NVARCHAR(36) PRIMARY KEY,
        user_id NVARCHAR(255) NOT NULL,
        document_id NVARCHAR(36),
        title NVARCHAR(MAX),
        created_at DATETIME2 DEFAULT GETUTCDATE(),
        updated_at DATETIME2 DEFAULT GETUTCDATE(),
        is_active BIT DEFAULT 1,
        INDEX idx_user_id (user_id),
        INDEX idx_document_id (document_id),
        INDEX idx_created_at (created_at)
    )
    """
    
    # Criar tabela conversation_messages
    messages_table = """
    CREATE TABLE conversation_messages (
        message_id NVARCHAR(36) PRIMARY KEY,
        conversation_id NVARCHAR(36) NOT NULL,
        user_id NVARCHAR(255) NOT NULL,
        role NVARCHAR(50) NOT NULL,
        content NVARCHAR(MAX) NOT NULL,
        tokens_used INT,
        model NVARCHAR(100),
        created_at DATETIME2 DEFAULT GETUTCDATE(),
        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
        INDEX idx_conversation_id (conversation_id),
        INDEX idx_user_id (user_id),
        INDEX idx_created_at (created_at)
    )
    """
    
    try:
        logger.info("Criando tabela conversations...")
        sql.execute(conversations_table, [])
        logger.info("✓ Tabela conversations criada com sucesso")
        
        logger.info("Criando tabela conversation_messages...")
        sql.execute(messages_table, [])
        logger.info("✓ Tabela conversation_messages criada com sucesso")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        migrate_create_conversations_table()
        print("✓ Migração concluída com sucesso!")
    except Exception as e:
        print(f"✗ Erro na migração: {e}")
