# Plataforma Luz - Documentação Integrada

**Versão do documento:** 2.0 (Consolidada)  
**Data de Atualização:** 27 de Março de 2026  
**Status:** ✅ Consolidado e Completo (com Arquitetura)  
**Público-alvo:** Cliente / Stakeholders / Times Técnicos  
**Escopo:** Visão da solução, fluxos, APIs, segurança e guias de integração  

---

## 📋 Sumário Executivo

**Luz** é uma plataforma corporativa de Assistente de RH com base de conhecimento integrada. Funciona permitindo que colaboradores autenticados façam perguntas em chat natural; respostas são geradas por IA usando documentos corporativos como base (RAG), respeitando rigorosamente o controle de acesso (RBAC) por cargo, país, cidade e unidade.

**Capacidades principais:**
- ✅ Chat inteligente com streaming em tempo real
- ✅ RAG (busca semântica em documentos)
- ✅ Upload e versionamento de documentos
- ✅ Dashboard com KPIs de uso
- ✅ RBAC em 4 dimensões (role, country, city, address)
- ✅ Autenticação SSO via Azure Entra ID
- ✅ Agentes especializados (HR, SMART, IDP, General)

---

# 1. OBJETIVO E ESCOPO

## 1.1 Propósito

Este documento consolida as especificações arquiteturais, técnicas e operacionais da Plataforma Luz em um único documento integrado, servindo como referência única para:

- **Cliente / Stakeholders**: Entendimento funcional e de negócio
- **Times Técnicos**: Implementação, integração e operação

## 1.2 O que está incluído

✅ Visão funcional da solução e principais capacidades  
✅ Fluxos principais (login, chat, ingestão, dashboard)  
✅ Resumo dos componentes e integrações Azure  
✅ **Arquitetura detalhada** (diagramas, componentes, decisões)  
✅ APIs expostas com exemplos completos  
✅ Segurança (autenticação, RBAC, guardrails)  
✅ Guias técnicos para Backend, Frontend e IA/LLM  
✅ Dados e persistência  
✅ Configuração e deployment  
✅ Troubleshooting e operação  

## 1.3 O que está fora do escopo (por enquanto)

❌ Governança de conteúdo e curadoria de documentos  
❌ Custos e dimensionamento financeiro  
❌ Roadmap de evolução futura  

---

# 2. VISÃO GERAL DA SOLUÇÃO

## 2.1 O que é a Plataforma Luz?

**Luz** é uma solução de IA generativa focada em suporte de RH corporativo. Integra:

1. **Base de Conhecimento:** Documentos corporativos (políticas, benefícios, procedimentos) armazenados e versionados
2. **Busca Semântica:** Vetorização e indexação em Azure AI Search
3. **IA Conversacional:** Agentes especializados usando Azure OpenAI (GPT-4o-mini)
4. **Segurança:** RBAC multi-dimensional com controle granular de acesso

## 2.2 Para quem é

| Persona | O que faz | Benefício |
|---------|----------|----------|
| **Colaborador** | Faz perguntas de RH no chat | Respostas instantâneas, 24/7, padronizadas |
| **Gestor/RH** | Publica documentos, analisa métricas | Visibilidade de uso, redução de tickets de suporte |
| **Administrador** | Gerencia permissões, prompts, agentes | Controle total da plataforma |

## 2.3 O que o usuário final vê

**Fluxo do Colaborador:**

```
1. Acessa https://luz.company.com
2. Autentica via Azure (SSO)
3. Entra em chat
4. Digita pergunta: "Quais benefícios temos?"
5. Recebe resposta com:
   - Texto em streaming (efeito de "digitação")
   - Documentos relacionados como fonte
   - Opção de avaliar resposta
6. Histórico persistido para referência
```

**Fluxo do Administrador:**

```
1. Acessa "Documentos"
2. Upload arquivo .pdf/.docx
3. Sistema sugere metadados (país, cidade, role)
4. Confirma ou corrige metadados
5. Documento publicado e imediatamente disponível no chat
6. Dashboard mostra impacto (uso, satisfação)
```

## 2.4 Capacidades de IA

| Capacidade | Detalhe |
|-----------|--------|
| **RAG (Retrieval-Augmented Generation)** | Busca vetorial semântica + RBAC no Azure AI Search |
| **Agentes Especializados** | HR, SMART, IDP/PDI, General com roteamento automático |
| **Detecção de Idioma** | PT/ES/EN com cache por sessão |
| **Memória Conversacional** | Contexto por conversa (15 mensagens, 1 hora TTL) |
| **Streaming SSE** | Respostas em tempo real como se fossem "digitadas" |
| **Guardrails** | Rate limiting, sanitização, detecção de prompt injection |
| **Quality Tiers** | Degradação graciosa quando documentos são insuficientes |

## 2.5 Stack Tecnológico

| Camada | Tecnologias |
|--------|-------------|
| **Frontend** | Angular (TypeScript), @elxjs/ui, ngx-markdown, ngx-translate, Chart.js |
| **Backend API** | FastAPI + Python 3.11, MSAL (Azure Entra ID), pyodbc (SQL Server) |
| **Serviço de IA** | FastAPI + Python 3.11, LangGraph, Async HTTP |
| **Armazenamento** | Azure SQL Server, Azure Blob Storage |
| **Search / IA** | Azure AI Search (vetorial), Azure OpenAI (GPT-4o-mini) |
| **Infraestrutura** | Docker/Compose (dev), Azure Container Apps (prod) |

---

# 3. ARQUITETURA DA SOLUÇÃO

## 3.1 Visão Geral (Diagrama Lógico)

