#!/bin/bash
# Exemplos corretos de como fazer ingestão de documentos

API_URL="http://localhost:8000/api/v1/documents"

echo "============================================================================"
echo "EXEMPLO 1: Ingerir documento novo (com arquivo real)"
echo "============================================================================"

# Criar arquivo de teste
echo "Este é um documento de teste" > /tmp/teste.txt

# Fazer ingestão com multipart/form-data
curl -X POST "$API_URL/ingest" \
  -F "file=@/tmp/teste.txt" \
  -F "user_id=user123" \
  -F "min_role_level=1" \
  | jq .

echo ""
echo "============================================================================"
echo "EXEMPLO 2: Ingerir com categoria"
echo "============================================================================"

curl -X POST "$API_URL/ingest" \
  -F "file=@/tmp/teste.txt" \
  -F "user_id=user123" \
  -F "category_id=1" \
  -F "min_role_level=1" \
  | jq .

echo ""
echo "============================================================================"
echo "EXEMPLO 3: Ingerir com todos os parâmetros"
echo "============================================================================"

curl -X POST "$API_URL/ingest" \
  -F "file=@/tmp/teste.txt" \
  -F "user_id=user123" \
  -F "category_id=1" \
  -F "min_role_level=1" \
  -F "allowed_countries=BR,US" \
  -F "allowed_cities=SP,RJ" \
  -F "collar=administrative" \
  -F "plant_code=001" \
  | jq .

echo ""
echo "============================================================================"
echo "EXEMPLO 4: Preview ANTES de ingerir (recomendado)"
echo "============================================================================"

# Primeiro fazer preview para extrair metadados
curl -X POST "$API_URL/ingest-preview" \
  -F "file=@/tmp/teste.txt" \
  | jq .

echo ""
echo "============================================================================"
echo "IMPORTANTE: Usar -F para multipart/form-data"
echo "============================================================================"
echo ""
echo "CORRETO (multipart/form-data):"
echo "  curl -X POST /ingest -F 'file=@documento.pdf' -F 'user_id=user123'"
echo ""
echo "ERRADO (JSON):"
echo "  curl -X POST /ingest -H 'Content-Type: application/json' -d '{\"file\": \"...\" }'"
echo ""
echo "ERRADO (application/x-www-form-urlencoded):"
echo "  curl -X POST /ingest -d 'file=...' -d 'user_id=user123'"
echo ""
echo "============================================================================"
