# Chat API com Histórico de Conversas - IMPLEMENTAÇÃO COMPLETA ✅

## O que foi feito

### 1. **Endpoint de Perguntas** ✅
```
POST /api/v1/chat/question
├─ Recebe pergunta do usuário
├─ Chama LLM Server: /api/v1/question
├─ Salva pergunta + resposta no banco
└─ Retorna resposta completa ao frontend
```

### 2. **Persistência de Conversas** ✅
```
Tabela: conversations
├─ conversation_id (UUID)
├─ user_id
├─ title (opcional)
├─ created_at
├─ updated_at
└─ is_active

Tabela: conversation_messages
├─ message_id (UUID)
├─ conversation_id (FK)
├─ user_id
├─ role (user | assistant)
├─ content (texto completo)
├─ model (ex: gpt-4o-mini)
├─ tokens_used
└─ created_at
```

### 3. **Endpoints CRUD** ✅
```
POST   /api/v1/chat/question                           → Fazer pergunta
GET    /api/v1/chat/conversations/{user_id}           → Listar conversas
GET    /api/v1/chat/conversations/{id}/detail         → Ver conversa completa
DELETE /api/v1/chat/conversations/{id}                → Deletar conversa
```

### 4. **Arquivos Criados** ✅

**Backend:**
- `app/routers/chat.py` - Endpoints de chat
- `app/services/conversation_service.py` - Lógica de persistência
- `app/models.py` - Models Pydantic (expandido com chat models)
- `app/providers/llm_server.py` - Novo método `ask_question()`

**Documentação:**
- `docs/CHAT_API.md` - API completa
- `docs/FRONTEND_INTEGRATION.md` - Guia de integração
- `CHAT_API_EXAMPLES.sh` - Exemplos CURL

**Testes:**
- `test_chat_api.py` - Suite de testes

### 5. **Models Pydantic** ✅
```
QuestionRequest         → Pergunta do usuário
QuestionResponse        → Resposta do LLM
ConversationCreate      → Criar conversa
ConversationResponse    → Conversa (listagem)
ConversationDetail      → Conversa (completo)
ConversationMessage     → Mensagem de conversa
ChatMessage             → Salvar mensagem
```

## Fluxo de Dados

```
┌─────────────────┐
│  Frontend       │
│  (Angular)      │
└────────┬────────┘
         │ POST /api/v1/chat/question
         │ {chat_id, user_id, question, ...}
         ↓
┌─────────────────────────────┐
│  Backend (FastAPI)          │
├─────────────────────────────┤
│ 1. Valida dados             │
│ 2. Cria/obtém conversa      │
│ 3. Chama LLM Server         │
│ 4. Salva pergunta/resposta  │
│ 5. Retorna resposta         │
└────────┬────────────────────┘
         │ Chamar LLM
         ↓
┌──────────────────────────────────────────────────┐
│  LLM Server                                      │
│  POST /api/v1/question                          │
├──────────────────────────────────────────────────┤
│ Processa pergunta                                │
│ Busca documentos relevantes                      │
│ Aplica RBAC (filtro por roles/país/cidade)      │
│ Gera resposta com GPT-4                          │
└────────┬────────────────────────────────────────┘
         │ Retorna {answer, sources, agente, ...}
         ↓
┌─────────────────────────────┐
│  Banco de Dados             │
│  SQL Server                 │
├─────────────────────────────┤
│ Salva:                      │
│ - conversation              │
│ - conversation_messages[2]  │
│   (user + assistant)        │
└─────────────────────────────┘
         ↓
┌─────────────────┐
│  Frontend       │
│  Exibe resposta │
│  + agente       │
│  + fontes       │
└─────────────────┘
```

## Campos da Request

```json
{
  "chat_id": "session_abc123",           // ID da conversa
  "user_id": "emp_12345",                // ID do usuário
  "name": "João Silva",                  // Nome
  "email": "joao@company.com",           // Email
  "country": "Brazil",                   // País (para RBAC)
  "city": "Sao Carlos",                  // Cidade (para RBAC)
  "roles": ["Employee", "Manager"],      // Roles (para RBAC)
  "department": "TI",                    // Departamento
  "job_title": "Analista",               // Cargo
  "collar": "white",                     // Tipo de collar
  "unit": "Engineering",                 // Unidade
  "question": "Quais benefícios?"        // Pergunta
}
```

## Campos da Response

