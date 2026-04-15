# 🚀 Como Rodar Localmente - Guia Completo

**Versão**: 1.0  
**Última atualização**: 20/03/2026  
**Para**: Desenvolvimento local, testes, integração

---

## 📋 Índice

1. [Pre-requisitos](#pre-requisitos)
2. [Setup Rápido (5 min)](#setup-rápido-5-min)
3. [Opção A: SEM Docker (Desenvolvimento Nativo)](#opção-a-sem-docker-desenvolvimento-nativo)
4. [Opção B: COM Docker (Recomendado)](#opção-b-com-docker-recomendado)
5. [Verificar Saúde & Testar](#verificar-saúde--testar)
6. [Rodar Testes Automatizados](#rodar-testes-automatizados)
7. [Troubleshooting Detalhado](#troubleshooting-detalhado)
8. [Limpeza & Reset](#limpeza--reset)

---

## Pre-requisitos

### Sistema Operacional
- ✅ Linux (Ubuntu/Debian), macOS, ou Windows 10/11
- ✅ Acesso a terminal/PowerShell

### Requisitos Obrigatórios

#### 1. Python 3.11+
```bash
python3 --version
# Deve retornar: Python 3.11.x ou superior

# Se não tiver:
# Ubuntu/Debian: sudo apt install python3.11 python3.11-venv
# macOS: brew install python@3.11
# Windows: https://www.python.org/downloads/
```

#### 2. pip e venv
```bash
python3 -m pip --version
python3 -m venv --help

# Se faltar:
# Ubuntu/Debian: sudo apt install python3-pip python3-venv
# macOS: vem com Python
# Windows: vem com Python
```

#### 3. Git
```bash
git --version
# Deve retornar: git version 2.x.x
```

#### 4. ODBC Driver 17/18 para SQL Server (Crítico!)

**O que é**: Driver ODBC necessário para conectar em SQL Server do Python

**Verificar se tem**:
```bash
odbcinst -q -l -d
# Procura por: "ODBC Driver 17 for SQL Server" ou "ODBC Driver 18 for SQL Server"
```

**Se NÃO tem - Instalar**:

**Linux (Debian/Ubuntu)**:
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/focal/prod.list | tee /etc/apt/sources.list.d/mssql-release.list
apt-get update
apt-get install -y odbc-driver-18-for-sql-server
```

**macOS**:
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew install mssql-tools18
```

**Windows**:
- Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
- Executar installer
- Reiniciar após instalar

---

## Setup Rápido (5 min)

Se já tem tudo instalado, use este comando para rodar tudo:

```bash
# 1. Clone
git clone <repo-url>
cd Embeddings

# 2. Python venv
python3 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# 3. Dependências
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
# Editar .env com suas credenciais Azure

# 5. Rodar (sem LLM para teste rápido)
SKIP_LLM_SERVER=true uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Testar em outro terminal
curl http://localhost:8000/
# Deve retornar JSON
```

✅ **Pronto!** Acesse http://localhost:8000/docs para Swagger UI

---

## Opção A: SEM Docker (Desenvolvimento Nativo)

Use esta opção se preferir desenvolvimento direto no seu SO (mais rápido em iterações).

### Passo 1: Clone o Repositório

```bash
git clone <repo-url>
cd Embeddings
pwd  # Verificar que está no diretório correto
```

### Passo 2: Criar Virtual Environment

Virtual environment isola as dependências do projeto (melhor prática).

```bash
# Criar venv
python3 -m venv venv

# Ativar venv
# Linux/macOS:
source venv/bin/activate

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (CMD):
.\venv\Scripts\activate.bat

# Verificar (prompt deve mostrar "(venv)")
which python  # Linux/macOS
# ou: where python  # Windows
```

**Saída esperada**:
```
(venv) user@machine:~/Embeddings$
```

### Passo 3: Instalar Dependências

```bash
# Upgrade pip
pip install --upgrade pip

# Instalar requirements
pip install -r requirements.txt

# Verificar instalação
pip list | grep fastapi
# Deve retornar: fastapi         0.x.x
```

**Tempo esperado**: 2-5 min (depende internet)

### Passo 4: Configurar Arquivo .env

```bash
# Copiar template
cp .env.example .env

# Editar com suas credenciais (use seu editor favorito)
nano .env
# ou: vim .env
# ou: code .env (VS Code)
```

**O que preencher em `.env`**:

```bash
# Obrigatórias (de seu Azure)
AZURE_TENANT_ID=d2007bef-127d-...      # Seu Azure Tenant ID
AZURE_CLIENT_ID=abeecec0-3c24-...      # Sua App ID
=83D8Q~ha1l...      # Seu App Secret
SQLSERVER_CONNECTION_STRING=Driver={ODBC Driver 18...}  # Sua SQL
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpoints...     # Seu Storage
=sk-...                # Sua OpenAI key

# Recomendado (com valores para dev)
LLM_SERVER_URL=http://localhost:8001
SKIP_LLM_SERVER=true              # Desabilitar LLM por enquanto

# Resto pode deixar com valores padrão
```

**Não tem credenciais?** → Ver [CONFIG_KEYS.md](CONFIG_KEYS.md) seção "Onde obter"

### Passo 5: Rodar o Servidor

```bash
# Comando básico
uvicorn app.main:app --reload --port 8000

# Com mais detalhes (debug)
uvicorn app.main:app --reload --port 8000 --log-level debug

# Em background (macOS/Linux)
uvicorn app.main:app --reload --port 8000 &
```

**Saída esperada**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Passo 6: Testar em Novo Terminal

```bash
# Abrir novo terminal (manter o servidor rodando)

# Health check
curl http://localhost:8000/
# Retorna: JSON com versão da API

# Swagger UI (abrir no navegador)
open http://localhost:8000/docs
# ou: firefox http://localhost:8000/docs

# Testar endpoint
curl -X GET http://localhost:8000/api/v1/master-data/locations?limit=5
# Retorna: lista de locations
```

### Passo 7: Parar Servidor

```bash
# Pressionar Ctrl+C no terminal onde uvicorn está rodando
# Ou se em background:
pkill -f uvicorn
```

---

## Opção B: COM Docker (Recomendado)

Use esta opção para ambiente isolado (simula melhor a produção).

### Pré-requisitos Docker

```bash
# Verificar se Docker está instalado
docker --version
# Deve retornar: Docker version 20.x.x+

docker-compose --version
# Deve retornar: Docker Compose version 2.x.x+

# Se não tiver:
# Baixar: https://www.docker.com/products/docker-desktop
```

### Passo 1: Preparar Arquivo .env

```bash
# Copiar template
cp .env.example .env

# Editar .env (mesmas credenciais da Opção A)
nano .env
```

### Passo 2: Build & Rodar

```bash
# Build image (primeira vez - leva ~5 min)
docker-compose build

# Rodar containers (API + Redis)
docker-compose up

# Ou em background:
docker-compose up -d
```

**Saída esperada**:
```
redis       | * Ready to accept connections
api         | INFO:     Uvicorn running on http://0.0.0.0:8000
api         | INFO:     Application startup complete
```

### Passo 3: Testar

```bash
# Health check
curl http://localhost:8000/

# Ver logs
docker-compose logs -f api

# Parar (se em background)
docker-compose down
```

### Passo 4: Troubleshooting Docker

```bash
# Ver containers rodando
docker-compose ps

# Ver logs de erro
docker-compose logs api

# Rebuild (se mudar código)
docker-compose up --build

# Reset completo (remove tudo)
docker-compose down -v
docker-compose up

# Usar bash inside container
docker-compose exec api bash
```

---

## Verificar Saúde & Testar

### 1. Health Check

```bash
# Request simples
curl http://localhost:8000/

# Saída esperada:
# {
#   "service": "Secure Document & Identity Platform",
#   "version": "1.0.0",
#   "status": "ok"
# }
```

### 2. Swagger UI Interativa

Abrir no navegador:
```
http://localhost:8000/docs
```

Você pode testar endpoints diretamente lá (botão "Try it out")

### 3. Testar Endpoint Real

```bash
# GET simples (Master Data)
curl -X GET http://localhost:8000/api/v1/master-data/locations?limit=10

# POST simples (com dados)
curl -X POST http://localhost:8000/api/v1/documents/ingest-preview \
  -F "file=@your-file.txt"

# Com mais verbosidade
curl -v -X GET http://localhost:8000/api/v1/master-data/locations
```

### 4. Usando VS Code REST Client (Recomendado)

1. Instalar extension: "REST Client" de Huachao Mao
2. Abrir `API_EXAMPLES.http`
3. Clique em "Send Request" acima de cada teste

**Vantagem**: Salva histórico, variáveis, melhor que curl

---

## Rodar Testes Automatizados

### Verificar Estructura

```bash
# Ver quais testes existem
find tests/ -name "test_*.py" -o -name "*_test.py"
```

### Rodar Todos os Testes

```bash
# Ativar venv (se não estiver)
source venv/bin/activate

# Rodar tudo
pytest

# Com mais detalhes
pytest -v

# Rodar teste específico
pytest tests/test_auth.py -v

# Com coverage (cobertura de código)
pytest --cov=app tests/
```

### Rodar Testes em Docker

```bash
docker-compose exec api pytest
docker-compose exec api pytest -v
```

### Entender Resultado

```
✅ PASSED  - Teste passou
❌ FAILED  - Teste falhou
⏭️ SKIPPED - Teste pulado
```

---

## Troubleshooting Detalhado

### ❌ "ModuleNotFoundError: No module named 'pyodbc'"

**Causa**: Dependências não instaladas

**Solução**:
```bash
# Ativar venv
source venv/bin/activate

# Reinstalar requirements
pip install --force-reinstall -r requirements.txt

# Verificar
python -c "import pyodbc; print(pyodbc.version)"
```

---

### ❌ "ODBC Driver 17 not found"

**Causa**: Driver ODBC para SQL Server não está instalado no SO

**Solução**:

**Linux (Debian/Ubuntu)**:
```bash
sudo curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
sudo curl https://packages.microsoft.com/config/ubuntu/focal/prod.list | tee /etc/apt/sources.list.d/mssql-release.list
sudo apt update
sudo apt install -y odbc-driver-18-for-sql-server
```

**macOS**:
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew install mssql-tools18
```

**Windows**:
1. Baixar: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
2. Executar `.exe`
3. Reiniciar

**Verificar após instalar**:
```bash
odbcinst -q -l -d | grep ODBC
```

---

### ❌ "Connection refused" (SQL Server)

**Causa**: SQL Server offline ou firewall bloqueando

**Solução**:

```bash
# 1. Verificar connection string em .env
cat .env | grep SQLSERVER_CONNECTION_STRING

# 2. Testar conexão com sqlcmd
sqlcmd -S your-server.database.windows.net -U user -P password

# 3. Se Azure SQL, verificar firewall
az sql server firewall-rule list --resource-group my-rg --server my-server

# 4. Se local, verificar SQL Server está rodando
# Windows: Services → SQL Server (SQLEXPRESS)
# Linux: systemctl status mssql-server
```

**Se for Azure SQL**:
```bash
# Pode precisar adicionar seu IP
az sql server firewall-rule create --name allow-my-ip \
  --resource-group my-rg \
  --server my-server \
  --start-ip-address <YOUR_IP> \
  --end-ip-address <YOUR_IP>
```

---

### ❌ " não definida"

**Causa**: `.env` não foi preenchido

**Solução**:
```bash
# 1. Verificar se .env existe
ls -la .env

# 2. Se não existe
cp .env.example .env

# 3. Editar e preenchida
nano .env
# Salvar: Ctrl+O, Enter, Ctrl+X

# 4. Verificar se foi lido
python -c "import os; print('' in os.environ or 'FALTA')"
# Se prints "FALTA", recarregar shell:
source venv/bin/activate
```

---

### ❌ "LLM Server timeout"

**Causa**: LLM Server offline ou URL incorreta

**Solução**:

**Opção 1 - Desabilitar LLM (para testes)**:
```bash
# No .env ou ao rodar
SKIP_LLM_SERVER=true uvicorn app.main:app --reload

# Ou editar .env:
SKIP_LLM_SERVER=true
```

**Opção 2 - Aumentar timeout**:
```bash
# No .env
LLM_SERVER_TIMEOUT=60

# Ou ao rodar
LLM_SERVER_TIMEOUT=60 uvicorn app.main:app --reload
```

**Opção 3 - Verificar LLM Server**:
```bash
# Se deve estar rodando localmente
curl http://localhost:8001/health

# Se deve estar em server remoto
curl https://your-llm-server/health
```

---

### ❌ "Port 8000 already in use"

**Causa**: Outro processo usando porta 8000

**Solução**:

```bash
# Linux/macOS: Ver processo
lsof -i :8000

# Matar processo
kill -9 <PID>

# Ou rodar em porta diferente
uvicorn app.main:app --reload --port 8001
```

---

### ❌ "venv: No such file or directory"

**Causa**: Virtual environment não foi criado

**Solução**:
```bash
# Criar venv
python3 -m venv venv

# Ativar
source venv/bin/activate

# Instalar deps
pip install -r requirements.txt
```

---

### ❌ "No module named 'app'"

**Causa**: Não está no diretório correto ou venv não está ativado

**Solução**:
```bash
# 1. Verificar diretório
pwd
# Deve terminar com: /Embeddings

# 2. Verificar venv ativo
which python
# Deve contêr: /venv/bin/python

# 3. Se não está ativo
source venv/bin/activate

# 4. Verificar estrutura
ls -la app/
# Deve ter: __init__.py, main.py, models.py, etc.
```

---

### ❌ "ImportError: azure-identity not available"

**Causa**: azure-identity não foi instalado

**Solução**:
```bash
pip install azure-identity
pip install -r requirements.txt
```

---

### ❌ "Redis connection error" (se usar cache)

**Causa**: Redis offline

**Solução**:

**Com Docker:**
```bash
docker-compose up  # Inicia Redis automaticamente
```

**Localmente:**
```bash
# Instalar Redis
# Ubuntu: sudo apt install redis-server
# macOS: brew install redis
# Windows: https://github.com/microsoftarchive/redis/releases

# Rodar Redis
redis-server

# Verificar
redis-cli ping  # Deve retornar: PONG
```

---

## Limpeza & Reset

### Remover Dependências (Desinstalar Tudo)

```bash
# Desativar venv (se ativado)
deactivate

# Remover venv
rm -rf venv
```

### Reset Completo de Docker

```bash
# Parar tudo
docker-compose down

# Remover volumes (CUIDADO - remove dados!)
docker-compose down -v

# Remover images
docker rmi embeddings_api  # ou nome da sua image

# Reconstruir e rodar
docker-compose up --build
```

### Limpar Cache Python

```bash
# Remover .pyc e __pycache__
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Limpar pip cache
pip cache purge
```

---

## 📚 Referências Rápidas

### Logs e Debug

```bash
# Ver logs detalhados
uvicorn app.main:app --reload --log-level debug

# Docker logs
docker-compose logs -f api

# Seguir logs em tempo real
docker-compose logs -f
```

### Arquivos Importantes

| Arquivo | Propósito |
|---------|-----------|
| `app/main.py` | Entrada da aplicação |
| `app/core/config.py` | Configurações |
| `requirements.txt` | Dependências |
| `.env.example` | Template de variáveis |
| `docker-compose.yml` | Config Docker |
| `Dockerfile` | Build da imagem |
| `pytest.ini` | Config de testes |

### Comandos Frequentes

```bash
# Ativar venv
source venv/bin/activate

# Rodar servidor
uvicorn app.main:app --reload

# Testar
pytest -v

# Rodar em Docker
docker-compose up

# Ver URLs
curl http://localhost:8000/docs

# Git
git status
git add .
git commit -m "msg"
git push
```

---

## ✅ Checklist Final

- [ ] Python 3.11+ instalado
- [ ] ODBC Driver instalado
- [ ] Git clonado
- [ ] venv criado e ativado
- [ ] requirements.txt instalado
- [ ] .env.example copiado → .env
- [ ] .env preenchido com credenciais
- [ ] Servidor rodando: `uvicorn app.main:app --reload`
- [ ] Health check: `curl http://localhost:8000/`
- [ ] Swagger funcionando: http://localhost:8000/docs
- [ ] Testes passando: `pytest`

---

## 🆘 Ainda com Problemas?

1. **Checar esse guia** - Troubleshooting acima
2. **Verificar [CONFIG_KEYS.md](CONFIG_KEYS.md)** - Para variáveis de ambiente
3. **Ver logs detalhados** - `uvicorn ... --log-level debug`
4. **Clonar novamente** - Se repo corrompido
5. **Reset Docker** - `docker-compose down -v && docker-compose up --build`
6. **Abrir issue no GitHub** - Com logs completos

---

## 🎉 Próximos Passos

Se tudo funcionou:
1. ✅ Explorar endpoints em Swagger UI
2. ✅ Testar `API_EXAMPLES.http`  
3. ✅ Ler documentação técnica em `/docs`
4. ✅ Começar desenvolvimento!

**Bem-vindo ao backend! 🚀**
