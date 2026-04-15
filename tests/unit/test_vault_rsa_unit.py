"""
Teste unitário do RSA encryption/decryption sem precisar do servidor
Valida que as chaves RSA podem ser buscadas e funcionam corretamente
"""

import sys
import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64

# Importar config para buscar chaves do Key Vault (ou env vars em dev)
from app.core.config import get_config


def encrypt_message(text: str, public_key_pem: str) -> str:
    """Encriptar mensagem com chave pública RSA"""
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode(),
        backend=default_backend()
    )
    
    ciphertext = public_key.encrypt(
        text.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return base64.b64encode(ciphertext).decode()


def decrypt_message(ciphertext_b64: str, private_key_pem: str) -> str:
    """Decriptar mensagem com chave privada RSA"""
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
        backend=default_backend()
    )
    
    ciphertext = base64.b64decode(ciphertext_b64.encode())
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return plaintext.decode()


def main():
    print("\n" + "="*70)
    print("TESTE UNITÁRIO: RSA ENCRYPTION/DECRYPTION")
    print("="*70)
    
    # Buscar chaves do Key Vault (ou env vars em dev)
    try:
        config = get_config()
        private_key_pem = config.get_rsa_private_key()
        public_key_pem = config.get_rsa_public_key()
        
        print("\n✓ Chaves RSA obtidas com sucesso do Key Vault")
        print(f"  - Public Key: {len(public_key_pem)} caracteres")
        print(f"  - Private Key: {len(private_key_pem)} caracteres")
    except ValueError as e:
        print(f"\n❌ ERRO ao buscar chaves do Key Vault: {e}")
        print("   Configure BD-PRIVATE-KEY e BD-PUBLIC-KEY no Azure Key Vault")
        print("   OU configure variáveis de ambiente: BD_PRIVATE_KEY e BD_PUBLIC_KEY")
        return 1
    
    # Segredos para testar
    TEST_SECRETS = {
        "AZURE-STORAGE-CONNECTION-STRING": "DefaultEndpointProtocol=https;AccountName=test;AccountKey=testkey123==;EndpointSuffix=core.windows.net",
        "CLIENT-SECRET": "super-secret-client-password-12345",
        "LANGCHAIN-BASE-URL": "https://langchain.example.com/api"
    }
    
    print("\n📝 Testando 3 segredos:")
    
    success_count = 0
    total = len(TEST_SECRETS)
    
    for key_name, secret_value in TEST_SECRETS.items():
        print(f"\n  🔐 {key_name}")
        
        try:
            # 1. Encriptar com chave pública
            encrypted = encrypt_message(secret_value, public_key_pem)
            print(f"     ✓ Encriptado (tamanho: {len(encrypted)} chars)")
            
            # 2. Decriptar com chave privada
            decrypted = decrypt_message(encrypted, private_key_pem)
            print(f"     ✓ Decriptado")
            
            # 3. Validar que é igual ao original
            if decrypted == secret_value:
                print(f"     ✅ VERIFICADO: Encriptação/Decriptação funcionou!")
                success_count += 1
            else:
                print(f"     ❌ ERRO: Decriptado não corresponde ao original")
                print(f"        Original: {secret_value[:50]}...")
                print(f"        Decriptado: {decrypted[:50]}...")
                
        except Exception as e:
            print(f"     ❌ ERRO: {str(e)}")
    
    # Resultado final
    print("\n" + "="*70)
    print(f"RESULTADO: {success_count}/{total} segredos encriptados/decriptados com sucesso")
    print("="*70)
    
    if success_count == total:
        print("\n🎉 SUCESSO! Encriptação RSA funcionando perfeitamente!")
        print("   O endpoint /vault/secrets pode usar estas chaves.")
        print("\n✅ Pronto para integração com LLM service!")
        return 0
    else:
        print(f"\n⚠️  FALHA! {total - success_count} segredo(s) falharam.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