```
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 FRONTEND (Angular)                       │
│  Login | Chat | Upload Documentos | Dashboard                  │
│  - MSAL para autenticação                                       │
│  - Cookies HTTPOnly para sessão                                 │
│  - Streaming SSE para chat em tempo real                        │
│  - i18n (PT/EN/ES) + Markdown rendering                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS + Cookies
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│           🔌 BACKEND API (FastAPI + Python 3.11)               │
├─────────────────────────────────────────────────────────────────┤
│ Routers (Endpoints):                                            │
│ ├─ Auth (login, logout, status)                                │
│ ├─ Documents (ingest-preview, ingest-confirm, list)            │
│ ├─ Chat (question, streaming, history)                         │
│ ├─ Master Data (locations, countries, categories)              │
│ ├─ Dashboard (KPIs, métricas)                                  │
│ ├─ Admin (gestão de admins, prompts)                           │
│ ├─ Job Title Roles (mapeamento cargo-permissão)                │
│ └─ Evaluation (E42, weaknesses, PDI)                           │
│                                                                  │
│ Services (Lógica):                                              │
│ ├─ document_service          (orquestração de ingestão)        │
│ ├─ conversation_service      (persistência de chat)            │
│ ├─ admin_service             (gerenciamento de admins)         │
│ ├─ sqlserver_documents       (operações diretas SQL)           │
│ └─ llm_integration           (chamadas ao serviço de IA)       │
│                                                                  │
│ Providers (Adapters):                                           │
│ ├─ auth_msal.py              (Azure Entra ID)                  │
│ ├─ storage.py                (Azure Blob)                      │
│ ├─ llm_server.py             (integração com serviço IA)       │
│ ├─ format_converter.py       (conversão PDF/DOCX/XLSX)         │
│ └─ metadata_extractor.py     (extração com IA)                 │
└──────────┬──────────────────────────────────────────┬──────────┘
           │                                          │
           │                                    HTTP (porta 8001)
           │                                          │
    ┌──────▼──────────┐                    ┌─────────▼────────────┐
    │ 🗄️ DADOS         │                    │ 🤖 SERVIÇO IA/LLM    │
    │ ─────────────── │                    │ (FastAPI + LangGraph)│
    │ Azure SQL:      │                    │                      │
    │ ├─ conversations│◄──────────────────┤ Pipeline:            │
    │ ├─ messages     │   History Loader   │ ├─ Guardrails       │
    │ ├─ documents    │   (1ª mensagem)    │ ├─ Language Detect  │
    │ ├─ versions     │                    │ ├─ Classifier       │
    │ └─ admin logs   │                    │ ├─ ⚡ Agents:        │
    │                 │                    │ │  ├─ HR (RAG)      │
    │ Azure Blob:     │                    │ │  ├─ SMART         │
    │ ├─ documents/*  │                    │ │  ├─ IDP/PDI       │
    │ │  version 1~N  │                    │ │  └─ General       │
    │ └─ __temp__/*   │                    │ ├─ Memory Update    │
    │                 │                    │ └─ Response (JSON   │
    │ Azure Search:   │◄───────────────────┤    ou SSE)          │
    │ ├─ chunks (vec) │   RAG + RBAC        │                      │
    │ ├─ embeddings   │   query             │ Dependencies:       │
    │ └─ metadata     │                    │ ├─ Azure OpenAI    │
    │                 │                    │ ├─ Azure Search    │
    │                 │                    │ └─ Backend (hist.) │
    └─────────────────┘                    └────────────────────┘
```

## 3.2 Descrição dos Componentes

### Frontend (Angular)

**Responsabilidades:**
- Renderizar interface de chat, documentos e dashboard
- Gerenciar autenticação via MSAL (Azure Entra ID)
- Enviar perguntas e receber respostas (streaming SSE)
- Upload de documentos (2 etapas: preview + confirm)
- Suportar múltiplos idiomas (i18n)

**Tecnologias principais:**
- Angular 16+, TypeScript
- @azure/msal-browser para autenticação
- ngx-markdown para renderizar respostas
- Chart.js para gráficos do dashboard
- HttpClient com interceptors (credentials, error handling)

**Comunicação:**
- POST/GET para API Backend
- credentials: 'include' para enviar cookies
- EventSource para SSE (streaming)

### Backend API (FastAPI)

**Responsabilidades:**
- Autenticação (Azure Entra ID) e sessão (JWT em cookies)
- Orquestração de ingestão de documentos (2 etapas)
- Persistência de conversas e mensagens (SQL Server)
- Integração com serviço de IA (chamadas HTTP)
- Exposição de APIs ao Frontend (CORS + autenticação)

**Estrutura:**
```
app/
  main.py                  # FastAPI principal
  core/
    config.py              # Configurações e KeyVault
    sqlserver.py           # Conexão e pooling SQL
  providers/
    auth_msal.py           # Azure Entra ID
    storage.py             # Azure Blob
    llm_server.py          # Chamadas ao serviço IA
    format_converter.py    # PDF/DOCX/XLSX → texto
  routers/
    auth.py, documents.py, chat.py, master_data.py, dashboard.py
    admin.py, prompts.py, user_preferences.py, ...
  services/
    document_service.py    # Orquestração
    conversation_service.py
    sqlserver_documents.py # Queries diretas
    admin_service.py
  tasks/
    cleanup_temp_uploads.py  # Limpeza assincronada
```

**Padrão de 5 Camadas:**
1. **HTTP Layer** (FastAPI)
2. **Routers** (Endpoints)
3. **Services** (Lógica de negócio)
4. **Providers** (Adapters para externos)
5. **External Services** (Azure, LLM)

### Serviço de IA/LLM (FastAPI + LangGraph)

**Responsabilidades:**
- Classificação de perguntas (HR / SMART / IDP / General)
- Execução de agentes especializados
- RAG com busca vetorial e RBAC
- Detecção de idioma e memória de sessão
- Guardrails e validação de segurança

**Pipeline (LangGraph):**
```
Request 
  → Guardrails (rate limit, sanitização)
  → History Loader (carrega contexto do backend)
  → Language Detector (cache por sessão)
  → Classifier (hr/smart/idp/general com stickiness)
      → HR Agent (RAG vetorial + RBAC)
      → Smart Agent (criação de metas)
      → IDP Agent (plano de desenvolvimento 70/20/10)
      → General Agent (fallback, saudações)
  → Memory Update (persistência de preferências)
  → Response (JSON ou Streaming SSE)
```

**Agentes:**

| Agente | Usa Docs | Temperatura | Tokens | Uso |
|--------|----------|------------|--------|-----|
| **HR** | ✅ RAG | 0.2 | 800 | Consultas RH com base documental |
| **SMART** | ❌ | 0.7 | 500 | Criação de objetivos SMART |
| **IDP/PDI** | ❌ | 0.7 | 600 | Plano de desenvolvimento individual |
| **General** | ❌ | 0.7 | 300 | Saudações, fallback |

**Agente HR — Quality Tiers:**
- **Tier 1** (score ≥0.70): Resposta normal com documentos
- **Tier 2** (0.50–0.69): Resposta com ressalva de incompletude
- **Tier 3** (0.35–0.49): Redireciona para General Agent
- **Tier 4** (<0.35): Redireciona para General Agent

