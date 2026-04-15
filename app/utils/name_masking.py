"""
Utilidades para mascarar/desmascarar nomes de usuários (LGPD compliance).

Mascara nomes no banco de dados para não ficarem legíveis diretamente.
"""

import base64
import os
import logging

logger = logging.getLogger(__name__)

# Salt para mascaramento (derivado do ambiente ou fixo)
MASKING_SALT = os.getenv("MASKING_SALT", "lgpd-compliance-salt-v1").encode()


def mask_user_name(user_name: str) -> str:
    """
    Mascara nome de usuário para armazenamento LGPD-compliant no DB.
    
    Usa base64 encoding com salt. Não é "seguro" em sentido criptográfico,
    mas impede leitura direta no DB e satisfaz requisitos LGPD.
    
    Args:
        user_name: Nome completo do usuário (ex: "Adele Vance")
    
    Returns:
        String mascarada (ex: "bGdwZC1jb21wbGlhbmNlLXNhbHQtdjE6QWRlbGUgVmFuY2U=")
    
    Raises:
        ValueError: Se user_name for vazio
    """
    if not user_name or not isinstance(user_name, str):
        raise ValueError("user_name deve ser uma string não-vazia")
    
    try:
        # Formato: salt:nome_original em base64
        combined = f"{MASKING_SALT.decode()}:{user_name}"
        masked = base64.b64encode(combined.encode()).decode()
        logger.debug(f"[NameMask] Mascarado: {user_name[:10]}... → {masked[:20]}...")
        return masked
    except Exception as e:
        logger.error(f"[NameMask] Erro ao mascarar: {e}")
        raise


def unmask_user_name(masked_name: str) -> str:
    """
    Desmascarar nome de usuário para apresentação ao usuário.
    
    Reverte o mascaramento aplicado por mask_user_name().
    
    Args:
        masked_name: String mascarada (ex: "bGdwZC1jb21wbGlhbmNlLXNhbHQtdjE6QWRlbGUgVmFuY2U=")
    
    Returns:
        Nome original (ex: "Adele Vance")
    
    Raises:
        ValueError: Se masked_name for inválido ou salt não corresponder
    """
    if not masked_name or not isinstance(masked_name, str):
        raise ValueError("masked_name deve ser uma string não-vazia")
    
    try:
        # Decodificar base64
        decoded = base64.b64decode(masked_name.encode()).decode()
        
        # Verificar e remover salt
        salt_str = MASKING_SALT.decode()
        if not decoded.startswith(f"{salt_str}:"):
            logger.warning(f"[NameMask] Salt inválido ao desmascarar")
            raise ValueError("Salt inválido: dado pode estar corrompido")
        
        # Extrair nome original
        original_name = decoded.split(":", 1)[1]
        logger.debug(f"[NameMask] Desmascarado: {masked_name[:20]}... → {original_name[:10]}...")
        return original_name
    
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"[NameMask] Erro ao desmascarar: {e}")
        raise ValueError(f"Erro ao desmascarar: {e}")


def unmask_list(masked_names: list) -> list:
    """
    Desmascarar lista de nomes.
    
    Args:
        masked_names: Lista de strings mascaradas
    
    Returns:
        Lista de nomes originais
    """
    result = []
    for masked in masked_names:
        try:
            result.append(unmask_user_name(masked))
        except Exception as e:
            logger.warning(f"[NameMask] Falha ao desmascarar item: {e}")
            result.append(masked)  # fallback: retornar como está
    return result
