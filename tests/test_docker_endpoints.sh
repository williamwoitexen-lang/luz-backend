#!/bin/bash

# ================================================================
# TEST ENDPOINTS IN DOCKER
# ================================================================
# 
# Uso:
#   bash test_docker_endpoints.sh
#
# Este script:
# 1. Constrói uma imagem Docker com ODBC drivers
# 2. Roda a aplicação em um container
# 3. Testa todos os endpoints GET contra Azure SQL Server
# 4. Limpa o container
#
# REQUISITOS:
#   - Docker instalado
#   - .env arquivo com SQLSERVER_CONNECTION_STRING
#
# ================================================================

set -e

echo ""
echo "=========================================="
echo "🐳 TESTANDO ENDPOINTS COM DOCKER"
echo "=========================================="
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "❌ Erro: Arquivo .env não encontrado!"
    echo ""
    echo "Crie um arquivo .env com o seguinte conteúdo:"
    echo "  SQLSERVER_CONNECTION_STRING=Driver={ODBC Driver 17 for SQL Server};Server=tcp:SEU-SERVER.database.windows.net,1433;Database=data;Uid=SEU-USER;Pwd=SEU-PASSWORD;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    echo ""
    exit 1
fi

echo "✅ Arquivo .env encontrado"
echo ""

# Parar container anterior se existir
if docker ps -a --format '{{.Names}}' | grep -q '^embeddings-test$'; then
    echo "🛑 Parando container anterior..."
    docker stop embeddings-test 2>/dev/null || true
    docker rm embeddings-test 2>/dev/null || true
fi

echo "📦 Construindo imagem Docker com ODBC drivers..."
docker build -t embeddings-api:test .

echo "✅ Imagem construída"
echo ""

echo "🚀 Iniciando container..."
docker run -d \
    --name embeddings-test \
    --env-file .env \
    -e STORAGE_TYPE=local \
    -e LOCAL_STORAGE_PATH=/app/storage/documents \
    -p 8000:8000 \
    -v "$(pwd)/storage:/app/storage" \
    embeddings-api:test \
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null

echo "⏳ Aguardando inicialização do container (15 segundos)..."
sleep 15

echo "✅ Container iniciado"
echo ""

# Função para testar um endpoint
test_endpoint() {
    local endpoint=$1
    local description=$2
    
    printf "%-50s" "📍 $description"
    
    response=$(curl -s -w "\n%{http_code}" http://localhost:8000$endpoint 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        # Contar registros se for array
        count=$(echo "$body" | jq 'if type == "array" then length else . | keys | length end' 2>/dev/null || echo "?")
        printf " ✅ %3d registros\n" "$count"
    else
        printf " ❌ Status %d\n" "$http_code"
        # Mostrar erro
        echo "   └─ $(echo "$body" | jq -r '.detail // .' 2>/dev/null | head -c 80)"
    fi
}

echo "════════════════════════════════════════════════════════════"
echo "🔵 TESTANDO ENDPOINTS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Testar endpoints
test_endpoint "/api/v1/master-data/locations" "GET /locations"
test_endpoint "/api/v1/master-data/countries" "GET /countries"
test_endpoint "/api/v1/master-data/countries?active_only=true" "GET /countries (apenas ativos)"
test_endpoint "/api/v1/master-data/regions" "GET /regions"
test_endpoint "/api/v1/master-data/regions?active_only=true" "GET /regions (apenas ativos)"
test_endpoint "/api/v1/master-data/roles" "GET /roles"
test_endpoint "/api/v1/master-data/roles?active_only=true" "GET /roles (apenas ativos)"
test_endpoint "/api/v1/master-data/categories" "GET /categories"
test_endpoint "/api/v1/master-data/categories?active_only=true" "GET /categories (apenas ativos)"
test_endpoint "/api/v1/master-data/hierarchy" "GET /hierarchy"
test_endpoint "/api/v1/master-data/hierarchy?active_only=true" "GET /hierarchy (apenas ativos)"
test_endpoint "/api/v1/master-data/states-by-country/Brazil" "GET /states-by-country/Brazil"
test_endpoint "/api/v1/master-data/cities-by-country/Brazil" "GET /cities-by-country/Brazil"
test_endpoint "/api/v1/master-data/cities-by-region/LATAM" "GET /cities-by-region/LATAM"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🐳 ACESSANDO A API"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📖 Documentação Swagger:"
echo "   http://localhost:8000/docs"
echo ""
echo "📖 ReDoc:"
echo "   http://localhost:8000/redoc"
echo ""
echo "Pressione ENTER para continuar e limpar os recursos..."
read

echo ""
echo "🛑 Parando container..."
docker stop embeddings-test > /dev/null
docker rm embeddings-test > /dev/null

echo "✅ Limpeza concluída"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "✨ Testes finalizados!"
echo "════════════════════════════════════════════════════════════"
