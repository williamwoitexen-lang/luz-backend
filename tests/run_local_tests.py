#!/usr/bin/env python3
"""
Teste Local dos Endpoints GET
Roda a aplicação FastAPI localmente e testa os endpoints.
"""

import asyncio
import subprocess
import time
import httpx
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1/master-data"
APP_PROCESS = None


def start_app():
    """Inicia a aplicação FastAPI."""
    global APP_PROCESS
    print("🚀 Iniciando aplicação FastAPI...")
    
    try:
        APP_PROCESS = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd="/workspaces/Embeddings",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"   PID: {APP_PROCESS.pid}")
        
        # Aguardar inicialização
        print("⏳ Aguardando inicialização (10 segundos)...")
        time.sleep(10)
        
        print("✅ Aplicação iniciada")
        return True
    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
        return False


def stop_app():
    """Para a aplicação."""
    global APP_PROCESS
    if APP_PROCESS:
        print("\n🛑 Parando aplicação...")
        APP_PROCESS.terminate()
        try:
            APP_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            APP_PROCESS.kill()
        print("✅ Aplicação parada")


async def test_endpoint(endpoint: str, description: str, client: httpx.AsyncClient) -> bool:
    """Testa um endpoint e retorna sucesso/falha."""
    try:
        response = await client.get(f"{BASE_URL}{endpoint}", timeout=10)
        
        status_ok = response.status_code == 200
        status_symbol = "✅" if status_ok else "❌"
        
        print(f"{status_symbol} {description:<50} [{response.status_code}]", end="")
        
        if status_ok:
            data = response.json()
            if isinstance(data, list):
                print(f" {len(data):>3} registros")
            else:
                print()
        else:
            error = response.json().get("detail", "Erro desconhecido")
            print(f"\n   └─ Erro: {str(error)[:80]}")
        
        return status_ok
    except Exception as e:
        print(f"❌ {description:<50} [ERRO]")
        print(f"   └─ {str(e)[:80]}")
        return False


async def run_tests():
    """Executa todos os testes."""
    print("\n" + "="*75)
    print("🔵 TESTANDO ENDPOINTS GET")
    print("="*75 + "\n")
    
    async with httpx.AsyncClient() as client:
        results = []
        
        # Locations
        results.append(await test_endpoint(
            "/locations",
            "GET /locations",
            client
        ))
        
        # Countries
        results.append(await test_endpoint(
            "/countries",
            "GET /countries",
            client
        ))
        
        results.append(await test_endpoint(
            "/countries?active_only=true",
            "GET /countries (active_only)",
            client
        ))
        
        # Regions
        results.append(await test_endpoint(
            "/regions",
            "GET /regions",
            client
        ))
        
        results.append(await test_endpoint(
            "/regions?active_only=true",
            "GET /regions (active_only)",
            client
        ))
        
        # Roles
        results.append(await test_endpoint(
            "/roles",
            "GET /roles",
            client
        ))
        
        results.append(await test_endpoint(
            "/roles?active_only=true",
            "GET /roles (active_only)",
            client
        ))
        
        # Categories
        results.append(await test_endpoint(
            "/categories",
            "GET /categories",
            client
        ))
        
        results.append(await test_endpoint(
            "/categories?active_only=true",
            "GET /categories (active_only)",
            client
        ))
        
        # Hierarchy
        results.append(await test_endpoint(
            "/hierarchy",
            "GET /hierarchy",
            client
        ))
        
        results.append(await test_endpoint(
            "/hierarchy?active_only=true",
            "GET /hierarchy (active_only)",
            client
        ))
        
        # States by country
        results.append(await test_endpoint(
            "/states-by-country/Brazil",
            "GET /states-by-country/Brazil",
            client
        ))
        
        # Cities by country
        results.append(await test_endpoint(
            "/cities-by-country/Brazil",
            "GET /cities-by-country/Brazil",
            client
        ))
        
        # Cities by region
        results.append(await test_endpoint(
            "/cities-by-region/LATAM",
            "GET /cities-by-region/LATAM",
            client
        ))
        
        # Summary
        print("\n" + "="*75)
        passed = sum(results)
        total = len(results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"📊 RESULTADO: {passed}/{total} endpoints funcionando ({percentage:.0f}%)")
        print("="*75 + "\n")
        
        return all(results)


def main():
    """Main entry point."""
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║     🧪 TESTE LOCAL DOS ENDPOINTS GET - MASTER DATA            ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    # Iniciar app
    if not start_app():
        print("❌ Não foi possível iniciar a aplicação")
        return 1
    
    try:
        # Rodar testes
        success = asyncio.run(run_tests())
        
        if success:
            print("✨ Todos os testes passaram!")
            print("\n📖 Documentação Swagger: http://localhost:8000/docs")
            print("📖 ReDoc: http://localhost:8000/redoc")
            return 0
        else:
            print("⚠️  Alguns testes falharam")
            print("\nDicas:")
            print("  1. Verificar se .env tem SQLSERVER_CONNECTION_STRING correto")
            print("  2. Verificar se Azure SQL Server está acessível")
            print("  3. Verificar se schema_seed.sql foi carregado")
            return 1
    
    finally:
        stop_app()


if __name__ == "__main__":
    sys.exit(main())
