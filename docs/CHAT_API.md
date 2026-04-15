# Chat com LLM Server - Documentação

## Visão Geral

O sistema agora suporta conversas com o LLM Server, salvando todo o histórico no banco de dados para criar um histórico de chat persistente.

## Fluxo

```
Frontend
   ↓
POST /api/v1/chat/question
   ↓
Backend:
  1. Cria/obtém conversa (usando chat_id como conversation_id)
  2. Chama LLM Server: POST /api/v1/question
  3. Salva pergunta + resposta no banco (conversations + conversation_messages)
  4. Retorna resposta do LLM para frontend
   ↓
Frontend recebe resposta + agente + documentos
```

## Endpoints

### 1. Fazer Pergunta e Obter Resposta

**POST** `/api/v1/chat/question`

**Request:**
```json
{
  "chat_id": "session_abc123",
  "question": "o que você pode me dizer sobre futebol?",
  "user_id": "emp_12345",
  "name": "João Silva",
  "email": "joao.silva@company.com",
  "country": "Brazil",
  "city": "Sao Carlos",
  "role_id": 1,
  "department": "TI",
  "job_title": "Analista de TI",
  "collar": "white",
  "unit": "Engineering",
  "agent_id": 1
}
```

**Response:**
```json
{
  "answer": "Olá, João! 😊 Eu sou a Luz, assistente de RH...",
  "source_documents": [],
  "num_documents": 0,
  "classification": {
    "category": "general",
    "confidence": 0.9
  },
  "retrieval_time": 0,
  "llm_time": 1.03,
  "total_time": 1.85,
  "total_time_ms": 1849,
  "message_id": "02353418-913e-4acc-beb8-673597ff98d7",
  "provider": "azure_openai",
  "model": "gpt-4o-mini",
  "generated_at": "2026-01-09T16:42:20.446004Z",
  "rbac_filter_applied": "min_role_level le 1 AND ...",
  "documents_returned": 5,
  "documents_filtered": 3,
  "top_sources": ["health_benefits_brazil.pdf"],
  "agente": "general",
  "prompt_tokens": 419,
  "completion_tokens": 93
}
```

### 2. Listar Conversas de um Usuário

**GET** `/api/v1/chat/conversations/{user_id}?limit=50`

**Response:**
```json
[
  {
    "conversation_id": "conv_abc123",
    "user_id": "emp_12345",
    "title": "Benefícios de Saúde",
    "created_at": "2026-01-09T10:00:00",
    "updated_at": "2026-01-09T16:42:20",
    "is_active": true,
    "message_count": 5
  }
]
```

### 3. Obter Detalhes Completos de uma Conversa

**GET** `/api/v1/chat/conversations/{conversation_id}/detail`

**Response:**
```json
{
  "conversation_id": "conv_abc123",
  "user_id": "emp_12345",
  "title": "Benefícios de Saúde",
  "created_at": "2026-01-09T10:00:00",
  "updated_at": "2026-01-09T16:42:20",
  "is_active": true,
  "messages": [
    {
      "message_id": "msg_001",
      "conversation_id": "conv_abc123",
      "role": "user",
      "content": "Quais são os benefícios de saúde?",
      "model": null,
      "prompt_tokens": null,
      "completion_tokens": null,
      "created_at": "2026-01-09T10:00:00"
    },
    {
      "message_id": "msg_002",
      "conversation_id": "conv_abc123",
      "role": "assistant",
      "content": "Os benefícios de saúde incluem plano Unimed...",
      "model": "gpt-4o-mini",
      "prompt_tokens": 450,
      "completion_tokens": 120,
      "created_at": "2026-01-09T10:00:02"
    }
  ]
}
```

### 4. Deletar Conversa (Soft Delete)

**DELETE** `/api/v1/chat/conversations/{conversation_id}`

**Response:**
```json
{
  "message": "Conversa deletada com sucesso",
  "conversation_id": "conv_abc123"
}
```

### 5. Avaliar Resposta (Rating)

**POST** `/api/v1/chat/{chat_id}/rate`

