# 📚 Índice de Documentação da Plataforma Luz

**Data**: 16 de Março de 2026  
**Versão**: 2.1  
**Status**: ✅ Atualizado com Streaming, Debug Endpoints e Stress Testing

---

## 📖 Documentação Disponível

### 🔐 Gerenciamento de Acesso

#### [Admin Management API](./ADMIN_MANAGEMENT_API.md)
- **O que é**: Sistema completo para gerenciar administradores e permissões
- **Casos de uso**:
  - Criar novo administrador no sistema
  - Atribuir features (permissões) específicas
  - Controlar acesso por agente
  - Inicializar primeiro admin (bootstrap)
  - Listar e consultar admins
- **Endpoints principais**:
  - `POST /api/v1/admins/init` - Inicializar primeiro admin
  - `POST /api/v1/admins` - Criar novo admin
  - `GET /api/v1/admins` - Listar admins
  - `PATCH /api/v1/admins/{admin_id}` - Atualizar admin
  - `POST /api/v1/admins/{admin_id}/features/{feature_id}` - Adicionar feature
  - `DELETE /api/v1/admins/{admin_id}/features/{feature_id}` - Remover feature
- **Autenticação**: Azure Entra ID (MSAL)
- **Autorização**: Apenas admins podem gerenciar admins

---

### 🤖 Gerenciamento de Prompts

#### [Prompts Management API](./PROMPTS_MANAGEMENT_API.md)
- **O que é**: Sistema para criar e gerenciar prompts customizados de LLM
- **Casos de uso**:
  - Criar prompts específicos para cada agente
  - Atualizar instruções do LLM
  - Sincronizar automaticamente com LLM Server
  - Rastrear versões de prompts
  - Deletar prompts não utilizados
- **Endpoints principais**:
  - `POST /api/v1/prompts` - Criar novo prompt
  - `GET /api/v1/prompts` - Listar todos os prompts
  - `GET /api/v1/prompts/{agente}` - Obter prompt específico
  - `PUT /api/v1/prompts/{agente}` - Atualizar prompt
  - `DELETE /api/v1/prompts/{agente}` - Deletar prompt
- **Autenticação**: Azure Entra ID (GET por usuário, POST/PUT/DELETE por admin)
- **Sincronização**: Automática com LLM Server com retry e backoff

---

### 💬 Chat e Conversações

#### [Chat API](./CHAT_API.md) - **ATUALIZADO**
- **O que é**: API para chat interativo com LLM
- **Casos de uso**:
  - Enviar mensagens e receber respostas
  - Busca semântica em documentos
  - Classificação de consultas
  - Rastreamento de tokens
  - **NOVO**: Streaming em tempo real (SSE)
  - **NOVO**: Auto-load de memory_preferences
- **Autenticação**: Bearer Token (JWT)
- **Modelos**: Suporta múltiplos agentes (LUZ, IGP, SMART)
- **Endpoints Stream**: `/api/v1/chat/question/stream`, `/api/v1/chat/test/stream`

---

### ⚙️ Processamento em Background

#### [Background Tasks & Task Queue](./BACKGROUND_TASKS.md)
- **O que é**: Documentação de tarefas assincronadas - ThreadPool + Celery
- **Componentes**:
  - ThreadPoolExecutor (5 workers) - tarefas rápidas e locais
  - Celery + Redis - tarefas distribuídas e long-running
- **Casos de uso**:
  - Salvar chat em background (ThreadPool)
  - Indexação de documentos (Celery)
  - Processamento pesado assincronamente
  - Retry automático para tarefas críticas
- **Monitoramento**: Flower dashboard para Celery
- **Threading**: Max 5 workers simultâneos, queue max 1000 tasks

---

### 🔧 Ferramentas de Diagnóstico e Testes

#### [Debug Endpoints](./DEBUG_ENDPOINTS.md)
- **O que é**: Endpoints para diagnóstico e troubleshooting
- **Casos de uso**:
  - Verificar configuração de variáveis de ambiente
  - Testar conectividade com LLM Server
  - Listar agentes configurados
  - Health checks de componentes
