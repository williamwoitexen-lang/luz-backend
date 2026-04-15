# Integração Frontend → Backend → LLM Server

## Visão Geral da Arquitetura

```
Frontend (Angular)
    ↓
POST /api/v1/chat/question
    ↓
Backend (FastAPI)
    ├─ Cria/obtém conversa no banco
    ├─ Chama LLM Server: POST /api/v1/question
    ├─ Salva pergunta + resposta no banco
    └─ Retorna resposta ao frontend
    ↓
Frontend exibe resposta + agente + documentos
```

## Fluxo Detalhado

### 1. Frontend envia pergunta

O frontend deve enviar uma requisição POST com:

```typescript
// Frontend (Angular)
interface QuestionRequest {
  chat_id: string;           // ID da sessão ou conversa
  user_id: string;           // ID do usuário autenticado
  name: string;              // Nome completo do usuário
  email: string;             // Email do usuário
  country: string;           // País (ex: "Brazil")
  city: string;              // Cidade
  roles: string[];           // Roles do usuário (ex: ["Employee", "Manager"])
  department: string;        // Departamento
  job_title: string;         // Cargo
  collar: string;            // Tipo de collar (ex: "white", "blue")
  unit: string;              // Unidade/Divisão
  question: string;          // A pergunta do usuário
}
```

### 2. Backend recebe e processa

O backend:
1. **Valida** os dados com Pydantic
2. **Cria/obtém** conversa no banco (usando `chat_id` como `conversation_id`)
3. **Chama LLM Server** com todas as informações do usuário
4. **Salva** a pergunta e resposta no banco em 2 linhas:
   - Role: "user", Content: pergunta
   - Role: "assistant", Content: resposta
5. **Retorna** a resposta completa ao frontend

### 3. LLM Server responde

O LLM Server retorna:

```json
{
  "answer": "Texto da resposta...",
  "source_documents": [...],
  "num_documents": 0,
  "classification": {
    "category": "general",
    "confidence": 0.9,
    "reasoning": "..."
  },
  "node_path": ["classifier", "general"],
  "retrieval_time": 0,
  "llm_time": 1.03,
  "total_time": 1.85,
  "message_id": "...",
  "provider": "azure_openai",
  "model": "gpt-4o-mini",
  "generated_at": "2026-01-09T16:42:20Z",
  "rbac_filter_applied": "min_role_level le 1 AND ...",
  "documents_returned": 5,
  "documents_filtered": 3,
  "top_sources": ["doc1.pdf", "doc2.pdf"],
  "total_time_ms": 1849,
  "agente": "general",
  "prompt_tokens": 419,
  "completion_tokens": 93
}
```

## Estrutura de Dados

### Request do Frontend

```json
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
  "question": "Quais benefícios de saúde temos?"
}
```

### Response do Backend

```json
{
  "answer": "Os benefícios incluem...",
  "source_documents": [
    {
      "title": "Benefícios de Saúde",
      "source": "health_benefits.pdf"
    }
  ],
  "num_documents": 1,
  "classification": {
    "category": "benefícios",
    "confidence": 0.95
  },
  "documents_returned": 1,
  "documents_filtered": 0,
  "top_sources": ["health_benefits.pdf"],
  "agente": "documents",
  "total_time_ms": 2345,
  "prompt_tokens": 450,
  "completion_tokens": 120
}
```

## Endpoints para Frontend

### 1. POST /api/v1/chat/question
Fazer pergunta e obter resposta.

**Input:**
- chat_id, user_id, name, email, country, city, roles, department, job_title, collar, unit, question

**Output:**
- answer, source_documents, classification, agente, total_time_ms, prompt_tokens, completion_tokens

### 2. GET /api/v1/chat/conversations/{user_id}
Listar todas as conversas do usuário.

**Output:**
- Array de conversas com conversation_id, title, created_at, message_count

### 3. GET /api/v1/chat/conversations/{conversation_id}/detail
Ver detalhes completos de uma conversa.

