"""
Testes unitários para cleanup_temp_uploads
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestCleanupTempUploads:
    """Testes para cleanup_temp_uploads"""
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_temp_uploads_with_records(self):
        """Testa limpeza quando há registros expirados"""
        from app.tasks import cleanup_temp_uploads as module
        
        with patch.object(asyncio, 'sleep', new_callable=AsyncMock) as mock_sleep:
            with patch.object(module, 'delete_expired_temp_uploads', return_value=5) as mock_delete:
                with patch.object(module, 'get_storage_provider') as mock_storage:
                    # Configurar sleep para parar após primeira iteração
                    mock_sleep.side_effect = [None, asyncio.CancelledError()]
                    
                    try:
                        await module.cleanup_expired_temp_uploads()
                    except asyncio.CancelledError:
                        pass
                    
                    # Verificar que delete foi chamado
                    mock_delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_temp_uploads_no_records(self):
        """Testa limpeza quando não há registros expirados"""
        from app.tasks import cleanup_temp_uploads as module
        
        with patch.object(asyncio, 'sleep', new_callable=AsyncMock) as mock_sleep:
            with patch.object(module, 'delete_expired_temp_uploads', return_value=0):
                with patch.object(module, 'get_storage_provider'):
                    # Configurar sleep para parar após primeira iteração
                    mock_sleep.side_effect = [None, asyncio.CancelledError()]
                    
                    try:
                        await module.cleanup_expired_temp_uploads()
                    except asyncio.CancelledError:
                        pass
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_temp_uploads_handles_error(self):
        """Testa que erros são tratados sem parar task"""
        from app.tasks import cleanup_temp_uploads as module
        
        with patch.object(asyncio, 'sleep', new_callable=AsyncMock) as mock_sleep:
            with patch.object(module, 'delete_expired_temp_uploads', side_effect=Exception("DB error")):
                # Configurar sleep para parar após primeira iteração
                mock_sleep.side_effect = [None, asyncio.CancelledError()]
                
                try:
                    await module.cleanup_expired_temp_uploads()
                except asyncio.CancelledError:
                    pass
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_temp_uploads_storage_error(self):
        """Testa tratamento de erro de storage"""
        from app.tasks import cleanup_temp_uploads as module
        
        with patch.object(asyncio, 'sleep', new_callable=AsyncMock) as mock_sleep:
            with patch.object(module, 'delete_expired_temp_uploads', return_value=3):
                with patch.object(module, 'get_storage_provider', side_effect=Exception("Storage error")):
                    # Configurar sleep para parar após primeira iteração
                    mock_sleep.side_effect = [None, asyncio.CancelledError()]
                    
                    try:
                        await module.cleanup_expired_temp_uploads()
                    except asyncio.CancelledError:
                        pass
    
    @pytest.mark.asyncio
    async def test_start_cleanup_task(self):
        """Testa que start_cleanup_task inicia a cleanup"""
        from app.tasks import cleanup_temp_uploads as module
        
        with patch.object(module, 'cleanup_expired_temp_uploads', new_callable=AsyncMock) as mock_cleanup:
            mock_cleanup.return_value = None
            
            await module.start_cleanup_task()
            
            mock_cleanup.assert_called_once()