- **Endpoints principais**:
  - `GET /api/v1/debug/env` - Diagnóstico de ambiente
  - `GET /api/v1/debug/agents` - Listar agentes
  - `GET /api/v1/debug/llm-health` - Health check LLM
- **Segurança**: Desabilitado em produção

#### [Stress Testing](./STRESS_TESTING.md)
- **O que é**: Ferramenta para testes de carga e performance
- **Casos de uso**:
  - Validar performance baseline
  - Simular carga de usuários
  - Identificar gargalos
  - Teste de capacidade
- **Endpoint**: `POST /api/v1/chat/stress-test`
- **Métricas**:
  - Latência (p50, p95, p99)
  - TTFT (Time-To-First-Token)
  - Throughput (req/s)
  - Taxa de sucesso

---

### 📄 Gerenciamento de Documentos

#### [Document Ingestion](./DOCUMENT_INGESTION.md) - **ATUALIZADO**
- **O que é**: Processo de upload e ingestão de documentos
- **Casos de uso**:
  - Upload de arquivos (PDF, DOCX, XLSX)
  - Extração automática de metadados com LLM
  - Preview antes de confirmar ingestão
  - Armazenamento em Azure Blob Storage
  - Versionamento de documentos
  - **NOVO**: Download com versioning (`version_number` parameter)
  - **NOVO**: Gerenciamento de localidades (location_ids)
- **Fluxo**: preview → confirm → armazenamento sincronizado

#### [Master Data API](./MASTER_DATA_API.md)
- **O que é**: API read-only para dados mestres
- **Casos de uso**:
  - Listar cargos e títulos
  - Obter mapeamento de papéis
  - Consultar categorias de benefícios
  - Obter dimensões (países, cidades, etc.)

---

### 👤 Preferências de Usuário

#### [User Preferences API](./USER_PREFERENCES_API.md)
- **O que é**: Sistema de preferências personalizadas por usuário
- **Casos de uso**:
  - Salvar preferências de idioma
  - Armazenar configurações de interface
  - Gerenciar agentes preferidos
  - Rastrear histórico de conversas

---

### 🌐 Integração Frontend

#### [Frontend Integration](./FRONTEND_INTEGRATION.md)
- **O que é**: Guia de integração para aplicações frontend
- **Tópicos**:
  - Autenticação via MSAL
  - Chamadas aos endpoints da API
  - Tratamento de respostas
  - Exemplo de implementação React/Angular

#### [LLM Server Endpoints](./LLM_SERVER_ENDPOINTS.md)
- **O que é**: Documentação dos endpoints do LLM Server
- **Tópicos**:
  - Endpoints de embeddings
  - Busca semântica
  - Management de prompts
  - Health check

---

### 🏗️ Arquitetura e Visão Geral

#### [Project Overview](./PROJECT_OVERVIEW.md)
- **O que é**: Visão geral executiva do projeto
- **Seções**:
  - Objetivos da plataforma
  - Stack tecnológico
  - Componentes principais
  - Fluxos de negócio

#### [Complete Documentation](./COMPLETE_DOCUMENTATION.md)
- **O que é**: Documentação técnica completa da plataforma
- **Seções**:
  - Arquitetura detalhada
  - Componentes do sistema
  - Fluxos principais
  - Estrutura de dados
  - Deployment

---

## 🗺️ Mapa de Navegação por Cenário

### Eu sou um **Administrador do Sistema**

Você gerencia admins e configurações globais.

1. Comece com: [Admin Management API](./ADMIN_MANAGEMENT_API.md)
   - Como inicializar o sistema
   - Como criar novos admins
   - Como atribuir permissões

2. Depois: [Prompts Management API](./PROMPTS_MANAGEMENT_API.md)
   - Como gerenciar instruções dos agentes
   - Como sincronizar com LLM Server

