"""
Endpoint para Testes de Stress do Chat
Permite testar o chat sob carga sem requisições externas
"""
import asyncio
import logging
import uuid
import traceback
import os
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat-stress-test"])

# Modelo de resposta do teste
class StressTestRequest(BaseModel):
    """Parâmetros para teste de stress"""
    concurrent_requests: int = 10  # Requisições simultâneas
    total_requests: int = 100      # Total de requisições
    question: str = "Qual é o processo de onboarding?"
    duration_seconds: int = None   # Duração máxima (opcional)

class StressTestResponse(BaseModel):
    """Resposta do teste de stress"""
    test_id: str
    status: str  # "running", "completed"
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    avg_ttft_ms: float
    p95_ttft_ms: float
    avg_tokens_per_second: float
    requests_per_second: float
    duration_seconds: float
    errors: Dict[str, int]
    timestamp: str

# Armazenar testes em execução
active_tests: Dict[str, Dict] = {}

async def simulate_question(question: str, user_id: str) -> Dict:
    """
    Simula uma pergunta ao chat fazendo requisição HTTP async para o endpoint de stream
    Isso reutiliza toda a lógica de persistência que já existe
    """
    import json
    import time
    import aiohttp
    
    try:
        start_time = time.time()
        answer = ""
        complete_received = False
        error_received = False
        ttft = None
        token_events = 0
        
        # Preparar payload
        payload = {
            "chat_id": str(uuid.uuid4()),
            "question": question,
            "user_id": user_id,
            "name": f"Stress Test {user_id}",
            "email": f"stress_{user_id}@stresstest.dev",
            "country": "BR",
            "city": "São Paulo",
            "role_id": 1,
            "department": "Test",
            "job_title": "Tester",
            "collar": "white",
            "unit": "Unit A"
        }
        
        # Fazer requisição streaming async para o endpoint de chat
        # Este endpoint já cuida de persistência no banco
        try:
            # Para stress test, usar localhost:8000 (mesmo container)
            # Se APP_BASE_URL_BACKEND for externa (HTTPS), usar localhost
            base_url = os.getenv("APP_BASE_URL_BACKEND", "http://localhost:8000")
            if "https://" in base_url:
                # URL externa, usar localhost para stress test
                base_url = "http://localhost:8000"
            
            stream_endpoint = f"{base_url}/api/v1/chat/question/stream"
            
            timeout = aiohttp.ClientTimeout(total=120, sock_read=120)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    stream_endpoint,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(f"[Stress Test] HTTP {response.status}: {error_text[:100]}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "time": time.time() - start_time,
                            "ttft": None,
                            "token_events": 0,
                            "token_chars": 0
                        }
                    
                    # Processar stream SSE async
                    buffer = ""
                    async for chunk in response.content.iter_any():
                        if chunk:
                            buffer += chunk.decode("utf-8", errors="ignore")
                            
                            while "\n\n" in buffer:
                                event_block, buffer = buffer.split("\n\n", 1)
                                event_block = event_block.strip()
                                
                                if not event_block:
                                    continue
                                
                                # Parsear evento SSE
                                event_type = None
                                event_data = None
                                
                                for line in event_block.split("\n"):
                                    if line.startswith("event:"):
                                        event_type = line.replace("event:", "").strip()
                                    elif line.startswith("data:"):
                                        event_data = line.replace("data:", "").strip()
                                
                                # Processar pelos tipos de evento
                                if event_type == "token" and event_data:
                                    try:
                                        token_obj = json.loads(event_data)
                                        content = token_obj.get("content", "")
                                        answer += content
                                        if ttft is None:
                                            ttft = time.time() - start_time
                                        token_events += 1
                                    except:
                                        pass
                                        
                                elif event_type == "complete" and event_data:
                                    try:
                                        complete_obj = json.loads(event_data)
                                        answer = complete_obj.get("answer", answer)
                                        complete_received = True
                                        logger.debug(f"[Stress Test] Complete event, answer: {len(answer)} chars")
                                    except json.JSONDecodeError:
                                        complete_received = True
                                        
                                elif event_type == "error" and event_data:
                                    error_received = True
                                    logger.warning(f"[Stress Test] Error: {event_data}")
        except asyncio.TimeoutError:
            logger.warning(f"[Stress Test] Request timeout for user {user_id}")
            return {
                "success": False,
                "error": "Request timeout",
                "time": time.time() - start_time,
                "ttft": ttft,
                "token_events": token_events,
                "token_chars": len(answer)
            }
        
        elapsed = time.time() - start_time
        
        # Verificar sucesso
        if error_received:
            return {
                "success": False,
                "error": "LLM error",
                "time": elapsed,
                "ttft": ttft,
                "token_events": token_events,
                "token_chars": len(answer)
            }
        elif complete_received and len(answer) > 0:
            return {
                "success": True,
                "response": answer,
                "time": elapsed,
                "ttft": ttft,
                "token_events": token_events,
                "token_chars": len(answer)
            }
        else:
            error_msg = f"complete={complete_received}, answer_len={len(answer)}"
            logger.warning(f"[Stress Test] Failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "time": elapsed,
                "ttft": ttft,
                "token_events": token_events,
                "token_chars": len(answer)
            }
            
    except Exception as e:
        logger.error(f"[Stress Test] Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": type(e).__name__,
            "time": 0,
            "ttft": None,
            "token_events": 0,
            "token_chars": 0
        }