```json
{
  "answer": "Os benefícios incluem...",
  "source_documents": [...],
  "num_documents": 2,
  "classification": {
    "category": "benefícios",
    "confidence": 0.95
  },
  "documents_returned": 2,
  "documents_filtered": 1,
  "top_sources": ["health.pdf", "benefits.pdf"],
  "agente": "documents",
  "total_time_ms": 2345,
  "prompt_tokens": 450,
  "completion_tokens": 120,
  "model": "gpt-4o-mini",
  "generated_at": "2026-01-09T16:42:20Z",
  "rbac_filter_applied": "min_role_level le 1 AND ..."
}
```

## Exemplos de Uso

### 1. Fazer Pergunta
```bash
curl -X POST 'http://localhost:8000/api/v1/chat/question' \
  -H 'Content-Type: application/json' \
  -d '{
    "chat_id": "conv_123",
    "user_id": "user_456",
    "name": "João",
    "email": "joao@company.com",
    "country": "Brazil",
    "city": "Sao Paulo",
    "roles": ["Employee"],
    "question": "Como solicitar folga?"
  }'
```

### 2. Listar Conversas
```bash
curl 'http://localhost:8000/api/v1/chat/conversations/user_456?limit=10'
```

### 3. Ver Detalhes da Conversa
```bash
curl 'http://localhost:8000/api/v1/chat/conversations/conv_123/detail'
```

### 4. Deletar Conversa
```bash
curl -X DELETE 'http://localhost:8000/api/v1/chat/conversations/conv_123'
```

## Dados Salvos no Banco

Para cada pergunta/resposta:

**Mensagem 1 (user):**
```sql
INSERT INTO conversation_messages VALUES (
  'msg_001',           -- message_id
  'conv_123',          -- conversation_id
  'user_456',          -- user_id
  'user',              -- role
  'Quais benefícios?', -- content
  NULL,                -- model
  NULL,                -- tokens_used
  GETUTCDATE()         -- created_at
)
```

**Mensagem 2 (assistant):**
```sql
INSERT INTO conversation_messages VALUES (
  'msg_002',
  'conv_123',
  'user_456',
  'assistant',
  'Os benefícios incluem...',
  'gpt-4o-mini',
  570,  -- prompt_tokens (450) + completion_tokens (120)
  GETUTCDATE()
)
```

## Recursos para o Frontend

### 1. Inicializar Chat
```typescript
this.chatService.startChat(userId).subscribe(conv => {
  this.conversationId = conv.conversation_id;
});
```

### 2. Enviar Pergunta
```typescript
this.chatService.askQuestion({
  chat_id: this.conversationId,
  user_id: this.userId,
  // ... outros campos
  question: userQuestion
}).subscribe(response => {
  this.displayAnswer(response.answer);
  this.displaySources(response.top_sources);
});
```

### 3. Carregar Histórico
```typescript
this.chatService.getConversationDetail(conversationId).subscribe(detail => {
  this.messages = detail.messages;
});
```

### 4. Listar Conversas Anteriores
```typescript
this.chatService.listConversations(userId).subscribe(conversations => {
  this.conversationHistory = conversations;
});
```

## Commits

1. **052c666** - Criar endpoint de chat com histórico de conversas
   - Novo endpoint POST /api/v1/chat/question
   - Integração com LLM Server
   - Sistema de persistência de conversas
   - Models Pydantic para validação

2. **c58b97e** - Adicionar documentação e testes do Chat API
   - Documentação completa em docs/
   - Exemplos CURL
   - Suite de testes

## Status

✅ **IMPLEMENTADO E PRONTO PARA INTEGRAÇÃO**

Próximos passos:
1. Frontend implementar componente de chat
2. Testar com LLM Server em produção
3. Configurar CORS para aplicação frontend
4. Monitorar performance e erros
5. Implementar dashboards com dados das conversas

## Monitoramento

Os dados salvos permitem:
- 📊 Dashboard de perguntas mais frequentes
- 📈 Análise de satisfação (agente + respostas)
- 🎯 Otimização de respostas baseado em histórico
- 🔍 Auditoria completa de todas as interações
- 💾 Retenção de histórico para melhorar contexto do LLM

## Segurança

✅ Autenticação: Via Entra ID (frontend)
✅ Autorização: RBAC aplicado no LLM Server
✅ Auditoria: Todas as mensagens com timestamp
✅ Validação: Pydantic valida todos os inputs
✅ Logging: DEBUG, INFO, ERROR para cada operação
