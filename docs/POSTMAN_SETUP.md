# Postman Collection Setup - Luz Backend API

## 📥 Como Importar

### Passo 1: Abra Postman
- Downloads: https://www.postman.com/downloads/
- Ou use Postman Web: https://web.postman.co

### Passo 2: Importar Collection
1. Clique em **Import** (canto superior esquerdo)
2. Selecione arquivo: `docs/Luz-API.postman_collection.json`
3. Clique **Import**

### Passo 3: Configurar Environment

#### Opção A: Variables Inline (Mais Simples)
1. Collection carrega com variáveis padrão:
   - `{{baseUrl}}` = `http://localhost:8000/api/v1`
   - `{{token}}` = vazio
   - `{{temp_id}}` = vazio

#### Opção B: Environment Variables (Recomendado)
1. Clique engrenagem (Settings)
2. **Create Environment** com nome `LUZ-LOCAL`
3. Adicione variáveis:
   ```
   baseUrl: http://localhost:8000/api/v1
   token: (deixe vazio, será preenchido após login)
   temp_id: (deixe vazio, será preenchido após preview)
   ```
4. Selecione este environment no dropdown

## 🔐 Fluxo de Autenticação

### Passo 1: Login com Azure AD
1. Na Collection, abra pasta **🔐 Authentication**
2. Selecione request **1. Login - Redirecionar para Azure AD**
3. Clique **Send** (abrirá janela de autenticação Azure)
4. Complete o login com credenciais Azure AD

### Passo 2: Copiar Token
1. Após login bem-sucedido, você verá:
   - Redirect para `http://localhost:8000/api/v1/...`
   - JWT token no cookie (HTTPOnly)
2. **O token é enviado automaticamente em requests posteriores**
   - Postman mantém cookies entre requests

### Verificar Autenticação
- Request **3. Check Auth Status** validará se JWT é válido

## 📋 Estrutura da Collection

### 🔐 Authentication (5 requests)
- Login (Azure AD redirect)
- Get Token (callback)
- Check Auth Status
- Get User Role
- Logout

### 📍 Master Data - Locations (9 requests)
- List all locations
- Active locations only
- Filter by country
- Filter by region
- Get all countries
- Get all regions
- Cities by country
- Cities by region
- Location hierarchy

### 👔 Master Data - Roles & Categories (6 requests)
- All roles
- Active roles
- Specific role by ID
- All categories
- Active categories
- Specific category by ID

### 📄 Documents - Ingest (3 requests)
- **Preview** (extrai metadados com LLM)
- **Confirm** (usa temp_id do preview)
- Direct ingest (upload + index em uma request)

### 📄 Documents - Manage (8 requests)
- List all documents (paginado)
- Filter by country
- Filter by category
- Get details
- Get versions
- Search (semântica)
- Update metadata
- Delete

### 💬 Chat & Conversations (3 requests)
- Ask question (com contexto de usuário)
- Get conversations by user
- Get conversation messages

### 📊 Dashboard & Analytics (3 requests)
- Dashboard stats
- Top questions
- User activity

### ⚙️ Health & Debug (2 requests)
- Health check
- Swagger UI link

## 🚀 Exemplos Comuns

### Exemplo 1: Fazer uma Pergunta ao Chat
```
1. Request: 💬 Chat & Conversations → 1. Ask Question
2. Body (JSON):
   {
     "chat_id": "session_test_1",
     "user_id": "alice@company.com",
     "name": "Alice Silva",
     "email": "alice@company.com",
     "country": "Brazil",
     "city": "São Paulo",
     "roles": ["Manager", "Employee"],
     "department": "HR",
     "job_title": "HR Manager",
     "collar": "white",
     "unit": "LATAM",
     "question": "Quais benefícios temos?"
   }
3. Click Send
```

### Exemplo 2: Upload de Documento
```
1. Preview + Confirm (2-step recomendado):
   a) Request: 📄 Documents - Ingest → 1. Ingest Preview
      - Selecione arquivo em "file"
      - Click Send → copia "temp_id" da resposta
   
   b) Request: 📄 Documents - Ingest → 2. Ingest Confirm
      - Substitua {{temp_id}} na URL com temp_id copiado
      - Preencha metadata (allowed_countries, category_id, etc)
      - Click Send

2. OU Direct Ingest (1-step mais rápido):
   a) Request: 📄 Documents - Ingest → 3. Direct Ingest
      - Preencha arquivo + metadados
      - Click Send
```

### Exemplo 3: Buscar Documentos
```
1. Request: 📄 Documents - Manage → 3. Filter Documents by Category
2. Modifique query parameter: category_id=1
3. Click Send
```

## 📝 Notas Importantes

### Variáveis Dinâmicas
- `{{baseUrl}}` - Use localhost (DEV), staging (QA), ou prod
- `{{token}}` - Preenchido automaticamente via HTTPOnly cookie
- `{{temp_id}}` - Copiar manualmente do response do Preview

### Headers Automáticos
- `Content-Type`: application/json (adicionado automaticamente)
- `Authorization`: Enviado via cookie HTTPOnly

### Timeouts
- Padrão: 5 minutos (some requests de LLM podem ser lentas)
- Para ajustar: Settings → General → Request timeout

### Cookies vs Token Header
- **Esta API usa HTTPOnly cookies**, não headers Authorization
- Postman detecta automaticamente e mantém cookies entre requests
- Se precisar usar header: adicione manualmente `Authorization: Bearer {{token}}`

## 🐛 Troubleshooting

### "401 Unauthorized"
1. Email do usuário não está cadastrado em Entra ID
2. Token expirou → refaça login
3. Cookies desativados no Postman → Settings → Cookies → enable

### "404 Not Found"
- URL errada (verificar `{{baseUrl}}`)
- Servidor não está rodando → `python -m app.main` ou Docker

### "500 Internal Server Error"
- LLM Server offline (para documentos + chat)
- Database connection problem
- Verificar logs: `docker logs container-name`

### Preview não retorna temp_id
- LLM pode estar lento (15-30s em documentos longos)
- Aumentar timeout em Postman Settings
- Verificar se LLM_SERVER_URL está correto

## 🔗 Links Úteis

| Recurso | Link |
|---------|------|
| Swagger API Docs | http://localhost:8000/docs |
| ReDoc Docs | http://localhost:8000/redoc |
| Config Reference | [CONFIG_KEYS.md](CONFIG_KEYS.md) |
| Troubleshooting | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Architecture | [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) |
| Local Setup | [RUN_LOCAL_COMPLETE_GUIDE.md](RUN_LOCAL_COMPLETE_GUIDE.md) |

## 📞 Dúvidas?

- Postman Learning Center: https://learning.postman.com/
- API Documentation: [docs/](.)
- Team Slack: #backend-api-support
