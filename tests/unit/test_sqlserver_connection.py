"""
Script para testar a connection string do SQL Server localmente
"""
import os
from dotenv import load_dotenv

load_dotenv()

conn_str = os.getenv("SQLSERVER_CONNECTION_STRING")
print(f"✅ SQLSERVER_CONNECTION_STRING presente: {bool(conn_str)}")
if conn_str:
    print(f"   Primeiros 100 chars: {conn_str[:100]}...")
    print(f"   Length: {len(conn_str)}")

try:
    import pyodbc
    print("✅ pyodbc importado com sucesso")
    
    if conn_str:
        print("\n🔄 Tentando conectar...")
        conn = pyodbc.connect(conn_str)
        print("✅ Conexão estabelecida!")
        conn.close()
except ImportError:
    print("⚠️  pyodbc não está instalado, tentando mock...")
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    import pyodbc_mock as pyodbc
    print("✅ Mock carregado")
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    import traceback
    traceback.print_exc()
