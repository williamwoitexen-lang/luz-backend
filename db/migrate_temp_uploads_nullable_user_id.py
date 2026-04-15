"""
Migração para tornar user_id nullable em temp_uploads
(user_id é preenchido apenas no ingest_confirm)
"""

from app.core.sqlserver import get_sqlserver_connection
import logging

logger = logging.getLogger(__name__)

def migrate_make_user_id_nullable():
    """Fazer user_id nullable em temp_uploads"""
    
    sql = get_sqlserver_connection()
    
    # Remover constraint NOT NULL de user_id (SQL Server não permite DROP CONSTRAINT direto)
    # Precisamos:
    # 1. Criar coluna temporária
    # 2. Copiar dados
    # 3. Deletar coluna antiga
    # 4. Renomear coluna nova
    
    queries = [
        # Adicionar coluna temporária nullable
        """
        ALTER TABLE temp_uploads
        ADD user_id_nullable NVARCHAR(255) NULL
        """,
        
        # Copiar dados
        """
        UPDATE temp_uploads
        SET user_id_nullable = user_id
        """,
        
        # Remover coluna antiga
        """
        ALTER TABLE temp_uploads
        DROP COLUMN user_id
        """,
        
        # Renomear coluna nova
        """
        EXEC sp_rename 'temp_uploads.user_id_nullable', 'user_id'
        """,
    ]
    
    try:
        for i, query in enumerate(queries, 1):
            logger.info(f"Executando migração - passo {i}/{len(queries)}")
            sql.execute(query, [])
            logger.info(f"✓ Passo {i} concluído")
        
        logger.info("✓ Migração concluída com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro na migração: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        migrate_make_user_id_nullable()
        print("✓ user_id is now nullable in temp_uploads!")
    except Exception as e:
        print(f"✗ Erro: {e}")
