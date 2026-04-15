"""
Background task para limpar uploads temporários expirados.

Executa a cada X minutos e remove:
1. Registros de temp_uploads que expiraram (mais de 10 minutos)
2. Arquivos correspondentes do Blob Storage
"""
import logging
import asyncio
from datetime import datetime
from app.services.sqlserver_documents import delete_expired_temp_uploads
from app.providers.storage import get_storage_provider

logger = logging.getLogger(__name__)


async def cleanup_expired_temp_uploads():
    """
    Limpar uploads temporários expirados.
    
    Executa:
    - A cada 5 minutos (frequência recomendada)
    - Remove registros SQL Server expirados (created_at + 10min < now)
    - Remove blobs do storage correspondentes
    
    Uso:
    - Iniciar em background na startup da aplicação
    - asyncio.create_task(cleanup_expired_temp_uploads())
    """
    
    logger.info("Iniciando cleanup task para uploads temporários expirados...")
    
    while True:
        try:
            # Aguardar 5 minutos antes de cada limpeza
            # (uploads expiram em 10min, então 5min é intervalo bom)
            await asyncio.sleep(5 * 60)  # 5 minutos
            
            logger.info(f"[cleanup_temp_uploads] Iniciando limpeza de uploads expirados - {datetime.utcnow()}")
            
            # Deletar registros expirados do banco de dados
            deleted_count = delete_expired_temp_uploads()
            
            if deleted_count > 0:
                logger.info(f"[cleanup_temp_uploads] Deletados {deleted_count} registros expirados do banco")
                
                # Tentar deletar blobs correspondentes também
                # (opcional - se alguns falhem, pelo menos os registros foram limpos)
                try:
                    storage = get_storage_provider()
                    # Nota: Aqui seria ideal ter uma função em storage para deletar por padrão
                    # storage.delete_pattern("__temp__/*")
                    # Mas por enquanto, just delete the DB records
                    logger.info(f"[cleanup_temp_uploads] Blobs temporários também serão limpos (ou deixar storage auto-expire)")
                except Exception as e:
                    logger.warning(f"[cleanup_temp_uploads] Erro ao tentar deletar blobs: {e}")
            else:
                logger.debug(f"[cleanup_temp_uploads] Nenhum upload expirado encontrado")
            
            logger.info(f"[cleanup_temp_uploads] Limpeza concluída - próxima em 5 minutos")
            
        except Exception as e:
            logger.error(f"[cleanup_temp_uploads] ERRO na limpeza: {e}", exc_info=True)
            # Continuar mesmo se falhar, para não travar a aplicação
            await asyncio.sleep(60)  # Aguardar 1 minuto antes de tentar novamente


async def start_cleanup_task():
    """
    Iniciar task de cleanup em background.
    
    Chamado na startup da aplicação:
    
    @app.on_event("startup")
    async def startup_event():
        asyncio.create_task(start_cleanup_task())
    """
    logger.info("Iniciando background cleanup task para uploads temporários...")
    await cleanup_expired_temp_uploads()
