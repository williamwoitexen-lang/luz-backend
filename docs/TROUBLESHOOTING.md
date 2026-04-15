# 🔧 Troubleshooting - Solução de Problemas Comuns

**Guia rápido para resolver os 20+ problemas mais comuns durante setup, testes e execução.**

---

## 📋 Índice de Problemas

### Setup & Dependências
- [Python não encontrado](#python-não-encontrado)
- [ODBC Driver não encontrado](#odbc-driver-não-encontrado)
- [ModuleNotFoundError ao rodar](#modulenotfounderror-ao-rodar)
- [pip install falha](#pip-install-falha)

### Variáveis de Ambiente
- [Variáveis não estão sendo lidas](#variáveis-não-estão-sendo-lidas)
- [ não definida](#azure_client_secret-não-definida)
- [KeyError em variáveis obrigatórias](#keyerror-em-variáveis-obrigatórias)

### Conexões & Rede
- [Connection refused (SQL Server)](#connection-refused-sql-server)
- [Connection refused (LLM Server)](#connection-refused-llm-server)
- [Timeout conectando ao Azure](#timeout-conectando-ao-azure)
- [Port 8000 já em uso](#port-8000-já-em-uso)

### Autenticação & Credenciais
- [MSAL authentication failed](#msal-authentication-failed)
- [Azure credentials expiradas](#azure-credentials-expiradas)
- [401 Unauthorized em endpoints](#401-unauthorized-em-endpoints)

### Aplicação & Runtime
- [Application failed to start](#application-failed-to-start)
- [Memory overflow / Out of memory](#memory-overflow--out-of-memory)
- [Endpoint retorna 500 Internal Server Error](#endpoint-retorna-500-internal-server-error)

### Docker & Containers
- [Docker daemon not running](#docker-daemon-not-running)
- [Container exits immediately](#container-exits-immediately)
- [Volume mounting issues](#volume-mounting-issues)

### Testes & CI/CD
- [Testes falhando localmente](#testes-falhando-localmente)
- [Testes passam local mas falham em CI](#testes-passam-local-mas-falham-em-ci)

---

## Setup & Dependências

### Python não encontrado

**Sintoma**:
```
command not found: python3
```

**Causa**: Python não está instalado ou não está no PATH

**Solução**:

```bash
# 1. Verificar se está instalado
python3 --version
# ou
python --version

# 2. Se não está instalado:
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# macOS
brew install python@3.11

# Windows
# Baixar de: https://www.python.org/downloads/
# ✅ Marcar "Add Python to PATH" durante instalação

# 3. Verificar após instalar
python3 --version  # Deve ser 3.11+
```

**Verificar PATH** (se problema persiste):
```bash
# Linux/macOS
echo $PATH | tr ':' '\n' | grep python

# Windows PowerShell
$env:PATH -split ';' | Select-String python

# Se Python não está em PATH:
# Linux/macOS: adicionar a ~/.bashrc ou ~/.zshrc
# export PATH="/usr/bin/python3:$PATH"
# Windows: Variáveis de ambiente → PATH
```

---

### ODBC Driver não encontrado

**Sintoma**:
```
pyodbc.DatabaseError: ('HY000', "[HY000] ODBC Driver 17 for SQL Server not found [ODBC Driver 17 for SQL Server]")
```

**Causa**: Driver ODBC para SQL Server não está instalado

**Solução** (por SO):

**Ubuntu/Debian**:
```bash
# 1. Adicionar repo da Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/focal/prod.list | tee /etc/apt/sources.list.d/mssql-release.list

# 2. Instalar
sudo apt update
sudo ACCEPT_EULA=Y apt install -y odbc-driver-18-for-sql-server

# 3. Verificar
odbcinst -q -l -d | grep "ODBC Driver"
```

**macOS**:
```bash
# 1. Instalar com Homebrew
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew install mssql-tools18

# 2. Atualizar PATH (se necessário)
echo 'export PATH="/usr/local/opt/mssql-tools18/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 3. Verificar
odbcinst -q -l -d
```

**Windows**:
```powershell
# 1. Download installer
# https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

# 2. Executar .msi (Next > Next > Finish)

# 3. ⚠️ REINICIAR Windows após instalar

# 4. Verificar no PowerShell
Get-OdbcDriver -Name "*SQL Server*"
```

---

### ModuleNotFoundError ao rodar

**Sintoma**:
```
ModuleNotFoundError: No module named 'pyodbc'
ModuleNotFoundError: No module named 'fastapi'
```

**Causa**: Dependências não instaladas ou venv não ativado

**Solução**:

```bash
# 1. Verificar se venv está ativo
# Linux/macOS: deve ter "(venv)" no prompt
# Windows: prompt contém "venv"

# Se NÃO ativo:
source venv/bin/activate  # Linux/macOS
# ou
.\venv\Scripts\activate   # Windows

# 2. Reinstalar dependências
pip install --upgrade pip
pip install --force-reinstall -r requirements.txt

# 3. Verificar instalação
pip list | grep fastapi
python -c "import pyodbc; print(pyodbc.version)"

# 4. Se ainda falhar, reconstruir venv
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### pip install falha

**Sintoma**:
```
ERROR: Could not find a version that satisfies the requirement...
ERROR: no module named 'setuptools'
```

**Causa**: pip corrompido, problemas de rede, versão Python incompatível

**Solução**:

```bash
# 1. Atualizar pip
python3 -m pip install --upgrade pip

# 2. Tentar novamente com verbose
pip install -v -r requirements.txt

# 3. Se falhar, limpar cache
pip cache purge
pip install -r requirements.txt

# 4. Problema de network/proxy:
pip install --proxy [user:passwd@]proxy.server:port -r requirements.txt

# 5. Última opção: instalar line-by-line
# Abrir requirements.txt e fazer:
pip install fastapi==0.x.x
pip install uvicorn==0.x.x
# ... etc
```

---

## Variáveis de Ambiente

### Variáveis não estão sendo lidas

**Sintoma**:
```python
os.environ.get('AZURE_TENANT_ID')  # Retorna None
```

**Causa**: `.env` não foi criado/preenchido ou não está sendo carregado

**Solução**:

```bash
# 1. Verificar se .env existe
ls -la .env
# Se não existe:
cp .env.example .env

# 2. Editar .env com valores reais
nano .env

# 3. Se estiver usando python-dotenv (FastAPI não carrega sozinho):
# Verificar if app/main.py tem:
from dotenv import load_dotenv
load_dotenv()

# 4. Recarregar shell
# Linux/macOS (se bash config):
source ~/.bashrc
source ~/.zshrc

# 5. Ou rodar com env vars explícitas:
AZURE_TENANT_ID=xxx AZURE_CLIENT_ID=yyy uvicorn app.main:app --reload
```

---

###  não definida

**Sintoma**:
```
ValueError:  não definida
KeyError: 
```

**Causa**: Variável não está em `.env` ou não foi preenchida

**Solução**:

```bash
# 1. Verificar conteúdo de .env
grep  .env

# 2. Se retornar vazio ou não existe:
echo "=seu-valor-aqui" >> .env

# 3. Se valor está vazio (placeholder):
# Editar .env e preencher com valor real
nano .env
# Encontrar: =
# Substituir por: =83D8Q~ha1l... (seu valor)

# 4. Recarregar Python REPL:
python3
import os
os.environ.get('')  # Deve retornar valor

# 5. Verificar se tem quotas/espaços extras:
cat .env | grep  | od -c  # Ver caracteres especiais
```

---

### KeyError em variáveis obrigatórias

**Sintoma**:
```
KeyError: 'SQLSERVER_CONNECTION_STRING'
```

**Causa**: Variável obrigatória não está definida

**Solução**:

```bash
# 1. Listar variáveis definidas
env | grep AZURE
env | grep SQL

# 2. Se retornar vazio, adicionar ao .env:
echo "SQLSERVER_CONNECTION_STRING=Driver={...}" >> .env

# 3. Listar variáveis obrigatórias (do config.py):
cat app/core/config.py | grep "ValueError"

# 4. Preencher cada uma em .env
# Ver CONFIG_KEYS.md para valores esperados

# 5. Verificar com Python:
python3 -c "from app.core.config import KeyVaultConfig; print(KeyVaultConfig.get_sqlserver_connection_string())"
```

---

## Conexões & Rede

### Connection refused (SQL Server)

**Sintoma**:
```
pyodbc.Error: ('08001', "[08001] [Microsoft][ODBC Driver 18 for SQL Server]Named Pipes Provider: Could not open a connection to SQL Server [53]. [53]")
```

**Causa**: SQL Server offline, firewall, ou connection string errada

**Solução**:

```bash
# 1. Verificar se SQL Server está online
# Azure: Azure Portal → SQL Servers → seu server → Status
# Local: Services (Windows) ou systemctl status mssql-server (Linux)

# 2. Testar conexão com sqlcmd
sqlcmd -S your-server.database.windows.net -U user@server -P "password"
# Deve conectar (prompt "1>")

# 3. Verificar connection string em .env
grep SQLSERVER_CONNECTION_STRING .env
# Formato esperado:
# Driver={ODBC Driver 18 for SQL Server};Server=your-server.database.windows.net;Database=your-db;UID=user;PWD=password;...

# 4. Se Azure SQL, adicionar firewall rule
az sql server firewall-rule list --resource-group my-rg --server my-server

# Se seu IP não está listado:
az sql server firewall-rule create --name allow-my-ip \
  --resource-group my-rg \
  --server my-server \
  --start-ip-address YOUR_PUBLIC_IP \
  --end-ip-address YOUR_PUBLIC_IP

# 5. Teste novamente
python3
import pyodbc
conn = pyodbc.connect("Driver={ODBC Driver 18 for SQL Server};Server=...",timeout=10)
print("Conectado!")
```

---

### Connection refused (LLM Server)

**Sintoma**:
```
requests.exceptions.ConnectionError: Connection refused
Failed to connect to LLM Server at http://localhost:8001
```

**Causa**: LLM Server offline ou URL incorreta

**Solução**:

```bash
# 1. Verificar se LLM Server deve estar rodando
grep LLM_SERVER_URL .env

# 2. Se é local (localhost:8001):
curl http://localhost:8001/health
# Se retorna erro, LLM não está rodando

# 3. Se é remoto, verificar URL:
curl https://your-llm-server/health

# 4. Se LLM não é crítico (dev/test), desabilitar:
# .env:
SKIP_LLM_SERVER=true

# 5. Se realmente precisa do LLM:
# Iniciar LLM Server (em outro terminal/container)
# Depois rodar backend

# 6. Verificar timeout configurado:
# .env: LLM_SERVER_TIMEOUT=30
# Se timeout muito curto, aumentar:
LLM_SERVER_TIMEOUT=60

# 7. Testes
python3
import requests
resp = requests.get("http://localhost:8001/health", timeout=10)
print(resp.status_code)
```

---

### Timeout conectando ao Azure

**Sintoma**:
```
TimeoutError: ...
socket.timeout: timed out
```

**Causa**: Rede lenta, Azure indisponível, ou timeout pequeno demais

**Solução**:

```bash
# 1. Aumentar timeout em .env
LLM_SERVER_TIMEOUT=60   # padrão 30
SQLSERVER_CONNECTION_STRING=...;Connection Timeout=60;  # aumentar

# 2. Verificar conectividade
curl -I https://your-azure-resource.azure.com
ping 8.8.8.8  # teste de rede

# 3. Verificar status do Azure
# Azure Portal → Status

# 4. Se é só lento (primeira chamada):
# Não é erro, é normal no Azure

# 5. Ver logs detalhados
uvicorn app.main:app --reload --log-level debug
```

---

### Port 8000 já em uso

**Sintoma**:
```
OSError: [Errno 48] Address already in use
bind() failed: [Errno 98] Address already in use
```

**Causa**: Outro processo usando porta 8000

**Solução**:

```bash
# 1. Ver processo usando porta 8000
# Linux/macOS:
lsof -i :8000

# Windows PowerShell:
Get-NetTCPConnection -LocalPort 8000

# 2. Matar processo (se for server anterior)
kill -9 <PID>  # Linux/macOS
Stop-Process -Id <PID> -Force  # Windows

# 3. Rodar em porta diferente
uvicorn app.main:app --reload --port 8001

# 4. Em Docker
docker-compose down  # parar containers
docker-compose up    # reiniciar

# 5. Verificar se serviço está em standby
sleep 5
uvicorn app.main:app --reload --port 8000
```

---

## Autenticação & Credenciais

### MSAL authentication failed

**Sintoma**:
```
msal.error.MsalError: AADSTS700016: Application with identifier 'xxx' was not found...
```

**Causa**: AZURE_CLIENT_ID inválido ou aplicação não registrada no Azure

**Solução**:

```bash
# 1. Verificar se AZURE_CLIENT_ID está correto
grep AZURE_CLIENT_ID .env

# 2. Comparar com Azure Portal
# Ir em: Azure Portal → Entra ID → App registrations
# Copiar exato: Application (client) ID

# 3. Verificar se app está ativa
# App → Properties → Enabled for users to sign-in?

# 4. Verificar AZURE_TENANT_ID também
# App → Overview → Directory (tenant) ID

# 5. Se mudou credenciais, regenerar secret:
# App → Certificates & secrets → New client secret
# Copiar novo valor para  no .env

# 6. Teste login
curl -X GET http://localhost:8000/api/v1/login
# Deve redirecionar para Azure
```

---

### Azure credentials expiradas

**Sintoma**:
```
AADSTS700082: The client secret expired...
Invalid token...
```

**Causa**:  venceu (válido por ~2 anos por padrão)

**Solução**:

```bash
# 1. Ir em Azure Portal
# Azure Portal → Entra ID → App registrations → Sua app
# Certificates & secrets → Client secrets

# 2. Se está com "X" vermelho ou "Expired":
# Criar novo secret:
# → New client secret → Descrição (ex: "Local Dev 2026") → Add

# 3. Copiar novo valor
# (⚠️ Só aparece uma vez!)

# 4. Atualizar .env
nano .env
# Encontrar: =old-value
# Substituir: =new-value

# 5. Testar
grep  .env  # Confirmação

# 6. Rodar novamente
uvicorn app.main:app --reload
```

---

### 401 Unauthorized em endpoints

**Sintoma**:
```
401 Unauthorized
```

**Causa**: JWT token ausente, inválido, ou expirado

**Solução**:

```bash
# 1. Verificar se está autenticado
curl http://localhost:8000/api/v1/auth/status

# 2. Fazer login primeiro (se necessário)
curl -X GET http://localhost:8000/api/v1/login
# Irá redirecionar para Azure

# 3. Se problema persiste, verificar token em cookie
# Usar browser dev tools → Application → Cookies
# Procurar por "jwt" ou "auth" cookie

# 4. Se teste de API (sem browser):
# Adicionar token manualmente no header
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/documents

# 5. Para bypass em DEV (se habilitado):
# Alguns endpoints podem ter SKIP_AUTH_DEV
LLM_SERVER_TIMEOUT=60  # não afeta auth, exemplo

# 6. Ver detalhes em logs
uvicorn app.main:app --reload --log-level debug | grep -i auth
```

---

## Aplicação & Runtime

### Application failed to start

**Sintoma**:
```
ERROR in application startup
Traceback (most recent call last):
  ...
```

**Causa**: Erro em startup (com frequência em config/imports)

**Solução**:

```bash
# 1. Ver erro completo nos logs
uvicorn app.main:app --reload --log-level debug

# 2. Erros comuns:
# - Variável de ambiente faltando → verificar .env
# - Module import failing → pip install -r requirements.txt
# - Bad connection string → testar sqlcmd

# 3. Teste import manualmente
python3
from app.main import app
# Se retorna erro, está no código

# 4. Verificar main.py syntax
python3 -m py_compile app/main.py

# 5. Se é erro de dependência:
pip install -r requirements.txt --force-reinstall

# 6. Último recurso: reconstruir ambiente
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

### Memory overflow / Out of memory

**Sintoma**:
```
MemoryError
OSError: memory allocation failed
```

**Causa**: Memory leak ou arquivo muito grande sendo processado

**Solução**:

```bash
# 1. Ver uso de memória
# Linux:
ps aux | grep uvicorn

# Docker:
docker stats

# 2. Verificar se é porque processando arquivo grande
# Máximo: 50MB por arquivo (ver app/services/document_service.py)

# 3. Se é memory leak:
# Rodar com limite de memória (Docker)
docker-compose down
# Editar docker-compose.yml:
# mem_limit: 1G  # 1GB max

# 4. Aumentar swap (Linux)
# sudo fallocate -l 4G /swapfile
# sudo chmod 600 /swapfile
# sudo mkswap /swapfile
# sudo swapon /swapfile

# 5. Reiniciar
uvicorn app.main:app --reload
```

---

### Endpoint retorna 500 Internal Server Error

**Sintoma**:
```
500 Internal Server Error
```

**Causa**: Erro não-tratado em endpoint (varies)

**Solução**:

```bash
# 1. Ver log detalhado de erro
uvicorn app.main:app --reload --log-level debug

# Procurar pelo endpoint no log (ex: POST /documents)

# 2. Erros comuns por endpoint:
# /documents → problema com SQL/Storage/LLM
# /login → problema com Azure
# /chat → problema com LLM Server

# 3. Testar com curl verbose
curl -v -X POST http://localhost:8000/api/v1/documents/ingest-preview \
  -F "file=@test.txt" 2>&1 | grep -A 20 "< HTTP"

# 4. Ver stack trace completo
# Aparece nos logs quando log-level=DEBUG

# 5. Adicionar print debugging (temporário)
# Editar router ou service
# Adicionar: print("DEBUG:", variable)

# 6. Se é SQL error:
# Testar query diretamente em sqlcmd

# 7. Se é LLM error:
# Verificar se LLM Server está online
curl http://localhost:8001/health
```

---

## Docker & Containers

### Docker daemon not running

**Sintoma**:
```
Cannot connect to Docker daemon
error during connect: this error may indicate the docker daemon is not running
```

**Causa**: Docker service não está ativo

**Solução**:

```bash
# Linux
sudo systemctl start docker
sudo systemctl status docker

# macOS (Docker Desktop)
# Abrir "Docker" app do Launchpad

# Windows (Docker Desktop)
# Abrir "Docker Desktop" do Start menu

# Verificar após iniciar
docker version
docker ps
```

---

### Container exits immediately

**Sintoma**:
```
docker-compose up → container starts e fecha logo
docker-compose ps → Exit code 1 ou similar
```

**Causa**: Erro durante startup do container

**Solução**:

```bash
# 1. Ver logs
docker-compose logs api

# 2. Erros comuns em container:
# - Variáveis de ambiente não passadas
# - .env.example commitado em vez de preenchido
# - Port já em uso

# 3. Referenciar .env em docker-compose.yml
# Verificar se tem:
# env_file:
#   - .env

# 4. Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up

# 5. Se problema persiste, entrar no container
docker-compose up -d
docker-compose exec api bash
# Dentro do container:
env | grep AZURE  # ver vars
python app/main.py  # tentar rodar py direto
```

---

### Volume mounting issues

**Sintoma**:
```
docker: Error response from daemon: invalid mount config
Permission denied when mounting volume
```

**Causa**: Path inválido ou permissões insuficientes

**Solução**:

```bash
# 1. Verificar docker-compose.yml volumes
# Se tem: ./storage:/app/storage
# Garantir que ./storage existe:
mkdir -p storage/documents storage/temp

# 2. Permissões (Linux)
sudo chown -R $USER:$USER storage/

# 3. Path deve ser relativo (recomendado)
# NÃO: /home/user/project/storage:/app/storage
# SIM: ./storage:/app/storage

# 4. Se ainda falha, testar volume diretamente:
docker volume ls
docker volume inspect <volume-name>

# 5. Reset volumes
docker-compose down -v
docker-compose up
```

---

## Testes & CI/CD

### Testes falhando localmente

**Sintoma**:
```
FAILED tests/test_auth.py::test_login
```

**Causa**: Depends on (fixture, mock, DB state, env var)

**Solução**:

```bash
# 1. Rodar teste com verbose
pytest tests/test_auth.py::test_login -v

# 2. Ver mais detalhes
pytest tests/test_auth.py::test_login -vv

# 3. Sem capturar output (ver prints)
pytest tests/test_auth.py -s

# 4. Teste específico com pdb (debugger)
pytest tests/test_auth.py --pdb

# 5. Verificar fixtures
# Procurar por @pytest.fixture em conftest.py
# Verificar se estão retornando corretos dados

# 6. Se é problema de DB:
# Reset DB para estado limpo
python db/run_schema.py

# 7. Se é problema de mock:
# Verificar que mock está retornando dados esperados
```

---

### Testes passam local mas falham em CI

**Sintoma**:
```
✅ Local: pytest passa
❌ CI (GitHub/Azure): pytest falha
```

**Causa**: Diferença de environment (vars de env, DB, mocks)

**Solução**:

```bash
# 1. Verificar variáveis de ambiente no CI
# GitHub: Actions → Secrets
# Azure: Pipelines → Library → Variable groups

# 2. Replicar CI localmente usando docker
docker-compose -f docker-compose.test.yml up

# 3. Verificar que testes não fazem I/O real
# NÃO devem:
# - Conectar em azure/produção
# - Fazer chamadas HTTP reais
# - Escrever em files system

# 4. Se é DB:
# CI deve usar DB separada (test DB)
# Verificar connection string em CI config

# 5. Mocks insuficientes:
# Adicionar mock para Azure/HTTP calls:
@patch('app.providers.auth_msal')
def test_login(mock_auth):
    mock_auth.return_value = {...}
    # ...

# 6. Ver logs CI completos:
# Click em job failed → View logs
```

---

## 🆘 Se Nada Funcionar

### Passo-a-passo Nuclear Reset

```bash
# 1. Parar tudo
docker-compose down -v
pkill -f uvicorn
deactivate 2>/dev/null

# 2. Remover arquivos corrompidos
rm -rf venv
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# 3. Reconstruir do zero
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Verificar credenciais
cp .env.example .env
# Editar .env manualmente

# 5. Testar import
python3 -c "from app.main import app; print('OK')"

# 6. Rodar
uvicorn app.main:app --reload
```

---

## 📞 Escalar para Suporte

Se nada da lista acima resolve:

1. **Coletar logs**:
```bash
uvicorn app.main:app --reload --log-level debug 2>&1 | tee error.log
# ou docker-compose logs > error.log
```

2. **Incluir info do sistema**:
```bash
python3 --version
docker --version
docker-compose --version
odbcinst -q -l -d
pip list | head -20
```

3. **Abrir issue no GitHub** com:
   - Comando que rodou
   - Erro completo (do log acima)
   - Sistema operacional
   - Versões (python, docker, etc)
   - Passos para reproduzir

---

## 🎯 Sumário de Ações Rápidas

| Problema | Ação Rápida |
|----------|------------|
| Module not found | `pip install -r requirements.txt` |
| ODBC não encontrado | Instalar driver (ver acima) |
| Conn refused SQL | `sqlcmd -S server` para testar |
| Conn refused LLM | `curl http://localhost:8001/health` |
| Port ocupada | `lsof -i :8000` + `kill -9 PID` |
| Variável faltando | Verificar `.env` + `source venv/bin/activate` |
| 401 Unauthorized | Fazer login primeiro |
| 500 Error | Ver logs com `--log-level debug` |
| Container exits | `docker-compose logs api` |
| Teste falha | `pytest -vv -s` |

---

## 📚 Referências

- **RUN_LOCAL_COMPLETE_GUIDE.md** - Setup passo-a-passo
- **CONFIG_KEYS.md** - Variáveis de ambiente
- **PROJECT_OVERVIEW.md** - Arquitetura geral
- [ODBC Driver Download](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [pytest Docs](https://pytest.org/)

---

**Última atualização**: 20/03/2026  
**Mantém por**: Backend Team  
**Adicione problemas que encontrar** → Issue no GitHub