### Dependências Azure

| Serviço | Uso |
|---------|-----|
| **Azure Entra ID** | Autenticação OAuth2, validação de tokens, lookup de usuários |
| **Azure SQL Server** | Conversas, mensagens, documentos, versões, dimensões |
| **Azure Blob Storage** | Armazenamento permanente de arquivos e uploads temporários |
| **Azure AI Search** | Índice vetorial/híbrido para busca de chunks com metadata RBAC |
| **Azure OpenAI** | Geração de respostas (GPT-4o-mini) e embeddings (text-embedding-ada-002) |

## 3.3 Decisões e Trade-offs

### Decisão 1: Dois Endpoints para Chat (JSON vs Streaming)

**É preciso manter ambos?** Sim. Razões:

- **POST /api/v1/chat/question** → JSON: Simples, sem overhead SSE
- **POST /api/v1/chat/question/stream** → SSE: UX melhor (digitação em tempo real)

**Trade-off:** Código duplicado no backend (proxy de SSE) + serviço de IA (dois grafos or um gerador manual). Mitigação: testes automatizados para sincronizar comportamento.

### Decisão 2: Preview + Confirm para Documentos (em vez de Upload Direto)

**Benefício:** Validação de metadados antes de indexar (reduz retrabalho).
**Trade-off:** 2 chamadas em vez de 1; backend mais complexo.
**Mitigação:** Frontend armazena temp_id em cache; usuário não sente o impacto.

### Decisão 3: RBAC em 4 Dimensões (role, country, city, address)

**Benefício:** Granularidade máxima; permite documentos por unidade física.
**Trade-off:** Filtros OData complexos; risco de misconfiguration.
**Mitigação:** Sistema normaliza valores (lowercase, sem acentos) via `utils/rbac_normalizer.py`.

### Decisão 4: Stickiness em Classificação (anti-oscilação entre agentes)

**Benefício:** Conversas mais coerentes (referências implícitas resolvidas).
**Trade-off:** Necessidade de 90% de confiança para trocar agente; pode ignorar mudança legítima.
**Threshold:** 0.90 (conservador); ajustável em config.

### Decisão 5: Memória em Dois Níveis (sessão + longo prazo)

**Benefício:** Balanceamento entre contexto recente e preferências persistentes.
**Trade-off:** Complexidade de gerenciar dois caches.
**Mitigação:** TTLs bem definidos; graeful degradation em falha.

### Risco: Desincronização entre Pipeline LangGraph e Gerador SSE

Se um novo node for adicionado ao grafo, deve ser registrado também no gerador SSE. Falha em registrar em um dos dois faz o comportamento diferir sutilmente entre os dois endpoints (nenhum erro explícito).

**Mitigação:** Testes de integração que rodam ambos os endpoints e comparam respostas.

---

# 4. COMPONENTES DO SISTEMA

## 4.1 Frontend (Angular)

Uma aplicação web SPA que renderiza:
- **Chat:** Conversa com IA, histórico, streaming
- **Documentos:** Upload (preview + confirm), listagem, download, deleção
- **Dashboard:** KPIs, gráficos de uso, avaliações
- **Admin:** Gestão de admins, prompts (se for admin)

**Características:**
- Multi-idioma (PT/EN/ES) com @ngx-translate
- Markdown rendering de respostas (ngx-markdown)
- Streaming SSE nativo (EventSource API)
- CORS + HTTPOnly cookies

## 4.2 Backend (FastAPI + Python 3.11)

Servidor de API REST que:
- Valida sessões (JWT via cookies)
- Orquestra ingestão de documentos
- Persiste conversas
- Chama serviço de IA com retry

**Endpoints principais:**
- GET `/api/v1/login` → redireciona para Azure AD
- POST `/api/v1/chat/question` → pergunta (resposta JSON)
- POST `/api/v1/chat/question/stream` → pergunta (resposta SSE)
- POST `/api/v1/documents/ingest-preview` → extrai metadados
- POST `/api/v1/documents/ingest-confirm/{temp_id}` → finaliza upload
- GET `/api/v1/master-data/*` → dados mestres (somente leitura)

## 4.3 Serviço de IA/LLM (FastAPI + LangGraph + Python 3.11)

Microserviço que:
- Classifica perguntas
- Executa agentes (HR, SMART, IDP, General)
- Recupera documentos com RBAC
- Gera respostas via GPT-4o-mini

**Endpoints:**
- POST `/api/v1/question` → pergunta (JSON)
- POST `/api/v1/question/stream` → pergunta (SSE)
- POST `/api/v1/documents` → upsert no índice
- DELETE `/api/v1/documents/{document_id}` → remover do índice
- GET `/api/v1/health` → health check

## 4.4 Dependências Azure

```
┌─────────────────────────────────────────────┐
│     Azure Services (Infraestrutura)         │
├─────────────────────────────────────────────┤
│ • Azure Entra ID      (autenticação)        │
│ • Azure SQL Server    (persistência)        │
│ • Azure Blob Storage  (armazenamento)       │
│ • Azure AI Search     (índice vetorial)     │
│ • Azure OpenAI        (LLM + embeddings)    │
│ • Azure Container App (orquestração)        │
│ • Azure Key Vault     (secrets)              │
└─────────────────────────────────────────────┘
```

---

# 5. FLUXOS PRINCIPAIS

## 5.1 Login e Sessão (SSO)

```
User Frontend                 Azure AD               Backend
  │                              │                     │
  ├─ Click "Login" ──────────────────────────────────►│
  │                              │                     │
  │  Backend gera URL e redireciona para Azure         │
  │                              │                     │
  │  ◄──────────────────── redirect────────────────────┤
  │                              │                     │
  ├──────────── acessa Azure AD ─────────────────────────►
  │                              │                     │
  │                          [Login Form]              │
  │                              │                     │
  │  ◄─────────────── ~redirecionado com code ────────┤
  │                              │                     │
  ├─ /auth/callback?code=ABC ────────────────────────►│
  │                              │                     │
  │  Backend troca código por tokens (MSAL)           │
  │                              │                     │
  │  Backend cria JWT interno + cookie HTTPOnly        │
  │                              │                     │
  │  ◄────────────── Set-Cookie: jwt=... ─────────────┤
  │                              │                     │
  │                     [Redirect para /app/chat]      │
```