async def run_stress_test_background(req: StressTestRequest, test_id: str):
    """
    Executa o teste de stress em background
    """
    start_time = datetime.now()
    
    # Inicializar métricas
    test_data = {
        "test_id": test_id,
        "successful": 0,
        "failed": 0,
        "response_times": [],
        "ttft_times": [],
        "tokens_per_second": [],
        "errors": {},
        "status": "running",
        "start_time": start_time.isoformat(),
        "end_time": None,
        "duration": 0,
        "total_requests_planned": req.total_requests,
        "result": None
    }
    active_tests[test_id] = test_data
    
    try:
        # Semáforo para controlar concorrência
        semaphore = asyncio.Semaphore(req.concurrent_requests)
        
        async def single_request(req_num: int):
            async with semaphore:
                try:
                    import time
                    start = time.time()
                    
                    result = await simulate_question(
                        req.question,
                        f"user_{uuid.uuid4().hex[:6]}"
                    )
                    
                    elapsed = result.get("time", time.time() - start)
                    
                    if result["success"]:
                        test_data["successful"] += 1
                        test_data["response_times"].append(elapsed)
                        ttft = result.get("ttft")
                        if ttft is not None:
                            test_data["ttft_times"].append(ttft)
                        token_events = result.get("token_events", 0)
                        if elapsed > 0 and token_events > 0:
                            test_data["tokens_per_second"].append(token_events / elapsed)
                    else:
                        test_data["failed"] += 1
                        error_type = result.get("error", "Unknown")[:50]
                        test_data["errors"][error_type] = test_data["errors"].get(error_type, 0) + 1
                        
                except Exception as e:
                    test_data["failed"] += 1
                    error_type = type(e).__name__
                    test_data["errors"][error_type] = test_data["errors"].get(error_type, 0) + 1
                    logger.warning(f"[Stress Test {test_id}] Erro: {e}")
        
        # Executar requisições
        tasks = []
        for i in range(req.total_requests):
            task = single_request(i)
            tasks.append(task)
            
            # Verificar timeout
            if req.duration_seconds:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > req.duration_seconds:
                    # Atingiu duração máxima
                    break
        
        # Aguardar todas as requisições
        await asyncio.gather(*tasks, return_exceptions=True)
        
    finally:
        # Calcular métricas
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        total = test_data["successful"] + test_data["failed"]
        success_rate = (test_data["successful"] / total * 100) if total > 0 else 0
        
        if test_data["response_times"]:
            import statistics
            response_times = test_data["response_times"]
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            sorted_times = sorted(response_times)
            p95_time = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else 0
            p99_time = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 1 else 0
        else:
            avg_time = min_time = max_time = p95_time = p99_time = 0
        
        if test_data["ttft_times"]:
            import statistics
            ttft_times = test_data["ttft_times"]
            avg_ttft = statistics.mean(ttft_times)
            sorted_ttft = sorted(ttft_times)
            p95_ttft = sorted_ttft[int(len(sorted_ttft) * 0.95)] if len(sorted_ttft) > 1 else sorted_ttft[0]
        else:
            avg_ttft = p95_ttft = 0
        
        if test_data["tokens_per_second"]:
            import statistics
            avg_tokens_per_second = statistics.mean(test_data["tokens_per_second"])
        else:
            avg_tokens_per_second = 0
        
        rps = (total / duration) if duration > 0 else 0
        
        # Armazenar resposta completa
        test_data["result"] = StressTestResponse(
            test_id=test_id,
            status="completed",
            total_requests=total,
            successful_requests=test_data["successful"],
            failed_requests=test_data["failed"],
            success_rate=success_rate,
            avg_response_time_ms=avg_time * 1000,
            min_response_time_ms=min_time * 1000,
            max_response_time_ms=max_time * 1000,
            p95_response_time_ms=p95_time * 1000,
            p99_response_time_ms=p99_time * 1000,
            avg_ttft_ms=avg_ttft * 1000,
            p95_ttft_ms=p95_ttft * 1000,
            avg_tokens_per_second=avg_tokens_per_second,
            requests_per_second=rps,
            duration_seconds=duration,
            errors=test_data["errors"],
            timestamp=end_time.isoformat()
        )
        
        test_data["status"] = "completed"
        test_data["end_time"] = end_time.isoformat()
        test_data["duration"] = duration