**Request:**
```json
{
  "rating": 4.5,
  "comment": "Resposta muito útil, mas faltou um detalhe"
}
```

**Parameters:**
- `chat_id`: ID da conversa a ser avaliada
- `rating`: Nota de 0.0 a 5.0 em múltiplos de 0.5 (ex: 0, 0.5, 1.0, 1.5, ..., 5.0)
- `comment`: Comentário opcional (obrigatório se rating = 1.0, para feedback de problemas)

**Response:**
```json
{
  "conversation_id": "conv_abc123",
  "rating": 4.5,
  "comment": "Resposta muito útil, mas faltou um detalhe",
  "message": "Avaliação salva com sucesso"
}
```

**Notas:**
- O endpoint de rating é **controlado 100% pelo frontend**
- Sistema de rating automático foi **removido**
- A avaliação é opcional e pode ser feita a qualquer momento após a conversa
- Uma conversa pode ser avaliada apenas uma vez (última avaliação sobrescreve a anterior)
- Se rating = 1.0, comentário é obrigatório (deve descrever o problema)

### 6. Streaming de Resposta em Tempo Real (SSE)

**POST** `/api/v1/chat/question/stream`

Permite receber a resposta do LLM em tempo real através de **Server-Sent Events (SSE)**, token por token, enquanto o LLM está gerando a resposta. Ideal para frontend exibir texto sendo digitado em tempo real (typewriter effect).

**Request:**
```json
{
  "chat_id": "session_abc123",
  "question": "Qual é a política de férias?",
  "user_id": "emp_12345",
  "name": "João Silva",
  "email": "joao.silva@company.com",
  "country": "Brazil",
  "city": "Sao Carlos",
  "role_id": 1,
  "department": "TI",
  "job_title": "Analista de TI",
  "collar": "white",
  "unit": "Engineering",
  "agent_id": 1
}
```

**Streaming Response (SSE - Server-Sent Events):**

O servidor envia eventos em tempo real:

```
data: {"event":"token","token":"A"}\n\n
data: {"event":"token","token":" "}\n\n
data: {"event":"token","token":"política"}\n\n
data: {"event":"token","token":" "}\n\n
...
data: {"event":"metadata","metadata":{"message_id":"02353418-913e-4acc-beb8-673597ff98d7","model":"gpt-4o-mini","prompt_tokens":419,"completion_tokens":93,"total_time_ms":1849}}\n\n
data: {"event":"complete","answer":"A política de férias..."}\n\n
```

**Eventos Enviados:**

1. **token** (múltiplos) - Cada caractere/token gerado
```json
{"event": "token", "token": "A"}
```

2. **metadata** (uma vez) - Metadados da resposta
```json
{
  "event": "metadata",
  "metadata": {
    "message_id": "02353418-913e-4acc-beb8-673597ff98d7",
    "model": "gpt-4o-mini",
    "prompt_tokens": 419,
    "completion_tokens": 93,
    "total_time_ms": 1849,
    "provider": "azure_openai"
  }
}
```

3. **complete** (uma vez) - Resposta completa ao final
```json
{
  "event": "complete",
  "answer": "A política de férias é de 30 dias por ano, com direito a adicional de 1/3..."
}
```

**Cliente JavaScript (Exemplo Completo):**

