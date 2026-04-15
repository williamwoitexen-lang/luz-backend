#!/usr/bin/env python3
"""
Script para testar o endpoint de DELETE de admin.

Uso:
    python test_delete_admin.py <admin_id> <auth_token>

Ou se preferir interativo:
    python test_delete_admin.py  # vai pedir os valores
"""

import requests
import json
import sys
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/v1/admins"

def test_delete_admin(admin_id: str, auth_token: str) -> dict:
    """Test DELETE endpoint for admin"""
    
    url = f"{ENDPOINT}/{admin_id}"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print("🧪 TESTANDO DELETE ADMIN")
    print(f"{'='*60}")
    print(f"URL: DELETE {url}")
    print(f"Admin ID: {admin_id}")
    print(f"Headers: {json.dumps({k: v[:20] + '...' if len(v) > 20 else v for k,v in headers.items()}, indent=2)}")
    
    try:
        print(f"\n📤 Enviando request...")
        response = requests.delete(url, headers=headers)
        
        print(f"📥 Response recebido:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Body: {response.text}")
        
        return {
            "status_code": response.status_code,
            "body": response.json() if response.text else {},
            "success": 200 <= response.status_code < 300
        }
        
    except Exception as e:
        print(f"❌ Erro ao fazer request: {e}")
        return {
            "status_code": None,
            "body": str(e),
            "success": False
        }

def test_get_admin(admin_id: str, auth_token: str) -> dict:
    """Test GET endpoint to fetch admin info"""
    
    url = f"{ENDPOINT}/{admin_id}"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print("🔍 BUSCANDO INFO DO ADMIN ANTES DO DELETE")
    print(f"{'='*60}")
    print(f"URL: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin encontrado:")
            print(f"   Email: {data.get('email')}")
            print(f"   Name: {data.get('name')}")
            print(f"   Is Active: {data.get('is_active')}")
            return data
        else:
            print(f"❌ Admin não encontrado: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def test_list_admins(auth_token: str) -> list:
    """List all admins"""
    
    url = ENDPOINT
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print("📋 LISTANDO TODOS OS ADMINS")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            admins = data.get('admins', [])
            print(f"✅ Total de admins: {len(admins)}")
            for admin in admins:
                print(f"   - {admin.get('admin_id')}: {admin.get('email')} (Active: {admin.get('is_active')})")
            return admins
        else:
            print(f"❌ Erro: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def main():
    """Main test function"""
    
    print("\n🚀 TESTE DE DELETE ADMIN")
    print("="*60)
    
    # Get inputs
    if len(sys.argv) > 2:
        admin_id = sys.argv[1]
        auth_token = sys.argv[2]
    elif len(sys.argv) > 1:
        admin_id = sys.argv[1]
        auth_token = input("Enter your auth token: ")
    else:
        # Interactive mode
        print("\nOpciones:")
        print("1. Testar DELETE de um admin específico")
        print("2. Listar todos os admins")
        
        choice = input("\nEscolha: ")
        
        if choice == "1":
            admin_id = input("Admin ID: ")
            auth_token = input("Auth token: ")
        else:
            auth_token = input("Auth token: ")
            # List admins first
            admins = test_list_admins(auth_token)
            if not admins:
                print("\n❌ Nenhum admin encontrado ou erro ao listar")
                return
            
            print("\nEscolha um admin para deletar:")
            for i, admin in enumerate(admins):
                print(f"{i}: {admin.get('admin_id')} - {admin.get('email')}")
            
            idx = int(input("Index: "))
            admin_id = admins[idx]['admin_id']
    
    # Test sequence
    print(f"\nAdmin ID selecionado: {admin_id}")
    
    # 1. Get admin info before delete
    before = test_get_admin(admin_id, auth_token)
    
    # 2. Delete admin
    result = test_delete_admin(admin_id, auth_token)
    
    # 3. Get admin info after delete (should be inactive)
    if result['success']:
        after = test_get_admin(admin_id, auth_token)
        if after:
            print(f"\n{'='*60}")
            print("📊 COMPARAÇÃO ANTES/DEPOIS")
            print(f"{'='*60}")
            print(f"Antes:  is_active = {before.get('is_active')}")
            print(f"Depois: is_active = {after.get('is_active')}")
            if before.get('is_active') and not after.get('is_active'):
                print("✅ DELETE FOI BEM-SUCEDIDO!")
            else:
                print("❌ DELETE NÃO FOI BEM-SUCEDIDO (admin ainda ativo)")

if __name__ == "__main__":
    main()