**Resultado:** Cookie HTTPOnly setado; próximas requisições incluem automaticamente.

## 5.2 Chat com IA

```
User (Frontend)    Backend API          Serviço IA         Azure OpenAI
     │                 │                    │                    │
     │─ pergunta ─────►│                    │                    │
     │                 │ cria conversa      │                    │
     │                 │ (SQL)              │                    │
     │                 │                    │                    │
     │                 ├─ POST /question ──►│ [Classificar]      │
     │                 │                    │ [Buscar docs]      │
     │                 │                    ├─ search ──────────►│
     │                 │                    │ [Gerar resposta]   │
     │                 │                    ├─ complete ───────►│
     │                 │                    │                    │
     │                 │◄─ resposta ───────┤                    │
     │◄─ resposta ─────┤                    │                    │
     │                 │ salva no SQL       │                    │
     │                 │                    │                    │
```

**Fluxo com Streaming (SSE):**
```
mesmo fluxo, mas:
- POST /question/stream
- evento: status (buscando docs)
- evento: answer_chunk (cada token)
- evento: answer_complete (fim)
```

## 5.3 Upload de Documento (2 Etapas)

### Etapa 1: Preview
```
User seleciona arquivo

Frontend: POST /documents/ingest-preview
  Body: multipart/form-data { file: documento.pdf }

Backend:
  1. Salva em storage/__temp__/{temp_id}/
  2. Extrai texto (UTF-8)
  3. Limpa (remove metadados, binário)
  4. Trunca se > 50k chars
  5. Chama serviço IA para extrair metadados
  6. Retorna temp_id + metadados sugeridos

Frontend:
  - Exibe preview de texto
  - Mostra metadados sugeridos
  - Usuário aprova ou edita
```

### Etapa 2: Confirm
```
User clica "Confirmar Publicação"

Frontend: POST /documents/ingest-confirm/{temp_id}
  Body: multipart/form-data {
    user_id: john_doe,
    allowed_countries: Brazil, USA,
    allowed_cities: São Paulo,
    min_role_level: 2,
    category_id: 5
  }

Backend:
  1. Recupera arquivo do temp storage
  2. Valida metadados
  3. **CHAMA SERVIÇO IA FIRST** (falha aqui = tudo falha)
     - Envia para indexação
     - Gera embeddings
  4. Só depois: INSERT documento (SQL)
  5. INSERT versão (SQL)
  6. Move arquivo temp → permanent (Blob)
  7. Delete arquivo temp

Frontend:
  - Exibe "Documento publicado!"
  - Remove do formulário de upload
```

**Regra crítica:** Se enviar para IA falhar, nada é salvo no SQL nem Blob.

## 5.4 Dashboard (KPIs)

```
Admin acessa /dashboard

Frontend: GET /dashboard/summary?start_date=...&end_date=...

Backend:
  - Consulta SQL Server
  - Agrega conversas por período
  - Calcula média de resposta
  - Conte avaliações
  - Estima custo de tokens

Backend retorna:
{
  "conversations": 1245,
  "avg_response_time_ms": 2145,
  "success_rate": 98.5,
  "rating_average": 4.2,
  "llm_tokens": 1275000,
  "estimated_cost": $44.25
}

Frontend:
  - Renderiza gráficos (Chart.js)
  - Exibe KPIs em cards
```

---

# 6. INTEGRAÇÃO VIA APIs

## 6.1 Backend API (FastAPI) — Endpoints Principais

### Autenticação

| Endpoint | Método | Autenticação | Descrição |
|----------|--------|--------------|-----------|
| `/api/v1/login` | GET | ❌ | Redireciona para Azure AD |
| `/api/v1/getatoken?code=...` | GET | ❌ | Callback Azure, seta cookie JWT |
| `/api/v1/logout` | GET | ❌ | Limpa cookie |
| `/api/v1/auth/status` | GET | ✅ | Verifica sessão ativa |

### Chat

| Endpoint | Método | Autenticação | Descrição |
|----------|--------|--------------|-----------|
| `/api/v1/chat/question` | POST | ✅ | Pergunta, resposta JSON |
| `/api/v1/chat/question/stream` | POST | ✅ | Pergunta, resposta SSE |
| `/api/v1/chat/conversations/{user_id}` | GET | ✅ | Lista conversas do usuário |
| `/api/v1/chat/conversations/{conversation_id}/detail` | GET | ✅ | Detalhes + mensagens |
| `/api/v1/chat/{chat_id}/rate` | POST | ✅ | Avaliar resposta |

### Documentos

| Endpoint | Método | Autenticação | Descrição |
|----------|--------|--------------|-----------|
| `/api/v1/documents/ingest-preview` | POST | ✅ | Upload preview |
| `/api/v1/documents/ingest-confirm/{temp_id}` | POST | ✅ | Confirmar e publicar |
| `/api/v1/documents` | GET | ✅ | Listar documentos |
| `/api/v1/documents/{id}` | GET | ✅ | Detalhes do documento |
| `/api/v1/documents/{id}/download` | GET | ✅ | Download arquivo |
| `/api/v1/documents/{id}/versions/{v}` | DELETE | ✅ | Deletar versão |

### Dados Mestres (somente leitura)

| Endpoint | Método | Responsabilidade |
|----------|--------|------------------|
| `/api/v1/master-data/locations` | GET | Localidades |
| `/api/v1/master-data/countries` | GET | Países |
| `/api/v1/master-data/categories` | GET | Categorias de documentos |
| `/api/v1/master-data/roles` | GET | Papéis/funções |

### Dashboard

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/dashboard/summary` | GET | KPIs agregados |
| `/api/v1/dashboard/detailed` | GET | Lista de conversas |

### Admin

| Endpoint | Método | Autenticação | Descrição |
|----------|--------|--------------|-----------|
| `/api/v1/admins/init` | POST | ❌ | Bootstrap 1º admin |
| `/api/v1/admins` | GET | ✅ Admin | Listar admins |
| `/api/v1/admins` | POST | ✅ Admin | Criar admin |
| `/api/v1/prompts/{agente}` | PUT | ✅ Admin | Atualizar prompt |

## 6.2 Exemplos de Requisições

### Exemplo 1: Fazer Pergunta (JSON)

```bash
curl -X POST https://api.luz.com/api/v1/chat/question \
  -H "Content-Type: application/json" \
  -b "jwt=<token>" \
  -d '{
    "chat_id": "session_abc123",
    "user_id": "emp_12345",
    "name": "João Silva",
    "email": "joao.silva@company.com",
    "country": "Brazil",
    "city": "São Paulo",
    "roles": ["Employee"],
    "department": "TI",
    "job_title": "Analista de TI",
    "collar": "white",
    "unit": "Engineering",
    "question": "Quais são os benefícios de saúde?"
  }'
