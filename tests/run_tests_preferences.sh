#!/bin/bash
# Script para executar testes de User Preferences e Memory Integration

echo "🧪 Executando testes de User Preferences e Memory Integration..."
echo "=========================================================================="

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Opções
if [ "$1" == "verbose" ] || [ "$1" == "-v" ]; then
    PYTEST_FLAGS="-v -s --tb=short"
    echo -e "${BLUE}Rodando testes em modo VERBOSE${NC}"
else
    PYTEST_FLAGS="-v --tb=short"
    echo -e "${BLUE}Rodando testes (use './run_tests_preferences.sh verbose' para output completo)${NC}"
fi

# Testes específicos
echo ""
echo -e "${YELLOW}[1/5] Testes de endpoints User Preferences...${NC}"
python -m pytest tests/test_user_preferences_memory_integration.py::TestUserPreferencesAPI $PYTEST_FLAGS

echo ""
echo -e "${YELLOW}[2/5] Testes de integração Chat + Memory...${NC}"
python -m pytest tests/test_user_preferences_memory_integration.py::TestChatMemoryIntegration $PYTEST_FLAGS

echo ""
echo -e "${YELLOW}[3/5] Testes de validação JSON...${NC}"
python -m pytest tests/test_user_preferences_memory_integration.py::TestMemoryPreferencesValidation $PYTEST_FLAGS

echo ""
echo -e "${YELLOW}[4/5] Testes de QuestionRequest com Memory...${NC}"
python -m pytest tests/test_user_preferences_memory_integration.py::TestQuestionRequestMemory $PYTEST_FLAGS

echo ""
echo -e "${YELLOW}[5/5] Testes end-to-end...${NC}"
python -m pytest tests/test_user_preferences_memory_integration.py::TestEndToEndMemoryFlow $PYTEST_FLAGS

# Summary
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Todos os testes passaram!${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}✗ Alguns testes falharam. Verifique o output acima.${NC}"
    exit 1
fi