```javascript
// URL do endpoint de streaming
const streamUrl = 'http://localhost:8000/api/v1/chat/question/stream';

// Dados da pergunta
const question = {
  chat_id: 'session_abc123',
  question: 'Qual é a política de férias?',
  user_id: 'emp_12345',
  name: 'João Silva',
  email: 'joao.silva@company.com',
  country: 'Brazil',
  city: 'Sao Carlos',
  role_id: 1,
  agent_id: 1
};

// Elemento HTML para exibir resposta
const responseDiv = document.getElementById('response');

// Usar EventSource para conectar ao streaming
async function streamQuestion() {
  const eventSource = new EventSource(
    streamUrl + '?q=' + encodeURIComponent(JSON.stringify(question))
  );

  let completeAnswer = '';

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      switch (data.event) {
        case 'token':
          // Exibir token (efeito de digitação)
          responseDiv.textContent += data.token;
          break;

        case 'metadata':
          // Salvar metadados
          console.log('Modelo:', data.metadata.model);
          console.log('Tokens:', data.metadata.prompt_tokens + data.metadata.completion_tokens);
          console.log('Tempo:', data.metadata.total_time_ms + 'ms');
          break;

        case 'complete':
          // Fechar conexão quando completo
          completeAnswer = data.answer;
          eventSource.close();
          console.log('Streaming concluído');
          break;
      }
    } catch (error) {
      console.error('Erro ao processar evento:', error);
    }
  };

  eventSource.onerror = (error) => {
    console.error('Erro no streaming:', error);
    eventSource.close();
  };
}

// Iniciar streaming
streamQuestion();
```

**Cliente Python (Exemplo Completo):**

```python
import requests
import json

question = {
    'chat_id': 'session_abc123',
    'question': 'Qual é a política de férias?',
    'user_id': 'emp_12345',
    'name': 'João Silva',
    'email': 'joao.silva@company.com',
    'country': 'Brazil',
    'city': 'Sao Carlos',
    'role_id': 1,
    'agent_id': 1
}

# Fazer request com streaming habilitado
response = requests.post(
    'http://localhost:8000/api/v1/chat/question/stream',
    json=question,
    stream=True
)

complete_answer = ''

# Processar eventos SSE
for line in response.iter_lines():
    if line:
        # Parse SSE format (data: {...})
        if line.startswith(b'data: '):
            event_data = json.loads(line[6:])  # Remove 'data: '

            if event_data['event'] == 'token':
                # Exibir token
                print(event_data['token'], end='', flush=True)

            elif event_data['event'] == 'metadata':
                # Salvar metadados
                print('\n\nMetadados:', event_data['metadata'])

            elif event_data['event'] == 'complete':
                # Streaming concluído
                complete_answer = event_data['answer']
                print('\n\nCompleto')

# Salvar caso precise da resposta completa
print(f'Resposta completa: {complete_answer}')
```

**Cliente cURL (Para Teste):**

```bash
# Enviar JSON como query parameter
curl -N http://localhost:8000/api/v1/chat/question/stream \
  -d '{
    "chat_id": "session_abc123",
    "question": "Qual é a política de férias?",
    "user_id": "emp_12345",
    "name": "João Silva",
    "email": "joao.silva@company.com",
    "country": "Brazil",
    "city": "Sao Carlos",
    "role_id": 1,
    "agent_id": 1
  }'
```

## Endpoint de Teste (Debug)

**GET** `/api/v1/chat/test/stream`

Endpoint de teste que simula um streaming de resposta sem chamar o LLM Server. Útil para testar cliente SSE sem dependências externas.

**Response:** Stream de eventos SSE igual ao `/question/stream`

```bash
curl -N http://localhost:8000/api/v1/chat/test/stream
```

## 7. Preferências de Memória (Auto-Load)

### Memory Preferences

A primeira mensagem de uma conversa carrega automaticamente as preferências de memória do usuário do banco de dados.

**O que é Memory Preferences:**
- Informações que o sistema "lembra" do usuário
- Salvos em `user_preferences.memory_preferences` (JSON)
- Automaticamente carregados quando conversa começa
- Contexto é passado para LLM nas futuras mensagens

**Exemplo:**
```json
{
  "preferred_section": "Benefits",
  "previous_questions": ["vacation policy", "health insurance"],
  "context": "Brasileiro, trabalha em São Carlos",
  "skill_level": "intermediate"
}
```

**Como Funciona:**

```
Cliente HTTP
   ↓
POST /api/v1/chat/question (primeira mensagem)
   │
   ├─ Backend detecta: primeira_msg == true
   │
   └─ Auto-load memory preferences:
      ├─ SELECT memory_preferences FROM user_preferences WHERE user_id = 'emp_12345'
      ├─ Se existe: passa para LLM como context
      └─ Se não existe: cria vazio {}
   ↓
LLM Server recebe prompt com context
   │
   ├─ "Contexto do usuário: [memory_preferences]"
   └─ Usa para personalizar resposta
   ↓
Response + Context fornecido
```

