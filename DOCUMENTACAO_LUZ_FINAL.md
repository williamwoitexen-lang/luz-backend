# Plataforma Luz - Documentação Consolidada

**Versão do documento:** 1.0 + Backend Atualizado  
**Data de Atualização:** 05 de Fevereiro de 2026  
**Status:** ✅ Consolidado (com Backend detalhado)  
**Público-alvo:** Cliente / Stakeholders / Times Técnicos  
**Escopo:** Visão da solução, fluxos, APIs e guias de integração  

**Observação:** O Capítulo 9 (Backend) foi atualizado com exemplos técnicos, retry com backoff e proxy SSE.

---

## Sumário

1. [Objetivo e escopo](#1-objetivo-e-escopo)
2. [Visão geral da solução](#2-visão-geral-da-solução)
3. [Arquitetura da solução](#3-arquitetura-da-solução)
4. [Componentes do sistema](#4-componentes-do-sistema)
5. [Fluxos principais](#5-fluxos-principais)
6. [Integração via APIs](#6-integração-via-apis)
7. [Segurança e controle de acesso](#7-segurança-e-controle-de-acesso)
8. [Frontend (Angular) - guia de implementação](#8-frontend-angular---guia-de-implementação)
9. [Backend (FastAPI) - guia de implementação](#9-backend-fastapi---guia-de-implementação)
10. [Serviço de IA/LLM](#10-serviço-de-iallm)
11. [Dados e persistência](#11-dados-e-persistência)
12. [Configuração e deployment](#12-configuração-e-deployment)
13. [Troubleshooting e operação](#13-troubleshooting-e-operação)
14. [Apêndices](#14-apêndices)

---

# 1. Objetivo e escopo

Este documento consolida as documentações de Backend, Frontend e Serviço de IA (LLM/RAG) do projeto Luz, com foco em entendimento do cliente e em integração ponta a ponta.

## Inclui:

- Visão funcional da solução e principais capacidades
- Fluxos principais (login, chat, ingestão/gestão de documentos e métricas)
- Resumo dos componentes e integrações com serviços Azure
- APIs expostas e como consumi-las (com exemplos)
- Segurança (autenticação, RBAC e guardrails)
- Guias técnicos resumidos por componente

## Não inclui (neste momento):

- Governança de conteúdo e processo de curadoria de documentos
- Custos e dimensionamento financeiro (dependem de quota e perfil de uso)

---

# 2. Visão geral da solução

**Luz** é uma plataforma de Assistente de RH com base de conhecimento corporativa. Usuários autenticados consultam a solução via chat; as respostas são geradas por IA e podem utilizar documentos oficiais (RAG), respeitando controle de acesso (RBAC).

## 2.1 Para quem é

- **Colaboradores:** tirar dúvidas de RH com rapidez e padronização
- **Gestores e RH:** analisar métricas de uso/satisfação e manter a base documental atualizada
- **Administradores:** publicar documentos com permissões e acompanhar impacto

## 2.2 O que o usuário final vê

- Login corporativo (SSO/Azure Entra ID)
- Chat com respostas em tempo real (streaming) ou em resposta única (JSON), dependendo do endpoint configurado
- Histórico de conversas
- Gestão de documentos: upload, versionamento, ativação/desativação e filtros por metadados
- Dashboard com KPIs (volume, tempo de resposta, avaliação)

## 2.3 Capacidades de IA

- **RAG:** busca vetorial + semântica em documentos indexados no Azure AI Search
- **RBAC na busca:** filtro por role_id (cargo/nível), país e cidade
- **Agentes especializados:** HR (com documentos), SMART (metas), IDP/PDI (70/20/10) e General (saudações/fallback)
- **Detecção automática de idioma** (PT/ES/EN) com cache por sessão
- **Memória conversacional** por sessão com janela e TTL
- **Streaming SSE** para UX de resposta em tempo real

## 2.4 Stack (resumo)

| Camada | Tecnologias / Serviços |
|--------|------------------------|
| **Frontend** | Angular (TypeScript), @elxjs/ui, ng2-charts/Chart.js, ngx-markdown, ngx-translate |
| **Backend (API)** | FastAPI + Python 3.11, MSAL (Azure Entra ID), SQL Server (Azure), Azure Blob Storage |
| **Serviço de IA/LLM** | FastAPI + Python 3.11, LangGraph, Azure OpenAI (gpt-4o-mini), Azure AI Search (vetores) |
| **Infra** | Docker/Docker Compose; Azure Container Apps (produção) |

---

# 3. Arquitetura da Solução

(Este capítulo está reservado para a arquitetura oficial — diagramas, decisões e visão de infraestrutura a serem inseridos posteriormente.)

---

# 4. Componentes do sistema

A solução é composta por três serviços principais e dependências de dados/infraestrutura.

## 4.1 Frontend (Angular)

Aplicação web onde o usuário interage com o chat, administra documentos e visualiza dashboards. Renderiza respostas em Markdown e suporta múltiplos idiomas.

## 4.2 Backend (FastAPI)

API que centraliza autenticação (Azure Entra ID), gerencia documentos (SQL + Blob), persiste conversas e integra com o serviço de IA.

## 4.3 Serviço de IA/LLM (FastAPI + LangGraph)

Serviço responsável por aplicar guardrails, classificar perguntas, executar agentes (HR/SMART/IDP/General) e retornar respostas. Para HR, consulta documentos via Azure AI Search com filtro RBAC e gera respostas com Azure OpenAI.

## 4.4 Dependências Azure

- **Azure Entra ID:** autenticação (OAuth2) e validação de tokens
- **Azure SQL Server:** persistência de conversas, documentos, versões e dimensões (categorias/roles/localidades)
- **Azure Blob Storage:** armazenamento de arquivos (documentos) e uploads temporários
- **Azure AI Search:** índice vetorial/semântico para busca de chunks e aplicação de RBAC
- **Azure OpenAI:** geração de respostas (LLM) e embeddings

---

# 5. Fluxos principais (do ponto de vista do usuário)

## 5.1 Login e sessão (SSO)

O usuário inicia o login no Frontend, é redirecionado para o Azure Entra ID e retorna com a sessão estabelecida via cookies HTTPOnly. Em todas as requisições subsequentes, o Frontend envia os cookies (withCredentials/credentials: 'include') e o Backend valida a sessão.

**Observação:** Algumas implementações de frontend consultam o endpoint `/me/info` para obter dados do usuário. No backend, a verificação equivalente é feita via `/api/v1/auth/status` (ou um endpoint compatível).

## 5.2 Chat com IA (pergunta e resposta)

**Fluxo recomendado (com persistência de histórico):**

1. Usuário digita a pergunta no Frontend
2. Frontend chama o Backend: `POST /api/v1/chat/question` (ou `/api/v1/chat/question/stream`, se habilitado)
3. Backend:
   - cria/recupera a conversa
   - chama o Serviço de IA/LLM (`POST /api/v1/question` ou `/api/v1/question/stream`)
   - salva pergunta/resposta no SQL Server
4. Frontend exibe a resposta, o agente selecionado e as fontes (quando aplicável)

O serviço de IA/LLM possui suporte nativo a streaming SSE. Caso o Backend exponha um endpoint proxy de streaming, o Frontend obtém streaming sem expor diretamente o serviço de IA ao navegador.

## 5.3 Gestão de documentos (base de conhecimento)

O upload segue um fluxo em duas etapas (Preview e Confirm) para permitir validação de metadados antes de indexar o conteúdo.

### Etapa 1 - PREVIEW:
- Frontend envia arquivo: `POST /api/v1/documents/ingest-preview`
- Backend extrai texto/preview, salva temporariamente e solicita sugestão de metadados via IA
- Backend retorna `temp_id` + metadados sugeridos

### Etapa 2 - CONFIRM:
- Frontend confirma metadados: `POST /api/v1/documents/ingest-confirm/{temp_id}`
- Backend processa o arquivo final, salva versão no SQL + Blob e envia conteúdo/metadata para indexação no Serviço de IA (se is_active=true)

### Regras importantes:

- Documentos com `is_active=false` ficam armazenados (SQL + Blob), mas não são enviados para o serviço de IA e não entram no chat
- Ao reativar um documento, a última versão é reindexada automaticamente no serviço de IA
- Se o texto extraído exceder 50k caracteres, o Backend trunca automaticamente para evitar falhas

## 5.4 Dashboard

O Dashboard exibe KPIs de uso (conversas, mensagens, usuários), além de gráficos como volume por assunto e distribuição de avaliações. Os dados são lidos do Backend, que consulta o SQL Server.

---

# 6. Integração via APIs

Esta seção resume os endpoints mais relevantes e fornece exemplos de payloads. Em produção, respeitar HTTPS, cookies e CORS.

## 6.1 Backend API (FastAPI)

### Principais grupos de endpoints:

| Área | Endpoints (principais) |
|------|------------------------|
| **Autenticação** | GET /api/v1/login • GET /api/v1/getatoken • GET /api/v1/logout • GET /api/v1/auth/status |
| **Chat** | POST /api/v1/chat/question • GET /api/v1/chat/conversations/{user_id} • GET /api/v1/chat/conversations/{conversation_id}/detail • DELETE /api/v1/chat/conversations/{conversation_id} • POST /api/v1/chat/{chat_id}/rate |
| **Documentos** | POST /api/v1/documents/ingest-preview • POST /api/v1/documents/ingest-confirm/{temp_id} • POST /api/v1/documents/ingest • GET /api/v1/documents • GET /api/v1/documents/{id} • GET /api/v1/documents/{id}/versions • DELETE /api/v1/documents/{id}/versions/{version} • GET /api/v1/documents/{id}/download |
| **Dados Mestres** | GET /api/v1/master-data/locations • GET /api/v1/master-data/countries • GET /api/v1/master-data/states-by-country/{country} • GET /api/v1/master-data/cities-by-country/{country} • GET /api/v1/master-data/cities-by-region/{region} • GET /api/v1/master-data/hierarchy • GET /api/v1/master-data/categories • GET /api/v1/master-data/roles |
| **Dashboard** | GET /api/v1/dashboard/* (KPIs e gráficos) |

### 6.1.1 Exemplo - enviar pergunta (JSON)

```
POST /api/v1/chat/question
Content-Type: application/json

{
  "chat_id": "session_abc123",
  "user_id": "emp_12345",
  "name": "João Silva",
  "email": "joao.silva@company.com",
  "country": "Brazil",
  "city": "Sao Carlos",
  "roles": ["Employee"],
  "department": "TI",
  "job_title": "Analista de TI",
  "collar": "white",
  "unit": "Engineering",
  "question": "Quais são os benefícios de saúde?"
}
```

**Resposta típica (campos mais comuns):**

```json
{
  "answer": "Olá, João! ...",
  "source_documents": [],
  "num_documents": 0,
  "classification": {"category": "general|hr|smart|idp", "confidence": 0.9},
  "retrieval_time": 0,
  "llm_time": 1.03,
  "total_time": 1.85,
  "total_time_ms": 1849,
  "message_id": "02353418-913e-4acc-beb8-673597ff98d7",
  "provider": "azure_openai",
  "model": "gpt-4o-mini",
  "generated_at": "2026-01-09T16:42:20Z",
  "agente": "general",
  "prompt_tokens": 419,
  "completion_tokens": 93
}
```

### 6.1.2 Exemplo - upload de documento (Preview + Confirm)

**Preview (multipart/form-data):**

```
POST /api/v1/documents/ingest-preview
Content-Type: multipart/form-data

file: documento.pdf
```

**Confirm (multipart/form-data):**

```
POST /api/v1/documents/ingest-confirm/{temp_id}
Content-Type: multipart/form-data

user_id: john_doe
min_role_level: 2
allowed_countries: Brazil,USA
allowed_cities: São Paulo
collar: white
plant_code: 123
```

## 6.2 Serviço de IA/LLM API (FastAPI)

### Endpoints principais:

| Função | Endpoint |
|--------|----------|
| Pergunta (JSON) | POST /api/v1/question |
| Pergunta (Streaming SSE) | POST /api/v1/question/stream |
| Upsert de documento no índice | POST /api/v1/documents |
| Delete de documento no índice | DELETE /api/v1/documents/{document_id} |
| Health check | GET /api/v1/health |

### 6.2.1 Exemplo - pergunta (cURL)

```bash
curl -X POST http://localhost:8001/api/v1/question \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quais sao os beneficios de saude?",
    "user_id": "emp_12345",
    "name": "Joao Silva",
    "country": "Brazil",
    "chat_id": "session_abc123",
    "job_title": "Analista de TI",
    "role_id": 1,
    "city": "Curitiba",
    "email": "joao.silva@company.com"
  }'
```

### 6.2.2 Exemplo - streaming SSE

O streaming segue o padrão Server-Sent Events (SSE), com eventos como status, document_retrieved e answer_chunk.

```
POST /api/v1/question/stream
Accept: text/event-stream
Content-Type: application/json

{ ... payload ... }

event: status
data: {"step":"retrieval","message":"Buscando documentos..."}

event: answer_chunk
data: {"delta":"Os benefícios incluem..."}

event: answer_complete
data: {"answer":"Resposta final completa"}
```

---

# 7. Segurança e controle de acesso

## 7.1 Autenticação (Azure Entra ID)

O Backend integra com Azure Entra ID (OAuth2/MSAL). O token de sessão é armazenado em cookie HTTPOnly (Secure + SameSite=None), e um middleware valida a assinatura do JWT contra as chaves públicas (JWKS) do Azure.

## 7.2 Autorização (RBAC) em três dimensões

O serviço de IA aplica RBAC na recuperação de documentos (Azure AI Search) usando filtros OData construídos a partir do contexto do usuário.

- **Role (role_id):** 15 níveis padrão + Admin (0) e Guest (99)
- **Country:** valida contra `allowed_countries` do documento (ou universal quando vazio)
- **City:** valida contra `allowed_cities` do documento (ou universal quando vazio)

### Roles pré-preenchidas (exemplos):

| role_id | Nome |
|---------|------|
| 1 | Analista |
| 4 | Coordenador |
| 8 | Gerente |
| 12 | Presidente |
| 15 | Vice-Presidente |

**Exemplo de filtro OData gerado (Gerente em Curitiba/Brazil):**

```
allowed_roles/any(r: r eq 8)
and (allowed_cities/any(ct: ct eq 'Curitiba') or not allowed_cities/any())
and (allowed_countries/any(c: c eq 'Brazil') or not allowed_countries/any())
```

### 7.2.1 RBAC — Quarta dimensão e nomenclatura de campos

Além das três dimensões documentadas (cargo, país, cidade), o sistema de RBAC possui uma quarta dimensão: endereço/unidade (`allowed_addresses` no índice do Azure Search). Isso permite restringir documentos a unidades físicas específicas dentro de uma mesma cidade.

O filtro OData completo gerado pelo serviço de IA, com as quatro dimensões, tem o formato:

```
allowed_roles/any(r: r eq 8)
and (allowed_countries/any(c: c eq 'brazil') or not allowed_countries/any())
and (allowed_cities/any(c: c eq 'sao carlos') or not allowed_cities/any())
and (allowed_addresses/any(a: a eq 23) or not allowed_addresses/any())
```

**Regra geral de filtragem:** lista vazia em qualquer dimensão significa acesso universal para aquela dimensão. Admin (role_id=0) bypassa todos os filtros.

**Nomenclatura de campos por contexto — atenção para não confundir:**

| Contexto | Campo na API | Campo interno |
|----------|--------------|---------------|
| Request /question | location_id | address_id (UserContext) |
| Upload de documento | allowed_location_ids | allowed_addresses (Azure Search) |

O mapeamento ocorre em `api/v1/question.py` ao construir o `UserContext` (`address_id=request.location_id`). Países e cidades são sempre normalizados para lowercase sem acento antes de qualquer comparação ("São Carlos" → "sao carlos"), via `utils/rbac_normalizer.py`.

## 7.3 Guardrails (segurança do prompt e abuso)

Antes do pipeline de agentes, o serviço de IA executa guardrails para reduzir risco operacional e ataques.

- **Rate limiting:** 5 requisições por minuto por usuário (ajustável)
- **Validação de tamanho de pergunta:** máximo 2000 caracteres
- **Sanitização:** bloqueio de null bytes e caracteres de controle
- **Detecção de prompt injection** (modo log ou block)

---

# 8. Frontend (Angular) - Guia de Implementação

## 8.1 Estrutura recomendada (Core / Shared / Features)

- **Core:** serviços singleton, interceptors, guards e layout
- **Shared:** componentes reutilizáveis, pipes e diretivas
- **Features:** módulos de negócio (auth, chat, documentos, dashboard) com lazy loading

```
src/
  app/
    core/
    shared/
    features/
      auth/
      chat/
      documentos/
      dashboard/
  assets/
  environments/
```

## 8.2 Chat com streaming SSE - exemplo (Fetch + ReadableStream)

Exemplo de serviço que consome SSE via Fetch API e emite eventos em um Observable, mantendo cookies com `credentials: 'include'`.

```typescript
// chat-stream.service.ts (exemplo)
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type StreamEvent =
  | { type: 'status'; data: any }
  | { type: 'document_retrieved'; data: any }
  | { type: 'answer_chunk'; data: { delta: string } }
  | { type: 'answer_complete'; data: any };

@Injectable({ providedIn: 'root' })
export class ChatStreamService {
  streamQuestion(url: string, payload: any): Observable<StreamEvent> {
    return new Observable<StreamEvent>((observer) => {
      const controller = new AbortController();

      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
        body: JSON.stringify(payload),
        credentials: 'include',
        signal: controller.signal,
      })
        .then(async (res) => {
          if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
          const reader = res.body.getReader();
          const decoder = new TextDecoder('utf-8');
          let buffer = '';

          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            const parts = buffer.split('\n\n');
            buffer = parts.pop() ?? '';

            for (const part of parts) {
              const lines = part.split('\n');
              const eventLine = lines.find((l) => l.startsWith('event:')) ?? 'event: message';
              const dataLine = lines.find((l) => l.startsWith('data:')) ?? 'data: {}';

              const eventType = eventLine.replace('event:', '').trim();
              const raw = dataLine.replace('data:', '').trim();

              let data: any = raw;
              try { data = JSON.parse(raw); } catch {}

              observer.next({ type: eventType as any, data } as StreamEvent);
            }
          }

          observer.complete();
        })
        .catch((err) => observer.error(err));

      return () => controller.abort();
    });
  }
}
```

## 8.3 Upload de documento (Preview + Confirm) - exemplo

```typescript
// documents.service.ts (exemplo)
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class DocumentsService {
  constructor(private http: HttpClient) {}

  ingestPreview(apiUrl: string, file: File) {
    const form = new FormData();
    form.append('file', file);
    return this.http.post(`${apiUrl}/api/v1/documents/ingest-preview`, form, { withCredentials: true });
  }

  ingestConfirm(apiUrl: string, tempId: string, metadata: Record<string, any>) {
    const form = new FormData();
    Object.entries(metadata).forEach(([k, v]) => form.append(k, String(v)));
    return this.http.post(`${apiUrl}/api/v1/documents/ingest-confirm/${tempId}`, form, { withCredentials: true });
  }
}
```

## 8.4 i18n e Markdown

- **i18n:** @ngx-translate/core com arquivos JSON em `src/assets/i18n` (pt/en/es)
- **Markdown:** ngx-markdown para renderizar respostas do chat com formatação rica
- A escolha de idioma pode ser persistida no localStorage

## 8.5 Interceptors e Guards (exemplos)

**CredentialsInterceptor:**

```typescript
// credentials.interceptor.ts (exemplo)
import { HttpInterceptorFn } from '@angular/common/http';

export const credentialsInterceptor: HttpInterceptorFn = (req, next) =>
  next(req.clone({ withCredentials: true }));
```

**ErrorInterceptor (401):**

```typescript
// error.interceptor.ts (exemplo)
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) =>
  next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401) window.location.href = '/login';
      return throwError(() => err);
    })
  );
```

---

# 9. Backend (FastAPI) - Guia de Implementação

## 9.1 Responsabilidades Principais

✅ Autenticação e sessão (Azure Entra ID / MSAL)  
✅ Persistência de conversas e documentos em SQL Server  
✅ Armazenamento de arquivos em Azure Blob Storage (permanente + temporário)  
✅ Orquestração de ingestão: extração de texto, metadados e envio ao serviço de IA  
✅ Camada de APIs consumida pelo Frontend (CORS + cookies)  

## 9.2 Estrutura de Pastas (Resumo)

```
app/
  main.py                          # FastAPI principal
  core/
    config.py                      # Configurações e KeyVault
    sqlserver.py                   # Conexão SQL Server
  providers/
    auth_msal.py                   # Azure Entra ID
    llm_server.py                  # Integração LLM
    format_converter.py            # Conversão de formatos (PDF/DOCX/XLSX)
    storage.py                     # Azure Blob Storage
    metadata_extractor.py          # Extração de metadados com IA
  routers/
    auth.py                        # Endpoints de autenticação
    documents.py                   # Endpoints de documentos
    chat.py                        # Endpoints de chat
    master_data.py                 # Endpoints de dados mestres
    dashboard.py                   # Endpoints de dashboard
    job_title_roles.py             # Endpoints de mapeamento cargo-papel
  services/
    document_service.py            # Orquestração de ingestão
    conversation_service.py        # Gerenciamento de conversas
    sqlserver_documents.py         # Operações diretas SQL
    job_title_role_service.py      # Lógica de cargo-papel
  tasks/
    cleanup_temp_uploads.py        # Limpeza assincronada de uploads temporários
```

## 9.3 Retry em Chamadas ao Serviço de IA (Exemplo Prático)

Implementar retry automático com backoff exponencial garante resiliência em caso de timeouts ou erros temporários do serviço de IA.

```python
# llm_client.py
import time
import requests
import logging

logger = logging.getLogger(__name__)

def post_with_retry(
    url: str,
    json_payload: dict,
    timeout_s: int,
    max_retries: int = 3,
    base_delay_s: float = 1.0,
) -> dict:
    """
    Envia POST com retry automático (exponential backoff).
    
    Retries em:
    - Erros de conexão (timeout, connection refused)
    - Erros 5xx (server error)
    
    Não retries em:
    - 4xx (erro do client)
    
    Args:
        url: URL do endpoint
        json_payload: Payload JSON
        timeout_s: Timeout por tentativa (segundos)
        max_retries: Número máximo de tentativas
        base_delay_s: Delay inicial (dobra a cada retry)
    
    Returns:
        Resposta JSON do servidor
        
    Raises:
        Exception: Se falhar após max_retries tentativas
    """
    delay = base_delay_s
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"[Attempt {attempt}/{max_retries}] POST {url}")
            
            resp = requests.post(url, json=json_payload, timeout=timeout_s)

            # Não retry em 4xx
            if 400 <= resp.status_code < 500:
                resp.raise_for_status()

            # Retry em 5xx
            if 500 <= resp.status_code < 600:
                raise RuntimeError(f"Server error {resp.status_code}")

            resp.raise_for_status()
            logger.debug(f"[Success] Status {resp.status_code}")
            return resp.json()

        except (requests.Timeout, requests.ConnectionError) as e:
            last_exception = e
            logger.warning(f"[Attempt {attempt}] Connection error: {str(e)[:50]}")
            
        except Exception as e:
            last_exception = e
            logger.warning(f"[Attempt {attempt}] Error: {str(e)[:50]}")

        if attempt == max_retries:
            logger.error(f"[Failed] Exceeded max retries ({max_retries})")
            raise last_exception

        logger.info(f"[Retry] Waiting {delay}s before attempt {attempt + 1}...")
        time.sleep(delay)
        delay *= 2  # Exponential backoff

    raise last_exception
```

**Uso:**

```python
# Em document_service.py
try:
    response = post_with_retry(
        url=f"{LLM_SERVER_URL}/api/v1/documents",
        json_payload={"document_id": doc_id, "content": content},
        timeout_s=30,
        max_retries=3,
        base_delay_s=1.0,
    )
    logger.info(f"Document {doc_id} indexed successfully")
except Exception as e:
    logger.error(f"Failed to index document {doc_id}: {e}")
    raise
```

## 9.4 Proxy de Streaming SSE (Opcional)

Para manter a autenticação no Backend e proxiar streaming do serviço de IA ao Frontend:

```python
# routers/chat.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import httpx
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/api/v1/chat/question/stream")
async def chat_question_stream(request: Request):
    """
    Proxy de streaming SSE.
    
    Frontend → Backend → Serviço IA
    
    Mantém autenticação Backend (JWT validado) e formata eventos para Frontend.
    Importante: adicionar autenticação antes de chamar o serviço de IA.
    """
    # Validar sessão do usuário (middleware faz isso, mas podemos explícito):
    user_id = request.state.user.get('sub')  # JWT sub claim
    if not user_id:
        return {"error": "Unauthorized"}, 401

    payload = await request.json()

    async def event_generator():
        """
        Generator que proxia events do serviço de IA.
        Envia cada chunk conforme recebe, mantendo baixa latência.
        """
        try:
            # Chamar serviço de IA com timeout adequado
            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream(
                    "POST",
                    f"{LLM_SERVER_URL}/api/v1/question/stream",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {os.getenv('LLM_SERVER_TOKEN', '')}",
                        "Accept": "text/event-stream",
                    },
                ) as response:
                    # Validar status HTTP
                    if response.status_code != 200:
                        logger.error(f"LLM Server error: {response.status_code}")
                        yield f"event: error\ndata: {{'message': 'LLM unavailable'}}\n\n"
                        return

                    # Proxiar cada chunk
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            yield chunk
                            
        except httpx.TimeoutException:
            logger.error("LLM Server timeout")
            yield f"event: error\ndata: {{'message': 'Request timeout'}}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            yield f"event: error\ndata: {{'message': '{str(e)[:50]}'}}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Uso no Frontend:**

```typescript
// chat.component.ts
this.chatService.streamQuestion(payload).subscribe({
  next: (event) => {
    if (event.type === 'answer_chunk') {
      this.responseText += event.data.delta;  // Efeito de digitação
    } else if (event.type === 'answer_complete') {
      this.finalizarResposta();
    }
  },
  error: (err) => console.error('Stream error:', err),
});
```

## 9.5 Validação de Autenticação (Middleware)

```python
# core/middleware.py
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    """
    Valida JWT do cookie HTTPOnly em toda requisição.
    """
    # Rotas públicas
    public_routes = ["/api/v1/login", "/api/v1/getatoken", "/api/v1/logout"]
    if request.url.path in public_routes:
        return await call_next(request)

    # Extrair JWT do cookie
    token = request.cookies.get("jwt")
    if not token:
        logger.warning(f"Missing JWT: {request.url.path}")
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        # Validar JWT assinatura + expiração
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=["HS256"])
        request.state.user = payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT expired")
        return JSONResponse({"error": "Token expired"}, status_code=401)
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT: {e}")
        return JSONResponse({"error": "Invalid token"}, status_code=401)

    response = await call_next(request)
    return response
```

## 9.6 Rota Completa de Chat (End-to-End)

```python
# routers/chat.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatRequest(BaseModel):
    chat_id: str
    user_id: str
    name: str
    email: str
    country: str
    city: str
    job_title: str
    question: str

class ChatResponse(BaseModel):
    message_id: str
    answer: str
    agent: str
    total_time_ms: float
    tokens: dict

@router.post("/api/v1/chat/question", response_model=ChatResponse)
async def chat_question(request: ChatRequest, req: Request):
    """
    Rota completa de chat: orquestra pergunta do usuário até resposta final.
    
    Fluxo:
    1. Validar autenticação (JWT do cookie)
    2. Buscar/criar conversa no SQL
    3. Chamar serviço de IA (com retry)
    4. Salvar pergunta e resposta no SQL
    5. Retornar resposta formatada ao frontend
    """
    # 1. Validação (middleware já feito, mas replicamos explicitamente)
    user_id = req.state.user.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 2. Criar/recuperar conversa
    try:
        conversation = await conversation_service.get_or_create(
            chat_id=request.chat_id,
            user_id=request.user_id,
            title=request.question[:100]  # Primeiro 100 chars como título
        )
        logger.info(f"Chat {request.chat_id}: Using conversation {conversation.conversation_id}")
    except Exception as e:
        logger.error(f"Failed to fetch conversation: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    
    # 3. Chamar serviço de IA (com retry já encapsulado)
    try:
        aia_response = await llm_client.post_with_retry(
            url=f"{LLM_SERVER_URL}/api/v1/question",
            json_payload={
                "question": request.question,
                "user_id": request.user_id,
                "chat_id": request.chat_id,
                "name": request.name,
                "country": request.country,
                "city": request.city,
                "job_title": request.job_title,
                "email": request.email,
            },
            timeout_s=30,
            max_retries=3
        )
        logger.info(f"LLM response: agent={aia_response.get('agent')}, tokens={aia_response.get('completion_tokens')}")
    except Exception as e:
        logger.error(f"LLM call failed after retries: {e}")
        # Fallback: resposta genérica
        aia_response = {
            "answer": "Desculpe, não consegui processar sua pergunta. Tente novamente.",
            "agent": "fallback",
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_time_ms": 0
        }
    
    # 4. Salvar no SQL (pergunta + resposta)
    message_id = str(uuid.uuid4())
    try:
        await conversation_service.save_message(
            message_id=message_id,
            conversation_id=conversation.conversation_id,
            user_id=request.user_id,
            role="user",
            content=request.question,
        )
        
        await conversation_service.save_message(
            message_id=str(uuid.uuid4()),
            conversation_id=conversation.conversation_id,
            user_id=request.user_id,
            role="assistant",
            content=aia_response["answer"],
            tokens_used=aia_response.get("completion_tokens", 0),
            model=aia_response.get("model", "gpt-4o-mini"),
            total_time=aia_response.get("total_time_ms", 0) / 1000.0,
        )
        logger.info(f"Messages saved for conversation {conversation.conversation_id}")
    except Exception as e:
        logger.error(f"Failed to save messages: {e}")
        # Não falha a resposta se o salvamento falhar (graceful degradation)
    
    # 5. Retornar resposta
    return ChatResponse(
        message_id=message_id,
        answer=aia_response.get("answer", ""),
        agent=aia_response.get("agent", "general"),
        total_time_ms=aia_response.get("total_time_ms", 0),
        tokens={
            "prompt": aia_response.get("prompt_tokens", 0),
            "completion": aia_response.get("completion_tokens", 0)
        }
    )
```

## 9.7 Upload e Ingestão de Documentos (Preview + Confirm)

```python
# routers/documents.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import tempfile
import os
import shutil

router = APIRouter()

@router.post("/api/v1/documents/ingest-preview")
async def ingest_preview(file: UploadFile = File(...), req: Request = None):
    """
    Etapa 1: Preview de upload
    - Validar arquivo (tipo, tamanho)
    - Extrair preview de texto
    - Salvar temporariamente em blob
    - Solicitar sugestão de metadados via IA
    - Retornar temp_id para etapa 2
    """
    user_id = req.state.user.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validar arquivo
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_FILE_SIZE} bytes)")
    
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX supported")
    
    # Extrair texto (usando format_converter provider)
    try:
        text_content = await format_converter.extract_text(file_content, file.content_type)
        if len(text_content) > 50000:
            text_content = text_content[:50000]  # Truncar
        preview = text_content[:500] + "..." if len(text_content) > 500 else text_content
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise HTTPException(status_code=422, detail="Could not extract text from file")
    
    # Salvar temporariamente em blob
    temp_id = str(uuid.uuid4())
    try:
        blob_path = f"temp-uploads/{user_id}/{temp_id}/{file.filename}"
        await storage.upload_blob(blob_path, file_content)
        logger.info(f"Temp file uploaded: {blob_path}")
    except Exception as e:
        logger.error(f"Blob upload failed: {e}")
        raise HTTPException(status_code=500, detail="Storage error")
    
    # Solicitar sugestão de metadados via IA
    try:
        metadata_suggestion = await llm_client.suggest_metadata(
            filename=file.filename,
            text_preview=preview,
            user_id=user_id
        )
    except Exception as e:
        logger.warning(f"Metadata suggestion failed (graceful degradation): {e}")
        metadata_suggestion = {
            "category": "general",
            "min_role_level": 1,
            "allowed_countries": [],
            "allowed_cities": []
        }
    
    return {
        "temp_id": temp_id,
        "filename": file.filename,
        "preview": preview,
        "suggested_metadata": metadata_suggestion
    }


@router.post("/api/v1/documents/ingest-confirm/{temp_id}")
async def ingest_confirm(
    temp_id: str,
    user_id: str,
    category_id: int = 1,
    min_role_level: int = 1,
    allowed_countries: str = "",
    allowed_cities: str = "",
    is_active: bool = True,
    req: Request = None
):
    """
    Etapa 2: Confirmação e indexação
    - Buscar arquivo temporário
    - Criar documento na base (SQL)
    - Criar versão (SQL + Blob permanente)
    - Enviar para indexação no serviço de IA
    - Deletar arquivo temporário
    """
    current_user = req.state.user.get('sub')
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Buscar arquivo temporário (metadata do SQL)
        temp_file = await sqlserver_documents.get_temp_upload(temp_id)
        if not temp_file:
            raise HTTPException(status_code=404, detail="Temp file not found")
        
        # Criar documento
        doc_id = str(uuid.uuid4())
        doc = await sqlserver_documents.create_document(
            document_id=doc_id,
            user_id=user_id,
            filename=temp_file.filename,
            category_id=category_id,
            is_active=is_active,
        )
        
        # Criar versão
        version_id = str(uuid.uuid4())
        await sqlserver_documents.create_version(
            version_id=version_id,
            document_id=doc_id,
            user_id=user_id,
            blob_path=f"documents/{doc_id}/v1/{temp_file.filename}",
            is_current=True
        )
        
        # Copiar do temp para permanente
        await storage.copy_blob(
            f"temp-uploads/{user_id}/{temp_id}/{temp_file.filename}",
            f"documents/{doc_id}/v1/{temp_file.filename}"
        )
        
        # Enviar para indexação (se ativo)
        if is_active:
            try:
                file_content = await storage.download_blob(f"documents/{doc_id}/v1/{temp_file.filename}")
                text_content = await format_converter.extract_text(
                    file_content,
                    temp_file.content_type
                )
                
                await llm_client.post_with_retry(
                    url=f"{LLM_SERVER_URL}/api/v1/documents",
                    json_payload={
                        "document_id": doc_id,
                        "content": text_content,
                        "allowed_roles": [min_role_level],
                        "allowed_countries": allowed_countries.split(",") if allowed_countries else [],
                        "allowed_cities": allowed_cities.split(",") if allowed_cities else [],
                    },
                    timeout_s=60,
                    max_retries=2
                )
                logger.info(f"Document {doc_id} indexed in LLM service")
            except Exception as e:
                logger.error(f"LLM indexing failed: {e}")
                # Não falha a criação; documento fica inativo até reindexação manual
        
        # Limpar temp
        await storage.delete_blob(f"temp-uploads/{user_id}/{temp_id}/{temp_file.filename}")
        await sqlserver_documents.delete_temp_upload(temp_id)
        
        logger.info(f"Document {doc_id} created and indexed successfully")
        return {"document_id": doc_id, "status": "active" if is_active else "inactive"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest confirm failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## 9.8 Rate Limiting e Throttling

```python
# core/rate_limiting.py
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

class RateLimiter:
    """
    Rate limiter em memória (local).
    Em produção com múltiplas instâncias, usar Redis.
    """
    def __init__(self, requests_per_minute: int = 5):
        self.requests_per_minute = requests_per_minute
        self.user_requests = defaultdict(list)  # user_id -> [timestamp, timestamp, ...]
        self.cleanup_task = None
    
    async def check_rate_limit(self, user_id: str) -> bool:
        """
        Retorna True se está dentro do limite, False se excedeu.
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)
        
        # Limpar requests antigos
        self.user_requests[user_id] = [
            ts for ts in self.user_requests[user_id]
            if ts > window_start
        ]
        
        # Verificar limite
        if len(self.user_requests[user_id]) >= self.requests_per_minute:
            return False
        
        # Adicionar novo request
        self.user_requests[user_id].append(now)
        return True
    
    async def cleanup_old_entries(self):
        """
        Limpa entries de usuários inativos (background task).
        Executar a cada 10 minutos.
        """
        while True:
            await asyncio.sleep(600)  # 10 minutos
            now = datetime.utcnow()
            window_start = now - timedelta(minutes=10)
            
            users_to_delete = []
            for user_id, requests in self.user_requests.items():
                # Se todos os requests são anteriores a 10 min, deletar user
                if all(ts <= window_start for ts in requests):
                    users_to_delete.append(user_id)
            
            for user_id in users_to_delete:
                del self.user_requests[user_id]
            
            logger.debug(f"Cleaned up {len(users_to_delete)} inactive users")

# Instância global
rate_limiter = RateLimiter(requests_per_minute=5)

# Middleware
async def rate_limit_middleware(request: Request, call_next):
    """
    Aplica rate limiting baseado em user_id do JWT.
    """
    # Rotas públicas (sem rate limit)
    public_routes = ["/api/v1/login", "/api/v1/health"]
    if request.url.path in public_routes:
        return await call_next(request)
    
    # Extrair user_id
    user_id = request.state.user.get('sub') if hasattr(request.state, 'user') else None
    if not user_id:
        user_id = request.client.host  # Fallback para IP
    
    # Verificar limite
    if not await rate_limiter.check_rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for user {user_id}")
        return JSONResponse(
            {"error": "Too many requests. Max 5 per minute."},
            status_code=429
        )
    
    return await call_next(request)
```

## 9.9 Logging Estruturado e Observabilidade

```python
# core/logging.py
import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger

def setup_logging(app_name: str = "luz-backend"):
    """
    Configura logging em JSON estruturado (pronto para observabilidade).
    Saída: STDOUT em JSON (parse por ELK/DataDog/AppInsights)
    """
    # RemoveHandler anterior
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler com JSON
    console_handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s %(exc_info)s'
    )
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    return root_logger

logger = logging.getLogger("luz-backend.routes")

# Exemplo de uso em uma rota
async def example_logged_endpoint(request: Request):
    """
    Demonstra logging estruturado com correlação.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.state.user.get('sub')
    
    logger.info(
        "Chat request received",
        extra={
            "correlation_id": correlation_id,
            "user_id": user_id,
            "endpoint": str(request.url.path),
            "method": request.method,
        }
    )
    
    try:
        # ... processar ...
        logger.info(
            "Chat request completed",
            extra={
                "correlation_id": correlation_id,
                "status": "success",
                "response_time_ms": 1234,
            }
        )
    except Exception as e:
        logger.error(
            "Chat request failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True
        )
        raise
```

## 9.10 Health Checks e Readiness

```python
# routers/health.py
from fastapi import APIRouter
from enum import Enum
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@router.get("/api/v1/health")
async def health_check():
    """
    Liveness probe: servidor está rodando?
    Resposta rápida (< 1s); não valida dependências.
    """
    return {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "luz-backend"
    }

@router.get("/api/v1/ready")
async def readiness_check():
    """
    Readiness probe: servidor está pronto para tráfego?
    Valida conexões críticas (SQL, Blob, LLM).
    Pode levar até 5s.
    """
    checks = {
        "database": await check_database(),
        "blob_storage": await check_blob_storage(),
        "llm_service": await check_llm_service(),
    }
    
    all_healthy = all(c["status"] == HealthStatus.HEALTHY for c in checks.values())
    
    status = HealthStatus.HEALTHY if all_healthy else HealthStatus.DEGRADED
    
    logger.info(f"Readiness check: {status}", extra={"checks": checks})
    
    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }

async def check_database():
    """Valida conexão com SQL Server."""
    try:
        result = await sqlserver.execute("SELECT 1")
        return {"status": HealthStatus.HEALTHY, "message": "Connected"}
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return {"status": HealthStatus.UNHEALTHY, "message": str(e)}

async def check_blob_storage():
    """Valida conexão com Azure Blob Storage."""
    try:
        # Teste de leitura de um arquivo conhecido
        await storage.list_blobs("documents/", max_results=1)
        return {"status": HealthStatus.HEALTHY, "message": "Connected"}
    except Exception as e:
        logger.error(f"Blob storage check failed: {e}")
        return {"status": HealthStatus.UNHEALTHY, "message": str(e)}

async def check_llm_service():
    """Valida conectividade com serviço de IA."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{LLM_SERVER_URL}/api/v1/health")
            if response.status_code == 200:
                return {"status": HealthStatus.HEALTHY, "message": "Connected"}
            else:
                return {"status": HealthStatus.DEGRADED, "message": f"HTTP {response.status_code}"}
    except Exception as e:
        logger.error(f"LLM service check failed: {e}")
        return {"status": HealthStatus.UNHEALTHY, "message": str(e)}
```

---

# 10. Serviço de IA/LLM (LangGraph + RAG) - Guia de Implementação

## 10.1 Pipeline (LangGraph)

Pipeline orquestrado com roteamento condicional após classificação:

```
Requisição HTTP
  → Guardrails Middleware (rate limit, sanitização)
  → History Loader (carrega histórico do backend na 1ª mensagem)
  → Language Detector (cache por sessão)
  → Classifier (hr / smart / idp / general)
      → HR Agent (RAG + RBAC)
      → Smart Agent (geração de metas)
      → IDP Agent (desenvolvimento 70/20/10)
      → General Agent (fallback)
  → Memory Update (sessão + preferências)
  → Response (JSON ou Streaming SSE)
```

## 10.1.1 Integração do History Loader com Backend

Na primeira mensagem de uma sessão, o serviço de IA pode carregar histórico recente via Backend:

```
GET {BACKEND_URL}/api/v1/chat/conversations/{chat_id}/detail
Timeout: 5s
Comportamento em falha: continua sem histórico (graceful degradation)
```

## 10.2 Classificação e Roteamento

| Categoria | Threshold (confiança) | Exemplo |
|-----------|----------------------|---------|
| hr | 0.5 | Quais são os benefícios de saúde? |
| smart | 0.7 | Quero definir meus objetivos |
| idp | 0.7 | Quero criar meu PDI |
| general | 0.8 | Olá / Obrigado |

**Stickiness (anti-oscilação):** Para trocar de agente, é necessário ~90% de confiança.

O classificador implementa um mecanismo de stickiness para evitar troca de agente entre mensagens consecutivas da mesma sessão. Para mudar de agente, o novo agente precisa atingir no mínimo 90% de confiança. Abaixo desse limiar, o sistema mantém o agente anterior ativo, mesmo que ele não seja o primeiro classificado. Esse comportamento é especialmente relevante em conversas de múltiplas mensagens, onde seguimentos naturais como "e no caso do estágio?" devem permanecer no contexto do agente que já está em uso.

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| stickiness_threshold | 0.90 | Confiança mínima para trocar de agente |
| default_category | hr | Agente ativado quando nenhum atinge o threshold |

## 10.2.1 Dois caminhos de execução independentes

O serviço de IA possui dois caminhos de execução completamente independentes, mapeados para endpoints distintos:

| Endpoint | Mecanismo | Como funciona |
|----------|-----------|---------------|
| POST /question | Grafo LangGraph compilado | Executa via `graph.ainvoke()`; todos os nodes rodam sequencialmente e o resultado é retornado como JSON ao final |
| POST /question/stream | Gerador manual SSE | Executa node por node de forma explícita; cada evento é enviado ao cliente em tempo real via Server-Sent Events |

**Impacto prático para manutenção:** Qualquer novo node adicionado ao pipeline precisa ser registrado em dois lugares — no grafo (`graph/builder.py`) e no gerador SSE (`api/v1/question.py`). Registrar apenas em um dos dois faz o novo comportamento funcionar somente em um dos endpoints, sem erro explícito.

## 10.3 Agentes Especializados

| Agente | Usa documentos | Temperature | Max tokens | Quando usar |
|--------|---|---|---|---|
| HR | Sim | 0.2 | 800 | Consultas de RH com base documental (RAG) |
| SMART | Não | 0.7 | 500 | Criação/refinamento de metas SMART |
| IDP/PDI | Não | 0.7 | 600 | Plano de desenvolvimento 70/20/10 |
| General | Não | 0.7 | 300 | Saudações, agradecimentos e fallback |

## 10.3.1 Agente HR — Quality Tiers

Quando o agente HR recupera documentos do Azure AI Search, ele avalia a qualidade dos resultados antes de gerar a resposta. O comportamento varia conforme o score de relevância dos documentos encontrados:

| Tier | Score máximo | Comportamento |
|------|---|---|
| 1 | ≥ 0.70 | Resposta normal com base nos documentos |
| 2 | 0.50 – 0.69 | Resposta com ressalva de que as informações podem estar incompletas |
| 3 | 0.35 – 0.49 | Redireciona para o General Agent (documentos insuficientes) |
| 4 | < 0.35 | Redireciona para o General Agent (nenhum documento relevante) |

O threshold de filtragem (`document_score_threshold = 0.35`) é configurável em `config/agents/hr_config.py`. Documentos abaixo desse valor são descartados antes da avaliação do tier.

## 10.3.2 Agente IDP/PDI — Detalhamento

O agente IDP guia o usuário na construção de um Plano de Desenvolvimento Individual (PDI) com base na metodologia 70/20/10:

- **70%** — Experiência prática (desafios e projetos no trabalho)
- **20%** — Exposição social (mentores, feedbacks, observação de líderes)
- **10%** — Educação formal (cursos, certificações, leituras)

O agente também considera as Competências Core da Electrolux na formulação do plano: Energy, Openness, Agility e Growth.

**Fluxo em 3 etapas com aprovação obrigatória:**

| Etapa | Nome | O que acontece |
|-------|------|---------------|
| 1 | Discovery | Levanta áreas de desenvolvimento com base nas avaliações de performance do usuário |
| 2 | Refinement | Aplica o modelo 70/20/10 e as competências core; o agente não avança sem confirmação explícita do usuário |
| 3 | Action Plan | Compila o documento final formatado, pronto para ser copiado no sistema de RH |

**Integração com WeaknessService:** Antes de executar, o agente IDP consulta o backend para obter as áreas de melhoria identificadas nas avaliações de performance do usuário (`POST /api/v1/e42/evaluation/weaknesses-only`). Esse dado alimenta a etapa de Discovery. A consulta tem cache local de 8 horas; em caso de falha, o agente continua sem os dados de avaliação (graceful degradation).

## 10.3.3 Query Enhancer (Exclusivo do Agente HR)

Antes do agente HR executar a busca vetorial, o pipeline passa por um node de aprimoramento de query. Este node usa o histórico da conversa para resolver ambiguidades e referências implícitas na pergunta do usuário:

- Referências como "isso", "e o outro", "também" são resolvidas para termos explícitos
- A query aprimorada é usada exclusivamente para a busca no Azure AI Search; a pergunta original é preservada na resposta ao usuário
- O resultado inclui os campos `original_query`, `enhanced_query` e `enhancement_applied`

| Característica | Detalhe |
|---|---|
| Quando executa | Somente quando o agente classificado é HR (~25% do tráfego total) |
| Impacto de latência | Evita ~400ms para SMART, IDP e General (node não é invocado) |
| Cache | Por sessão, chave composta por query + language |
| Feature flag | QUERY_ENHANCEMENT_ENABLED (desabilita o node sem alterar código) |

## 10.4 RAG, Chunking e Índice (Azure AI Search)

Para consultas HR, o serviço recupera chunks no Azure AI Search. Documentos são divididos em chunks (ex.: 500 caracteres com overlap) e indexados com embeddings e metadados RBAC.

**Campos relevantes no índice (exemplos):**
- `content`, `content_vector` (embedding 1536 dimensões), `document_id`, `chunk_index`, `source_file`
- `allowed_roles` (Collection(Int32)), `allowed_countries` (Collection(String)), `allowed_cities` (Collection(String)), `category_id` (Int32)

## 10.5 Memória Conversacional

O sistema possui dois mecanismos de memória distintos e independentes:

### 10.5.1 Memória de Sessão

Cache em memória local, identificado por `chat_id`. Armazena o histórico de mensagens da conversa corrente, o idioma detectado, os últimos documentos recuperados e as queries aprimoradas. Descartado ao fim do TTL.

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| window_size | 15 | Mensagens mantidas na janela |
| session_ttl | 3600s | TTL da sessão (1 hora) |
| cleanup_interval | 300s | Intervalo de limpeza automática (5 min) |
| max_sessions | 1000 | Limite de sessões simultâneas |

### 10.5.2 Memória de Longo Prazo

Preferências do usuário que persistem entre diferentes chats, identificadas por `user_id` e armazenadas no Backend. Não deve ser confundida com o histórico de conversa.

**Ordem de prioridade na aquisição (3 fontes):**

1. Campo `memory` incluído no body do request (o Backend envia este campo apenas no primeiro request de chats novos)
2. Cache local com TTL de 8 horas (evita consultas repetidas ao Backend)
3. GET ao endpoint do Backend (fallback quando cache expirou e campo não veio no request)

**Memory Editor (atualização em background):** Após o evento `complete` ser enviado ao usuário, o sistema avalia se a conversa gerou informações relevantes para atualizar as preferências de longo prazo. O editor executa de forma assincronada — nunca bloqueia a resposta. O threshold de confiança para acionar a atualização é de 95% (conservador por design). Por segurança, o editor bloqueia tentativas de armazenar permissões, roles ou instruções de manipulação do sistema.

---

# 11. Dados e Persistência

O Backend persiste conversas, mensagens, documentos e versões em SQL Server. Os arquivos ficam no Azure Blob Storage, e os chunks indexados ficam no Azure AI Search via serviço de IA.

## 11.1 Entidades Principais (Visão Resumida)

| Entidade | Descrição | Onde fica |
|----------|-----------|-----------|
| conversations | Cabeçalho da conversa (título, status, rating) | SQL Server |
| conversation_messages | Mensagens do usuário e da IA, com métricas/tokens | SQL Server |
| documents | Documento lógico e metadados (RBAC, categoria, status) | SQL Server |
| versions | Versões do arquivo e caminho no blob | SQL Server + Blob |
| chunks | Conteúdo fragmentado com embeddings e RBAC | Azure AI Search (índice vetorial) |

## 11.2 DDL (Opcional - Referência)

Recorte de schema (exemplos):

```sql
-- conversations (resumo)
CREATE TABLE conversations (
  conversation_id NVARCHAR(36) PRIMARY KEY,
  user_id NVARCHAR(255) NOT NULL,
  title NVARCHAR(MAX),
  created_at DATETIME2 DEFAULT GETUTCDATE(),
  updated_at DATETIME2 DEFAULT GETUTCDATE(),
  is_active BIT DEFAULT 1,
  rating FLOAT,
  rating_timestamp DATETIME2,
  rating_comment NVARCHAR(MAX)
);

-- conversation_messages (resumo)
CREATE TABLE conversation_messages (
  message_id NVARCHAR(36) PRIMARY KEY,
  conversation_id NVARCHAR(36) NOT NULL,
  user_id NVARCHAR(255) NOT NULL,
  role NVARCHAR(50) NOT NULL,
  content NVARCHAR(MAX) NOT NULL,
  tokens_used INT,
  model NVARCHAR(100),
  retrieval_time FLOAT,
  llm_time FLOAT,
  total_time FLOAT,
  created_at DATETIME2 DEFAULT GETUTCDATE()
);
```

---

# 12. Configuração e Deployment

## 12.1 Ambientes

- **Local:** docker-compose (backend + dependências)
- **Azure:** Container Apps (backend e serviço de IA), SQL Server, Blob Storage, AI Search, Azure OpenAI

## 12.2 Variáveis de Ambiente (Backend - Principais)

```bash
# Azure AD
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...

# URLs
APP_BASE_URL_BACKEND=https://backend.example.com
APP_BASE_URL_FRONTEND=https://frontend.example.com

# LLM Server (com retry)
LLM_SERVER_URL=https://llm-server.example.com
LLM_SERVER_TIMEOUT=300
LLM_SERVER_MAX_RETRIES=3
LLM_SERVER_RETRY_DELAY=1

# Blob Storage
AZURE_STORAGE_ACCOUNT_NAME=...
AZURE_STORAGE_ACCOUNT_KEY=...

# SQL Server
DB_HOST=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...

# CORS
CORS_ORIGINS=https://frontend.example.com

# Features
SKIP_LLM_SERVER=false
SKIP_LLM_METADATA_EXTRACTION=false
```

## 12.3 Variáveis de Ambiente (Serviço de IA - Principais)

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_API_INSTANCE_NAME=...
AZURE_OPENAI_API_DEPLOYMENT_NAME=...

# Embeddings
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=...   # ex.: text-embedding-ada-002

# Azure AI Search
AZURE_SEARCH_ENDPOINT=...
AZURE_SEARCH_API_KEY=...
AZURE_SEARCH_INDEX_NAME=...

# (Opcional) Fallback OpenAI
OPENAI_API_KEY=...
OPENAI_MODEL_NAME=...

# (Opcional) Key Vault
KEYVAULT_URL=...
```

## 12.4 Execução Local (Comandos)

```bash
# Backend (stack local)
docker-compose up

# Serviço de IA (build/run)
docker build -t luz-langchain .
docker run -p 8001:8001 --env-file .env luz-langchain
```

## 12.5 Deploy Azure (Exemplo)

```bash
az containerapp create \
  --resource-group <resource-group> \
  --name luz-backend \
  --image <registry>.azurecr.io/luz-backend:latest \
  --environment <containerapp-environment>
```

---

# 13. Troubleshooting e Operação

| Sintoma | Causa Provável | Ação |
|---------|---|---|
| 401 Unauthorized | Sessão expirada / cookie inválido | Refazer login |
| 422 Unprocessable Entity | Texto extraído > 50k chars | Validar documento; backend trunca automaticamente |
| 500 LLM connection error | Serviço de IA indisponível | Verificar status do container/URL; (opcional) SKIP_LLM_SERVER=true |
| 500 LLM timeout | Serviço de IA lento | Aumentar timeout; checar latência e quotas |
| 404 Not found | document_id inexistente | Validar ID e ambiente |

## 13.1 Dicas de Operação

- Verificar health checks do Backend e do serviço de IA
- Validar conexão do serviço de IA com Azure OpenAI e Azure AI Search (quota e chaves)
- Ao investigar baixa recuperação de documentos, conferir RBAC e metadados de publicação (allowed_roles/countries/cities)
- Monitorar rate limit e ajustar conforme perfil de uso

---

# 14. Apêndices

## 14.1 Glossário

| Termo | Significado |
|-------|-----------|
| RAG | Retrieval-Augmented Generation: geração com base em documentos recuperados |
| RBAC | Role-Based Access Control: controle de acesso por perfis e contexto |
| SSE | Server-Sent Events: streaming de eventos via HTTP |
| Chunk | Fragmento de documento indexado para busca |
| Embedding | Representação vetorial do texto para busca por similaridade |

## 14.2 Checklist Rápido de Entrega

- ✅ CORS configurado com allow_credentials e origem do frontend
- ✅ Cookies de sessão funcionando (HTTPS, SameSite=None)
- ✅ Serviço de IA com health check OK e conectividade com Azure OpenAI + Azure AI Search
- ✅ Documento ingestado aparece para usuário permitido (validar RBAC)
- ✅ Dashboard carregando métricas a partir do SQL

---

**Documentação Consolidada - Versão 1.0 + Backend Atualizado**  
**Pronta para Cliente e Times Técnicos**  
**Data: 27 de Março de 2026**
