#!/usr/bin/env bash
# Exemplos de uso da API de documentos com categoria

API_URL="http://localhost:8000/api/v1/documents"

# ============================================================================
# EXEMPLO 1: Ingerir documento novo COM categoria
# ============================================================================
echo "1. Ingerir documento novo com categoria_id=1 (Admissão)"

curl -X POST "$API_URL/ingest" \
  -F "file=@path/to/file.pdf" \
  -F "user_id=user123" \
  -F "category_id=1" \
  -F "min_role_level=1" \
  | jq .

# ============================================================================
# EXEMPLO 2: Ingerir documento SEM categoria (categoria_id=null)
# ============================================================================
echo -e "\n2. Ingerir documento SEM categoria"

curl -X POST "$API_URL/ingest" \
  -F "file=@path/to/file.pdf" \
  -F "user_id=user123" \
  -F "min_role_level=1" \
  | jq .

# ============================================================================
# EXEMPLO 3: Atualizar documento (nova versão) COM categoria
# ============================================================================
echo -e "\n3. Atualizar documento existente (document_id=5) com nova categoria"

curl -X POST "$API_URL/ingest" \
  -F "file=@path/to/updated.pdf" \
  -F "user_id=user123" \
  -F "document_id=5" \
  -F "category_id=3" \
  | jq .

# ============================================================================
# EXEMPLO 4: Listar documentos SEM filtro de categoria
# ============================================================================
echo -e "\n4. Listar todos os documentos"

curl -X GET "$API_URL?limit=10&offset=0" | jq .

# ============================================================================
# EXEMPLO 5: Listar documentos COM filtro de categoria
# ============================================================================
echo -e "\n5. Listar documentos da categoria 1 (Admissão)"

curl -X GET "$API_URL?category_id=1&limit=10&offset=0" | jq .

# ============================================================================
# EXEMPLO 6: Listar documentos de usuário COM filtro de categoria
# ============================================================================
echo -e "\n6. Listar documentos do usuário com categoria 5"

curl -X GET "$API_URL?user_id=user123&category_id=5&limit=10&offset=0" | jq .

# ============================================================================
# EXEMPLO 7: Combinações de filtros
# ============================================================================
echo -e "\n7. Listar documentos com múltiplos filtros"

curl -X GET "$API_URL?user_id=user123&category_id=2&filename=beneficios&limit=10&offset=0" | jq .

# ============================================================================
# LISTA DE CATEGORIAS DISPONÍVEIS (dim_categories)
# ============================================================================
echo -e "\n\nCATEGORIAS DISPONÍVEIS (use category_id):"
echo "1 - Admissão"
echo "2 - Folha de Pagamento"
echo "3 - Férias e Ausências"
echo "4 - Jornada e Ponto"
echo "5 - Saúde e Bem-Estar"
echo "6 - Desenvolvimento e Carreira"
echo "7 - Movimentações Internas"
echo "8 - Políticas e Normas"
echo "9 - Diversidade e Inclusão"
echo "10 - Segurança da Informação"
echo "11 - Relações Trabalhistas"
echo "12 - Desligamento"
echo "13 - RH Geral"

# ============================================================================
# RESPOSTA ESPERADA - List Documents
# ============================================================================
echo -e "\n\nRESPOSTA ESPERADA (GET /documents):"
cat << 'EOF'
{
  "documents": [
    {
      "document_id": "1",
      "title": "beneficios_admissao.pdf",
      "user_id": "user123",
      "category_id": 1,                    ← NOVO CAMPO
      "created_at": "2026-01-06T10:30:00",
      "updated_at": "2026-01-06T10:30:00",
      "is_active": true,
      "min_role_level": 1,
      "allowed_countries": "BR,US",
      "allowed_cities": "SP,RJ",
      "collar": "administrative",
      "plant_code": "001",
      "version_count": 2
    }
  ],
  "count": 1,
  "offset": 0,
  "limit": 100
}
EOF

# ============================================================================
# RESPOSTA ESPERADA - Ingest Document
# ============================================================================
echo -e "\n\nRESPOSTA ESPERADA (POST /ingest):"
cat << 'EOF'
{
  "status": "success",
  "document_id": 1,
  "version_number": 1,
  "category_id": 1,                       ← NOVO CAMPO
  "filename": "beneficios_admissao.pdf",
  "file_size_bytes": 245612,
  "user_id": "user123",
  "blob_path": "documents/user123/1/v1/beneficios_admissao.pdf",
  "message": "Document ingested successfully"
}
EOF