```

**Resposta:**
```json
{
  "answer": "Olá João! Temos os seguintes benefícios de saúde...",
  "source_documents": [
    { "title": "Benefícios de Saúde 2026", "source": "health_benefits.pdf" }
  ],
  "classification": { "category": "hr", "confidence": 0.95 },
  "total_time_ms": 1849,
  "prompt_tokens": 419,
  "completion_tokens": 93,
  "agente": "HR",
  "model": "gpt-4o-mini"
}
```

### Exemplo 2: Upload de Documento (Preview + Confirm)

**Preview:**
```bash
curl -X POST https://api.luz.com/api/v1/documents/ingest-preview \
  -b "jwt=<token>" \
  -F "file=@beneficios.pdf"
```

**Resposta do Preview:**
```json
{
  "temp_id": "temp_abc123",
  "filename": "beneficios.pdf",
  "extracted_fields": {
    "min_role_level": 2,
    "allowed_countries": ["Brazil"],
    "allowed_cities": ["São Paulo", "Curitiba"],
    "collar": "white",
    "confidence": "high"
  }
}
```

**Confirm:**
```bash
curl -X POST https://api.luz.com/api/v1/documents/ingest-confirm/temp_abc123 \
  -b "jwt=<token>" \
  -F "user_id=john_doe" \
  -F "min_role_level=2" \
  -F "allowed_countries=Brazil" \
  -F "allowed_cities=São Paulo,Curitiba" \
  -F "collar=white" \
  -F "category_id=5"
```

**Resposta do Confirm:**
```json
{
  "document_id": "uuid-xxx",
  "version": 1,
  "status": "ingested",
  "message": "Documento publicado com sucesso!"
}
```

### Exemplo 3: Streaming SSE

```bash
curl -X POST https://api.luz.com/api/v1/chat/question/stream \
  -H "Accept: text/event-stream" \
  -b "jwt=<token>" \
  -d '{...pergunta...}'
```

**Resposta (stream):**
```
event: status
data: {"step":"retrieval","message":"Buscando documentos..."}

event: answer_chunk
data: {"delta":"Os"}

event: answer_chunk
data: {"delta":" benefícios"}

event: answer_chunk
data: {"delta":" incluem..."}

event: answer_complete
data: {"answer":"Resposta completa aqui"}
```

## 6.3 Serviço de IA/LLM API

**Endpoints internos** (Backend chama):

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/question` | POST | Pergunta (JSON) |
| `/api/v1/question/stream` | POST | Pergunta (SSE) |
| `/api/v1/documents` | POST | Indexar documento |
| `/api/v1/documents/{id}` | DELETE | Remover do índice |

---

# 7. SEGURANÇA E CONTROLE DE ACESSO

## 7.1 Autenticação (Azure Entra ID + MSAL)

**Fluxo completo:**

1. Frontend abre pop-up MSAL
2. Usuário autentica em Azure AD
3. Azure retorna authorization code
4. Frontend envia code ao Backend
5. Backend troca code por tokens (via MSAL)
6. Backend cria JWT interno
7. JWT é armazenado em cookie **HTTPOnly** (seguro contra XSS)
8. Próximas requisições incluem cookie automaticamente

**Configuração de Cookie:**
- `HttpOnly`: JavaScript não acessa
- `Secure`: Apenas HTTPS em produção
- `SameSite=None`: Requisições cross-site (com Secure)

**Validação JWT:**
- Assinatura verificada contra JWKS do Azure
- Expiração validada
- Se inválido: 401 Unauthorized

## 7.2 Autorização (RBAC em 4 Dimensões)

**O documento é acessível SE (em SQL):**

```sql
-- Filtro RBAC para documento X
role_max >= document.min_role_level
AND (document.allowed_countries IS NULL OR user.country IN document.allowed_countries)
AND (document.allowed_cities IS NULL OR user.city IN document.allowed_cities)
AND (document.allowed_addresses IS NULL OR user.address_id IN document.allowed_addresses)
```

**Exemplo prático:**

```
Documento: "Benefícios de Saúde"
- min_role_level: 2 (Coordenador+)
- allowed_countries: Brazil, USA
- allowed_cities: São Paulo, Boston
- allowed_addresses: [8, 15]  (unidade 8 e 15)

Usuário 1: role=4, country=Brazil, city=São Paulo, address=8  ✅ Acesso
Usuário 2: role=1, country=Brazil, city=São Paulo, address=8  ❌ Acesso negado (role=1)
Usuário 3: role=4, country=Brazil, city=Brasília, address=8   ❌ Acesso negado (city)
Usuário 4: role=4, country=Brazil, city=São Paulo, address=23 ❌ Acesso negado (address)
```

**Roles padrão:**

| role_id | Nome | Nível |
|---------|------|-------|
| 0 | Admin | Super (bypassa RBAC) |
| 1 | Operacional | Junior |
| 4 | Coordenador | Coordinator |
| 8 | Gerente | Manager |
| 12 | Diretor | Director |
| 15 | VP | Vice-President |
| 99 | Guest | Public (mínimo) |

**Aplicação no Serviço de IA:**

Ao recuperar documentos no Azure AI Search, o serviço gera um filtro OData:

```
allowed_roles/any(r: r eq 8)
and (allowed_countries/any(c: c eq 'brazil') or not allowed_countries/any())
and (allowed_cities/any(c: c eq 'sao paulo') or not allowed_cities/any())
and (allowed_addresses/any(a: a eq 8) or not allowed_addresses/any())
```

(Lista vazia = acesso universal para aquela dimensão)

## 7.3 Guardrails (Segurança do Prompt)

**Antes do pipeline de agentes:**

1. **Rate Limiting:** 5 requisições/minuto por usuário
2. **Validação de tamanho:** Máximo 2000 caracteres
3. **Sanitização:** Bloqueio de null bytes e caracteres de controle
4. **Detecção de Prompt Injection:** Modo log ou block
5. **Bloqueio de PII:** Não armazena dados sensíveis em logs