**Output:**
- Conversa com array de mensagens (user + assistant)

### 4. DELETE /api/v1/chat/conversations/{conversation_id}
Deletar uma conversa.

## Fluxo no Frontend (Angular)

### 1. Iniciar chat

```typescript
// chat.component.ts
this.chatService.startChat(userId).subscribe(
  (conversation) => {
    this.conversationId = conversation.conversation_id;
    this.messages = [];
  }
);
```

### 2. Enviar pergunta

```typescript
// chat.component.ts
this.chatService.askQuestion({
  chat_id: this.conversationId,
  user_id: this.userId,
  name: this.userName,
  email: this.userEmail,
  country: this.userCountry,
  city: this.userCity,
  roles: this.userRoles,
  department: this.userDepartment,
  job_title: this.userJobTitle,
  collar: this.userCollar,
  unit: this.userUnit,
  question: userQuestion
}).subscribe(
  (response) => {
    // Adicionar pergunta à conversa
    this.messages.push({
      role: 'user',
      content: userQuestion,
      timestamp: now
    });
    
    // Adicionar resposta
    this.messages.push({
      role: 'assistant',
      content: response.answer,
      timestamp: now,
      sources: response.top_sources,
      agent: response.agente,
      timeMs: response.total_time_ms
    });
  }
);
```

### 3. Listar conversas anteriores

```typescript
// chat-history.component.ts
this.chatService.listConversations(userId).subscribe(
  (conversations) => {
    this.conversations = conversations;
    // conversations[i].message_count -> número de mensagens
    // conversations[i].updated_at -> última atualização
  }
);
```

### 4. Ver detalhes de conversa

```typescript
// chat-detail.component.ts
this.chatService.getConversationDetail(conversationId).subscribe(
  (detail) => {
    // detail.messages[i].role: 'user' | 'assistant'
    // detail.messages[i].content: texto da mensagem
    // detail.messages[i].model: modelo LLM (se assistant)
  }
);
```

## Dados Armazenados no Banco

### Tabela: conversations
- conversation_id (PK)
- user_id (FK)
- title (opcional)
- created_at
- updated_at
- is_active

### Tabela: conversation_messages
- message_id (PK)
- conversation_id (FK)
- user_id (FK)
- role (user | assistant)
- content (texto completo)
- model (ex: gpt-4o-mini)
- tokens_used (prompt + completion)
- created_at

## Casos de Uso

### 1. Chat em tempo real
Frontend faz pergunta → Backend chama LLM → Resposta retorna em ~2s

### 2. Histórico de chat
Frontend lista conversas → Mostra últimas perguntas/respostas

### 3. Análise de conversas
Backend consulta conversation_messages → Dashboard de perguntas frequentes

### 4. Recomendações personalizadas
Usar histórico de conversa para melhorar próximas respostas do LLM

### 5. Auditoria
Cada pergunta/resposta é rastreada com timestamp e metadados

## Tratamento de Erros

### Se LLM Server está indisponível
```
Status: 500
Error: "Erro ao processar pergunta: LLM Server connection failed"
```

### Se conversa não existe
```
Status: 404
Error: "Conversa não encontrada: conv_123"
```

### Se faltar campo obrigatório
```
Status: 422
Error: "name field is required"
```

## Performance

- **Tempo de resposta**: 1-3 segundos (dependendo do tamanho da pergunta e documentos)
- **Timeout**: 300 segundos (para arquivos grandes)
- **Limite de conversas**: 50 por padrão (ajustável via query param)

## Segurança

- **Autenticação**: Via Entra ID (assumir que frontend já autenticou)
- **Autorização**: RBAC aplicado no LLM Server (filtro de documentos)
- **Auditoria**: Todas as perguntas/respostas são registradas com timestamp

## Próximos Passos

1. **Frontend implementar**: Componente de chat com histórico
2. **Backend monitorar**: Erros e latência de perguntas
3. **Analytics**: Dashboard de perguntas mais frequentes
4. **Melhorias**: Usar histórico para melhorar contexto do LLM