@router.post("/stress-test", response_model=dict)
async def run_stress_test(req: StressTestRequest) -> Dict:
    """
    Inicia um teste de stress de forma assincronamente
    
    Retorna imediatamente com o test_id. Use GET /stress-test/{test_id} para obter o resultado
    
    As requisições chamam o endpoint `/api/v1/chat/question/stream` que já salva automaticamente no banco.
    
    Exemplo:
    POST /api/v1/chat/stress-test
    {
        "concurrent_requests": 10,
        "total_requests": 100,
        "question": "Qual é o processo de onboarding?",
        "duration_seconds": 300
    }
    
    **Parâmetros:**
    - `concurrent_requests`: Número de requisições simultâneas (padrão: 10)
    - `total_requests`: Total de requisições a fazer (padrão: 100)
    - `question`: Pergunta para testar (padrão: "Qual é o processo de onboarding?")
    - `duration_seconds`: Duração máxima do teste em segundos (opcional)
    
    Resposta (imediata):
    {
        "test_id": "abc123",
        "status": "running",
        "message": "Use GET /api/v1/chat/stress-test/abc123 para obter o resultado"
    }
    """
    test_id = str(uuid.uuid4())[:8]
    
    # Inicializar estrutura vazia (MUITO rápido)
    active_tests[test_id] = {
        "test_id": test_id,
        "successful": 0,
        "failed": 0,
        "response_times": [],
        "ttft_times": [],
        "tokens_per_second": [],
        "errors": {},
        "status": "running",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "duration": 0,
        "total_requests_planned": req.total_requests,
        "result": None
    }
    
    # Disparar em background (não-bloqueante, < 1ms)
    asyncio.create_task(run_stress_test_background(req, test_id))
    
    # Retornar IMEDIATAMENTE (< 100ms total)
    return {
        "test_id": test_id,
        "status": "running",
        "check_url": f"/api/v1/chat/stress-test/{test_id}"
    }