3. Referência: [Complete Documentation](./COMPLETE_DOCUMENTATION.md)
   - Arquitetura completa do sistema

---

### Eu sou um **Desenvolvedor Frontend**

Você integra a plataforma em aplicações web.

1. Comece com: [Project Overview](./PROJECT_OVERVIEW.md)
   - Entender a visão geral

2. Depois: [Frontend Integration](./FRONTEND_INTEGRATION.md)
   - Como autenticar usuários
   - Como chamar os endpoints
   - Exemplos de código

3. APIs específicas conforme necessário:
   - [Chat API](./CHAT_API.md) - Para chat
   - [Document Ingestion](./DOCUMENT_INGESTION.md) - Para upload
   - [Master Data API](./MASTER_DATA_API.md) - Para dados mestres
   - [User Preferences API](./USER_PREFERENCES_API.md) - Para preferências

---

### Eu sou um **Desenvolvedor Backend**

Você trabalha com APIs e lógica de negócio.

1. Comece com: [Complete Documentation](./COMPLETE_DOCUMENTATION.md)
   - Arquitetura e componentes

2. Depois: [Admin Management API](./ADMIN_MANAGEMENT_API.md)
   - Sistema de permissões

3. E também: [Prompts Management API](./PROMPTS_MANAGEMENT_API.md)
   - Gerenciamento de prompts

4. APIs específicas:
   - [Chat API](./CHAT_API.md)
   - [Document Ingestion](./DOCUMENT_INGESTION.md)
   - [Master Data API](./MASTER_DATA_API.md)

5. Referência: [LLM Server Endpoints](./LLM_SERVER_ENDPOINTS.md)

---

## 🚀 Documentos de Operações e Deployment

### [Debug Endpoints](./DEBUG_ENDPOINTS.md)
Ferramentas de diagnóstico para verificar saúde do sistema:
- Validar configurações
- Testar componentes (DB, Storage, LLM)
- Listar agentes
- health checks

### [Stress Testing](./STRESS_TESTING.md)
Guia para testes de carga e performance:
- Como executar stress tests
- Interpretar métricas (latência, throughput)
- Encontrar limites de capacidade
- Baseline de performance

### [Multi-Instance Refactoring](./MULTI_INSTANCE_REFACTORING.md)
Planejamento técnico para suportar múltiplas instâncias:
- Problema identificado (estado em memória)
- Solução proposta (Blob Storage, Redis)
- Roadmap de implementação
- Impacto no auto-scaling

---

## 📊 Matriz de Recursos por Documentação

---

### Eu preciso de um **Guia Rápido**

Problema | Documento | Seção
----------|-----------|-------
"Como criar um admin?" | [Admin Management API](./ADMIN_MANAGEMENT_API.md) | Criar Novo Admin
"Como atualizar prompt do LLM?" | [Prompts Management API](./PROMPTS_MANAGEMENT_API.md) | Atualizar Prompt
"Como fazer upload de arquivo?" | [Document Ingestion](./DOCUMENT_INGESTION.md) | Fluxo de Ingestão
"Quais são os endpoints disponíveis?" | [Complete Documentation](./COMPLETE_DOCUMENTATION.md) | APIs de Chat/Docs
"Como autenticar no frontend?" | [Frontend Integration](./FRONTEND_INTEGRATION.md) | Autenticação MSAL
"Quais dados mestres estão disponíveis?" | [Master Data API](./MASTER_DATA_API.md) | Endpoints de Dados
"Como o LLM processa consultas?" | [Chat API](./CHAT_API.md) | Fluxo de Chat
"Como sincronizar com LLM Server?" | [Prompts Management API](./PROMPTS_MANAGEMENT_API.md) | Sincronização com LLM Server

---

## 📊 Matriz de Recursos x Documentos