---

# 8. FRONTEND (Angular) — GUIA DE IMPLEMENTAÇÃO

## 8.1 Estrutura Recomendada

```
src/
  ├── app/
  │   ├── core/                    # Singleton services
  │   │   ├── guards/              # Auth guard, role guard
  │   │   ├── interceptors/        # Credentials, error
  │   │   ├── services/            # Auth, HTTP setup
  │   │   └── layout.component.ts
  │   │
  │   ├── shared/                  # Componentes reutilizáveis
  │   │   ├── components/
  │   │   │   ├── chat-message.component.ts
  │   │   │   ├── markdown-loader.component.ts
  │   │   │   └── loading-spinner.component.ts
  │   │   ├── pipes/               # i18n, formatting
  │   │   └── directives/
  │   │
  │   ├── features/                # Lazy-loaded modules
  │   │   ├── auth/
  │   │   │   ├── login.component.ts
  │   │   │   └── auth.module.ts
  │   │   ├── chat/
  │   │   │   ├── chat.component.ts
  │   │   │   ├── chat.service.ts
  │   │   │   └── chat.module.ts
  │   │   ├── documents/
  │   │   └── dashboard/
  │   │
  │   ├── app.component.ts
  │   ├── app-routing.module.ts
  │   └── app.module.ts
  │
  ├── assets/
  │   ├── i18n/
  │   │   ├── pt.json
  │   │   ├── en.json
  │   │   └── es.json
  │   └── ...
  │
  ├── environments/
  │   ├── environment.ts           # dev
  │   └── environment.prod.ts      # prod
  │
  └── main.ts
```

## 8.2 Chat com Streaming SSE — Exemplo de Código

```typescript
// chat-stream.service.ts
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type StreamEvent =
  | { type: 'status'; data: { message: string } }
  | { type: 'answer_chunk'; data: { delta: string } }
  | { type: 'answer_complete'; data: { answer: string } };

@Injectable({ providedIn: 'root' })
export class ChatStreamService {
  private apiUrl = environment.apiUrl;

  streamQuestion(payload: any): Observable<StreamEvent> {
    return new Observable<StreamEvent>((observer) => {
      const controller = new AbortController();

      fetch(`${this.apiUrl}/api/v1/chat/question/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(payload),
        credentials: 'include', // Envia cookies
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
              const eventLine =
                lines.find((l) => l.startsWith('event:')) ?? 'event: message';
              const dataLine =
                lines.find((l) => l.startsWith('data:')) ?? 'data: {}';

              const eventType = eventLine.replace('event:', '').trim();
              const raw = dataLine.replace('data:', '').trim();

              let data: any = raw;
              try {
                data = JSON.parse(raw);
              } catch {}

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

## 8.3 Upload de Documento (Preview + Confirm)

```typescript
// documents.service.ts
@Injectable({ providedIn: 'root' })
export class DocumentsService {
  constructor(private http: HttpClient) {}

  ingestPreview(file: File) {
    const form = new FormData();
    form.append('file', file);
    return this.http.post(
      `${environment.apiUrl}/api/v1/documents/ingest-preview`,
      form,
      { withCredentials: true }
    );
  }

  ingestConfirm(tempId: string, metadata: Record<string, any>) {
    const form = new FormData();
    Object.entries(metadata).forEach(([k, v]) => form.append(k, String(v)));
    return this.http.post(
      `${environment.apiUrl}/api/v1/documents/ingest-confirm/${tempId}`,
      form,
      { withCredentials: true }
    );
  }
}
```

## 8.4 Interceptors

```typescript
// credentials.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';

export const credentialsInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req.clone({ withCredentials: true }));
};

// error.interceptor.ts
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401) {
        // Redirecionar para login
        window.location.href = '/login';
      }
      return throwError(() => err);
    })
  );
};
```

---

# 9. BACKEND (FastAPI) — GUIA DE IMPLEMENTAÇÃO

## 9.1 Responsabilidades Principais

✅ Autenticação e sessão (Azure Entra ID)
✅ Persistência de conversas e documentos (SQL Server)
✅ Armazenamento de arquivos (Azure Blob)
✅ Orquestração de ingestão (extração, metadados)
✅ Proxy de chat e streaming SSE
✅ APIs para Frontend (CORS + cookies)

