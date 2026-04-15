#!/bin/bash

# Exemplos de CURL para testar o Chat API

echo "=== CHAT API - EXEMPLOS COM CURL ==="
echo ""

# 1. Fazer uma pergunta
echo "1. Fazer pergunta ao LLM Server:"
echo "---"
curl -X POST 'http://localhost:8000/api/v1/chat/question' \
  -H 'Content-Type: application/json' \
  -d '{
  "chat_id": "session_example_001",
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
  "question": "Quais são os benefícios de saúde disponíveis?"
}' | jq '.' | head -30

echo ""
echo ""

# 2. Listar conversas de um usuário
echo "2. Listar conversas do usuário:"
echo "---"
curl -X GET 'http://localhost:8000/api/v1/chat/conversations/emp_12345?limit=10' \
  -H 'Content-Type: application/json' | jq '.'

echo ""
echo ""

# 3. Obter detalhes completos de uma conversa
echo "3. Obter detalhes da conversa:"
echo "---"
curl -X GET 'http://localhost:8000/api/v1/chat/conversations/session_example_001/detail' \
  -H 'Content-Type: application/json' | jq '.'

echo ""
echo ""

# 4. Fazer outra pergunta na mesma conversa
echo "4. Fazer segunda pergunta (mesma conversa):"
echo "---"
curl -X POST 'http://localhost:8000/api/v1/chat/question' \
  -H 'Content-Type: application/json' \
  -d '{
  "chat_id": "session_example_001",
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
  "question": "Como solicitar uma folga?"
}' | jq '.answer'

echo ""
echo ""

# 5. Ver a conversa atualizada
echo "5. Ver conversa com ambas as mensagens:"
echo "---"
curl -X GET 'http://localhost:8000/api/v1/chat/conversations/session_example_001/detail' \
  -H 'Content-Type: application/json' | jq '.messages | length'

echo ""
echo ""

# 6. Deletar conversa
echo "6. Deletar conversa:"
echo "---"
curl -X DELETE 'http://localhost:8000/api/v1/chat/conversations/session_example_001' \
  -H 'Content-Type: application/json' | jq '.'

echo ""
echo "=== FIM DOS EXEMPLOS ==="