| Recurso | Admin API | Prompts API | Chat API | Document API | Master Data | Frontend |
|---------|-----------|-------------|----------|--------------|-------------|----------|
| **Autenticação** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Criar recurso** | ✅ Create | ✅ Create | POST msg | ✅ Upload | ❌ Read-only | - |
| **Ler/Listar** | ✅ Get/List | ✅ Get/List | GET | ✅ Get | ✅ Get/List | - |
| **Atualizar** | ✅ Patch | ✅ Put | - | - | ❌ Read-only | - |
| **Deletar** | ✅ Delete | ✅ Delete | - | - | ❌ Read-only | - |
| **Versionamento** | ❌ | ✅ | ❌ | ✅ | ❌ | - |
| **Sincronização** | ❌ | ✅ LLM | ✅ LLM | ❌ | ❌ | - |
| **Permissões** | ❌ Admin | ❌ Admin | ✅ User | ✅ User | ✅ User | - |

---

## 🔄 Fluxos de Integração

### Fluxo 1: Setup Inicial do Sistema

```
1. Admin Manager inicia sistema
   ↓
2. [Admin Management API] → POST /api/v1/admins/init
   Cria primeiro admin (sem auth necessária)
   ↓
3. Admin autentica e cria mais admins/features
   [Admin Management API] → POST /api/v1/admins
   ↓
4. Admin gerencia prompts dos agentes
   [Prompts Management API] → POST /api/v1/prompts
```

---

### Fluxo 2: Usuário Final Usa o Chat

```
1. Frontend autentica usuario
   [Frontend Integration] → MSAL Login
   ↓
2. Usuario faz pergunta
   [Chat API] → POST /api/v1/chat
   ↓
3. LLM usa prompt do agente
   (Prompt management já foi feito por admin)
   ↓
4. Resposta retorna com documentos relacionados
```

---

### Fluxo 3: Admin Gerencia Recursos

```
1. Admin (via Frontend)
   ↓
2. Cria novo admin
   [Admin Management API] → POST /api/v1/admins
   ↓
3. Atribui features
   [Admin Management API] → POST /{admin_id}/features
   ↓
4. Precisa atualizar prompt?
   [Prompts Management API] → PUT /api/v1/prompts/{agente}
   └→ Auto-sincroniza com LLM Server
```

---

## 📱 Tecnologias Mencionadas

- **FastAPI** - Framework web Python
- **Azure Entra ID / MSAL** - Autenticação
- **Azure SQL Database** - Banco de dados
- **Azure Blob Storage** - Armazenamento de arquivos
- **Azure OpenAI** - LLM e Embeddings
- **Azure AI Search** - Busca semântica
- **React/Angular** - Frontend
- **Docker** - Containerização
- **Python 3.11** - Runtime backend

---

## 🚀 Primeiros Passos

### Opção A: Sou Admin
1. Leia [Admin Management API](./ADMIN_MANAGEMENT_API.md) - Seção "Visão Geral"
2. Execute `/api/v1/admins/init`
3. Leia [Prompts Management API](./PROMPTS_MANAGEMENT_API.md)
4. Crie prompts para seus agentes

### Opção B: Sou Developer Frontend
1. Leia [Project Overview](./PROJECT_OVERVIEW.md)
2. Leia [Frontend Integration](./FRONTEND_INTEGRATION.md)
3. Implemente autenticação MSAL
4. Integre endpoints da API

### Opção C: Sou Developer Backend
1. Leia [Complete Documentation](./COMPLETE_DOCUMENTATION.md)
2. Leia [Admin Management API](./ADMIN_MANAGEMENT_API.md)
3. Leia [Prompts Management API](./PROMPTS_MANAGEMENT_API.md)
4. Estude a arquitetura de sincronização

---

## 📞 Suporte

Para dúvidas ou contribuições:
- Consulte o documento específico relevante
- Revise exemplos de código (cURL, Python, JavaScript)
- Verifique a seção de "Tratamento de Erros"
- Consulte "Troubleshooting" (quando disponível)

---

**Última atualização**: 23 de Fevereiro de 2026  
**Versão da plataforma**: 1.2  
**Status**: Production-Ready