## 9.2 Exemplo: Retry com Backoff Exponencial

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
    """
    delay = base_delay_s
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"[Attempt {attempt}] POST {url}")
            resp = requests.post(url, json=json_payload, timeout=timeout_s)

            # Não retry em 4xx
            if 400 <= resp.status_code < 500:
                resp.raise_for_status()

            # Retry em 5xx
            if 500 <= resp.status_code < 600:
                raise RuntimeError(f"Server error {resp.status_code}")

            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"[Failed after {max_retries} attempts] {e}")
                raise

            logger.warning(f"[Attempt {attempt} failed] Retrying in {delay}s... ({str(e)[:50]})")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

    raise last_exception
```

## 9.3 Proxy de Streaming SSE (para Backend)

```python
# routers/chat.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import httpx

router = APIRouter()

@router.post("/api/v1/chat/question/stream")
async def chat_question_stream(request: Request):
    """
    Proxy de streaming SSE.
    Frontend → Backend → Serviço IA
    
    Mantém autenticação Backend e formata eventos para Frontend.
    """
    payload = await request.json()

    async def event_generator():
        try:
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
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"event: error\ndata: {{'message': '{str(e)}'}}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

# 10. SERVIÇO DE IA/LLM (LangGraph + Python 3.11) — GUIA

## 10.1 Pipeline LangGraph

```
┌─────────────────────┐
│ HTTP Request        │ (user_id, question, context...)
└──────────┬──────────┘
           │
     ┌─────▼────────────────────┐
     │ Guardrails Middleware    │ rate limit, sanitize
     └─────┬────────────────────┘
           │
     ┌─────▼────────────────────┐
     │ History Loader (1ª msg)  │ GET /backend/conversations/{chat_id}
     └─────┬────────────────────┘
           │
     ┌─────▼────────────────────┐
     │ Language Detector        │ (cache por sessão)
     └─────┬────────────────────┘
           │
     ┌─────▼────────────────────────────────────┐
     │ Classifier (confidence + stickiness)     │
     │ hr: 0.5 | smart: 0.7 | idp: 0.7 | gen: 0.8
     └─────┬──────────────────────────┬─────────┘
           │                          │
      ┌────▼─────────┐    ┌──────────▼────────┐
      │ HR Agent     │    │ Smart/IDP/General │
      │ (RAG)        │    │ (no docs)         │
      ├──────────────┤    └───────────────────┘
      │ Query        │
      │ Enhancer     │
      │ (resolve     │
      │ refs)        │
      │              │
      │ Azure Search │
      │ (RBAC        │
      │  filter)     │
      │              │
      │ Quality      │
      │ Tier eval    │
      │              │
      │ GPT-4o-mini  │
      └──────┬───────┘
             │
     ┌───────▼──────────────┐
     │ Memory Update        │ (sessão + longo prazo)
     └───────┬──────────────┘
             │
     ┌───────▼──────────────┐
     │ Response             │ JSON ou SSE
     └──────────────────────┘
```

## 10.2 Classificação com Stickiness

```python
# classifier.py (simplificado)
class Classifier:
    CONFIDENCE_THRESHOLDS = {
        'hr': 0.5,
        'smart': 0.7,
        'idp': 0.7,
        'general': 0.8,
    }
    STICKINESS_THRESHOLD = 0.90

    def classify(self, question: str, session_state: dict) -> str:
        """
        Classifica pergunta, respeitando stickiness.
        """
        # Calcular confiança para cada categoria
        scores = {
            'hr': self._score_hr(question),
            'smart': self._score_smart(question),
            'idp': self._score_idp(question),
            'general': self._score_general(question),
        }

        # Melhor categoria
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        # Categoria anterior (sessão)
        current_category = session_state.get('current_category', 'hr')

        # Stickiness: manter categoria anterior se nova category não tem 90% de confiança
        if (
            current_category != best_category
            and best_score < self.STICKINESS_THRESHOLD
        ):
            return current_category

        return best_category
```

## 10.3 Agente HR — Quality Tiers

```python
# agents/hr_agent.py
class HRAgent:
    QUALITY_THRESHOLD = 0.35
    
    async def execute(self, state: dict) -> dict:
        """
        1. Recupera documentos
        2. Avalia qualidade
        3. Redireciona se necessário
        """
        question = state['question']
        user_context = state['user_context']
        
        # [1] Recuperar do Azure AI Search com RBAC
        documents = await self.retriever.search(
            query=question,
            rbac_filter=user_context.to_odata_filter(),
            top_k=5,
        )
        
        # [2] Avaliar qualidade
        if not documents or max(d.score for d in documents) < 0.35:
            # Tier 4: nenhum documento relevante
            return await self.redirect_to_general_agent(state)
        
        max_score = max(d.score for d in documents)
        
        if max_score < 0.5:
            # Tier 3: documentos insuficientes
            return await self.redirect_to_general_agent(state)
        
        # [3] Gerar resposta
        response = await self.llm.complete(
            prompt=self.build_prompt(question, documents),
            temperature=0.2,
            max_tokens=800,
        )
        
        # Adicionar metadados
        return {
            'answer': response,
            'documents': documents,
            'quality_tier': 1 if max_score >= 0.7 else 2,
        }
```

## 10.4 Dois Caminhos de Execução Independentes

**Problema:** Se adicionar um novo node ao grafo, também precisa registrar no gerador SSE (ou vice-versa). Não há erro se esquecer em um dos dois.

**Mitigação:**
- Testes de integração que rodamambos os endpoints
- Comparar respostas
- CI/CD bloqueia merge se divergirem

```python
# tests/test_endpoint_parity.py
@pytest.mark.asyncio
async def test_json_vs_stream_parity():
    """
    Testa que /question e /question/stream retornam a mesma resposta.
    """
    payload = {...}
    
    # JSON
    resp_json = await client.post('/api/v1/question', json=payload)
    answer_json = resp_json.json()['answer']
    
    # Stream
    events = []
    async with client.stream('POST', '/api/v1/question/stream', json=payload) as r:
        async for line in r.aiter_lines():
            events.append(line)
    answer_stream = ''.join(e['delta'] for e in events if e['type'] == 'answer_chunk')
    
    # Validar paridade
    assert answer_json.strip() == answer_stream.strip(), "Respostas divergem!"
```

---

# 11. DADOS E PERSISTÊNCIA

## 11.1 Modelo de Dados (visão resumida)

### Conversas e Mensagens

```sql
-- conversations
CREATE TABLE conversations (
  conversation_id NVARCHAR(36) PRIMARY KEY,
  user_id NVARCHAR(255) NOT NULL,
  title NVARCHAR(MAX),
  created_at DATETIME2 DEFAULT GETUTCDATE(),
  updated_at DATETIME2 DEFAULT GETUTCDATE(),
  is_active BIT DEFAULT 1,
  rating FLOAT,
  rating_comment NVARCHAR(MAX)
);

-- conversation_messages
CREATE TABLE conversation_messages (
  message_id NVARCHAR(36) PRIMARY KEY,
  conversation_id NVARCHAR(36) NOT NULL,
  role NVARCHAR(50) NOT NULL,  -- user, assistant
  content NVARCHAR(MAX) NOT NULL,
  tokens_used INT,
  model NVARCHAR(100),
  retrieval_time FLOAT,
  llm_time FLOAT,
  total_time FLOAT,
  created_at DATETIME2 DEFAULT GETUTCDATE(),
  FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);
```

### Documentos

```sql
-- documents (metadados)
CREATE TABLE documents (
  document_id NVARCHAR(36) PRIMARY KEY,
  title NVARCHAR(255) NOT NULL,
  category_id INT,
  summary NVARCHAR(MAX),
  allowed_countries NVARCHAR(500),  -- CSV: Brazil,USA
  allowed_cities NVARCHAR(1000),     -- CSV: São Paulo,Curitiba
  min_role_level INT DEFAULT 1,
  collar NVARCHAR(50),               -- white, blue, all
  plant_code INT,
  created_at DATETIME2 DEFAULT GETUTCDATE(),
  created_by NVARCHAR(255),
  updated_at DATETIME2 DEFAULT GETUTCDATE(),
  updated_by NVARCHAR(255),
  is_active BIT DEFAULT 1
);

-- versions (rastreamento de arquivos)
CREATE TABLE versions (
  version_id NVARCHAR(36) PRIMARY KEY,
  document_id NVARCHAR(36) NOT NULL,
  version_number INT NOT NULL,
  blob_path NVARCHAR(500),           -- caminho em Azure Blob
  filename NVARCHAR(255),
  created_at DATETIME2 DEFAULT GETUTCDATE(),
  created_by NVARCHAR(255),
  status NVARCHAR(20) DEFAULT 'active',
  FOREIGN KEY (document_id) REFERENCES documents(document_id)
);
```

### Armazenamento

```
Azure Blob Storage:
storage/
├── documents/
│   ├── {document_id}/
│   │   ├── 1/documento.pdf
│   │   ├── 2/documento.pdf
│   │   └── ...
│   └── ...
└── __temp__/
    ├── {temp_id}/arquivo.pdf  (expira em 10 min)
    └── ...

Azure AI Search Index (chunks):
├── content (texto)
├── content_vector (embeddings 1536-dim)
├── document_id
├── chunk_index
├── source_file
├── allowed_roles (Collection(Int32))
├── allowed_countries (Collection(String))
├── allowed_cities (Collection(String))
├── allowed_addresses (Collection(Int32))
└── category_id
```

---

# 12. CONFIGURAÇÃO E DEPLOYMENT

## 12.1 Variáveis de Ambiente — Backend

```bash
# ===== AUTENTICAÇÃO AZURE =====
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<client-id>
AZURE_CLIENT_SECRET=<secret>
AZURE_STORAGE_CONNECTION_STRING=<connection-string>

# ===== URLs =====
APP_BASE_URL_BACKEND=https://api.luz.com
APP_BASE_URL_FRONTEND=https://luz.com
LLM_SERVER_URL=https://iai-llm.internal
CORS_ORIGINS=https://luz.com

# ===== BANCO DE DADOS =====
DB_HOST=luz-db.database.windows.net
DB_NAME=luz_production
DB_USER=luz_user
DB_PASSWORD=<password>

# ===== BLOB STORAGE =====
AZURE_STORAGE_ACCOUNT_NAME=luzstorageacc
AZURE_STORAGE_ACCOUNT_KEY=<key>

# ===== LLM SERVER (Retry) =====
LLM_SERVER_TIMEOUT=300
LLM_SERVER_MAX_RETRIES=3
LLM_SERVER_RETRY_DELAY=1

# ===== FEATURES =====
SKIP_LLM_SERVER=false
SKIP_LLM_METADATA_EXTRACTION=false
```

## 12.2 Variáveis de Ambiente — Serviço de IA

```bash
# ===== AZURE OPENAI =====
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_API_INSTANCE_NAME=luz-openai
AZURE_OPENAI_API_DEPLOYMENT_NAME=gpt-4o-mini

# ===== EMBEDDINGS =====
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002

# ===== AZURE AI SEARCH =====
AZURE_SEARCH_ENDPOINT=https://luz-search.search.windows.net
AZURE_SEARCH_API_KEY=<key>
AZURE_SEARCH_INDEX_NAME=luz-chunks

# ===== BACKEND (para carregar histórico) =====
BACKEND_URL=https://api.luz.com
```

## 12.3 Execução Local (Docker Compose)

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - SKIP_LLM_SERVER=false
      - DB_HOST=sqlserver
      - AZURE_STORAGE_CONNECTION_STRING=...
    depends_on:
      - sqlserver

  iai-llm:
    build: ./iai-llm
    ports:
      - "8001:8001"
    environment:
      - AZURE_OPENAI_API_KEY=...
      - AZURE_SEARCH_API_KEY=...

  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      - SA_PASSWORD=Dev@1234
      - ACCEPT_EULA=Y
    ports:
      - "1433:1433"

  frontend:
    build: ./frontend
    ports:
      - "4200:4200"
    environment:
      - API_URL=http://localhost:8000
```

```bash
docker-compose up
# Backend: http://localhost:8000/docs
# Serviço IA: http://localhost:8001/docs
# Frontend: http://localhost:4200
```

---

# 13. TROUBLESHOOTING E OPERAÇÃO

## 13.1 Erros Comuns

| Erro | Causa | Ação |
|------|-------|------|
| 401 Unauthorized | Sessão expirada | Refazer login |
| 422 Unprocessable Entity | Documento > 50k chars | Backend trunca; validar arq |
| 500 LLM connection error | Serviço IA offline | Verificar container/URL |
| 502 Bad Gateway | Serviço IA lento | Aumentar timeout |
| 404 Not found | document_id inválido | Verificar ID |

## 13.2 Health Checks Recomendados

```bash
# Backend
curl https://api.luz.com/api/v1/auth/status -b "jwt=..."

# Serviço IA
curl https://iai-llm.internal/api/v1/health

# SQL Server
sqlcmd -S luz-db.database.windows.net -U luz_user -P ... -Q "SELECT 1"

# Azure Search
curl -H "api-key: <key>" https://luz-search.search.windows.net/indexes?api-version=...
```

## 13.3 Operação

- Monitorar latência (p95, p99)
- Verificar taxa de sucesso de ingestão
- Acompanhar quota de tokens (Azure OpenAI)
- Validar RBAC ao investigar "acesso negado"
- Revisar "quality tier" de documentos insuficientes

---

# 14. APÊNDICES

## 14.1 Glossário

| Termo | Significado |
|-------|-----------|
| **RAG** | Retrieval-Augmented Generation: gerar com base em docs |
| **RBAC** | Role-Based Access Control: acesso por perfil |
| **SSE** | Server-Sent Events: streaming via HTTP |
| **Chunk** | Fragmento de documento indexado |
| **Embedding** | Vetor que representa semântica do texto |
| **Tier** | Nível de qualidade de recuperação de documentos |
| **Stickiness** | Manter agente anterior quando novo tem baixa confiança |

## 14.2 Checklist de Entrega

- ✅ CORS configurado com allow_credentials
- ✅ Cookies HTTPOnly funcionando
- ✅ Serviço IA com health check OK
- ✅ Documento ingestado visível para usuário permitido (RBAC)
- ✅ Dashboard carregando métricas
- ✅ Streaming SSE funcionando
- ✅ Re-tentativa com backoff em caso de falha
- ✅ Logs estruturados em produção
- ✅ Testes de paridade JSON vs Stream
- ✅ Documentação atualizada

---

**Documentação Consolidada e Integrada - Versão 2.0**  
**Plataforma Luz**  
**Data: 27 de Março de 2026**  
**Status: ✅ Pronto para Cliente / Stakeholders / Times Técnicos**