**Frontend não precisa fazer nada:**
- Memory preferences são carregadas automaticamente pelo backend
- Todas as mensagens da conversa usam o contexto
- Sem API call adicional necessária

### Preferred Language

Similarhmente, `preferred_language` é carregado automaticamente:

**Em `user_preferences` table:**
```sql
user_id: 'emp_12345'
preferred_language: 'pt-BR'  -- Português Brasileiro
```

**Comportamento:**
- Primeira mensagem carrega `preferred_language`
- LLM Server recebe como parte do contexto
- Todas respostas seguem esse idioma
- Se não especificado: fallback para `en-US`

**Exemplo Completo:**

```python
# Backend (em routers/chat.py) - já implementado
@app.post("/api/v1/chat/question")
async def ask_question(request: ChatRequest, current_user = Depends(get_current_user)):
    
    # 1. Na primeira mensagem da conversa
    if is_first_message_in_conversation(request.chat_id):
        
        # Auto-load memory preferences
        prefs = await user_preference_service.get_preferences(request.user_id)
        memory_preferences = prefs.get("memory_preferences", {})
        preferred_language = prefs.get("preferred_language", "en-US")
        
        # Passar para LLM Server
        llm_request = {
            "question": request.question,
            "context": {
                "memory_preferences": memory_preferences,
                "preferred_language": preferred_language,
                "user_info": {...}
            }
        }
    
    # 2. Chamar LLM
    response = await llm_server.ask(llm_request)
    
    # 3. Retornar com contexto
    return {
        "answer": response.answer,
        "context_provided": True,
        "language": preferred_language
    }
```

### Atualizar Preferências

Para atualizar memory_preferences ou preferred_language, use [User Preferences API](./USER_PREFERENCES_API.md):

```bash
# Atualizar memory_preferences
curl -X PUT http://localhost:8000/api/v1/user-preferences/memory \
  -H "Authorization: Bearer {token}" \
  -d '{
    "memory_preferences": {
      "preferred_section": "Health Insurance",
      "previous_questions": ["coverage", "deductible"]
    }
  }'

# Atualizar preferred_language
curl -X PUT http://localhost:8000/api/v1/user-preferences/language \
  -H "Authorization: Bearer {token}" \
  -d '{
    "preferred_language": "es-ES"
  }'
```

### Notas Importantes

- ⚠️ Memory preferences são carregados **uma vez** na primeira mensagem
- 📝 Para mudanças aplicarem: comece nova conversa
- 🔄 Preferências em cache: até 15 minutos
- 💾 Salvo em Redis se disponível, fallback SQL Server

## Estrutura do Banco

### Tabela: `conversations`
```sql
CREATE TABLE conversations (
    conversation_id NVARCHAR(36) PRIMARY KEY,
    user_id NVARCHAR(255) NOT NULL,
    document_id INT,
    title NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    is_active BIT DEFAULT 1,
    rating FLOAT,                           -- Avaliação de 0.0 a 5.0 (múltiplos de 0.5)
    rating_timestamp DATETIME2,             -- Quando foi avaliada
    rating_comment NVARCHAR(MAX),           -- Comentário/feedback do usuário
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_rating (rating)
);
```

### Tabela: `conversation_messages`
```sql
CREATE TABLE conversation_messages (
    message_id NVARCHAR(36) PRIMARY KEY,
    conversation_id NVARCHAR(36) NOT NULL,
    user_id NVARCHAR(255) NOT NULL,
    role NVARCHAR(50) NOT NULL,  -- 'user' ou 'assistant'
    content NVARCHAR(MAX) NOT NULL,
    tokens_used INT,
    model NVARCHAR(100),
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_user_id (user_id)
);
```

## Dados Salvos

