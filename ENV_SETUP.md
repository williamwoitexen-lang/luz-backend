# 🔐 Setup de Credenciais Locais

## Como Configurar `.env` para Desenvolvimento

### 1️⃣ Copiar Template

```bash
cp .env.example .env
```

### 2️⃣ Preencher Variáveis

Abra `.env` e substitua os placeholders:

| Variável | Onde Encontrar | Exemplo |
|----------|----------------|---------|
| `AZURE_TENANT_ID` | Azure Portal → Entra ID → Overview | `d2007bef-127d-...` |
| `AZURE_CLIENT_ID` | Azure Portal → App Registrations | `abeecec0-3c24-...` |
| `` | Azure Portal → App → Certificates & secrets | `83D8Q~ha1l...` |
| `SQLSERVER_CONNECTION_STRING` | Azure Portal → SQL Server → Connection strings | `Driver={ODBC...}` |
| `AZURE_STORAGE_ACCOUNT_NAME` | Azure Portal → Storage Account → Overview | `yourstorageaccount` |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Portal → Storage → Access keys | `DefaultEndpoints...` |
| `OPENAI_API_KEY` | Azure Portal → OpenAI → Keys and Endpoint | `sk-proj-...` |

### 3️⃣ ⚠️ IMPORTANTE

- **NUNCA** faça commit do `.env`
- `.env` está no `.gitignore` ✅
- Se acidentalmente commitou: avisar time imediatamente e revogar credenciais

### 4️⃣ Testar

```bash
# Verificar que .env foi carregado
uvicorn app.main:app --reload

# Em outro terminal
curl http://localhost:8000/
# Se retorna JSON → ✅ Setup correto
```

### 5️⃣ Para a Reunião

- ✅ `.env.example` existe e está commitado
- ✅ `.env` real está no `.gitignore` 
- ✅ Credenciais seguras
- ✅ Pronto para apresentar

---

## Troubleshooting

**"ModuleNotFoundError" ao rodar**
```bash
pip install -r requirements.txt
```

**"KeyError: AZURE_TENANT_ID"**
→ Verificar se `.env` foi copiado e preenchido

**"Connection refused" (SQL Server)**
→ Verificar SQLSERVER_CONNECTION_STRING está correto

---

## Para Produção

Em produção, **NUNCA** use `.env`:

1. Variáveis vêm do **Azure KeyVault** via pipeline
2. Docker container recebe variáveis do **Azure App Service** ou **Azure Container Instances**
3. Nenhum arquivo `.env` no servidor

---

✅ **Setup completo! Pronto para reunião.** 🚀