@router.get("/stress-test/{test_id}")
async def get_stress_test_status(test_id: str) -> Dict:
    """
    Obter status de um teste em execução ou resultado completo
    
    GET /api/v1/chat/stress-test/abc123
    
    Resposta quando rodando:
    {
        "test_id": "abc123",
        "status": "running",
        "progress": "45/100 requisições completas",
        "successful": 45,
        "failed": 0,
        "success_rate": "100.0%",
        "elapsed": "2.3s"
    }
    
    Resposta quando completo:
    {
        "test_id": "abc123",
        "status": "completed",
        "total_requests": 100,
        "successful_requests": 98,
        "failed_requests": 2,
        "success_rate": 98.0,
        "avg_response_time_ms": 1250.5,
        ...
    }
    """
    try:
        if test_id not in active_tests:
            raise HTTPException(status_code=404, detail=f"Teste '{test_id}' não encontrado")
        
        test = active_tests[test_id]
        total_done = test["successful"] + test["failed"]
        total_planned = test.get("total_requests_planned", 100)
        success_rate = (test["successful"] / total_done * 100) if total_done > 0 else 0
        
        # Calcular tempo decorrido
        now = datetime.now()
        start = datetime.fromisoformat(test.get("start_time", now.isoformat()))
        elapsed = (now - start).total_seconds()
        
        if test["status"] == "running":
            # Retornar progresso enquanto rodando
            return {
                "test_id": test_id,
                "status": "running",
                "progress": f"{total_done}/{total_planned} requisições completas",
                "successful": test["successful"],
                "failed": test["failed"],
                "success_rate": f"{success_rate:.1f}%",
                "start_time": test.get("start_time"),
                "elapsed_seconds": f"{elapsed:.1f}s"
            }
        else:
            # Retornar resultado completo quando terminou
            result = test.get("result")
            if result:
                # Se for objeto StressTestResponse, converter para dict
                if hasattr(result, "dict"):
                    return result.dict()
                elif isinstance(result, dict):
                    return result
                else:
                    # Fallback: retornar dados básicos
                    return {
                        "test_id": test_id,
                        "status": "completed",
                        "total_requests": total_done,
                        "successful_requests": test["successful"],
                        "failed_requests": test["failed"],
                        "success_rate": success_rate,
                        "errors": test.get("errors", {}),
                        "duration_seconds": test.get("duration", 0)
                    }
            else:
                return {
                    "test_id": test_id,
                    "status": "completed",
                    "total_requests": total_done,
                    "successful_requests": test["successful"],
                    "failed_requests": test["failed"],
                    "success_rate": success_rate,
                    "errors": test.get("errors", {}),
                    "end_time": test.get("end_time"),
                    "duration_seconds": test.get("duration", 0)
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar status do teste {test_id}: {e}")
        logger.error(traceback.format_exc())
        # Tentar retornar o que conseguir reconstructir
        if test_id in active_tests:
            test = active_tests[test_id]
            return {
                "test_id": test_id,
                "status": test.get("status", "unknown"),
                "error": str(e),
                "available_data": {
                    "successful": test.get("successful", 0),
                    "failed": test.get("failed", 0)
                }
            }
        raise HTTPException(status_code=500, detail=f"Erro ao processar teste: {str(e)}")


@router.get("/stress-tests/list")
async def list_stress_tests() -> Dict:
    """
    Listar todos os testes (em execução ou completados)
    
    GET /api/v1/chat/stress-tests/list
    """
    tests_list = []
    for test_id, test in active_tests.items():
        total = test["successful"] + test["failed"]
        success_rate = (test["successful"] / total * 100) if total > 0 else 0
        
        tests_list.append({
            "test_id": test_id,
            "status": test["status"],
            "total_requests": total,
            "successful": test["successful"],
            "failed": test["failed"],
            "success_rate": f"{success_rate:.1f}%"
        })
    
    return {
        "total_tests": len(tests_list),
        "tests": tests_list
    }


@router.post("/stress-test-simple")
async def run_stress_test_simple(
    concurrent: int = Query(10, description="Requisições simultâneas"),
    total: int = Query(100, description="Total de requisições")
) -> Dict:
    """
    Versão simples do teste de stress (sem JSON body) - assincronamente
    
    POST /api/v1/chat/stress-test-simple?concurrent=20&total=200
    
    Retorna imediatamente com test_id. Use GET /stress-test/{test_id} para obter o resultado
    """
    req = StressTestRequest(
        concurrent_requests=concurrent,
        total_requests=total
    )
    return await run_stress_test(req)