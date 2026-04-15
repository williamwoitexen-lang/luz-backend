#!/usr/bin/env python3
"""
Script para buscar dados reais do Azure SQL Server usando Azure CLI credentials
"""
import pytest
pyodbc = pytest.importorskip("pyodbc", reason="pyodbc/ODBC driver not available in CI environment")
import subprocess
import json
import os

def get_sql_server_token():
    """Obter token para SQL Server do Azure CLI"""
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource", "https://database.windows.net"],
            capture_output=True,
            text=True,
            check=True
        )
        token_response = json.loads(result.stdout)
        return token_response["accessToken"]
    except Exception as e:
        print(f"❌ Erro ao obter token: {e}")
        return None

def main():
    print("✅ pyodbc importado com sucesso\n")
    
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║    🔍 BUSCANDO DADOS REAIS DO AZURE SQL SERVER (Azure CLI)   ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    server = "elxa3sql-peoplechatbot-dev-001.database.windows.net"
    database = "data"
    
    print("🔗 Obtendo token do Azure CLI...")
    access_token = get_sql_server_token()
    
    if not access_token:
        print("❌ Não foi possível obter o token. Verifique se você fez 'az login'")
        return 1
    
    print("✅ Token obtido com sucesso\n")
    
    try:
        print("🔗 Conectando ao Azure SQL Server...")
        
        # Preparar o token para pyodbc (precisa estar em UTF-16-LE)
        token_bytes = access_token.encode("utf-16-le")
        
        # Criar conexão
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server={server};"
            f"Database={database};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        conn = pyodbc.connect(connection_string, attrs_before={1256: token_bytes})
        cursor = conn.cursor()
        print("✅ Conectado ao Azure SQL Server!\n")
        
        # Buscar locations
        print("📍 Buscando Locations...")
        cursor.execute("""
            SELECT location_id, country_name, state_name, city_name, region, continent, operation_type, is_active
            FROM dim_electrolux_locations
            ORDER BY country_name, state_name, city_name
        """)
        locations = cursor.fetchall()
        print(f"✅ Encontradas {len(locations)} locations\n")
        
        # Buscar roles
        print("👤 Buscando Roles...")
        cursor.execute("""
            SELECT role_id, role_name, is_active
            FROM dim_roles
            ORDER BY role_id
        """)
        roles = cursor.fetchall()
        print(f"✅ Encontradas {len(roles)} roles\n")
        
        # Buscar categories
        print("📂 Buscando Categories...")
        cursor.execute("""
            SELECT category_id, category_name, description, is_active
            FROM dim_categories
            ORDER BY category_id
        """)
        categories = cursor.fetchall()
        print(f"✅ Encontradas {len(categories)} categories\n")
        
        # Exibir resultados
        print("\n" + "="*80)
        print("LOCATIONS (Primeiras 15)")
        print("="*80)
        for loc in locations[:15]:
            location_id, country, state, city, region, continent, op_type, is_active = loc
            status = "🟢 ATIVO" if is_active else "🔴 INATIVO"
            print(f"  {status} | {country} > {state} > {city} | {region} ({continent})")
        if len(locations) > 15:
            print(f"  ... e mais {len(locations) - 15} locations")
        
        print("\n" + "="*80)
        print("ROLES (Todas)")
        print("="*80)
        for role in roles:
            role_id, role_name, is_active = role
            status = "🟢 ATIVO" if is_active else "🔴 INATIVO"
            print(f"  {status} | {role_id}: {role_name}")
        
        print("\n" + "="*80)
        print("CATEGORIES (Todas)")
        print("="*80)
        for cat in categories:
            cat_id, cat_name, description, is_active = cat
            status = "🟢 ATIVO" if is_active else "🔴 INATIVO"
            print(f"  {status} | {cat_id}: {cat_name}")
            if description:
                print(f"      Descrição: {description}")
        
        # Summary
        print("\n" + "="*80)
        print("📊 RESUMO")
        print("="*80)
        active_locations = sum(1 for loc in locations if loc[7])
        inactive_locations = len(locations) - active_locations
        active_roles = sum(1 for role in roles if role[2])
        inactive_roles = len(roles) - active_roles
        active_categories = sum(1 for cat in categories if cat[3])
        inactive_categories = len(categories) - active_categories
        
        print(f"✅ Locations:   {active_locations} ativas, {inactive_locations} inativas (Total: {len(locations)})")
        print(f"✅ Roles:       {active_roles} ativas, {inactive_roles} inativas (Total: {len(roles)})")
        print(f"✅ Categories:  {active_categories} ativas, {inactive_categories} inativas (Total: {len(categories)})")
        
        # Validação
        print("\n" + "="*80)
        print("✅ VALIDAÇÃO")
        print("="*80)
        
        validations = [
            (len(locations) >= 11, f"Locations count: {len(locations)} >= 11"),
            (len(roles) >= 15, f"Roles count: {len(roles)} >= 15"),
            (len(categories) >= 14, f"Categories count: {len(categories)} >= 14"),
            (active_locations > 0, f"Active locations: {active_locations} > 0"),
            (active_roles > 0, f"Active roles: {active_roles} > 0"),
            (active_categories > 0, f"Active categories: {active_categories} > 0"),
        ]
        
        for passed, msg in validations:
            status = "✅" if passed else "❌"
            print(f"{status} {msg}")
        
        all_passed = all(v[0] for v in validations)
        if all_passed:
            print("\n✅ TODOS OS TESTES PASSARAM! Dados reais estão acessíveis.")
        else:
            print("\n⚠️ Alguns testes falharam. Verifique os dados no Azure.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {type(e).__name__}")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
