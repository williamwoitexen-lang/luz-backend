# LLM Integration Troubleshooting Guide

**Versão**: 2.0 | **Última Atualização**: 2026-01-15 | **Status**: Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Common LLM Failures](#common-llm-failures)
3. [Retry & Backoff Strategy](#retry--backoff-strategy)
4. [Fallback Mechanisms](#fallback-mechanisms)
5. [Logging & Debugging](#logging--debugging)
6. [Performance Tuning](#performance-tuning)
7. [Data Sensitivity in Logs](#data-sensitivity-in-logs)
8. [Testing Without LLM](#testing-without-llm)
9. [Monitoring & Alerts](#monitoring--alerts)
10. [FAQ](#faq)

---

## Overview

### What is LLM Integration?

The Luz backend uses Azure OpenAI LLM for:

| Feature | LLM Usage | Module |
|---------|-----------|--------|
| Document Metadata Extraction | Preview step: extract title, category, locations | `/app/services/document_service.py` |
| Semantic Chat | Answer user questions using document context | `/app/services/chat_service.py` |
| Intent Classification | Understand user intent before answering | `/app/providers/llm_intent_provider.py` |
| Response Ranking | Score top-k documents by relevance | `/app/providers/llm_ranking_provider.py` |

### Configuration Reference

```python
# app/core/config.py
LLM_SERVER_URL = env("LLM_SERVER_URL")
LLM_SERVER_TIMEOUT = int(env("LLM_SERVER_TIMEOUT", "30"))  
LLM_API_KEY = env("LLM_API_KEY")
LLM_MODEL_NAME = env("LLM_MODEL_NAME")  # e.g., "gpt-4", "gpt-35-turbo"
LLM_MAX_TOKENS = int(env("LLM_MAX_TOKENS", "2000"))
SKIP_LLM_SERVER = env("SKIP_LLM_SERVER", "false").lower() == "true"
LLM_RETRY_ATTEMPTS = int(env("LLM_RETRY_ATTEMPTS", "3"))
LLM_RETRY_BACKOFF_BASE = float(env("LLM_RETRY_BACKOFF_BASE", "1.0"))  # seconds
```

---

## Common LLM Failures

### 1. Connection Timeout (ReadTimeout)

#### Symptom
```
httpx.ReadTimeout: The server did not send any data in response to 
attempt #1 across to https://xxx.openai.azure.com/...
```

#### Causes
- LLM server is down/unreachable
- Network latency spike
- Request too large (exceeds token limits)
- LLM service is overloaded

#### Solutions

**Immediate Action**:
```bash
# Check if LLM server is reachable
curl -v https://xxx.openai.azure.com/openai/deployments/gpt-4/chat/completions \
  -H "api-key: YOUR_KEY"

# OR check Azure Portal
# → Go to Azure OpenAI → Deployments → Check deployment status
```

**Short-term**:
1. Increase timeout in config:
   ```env
   LLM_SERVER_TIMEOUT=60  # increase from default 30s
   ```

2. Check Azure OpenAI quota:
   ```bash
   # Azure Portal → OpenAI → Monitoring → Metrics
   # Look for: Tokens Used, Request Count
   ```

3. Try with smaller document chunk:
   ```python
   # Reduce context window in request
   MAX_CONTEXT_CHARS = 3000  # reduce from 5000
   ```

**Long-term**:
- Configure retry with exponential backoff (see [Retry Strategy](#retry--backoff-strategy))
- Use fallback to keyword search (see [Fallback Mechanisms](#fallback-mechanisms))
- Scale up Azure OpenAI deployment

---

### 2. Authentication Error (401/403)

#### Symptom
```
401 Unauthorized: Invalid API key
OR
403 Forbidden: Quota exceeded
```

#### Causes
- `LLM_API_KEY` is wrong/expired
- `LLM_SERVER_URL` points to wrong deployment
- Azure subscription quota exceeded

#### Solutions

**Verify Configuration**:
```bash
# Check environment variables are set
echo $LLM_API_KEY
echo $LLM_SERVER_URL
echo $LLM_MODEL_NAME

# Expected format:
# LLM_API_KEY=abc123xyz...
# LLM_SERVER_URL=https://resource-name.openai.azure.com/
# LLM_MODEL_NAME=gpt-4
```

**Verify Azure Credentials** (if using KeyVault):
```bash
# Check if deployment exists
az deployment show --name my-deployment

# Check API key in KeyVault
az keyvault secret show --vault-name my-vault --name LLM-API-KEY
```

**Check Quota**:
```bash
# Azure CLI
az monitor metrics list \
  --resource-group my-rg \
  --resource-type Microsoft.CognitiveServices/accounts \
  --resource my-openai-resource \
  --metric "TokenUsed" \
  --interval PT1H \
  --start-time 2026-01-01T00:00:00Z
```

---

### 3. Rate Limiting (429 Too Many Requests)

#### Symptom
```
429 Too Many Requests: Rate limit exceeded
OR
429 - {"error":{"code":"RateLimitExceeded",...}}
```

#### Causes
- Too many concurrent requests to LLM
- Burst traffic exceeding TPM (Tokens Per Minute)
- Multiple services hitting LLM simultaneously

#### Solutions

**Immediate**:
```python
# Implement request queuing
from asyncio import Semaphore

# In your LLM provider
llm_semaphore = Semaphore(3)  # Max 3 concurrent LLM requests

async def call_llm(prompt):
    async with llm_semaphore:
        response = await llm_client.call(prompt)
    return response
```

**Configuration**:
```env
# Add rate limit config
LLM_MAX_CONCURRENT_REQUESTS=3
LLM_REQUEST_TIMEOUT_QUEUE=60  # seconds waiting in queue

# In config.py
LLM_MAX_CONCURRENT = int(env("LLM_MAX_CONCURRENT_REQUESTS", "3"))
```

**Long-term**:
- Scale up Azure OpenAI TPM quota
- Implement request batching (batch similar requests)
- Use caching for repeated questions

---

### 4. Invalid Request (400 Bad Request)

#### Symptom
```
400 Bad Request: {"error":{"message":"Invalid request format"}}
OR
400: Tokens exceed max_tokens
```

#### Causes
- Prompt template has invalid format
- Token count exceeds `LLM_MAX_TOKENS`
- Special characters not properly escaped
- Requested model doesn't exist

#### Solutions

**Check Prompt Format**:
```python
# Ensure correct ChatCompletion format
messages = [
    {"role": "system", "content": "You are helpful assistant"},
    {"role": "user", "content": user_query},
]
# ✅ Correct

# ❌ Wrong - missing role/content
messages = [{"text": "hello"}]
```

**Check Token Count**:
```python
from app.providers.llm_provider import count_tokens

prompt = "This is my long document..."
token_count = count_tokens(prompt)

if token_count > LLM_MAX_TOKENS - 100:  # 100 buffer for response
    # Truncate context
    prompt = prompt[:3000]  # reduce chars
```

**Verify Model Name**:
```bash
# List available models via Azure Portal
# Cognitive Services | your-resource | Model deployments

# Expected format: "gpt-4", "gpt-35-turbo", "text-embedding-ada-002"
# NOT "gpt-4-32k" unless you created that deployment
```

---

### 5. Slow Response (Timeout after retries)

#### Symptom
```
Total LLM call time: 45 seconds (expected < 10s)
OR
LLM timeout after 3 retry attempts
```

#### Causes
- Very long document/prompt (thousands of tokens)
- LLM server overloaded
- Network latency

#### Solutions

**Optimize Input**:
```python
# app/services/document_service.py

def extract_metadata(document_text: str) -> dict:
    # ❌ Bad: send entire 50-page document
    prompt = f"Extract metadata from: {full_document}"
    
    # ✅ Good: send only first 3000 chars
    truncated = document_text[:3000]
    prompt = f"Extract metadata from: {truncated}"
    
    return llm_client.call(prompt)
```

**Reduce max_tokens**:
```env
# Reduce response length requirement
LLM_MAX_TOKENS=500  # from 2000
```

**Use Streaming** (for long responses):
```python
# Instead of waiting for full response:
# async def call_llm(prompt):
#     response = await client.call(prompt)  # wait 30s
#     return response

# Use streaming:
async def call_llm_streaming(prompt):
    async for chunk in client.stream(prompt):
        yield chunk  # Return partial results immediately
```

---

## Retry & Backoff Strategy

### Configuration

The system uses **exponential backoff with jitter** by default:

```env
LLM_RETRY_ATTEMPTS=3
LLM_RETRY_BACKOFF_BASE=1.0  # seconds
LLM_RETRY_BACKOFF_MAX=30.0   # max seconds between retries
LLM_RETRY_JITTER=True        # add randomness to avoid thundering herd
```

### Implementation

```python
# app/core/llm_retry.py
import asyncio
import random
from typing import Callable, TypeVar

T = TypeVar("T")

async def retry_with_backoff(
    func: Callable,
    *args,
    max_attempts: int = 3,
    base_backoff: float = 1.0,
    backoff_max: float = 30.0,
    jitter: bool = True,
    **kwargs
) -> T:
    """
    Retry function with exponential backoff + jitter
    
    Backoff formula: min(backoff_max, base_backoff * (2 ^ attempt)) ± jitter
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt == max_attempts - 1:
                # Last attempt failed
                raise
            
            # Calculate backoff with exponential growth
            backoff = min(backoff_max, base_backoff * (2 ** attempt))
            
            if jitter:
                # Add jitter: ±25% randomness
                jitter_amount = backoff * 0.25 * random.random()
                backoff += jitter_amount
            
            print(f"Attempt {attempt + 1} failed: {e}")
            print(f"Retrying in {backoff:.2f}s...")
            await asyncio.sleep(backoff)
    
    raise last_exception
```

### Usage Example

```python
# app/services/chat_service.py
from app.core.llm_retry import retry_with_backoff

async def answer_question(user_query: str) -> str:
    """
    Answer question with automatic retry on LLM failure
    """
    
    def llm_call():
        return self.llm_provider.call_chat(user_query)
    
    response = await retry_with_backoff(
        llm_call,
        max_attempts=3,
        base_backoff=1.0,
        backoff_max=30.0,
    )
    
    return response
```

### When NOT to Retry

```python
# ❌ Don't retry on permanent failures:
if error_code == 401:  # Authentication error
    raise error  # No point retrying
    
if error_code == 400:  # Bad request
    raise error  # Need to fix prompt
    
# ✅ Retry on transient failures:
if error_code == 429:  # Rate limit
    retry()
    
if error_code == 503:  # Service unavailable
    retry()
    
if isinstance(error, Timeout):
    retry()
```

---

## Fallback Mechanisms

### Strategy 1: Keyword Search Fallback

When LLM fails, fall back to BM25 (keyword-based search):

```python
# app/services/chat_service.py

async def answer_question(user_query: str) -> dict:
    """
    Try LLM first, fallback to keyword search
    """
    try:
        # Try semantic search with LLM
        documents = await self.llm_provider.semantic_search(user_query)
        source = "LLM"
    except Exception as e:
        print(f"LLM failed: {e}, falling back to keyword search")
        
        # Fallback: keyword search (always works)
        documents = await self.search_provider.bm25_search(user_query)
        source = "BM25-FALLBACK"
    
    answer = format_response(documents)
    answer["_metadata"]["source"] = source
    answer["_metadata"]["fallback_used"] = source != "LLM"
    
    return answer
```

### Strategy 2: Cached Response Fallback

Cache repeated questions to avoid hitting LLM:

```python
# app/services/cache_service.py
from functools import lru_cache
import hashlib

class LLMCacheService:
    """Cache LLM responses to reduce API calls"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl_seconds = 86400  # 24 hours
    
    def cache_key(self, query: str, user_context: dict) -> str:
        """Generate unique cache key"""
        # Include query + key context (location, role)
        content = f"{query}:{user_context['country']}:{user_context['role']}"
        return f"llm_response:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def get_or_call(self, query: str, user_context: dict, llm_call_func):
        """Get from cache or call LLM and cache result"""
        key = self.cache_key(query, user_context)
        
        # Try cache first
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # Call LLM
        try:
            response = await llm_call_func(query, user_context)
        except LLMError as e:
            # On LLM failure, try returning old cached response
            old_response = await self.redis.get(f"{key}:old")
            if old_response:
                print(f"Using stale cache due to LLM failure")
                return json.loads(old_response)
            raise
        
        # Cache successful response
        await self.redis.set(key, json.dumps(response), ex=self.ttl_seconds)
        # Also keep old version for stale fallback
        await self.redis.set(f"{key}:old", json.dumps(response), ex=self.ttl_seconds * 7)
        
        return response
```

### Strategy 3: Graceful Degradation

Return partial answer instead of failing:

```python
# app/services/chat_service.py

async def answer_question(query: str) -> dict:
    """
    Answer question with graceful degradation
    """
    
    # Step 1: Try to get semantic results
    try:
        documents = await self.llm_provider.semantic_search(query)
        semantic_success = True
    except Exception as e:
        documents = []
        semantic_success = False
    
    # Step 2: If semantic failed, try keyword search
    if not documents:
        documents = await self.search_provider.keyword_search(query)
    
    # Step 3: Format response
    response = {
        "answer": format_documents(documents),
        "source_documents": documents,
        "_metadata": {
            "semantic_success": semantic_success,
            "has_results": len(documents) > 0,
            "warning": None
        }
    }
    
    # Step 4: Add warning if degraded
    if not semantic_success:
        response["_metadata"]["warning"] = \
            "LLM was unavailable. Results based on keyword search instead of semantic search."
    
    return response
```

---

## Logging & Debugging

### What IS Logged (Safe)

```python
# ✅ Safe to log
print(f"LLM call started for query: {query[:100]}")  # First 100 chars only
print(f"LLM response time: 2.3 seconds")
print(f"Token usage: 450 input, 150 output")
print(f"Source documents: 3 relevant documents found")
print(f"LLM model: gpt-4")
```

### What is NOT Logged (Sensitive)

```python
# ❌ Never log these:
# - Full API key
api_key = "sk-proj-abc123xyz"  # DON'T log
# - Full user document content
print(f"User provided: {full_document}")  # DON'T log
# - Full prompt sent to LLM
print(f"Prompt: {full_prompt}")  # DON'T log (contains document)
# - User location/department (in some contexts)
```

### Debug Mode

Enable verbose logging:

```env
# .env
DEBUG_LLM=true
LOG_LEVEL=DEBUG
```

```python
# app/core/logging_config.py
import logging

if env("DEBUG_LLM", "false").lower() == "true":
    # Only in development!
    logging.getLogger("app.providers.llm_provider").setLevel(logging.DEBUG)
    
    logger.debug(f"LLM Request (first 200 chars): {str(request)[:200]}")
    logger.debug(f"LLM Response (first 500 chars): {str(response)[:500]}")
```

### Production Logging

Structured logging for production:

```python
# app/providers/llm_provider.py
import json
from datetime import datetime

async def call_llm(query: str, user_id: str) -> str:
    """Call LLM with structured logging"""
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "llm_call",
        "user_id": user_id,
        "query_length": len(query),
        "status": "started"
    }
    
    try:
        start_time = time.time()
        response = await self.client.call(query)
        duration = time.time() - start_time
        
        log_entry.update({
            "status": "success",
            "duration_seconds": round(duration, 2),
            "response_length": len(response),
            "model": self.model_name
        })
        
    except Timeout as e:
        log_entry["status"] = "timeout"
        log_entry["error"] = str(e)
        
    except RateLimitError as e:
        log_entry["status"] = "rate_limited"
        log_entry["error"] = "Rate limit exceeded"
        
    except Exception as e:
        log_entry["status"] = "error"
        log_entry["error_type"] = type(e).__name__
        log_entry["error"] = str(e)
    
    # Log as JSON
    print(json.dumps(log_entry))
    
    if log_entry["status"] != "success":
        raise Exception(f"LLM call failed: {log_entry['error']}")
    
    return response
```

---

## Performance Tuning

### Metric 1: Response Time

**Target**: < 5 seconds per question

```bash
# Monitor in logs
# "duration_seconds": 4.2 ✅ Good
# "duration_seconds": 12.1 ❌ Too slow
```

**If too slow**:
1. Reduce context window (see [Slow Response](#5-slow-response-timeout-after-retries))
2. Use caching for repeated questions
3. Increase LLM_MAX_TOKENS_RESPONSE (let LLM answer quicker)

### Metric 2: Token Efficiency

**Target**: < 1000 tokens per question

```python
from app.providers.llm_provider import count_tokens

query = "..."
context = "..."
full_prompt = f"...\n{query}\n{context}"

token_count = count_tokens(full_prompt)
if token_count > 1000:
    print(f"⚠️  High token usage: {token_count}")
    # Reduce context
```

### Metric 3: Error Rate

**Target**: < 1% LLM errors

```python
# Track metrics
class LLMMetrics:
    def __init__(self):
        self.total_calls = 0
        self.failed_calls = 0
    
    def add_call(self, success: bool):
        self.total_calls += 1
        if not success:
            self.failed_calls += 1
    
    @property
    def error_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return (self.failed_calls / self.total_calls) * 100
    
    def check_slo(self):
        if self.error_rate > 1.0:
            alert("High LLM error rate: {:.2f}%".format(self.error_rate))
```

---

## Data Sensitivity in Logs

### Classification

```python
# app/core/data_classification.py

class DataClassification:
    
    PUBLIC = "public"
    CONFIDENTIAL = "confidential"
    SENSITIVE_PII = "sensitive_pii"
    
    SENSITIVE_KEYWORDS = [
        "salary",
        "medical",
        "health",
        "ssn",
        "credit card",
        "bank account",
        "password",
        "authentication_token",
    ]

def classify_user_data(data: str) -> str:
    """Classify data sensitivity level"""
    
    data_lower = data.lower()
    
    # Check for sensitive keywords
    for keyword in DataClassification.SENSITIVE_KEYWORDS:
        if keyword in data_lower:
            return DataClassification.SENSITIVE_PII
    
    # If contains personal indicators
    if any(x in data_lower for x in ["@company.com", "employee", "department"]):
        return DataClassification.CONFIDENTIAL
    
    return DataClassification.PUBLIC
```

### Log Filtering

```python
# app/providers/llm_provider.py

def sanitize_for_logging(query: str, max_length: int = 100) -> str:
    """Remove sensitive data before logging"""
    
    classification = classify_user_data(query)
    
    if classification == DataClassification.SENSITIVE_PII:
        return "[REDACTED - PII]"
    
    if classification == DataClassification.CONFIDENTIAL:
        return f"{query[:max_length]}... [TRUNCATED]"
    
    # Public data - full logging OK
    return query
```

---

## Testing Without LLM

### Mock Mode

Disable LLM calls during testing:

```env
# .env.test
SKIP_LLM_SERVER=true
LLM_MOCK_RESPONSES=true
```

```python
# app/core/config.py
SKIP_LLM_SERVER = env("SKIP_LLM_SERVER", "false").lower() == "true"
LLM_MOCK_RESPONSES = env("LLM_MOCK_RESPONSES", "false").lower() == "true"
```

### Mock Provider

```python
# app/providers/llm_mock_provider.py

class MockLLMProvider:
    """Mock LLM for testing without Azure OpenAI"""
    
    async def call_chat(self, query: str) -> str:
        """Return canned responses for testing"""
        
        if "benefits" in query.lower():
            return "We offer health insurance, dental, vision, and 401k."
        
        if "vacation" in query.lower():
            return "Employees get 20 days of paid time off per year."
        
        if "locations" in query.lower():
            return "We have offices in Brazil, USA, and Europe."
        
        # Default response
        return "I'm a mock LLM. This is a test response."
    
    async def semantic_search(self, query: str, top_k: int = 3) -> List[Document]:
        """Return mock documents"""
        return [
            Document(id="1", content="Sample document 1", score=0.95),
            Document(id="2", content="Sample document 2", score=0.87),
        ]
```

### Test Example

```python
# tests/test_chat_with_mock_llm.py

import pytest
from app.providers.llm_mock_provider import MockLLMProvider
from app.services.chat_service import ChatService

@pytest.fixture
def mock_llm():
    return MockLLMProvider()

@pytest.mark.asyncio
async def test_answer_question_with_mock_llm(mock_llm):
    """Test chat service with mocked LLM"""
    
    service = ChatService(llm_provider=mock_llm)
    
    response = await service.answer_question("What benefits do we have?")
    
    assert "health insurance" in response.lower()
    assert response != ""
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

```python
# app/monitoring/metrics.py

class LLMMetrics:
    
    def __init__(self):
        self.calls_total = 0
        self.calls_success = 0
        self.calls_failed = 0
        self.response_times = []
        self.token_usage = []
    
    def record_call(self, duration: float, tokens: int, success: bool):
        """Record LLM call metrics"""
        
        self.calls_total += 1
        self.response_times.append(duration)
        self.token_usage.append(tokens)
        
        if success:
            self.calls_success += 1
        else:
            self.calls_failed += 1
    
    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def error_rate(self) -> float:
        if self.calls_total == 0:
            return 0.0
        return (self.calls_failed / self.calls_total) * 100
    
    @property
    def avg_token_usage(self) -> float:
        if not self.token_usage:
            return 0.0
        return sum(self.token_usage) / len(self.token_usage)
```

### Alert Rules

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error Rate | > 5% | Page on-call |
| Avg Response Time | > 15s | Investigate LLM load |
| Token Usage | > 90% of quota | Notify team |
| 4xx errors | > 10/min | Check authentication |
| 5xx errors | > 5/min | Check LLM availability |

### Alert Configuration

```python
# app/monitoring/alerts.py

class LLMAlertManager:
    
    async def check_slos(self, metrics: LLMMetrics):
        """Check SLOs and send alerts"""
        
        if metrics.error_rate > 5.0:
            await self.alert_critical(
                f"High LLM error rate: {metrics.error_rate:.1f}%"
            )
        
        if metrics.avg_response_time > 15.0:
            await self.alert_warning(
                f"High LLM latency: {metrics.avg_response_time:.1f}s"
            )
        
        if metrics.avg_token_usage > 1500:
            await self.alert_info(
                f"High avg token usage: {metrics.avg_token_usage:.0f} tokens"
            )
```

---

## FAQ

### Q: Why is my document preview taking 30 seconds?

**A**: LLM metadata extraction is slow for long documents.

Solutions:
1. Reduce document to first 5000 characters: `document[:5000]`
2. Set `LLM_SERVER_TIMEOUT=60` (increase patience)
3. Use `Direct Ingest` instead of preview (skip metadata extraction)

---

### Q: Should I cache LLM responses?

**A**: Yes, strongly recommended!

```python
# Cache identical questions
response = await cache_service.get_or_call(
    query="What are benefits?",
    user_context={"country": "Brazil", "role": "Employee"},
    llm_call_func=llm_provider.answer,
)
```

Expected savings: 40-60% reduction in LLM API calls.

---

### Q: What if LLM returns hallucinated answer?

**A**: Always verify against source documents:

```python
# ✅ Good: Show sources
response = {
    "answer": llm_response,
    "source_documents": documents,  # Source of truth
    "confidence": 0.85,
}

# ❌ Bad: LLM answer without sources
response = {"answer": llm_response}
```

Users can fact-check by reading sources.

---

### Q: Can I use cheaper LLM models?

**A**: Yes, but with tradeoffs:

| Model | Cost | Speed | Quality |
|-------|------|-------|---------|
| gpt-4 | $$ | Slow | Excellent |
| gpt-35-turbo | $ | Fast | Good |
| text-davinci-003 | $ | Medium | Medium |

Recommendation: Use `gpt-35-turbo` for chat, `gpt-4` for complex extraction.

---

### Q: How long are LLM responses cached?

**A**: Configurable, default 24 hours:

```env
LLM_CACHE_TTL_SECONDS=86400  # 24 hours
```

Shorter cache = fresher answers but more API calls.
Longer cache = more savings but stale responses.

---

### Q: What's the difference between timeout and rate limiting?

**A**:

| Issue | Cause | HTTP Code | Retry? |
|-------|-------|-----------|--------|
| Timeout | Server took too long | 504 | Yes ✅ |
| Rate Limit | Too many requests | 429 | Yes ✅ (with backoff) |
| Auth Error | Wrong credentials | 401 | No ❌ |
| Bad Request | Invalid format | 400 | No ❌ |

---

## Related Documentation

- [CONFIG_KEYS.md](CONFIG_KEYS.md) - LLM configuration reference
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General backend troubleshooting
- [RUN_LOCAL_COMPLETE_GUIDE.md](RUN_LOCAL_COMPLETE_GUIDE.md) - Set up LLM locally

---

**Need Help?**

- Azure OpenAI Docs: https://learn.microsoft.com/azure/cognitive-services/openai/
- OpenAI API Docs: https://platform.openai.com/docs/
- Team Slack: #backend-api-support
