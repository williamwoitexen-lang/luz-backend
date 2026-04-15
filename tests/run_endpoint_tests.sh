#!/bin/bash

# Iniciar aplicação em background
cd /workspaces/Embeddings
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
APP_PID=$!

# Aguardar inicialização
sleep 4

# Executar testes
python test_get_endpoints.py

# Matar aplicação
kill $APP_PID 2>/dev/null || true
