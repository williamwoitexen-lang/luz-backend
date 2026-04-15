#!/usr/bin/env python3
"""
Script para testar o endpoint de stress test assincronamente
Uso: python tests/test_stress_async.py --url http://localhost:8000 --concurrent 10 --total 50
"""
import requests
import json
import sys
import argparse
import time
from typing import Dict

class AsyncStressTestClient:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if token else ""
        }
    
    def start_stress_test(self, concurrent: int = 10, total: int = 100, question: str = None) -> Dict:
        """Iniciar teste de stress - retorna imediatamente com test_id"""
        url = f"{self.base_url}/api/v1/chat/stress-test"
        
        payload = {
            "concurrent_requests": concurrent,
            "total_requests": total,
        }
        
        if question:
            payload["question"] = question
        
        try:
            print(f"\n{'='*70}")
            print(f"🚀 INICIANDO TESTE DE STRESS ASSINCRONAMENTE".center(70))
            print(f"{'='*70}")
            print(f"URL: {url}")
            print(f"Concurrent: {concurrent}")
            print(f"Total: {total}")
            print(f"Enviando requisição...\n")
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10  # Timeout curto para iniciar
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ TESTE INICIADO!")
                print(f"   Test ID: {result.get('test_id')}")
                print(f"   Status: {result.get('status')}")
                print(f"   Mensagem: {result.get('message')}")
                return result
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"❌ Timeout ao iniciar teste")
            return None
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
    
    def check_progress(self, test_id: str) -> Dict:
        """Obter status/progresso do teste"""
        url = f"{self.base_url}/api/v1/chat/stress-test/{test_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erro ao obter status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
    
    def wait_for_completion(self, test_id: str, max_wait_minutes: int = 30, check_interval: int = 5) -> Dict:
        """Esperar pela conclusão do teste"""
        print(f"\n{'='*70}")
        print(f"⏳ AGUARDANDO CONCLUSÃO DO TESTE".center(70))
        print(f"{'='*70}")
        print(f"Test ID: {test_id}")
        print(f"Polling a cada {check_interval}s, máximo {max_wait_minutes} minutos\n")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while True:
            elapsed = time.time() - start_time
            
            result = self.check_progress(test_id)
            if not result:
                time.sleep(check_interval)
                continue
            
            status = result.get("status")
            
            if status == "running":
                progress = result.get("progress")
                duration = result.get("duration_so_far", "N/A")
                success_rate = result.get("success_rate")
                print(f"[{elapsed/60:.1f}min] ⏳ {progress} | Success: {success_rate} | Elapsed: {duration}s")
                
            elif status == "completed":
                print(f"\n✅ TESTE CONCLUÍDO!\n")
                self._print_results(result)
                return result
            
            if elapsed > max_wait_seconds:
                print(f"❌ Timeout após {max_wait_minutes} minutos")
                return None
            
            time.sleep(check_interval)
    
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
        
        if result.get('avg_response_time_ms') is not None:
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
        description="🚀 Cliente para Teste de Stress Assincronamente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS:

# Teste simples em azure (async)
python tests/test_stress_async.py \\
  --url https://seu-app-dev.azurewebsites.net \\
  --token "seu_jwt_token" \\
  --concurrent 20 \\
  --total 200

# Teste progressivo (local)
python tests/test_stress_async.py \\
  --url http://localhost:8000 \\
  --concurrent 50 \\
  --total 500

# Teste muito pesado (aguarda com polling)
python tests/test_stress_async.py \\
  --url https://seu-api.azurewebsites.net \\
  --token "token" \\
  --concurrent 100 \\
  --total 1000
        """)
    
    parser.add_argument("--url", required=True, help="URL base da API (ex: http://localhost:8000)")
    parser.add_argument("--token", help="JWT token para autenticação (opcional)")
    parser.add_argument("--concurrent", type=int, default=10, help="Requisições simultâneas (default: 10)")
    parser.add_argument("--total", type=int, default=100, help="Total de requisições (default: 100)")
    parser.add_argument("--question", help="Pergunta customizada (default: padrão)")
    parser.add_argument("--wait-timeout", type=int, default=30, help="Timeout em minutos para aguardar (default: 30)")
    parser.add_argument("--check-interval", type=int, default=5, help="Intervalo em segundos para checar status (default: 5)")
    
    args = parser.parse_args()
    
    client = AsyncStressTestClient(args.url, args.token)
    
    # 1. Iniciar teste
    result = client.start_stress_test(
        concurrent=args.concurrent,
        total=args.total,
        question=args.question
    )
    
    if result and 'test_id' in result:
        test_id = result['test_id']
        
        # 2. Aguardar conclusão
        final_result = client.wait_for_completion(
            test_id,
            max_wait_minutes=args.wait_timeout,
            check_interval=args.check_interval
        )
        
        if final_result:
            return 0
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