Para cada pergunta/resposta, salvamos:

**Pergunta (role='user'):**
- `conversation_id`: ID da conversa
- `user_id`: ID do usuário
- `role`: "user"
- `content`: Pergunta do usuário
- `created_at`: Timestamp

**Resposta (role='assistant'):**
- `conversation_id`: ID da conversa
- `user_id`: ID do usuário
- `role`: "assistant"
- `content`: Resposta completa do LLM Server
- `model`: Modelo usado (ex: "gpt-4o-mini")
- `tokens_used`: Total de tokens (prompt + completion)
- `created_at`: Timestamp

## Dados do LLM Server Salvos

Cada resposta do LLM Server inclui:

- **answer**: Resposta em texto
- **rbac_filter_applied**: Filtro RBAC aplicado para os documentos
- **documents_returned**: Documentos que corresponderam
- **documents_filtered**: Documentos excluídos por RBAC
- **top_sources**: Nomes dos arquivos principais
- **total_time_ms**: Tempo total em ms
- **agente**: "general" ou "documents"
- **prompt_tokens**: Tokens de entrada
- **completion_tokens**: Tokens de saída

## Múltiplos Agentes (IAs)

O sistema suporta diferentes agentes/IAs via parâmetro `agent_id`:

| agent_id | Nome | Descrição |
|----------|------|-----------|
| 1 | LUZ | Gerenciador de assuntos de RH (padrão) |
| 2 | IGP | Gerenciador IGP (a ser definido) |
| 3 | SMART | Gerenciador SMART (a ser definido) |

**Como usar:**

```json
{
  "chat_id": "session_123",
  "question": "Minha pergunta",
  "user_id": "emp_12345",
  "name": "João",
  "email": "joao@company.com",
  "agent_id": 2
}
```

Se não informado, o padrão é `agent_id: 1` (LUZ).

## Fluxo de Uso

### 1. Frontend faz pergunta
```bash
curl -X POST http://localhost:8000/api/v1/chat/question \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "conv_abc123",
    "user_id": "emp_12345",
    "name": "João Silva",
    "email": "joao@company.com",
    "country": "Brazil",
    "city": "São Carlos",
    "role_id": 1,
    "question": "Quais benefícios temos?",
    "agent_id": 1
  }'
```

### 2. Backend processa
1. Cria conversa se não existir
2. Chama LLM Server
3. Salva pergunta e resposta
4. Retorna resposta

### 3. Frontend pode listar conversas
```bash
curl http://localhost:8000/api/v1/chat/conversations/emp_12345
```

### 4. Frontend pode ver detalhes
```bash
curl http://localhost:8000/api/v1/chat/conversations/conv_abc123/detail
```

## Próximos Passos

1. **Dashboards**: Usar `conversation_messages` para criar dashboards de perguntas mais frequentes
2. **Analytics**: Trackear sentimento, categorias de perguntas, tempo de resposta
3. **Recomendações**: Usar histórico para recomendar documentos relevantes
4. **Personalizações**: Usar histórico de conversa para melhorar respostas do LLM

## CURL Examples

### Fazer pergunta
```bash
curl -X POST 'http://localhost:8000/api/v1/chat/question' \
  -H 'Content-Type: application/json' \
  -d '{
    "chat_id": "session_123",
    "user_id": "user_456",
    "name": "John Doe",
    "email": "john@example.com",
    "country": "Brazil",
    "city": "Sao Paulo",
    "role_id": 1,
    "department": "Engineering",
    "job_title": "Engineer",
    "collar": "white",
    "unit": "Tech",
    "question": "How do I request time off?",
    "agent_id": 1
  }'
```

### Listar conversas
```bash
curl 'http://localhost:8000/api/v1/chat/conversations/user_456?limit=10'
```

### Ver detalhes da conversa
```bash
curl 'http://localhost:8000/api/v1/chat/conversations/session_123/detail'
```

### Deletar conversa
```bash
curl -X DELETE 'http://localhost:8000/api/v1/chat/conversations/session_123'
```
