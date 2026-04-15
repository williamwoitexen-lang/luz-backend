#!/usr/bin/env python3
"""
Cliente para testar o endpoint de stress test
Uso: python tests/endpoint_stress_test.py --url https://seu-api.azurewebsites.net --token seu_token
"""
import requests
import json
import sys
import argparse
import time
from typing import Dict
from datetime import datetime

class StressTestClient:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if token else ""
        }
    
    def run_stress_test(self, concurrent: int = 10, total: int = 100, question: str = None) -> Dict:
        """Executar teste de stress via endpoint"""
        url = f"{self.base_url}/api/v1/chat/stress-test"
        
        payload = {
            "concurrent_requests": concurrent,
            "total_requests": total,
        }
        
        if question:
            payload["question"] = question
        
        try:
            print(f"\n{'='*70}")
            print(f"🌐 TESTE DE STRESS VIA ENDPOINT DO SERVIDOR".center(70))
            print(f"{'='*70}")
            print(f"URL: {url}")
            print(f"Concurrent: {concurrent}")
            print(f"Total: {total}")
            print(f"Enviando requisição...\n")
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=600
            )
            
            if response.status_code == 200:
                result = response.json()
                self._print_results(result)
                return result
            else:
                print(f"❌ Erro HTTP {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"❌ Timeout após 10 minutos")
            return None
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
    
    def run_stress_test_simple(self, concurrent: int = 10, total: int = 100) -> Dict:
        """Versão simples sem JSON body"""
        url = f"{self.base_url}/api/v1/chat/stress-test-simple"
        
        params = {
            "concurrent": concurrent,
            "total": total
        }
        
        try:
            print(f"\n{'='*70}")
            print(f"🌐 TESTE DE STRESS VIA ENDPOINT (Versão Simples)".center(70))
            print(f"{'='*70}")
            print(f"URL: {url}")
            print(f"Concurrent: {concurrent}")
            print(f"Total: {total}")
            print(f"Enviando requisição...\n")
            
            response = requests.post(
                url,
                params=params,
                headers=self.headers,
                timeout=600
            )
            
            if response.status_code == 200:
                result = response.json()
                self._print_results(result)
                return result
            else:
                print(f"❌ Erro HTTP {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"❌ Timeout após 10 minutos")
            return None
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
    
    def get_test_status(self, test_id: str) -> Dict:
        """Obter status de um teste em execução"""
        url = f"{self.base_url}/api/v1/chat/stress-test/{test_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Teste não encontrado: {test_id}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao obter status: {e}")
            return None
    
    def list_tests(self) -> Dict:
        """Listar todos os testes"""
        url = f"{self.base_url}/api/v1/chat/stress-tests/list"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erro: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao listar testes: {e}")
            return None
    
    def _print_results(self, result: Dict):
        """Formatar e imprimir resultados"""
        print(f"{'='*70}")
        print("📊 RESULTADO DO TESTE DE STRESS".center(70))
        print(f"{'='*70}")
        
        print(f"\n✅ SUMÁRIO:")
        print(f"  Test ID: {result.get('test_id')}")
        print(f"  Status: {result.get('status')}")
        print(f"  Total Requisições: {result.get('total_requests')}")
        print(f"  Bem-sucedidas: {result.get('successful_requests')}")
        print(f"  Falhadas: {result.get('failed_requests')}")
        print(f"  Taxa de Sucesso: {result.get('success_rate'):.1f}%")
        
        print(f"\n⏱️  TEMPO DE RESPOSTA:")
        print(f"  Mínimo: {result.get('min_response_time_ms'):.0f}ms")
        print(f"  Máximo: {result.get('max_response_time_ms'):.0f}ms")
        print(f"  Média: {result.get('avg_response_time_ms'):.0f}ms")
        print(f"  P95: {result.get('p95_response_time_ms'):.0f}ms")
        print(f"  P99: {result.get('p99_response_time_ms'):.0f}ms")
        
        print(f"\n🚀 THROUGHPUT:")
        print(f"  Requisições/s: {result.get('requests_per_second'):.2f}")
        print(f"  Duração: {result.get('duration_seconds'):.2f}s")
        
        if result.get('errors'):
            print(f"\n❌ ERROS:")
            for error_type, count in result.get('errors', {}).items():
                print(f"  {error_type}: {count}")
        
        print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="🌐 Cliente para Teste de Stress via Endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS:

# Teste simples em Azure
python tests/endpoint_stress_test.py \\
  --url https://seu-app-dev.azurewebsites.net \\
  --token "seu_jwt_token" \\
  --concurrent 20 \\
  --total 200

# Teste progressivo (local)
python tests/endpoint_stress_test.py \\
  --url http://localhost:8000 \\
  --concurrent 50 \\
  --total 500

# Teste muito pesado
python tests/endpoint_stress_test.py \\
  --url https://seu-api.azurewebsites.net \\
  --token "token" \\
  --concurrent 100 \\
  --total 1000

# Listar testes
python tests/endpoint_stress_test.py \\
  --url https://seu-api.azurewebsites.net \\
  --list
"""
    )
    
    parser.add_argument("--url", type=str, required=True, help="URL base da API")
    parser.add_argument("--token", type=str, help="JWT token (opcional)")
    parser.add_argument("--concurrent", type=int, default=10, help="Requisições simultâneas")
    parser.add_argument("--total", type=int, default=100, help="Total de requisições")
    parser.add_argument("--question", type=str, help="Pergunta customizada (opcional)")
    parser.add_argument("--status", type=str, help="Ver status de um teste (test_id)")
    parser.add_argument("--list", action="store_true", help="Listar todos os testes")
    
    args = parser.parse_args()
    
    client = StressTestClient(args.url, args.token)
    
    # Listar testes
    if args.list:
        tests = client.list_tests()
        if tests:
            print(f"\n{'='*70}")
            print(f"📋 TESTES REGISTRADOS".center(70))
            print(f"{'='*70}\n")
            print(f"Total: {tests.get('total_tests')}\n")
            
            for test in tests.get('tests', []):
                print(f"  ID: {test['test_id']:10} | Status: {test['status']:10} | " +
                      f"Sucesso: {test['success_rate']:7} | " +
                      f"Requisições: {test['total_requests']}")
            print(f"\n{'='*70}\n")
        return 0
    
    # Ver status de um teste
    if args.status:
        status = client.get_test_status(args.status)
        if status:
            print(json.dumps(status, indent=2))
        return 0 if status else 1
    
    # Executar teste
    result = client.run_stress_test_simple(args.concurrent, args.total)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
