#!/bin/bash
# Script para rodar testes organizados

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    echo "Uso: ./run_tests.sh [opção]"
    echo ""
    echo "Opções:"
    echo "  all         - Roda todos os testes (padrão)"
    echo "  unit        - Roda apenas testes unitários"
    echo "  integration - Roda apenas testes de integração"
    echo "  quick       - Roda testes rápidos (sem marca 'slow')"
    echo "  coverage    - Roda com coverage report"
    echo "  watch       - Roda em modo watch (reexecuta ao salvar)"
    echo "  <arquivo>   - Roda teste específico"
    echo ""
}

run_all() {
    echo -e "${BLUE}🧪 Rodando TODOS os testes...${NC}"
    pytest tests/ -v
}

run_unit() {
    echo -e "${BLUE}🧪 Rodando testes UNITÁRIOS...${NC}"
    pytest tests/unit/ -v
}

run_integration() {
    echo -e "${BLUE}🧪 Rodando testes de INTEGRAÇÃO...${NC}"
    pytest tests/integration/ -v
}

run_quick() {
    echo -e "${BLUE}⚡ Rodando testes RÁPIDOS (sem 'slow')...${NC}"
    pytest tests/ -v -m "not slow"
}

run_coverage() {
    echo -e "${BLUE}📊 Rodando testes COM COVERAGE...${NC}"
    pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
    echo -e "${GREEN}✓ Coverage report gerado em htmlcov/index.html${NC}"
}

run_watch() {
    echo -e "${BLUE}👁️  Modo WATCH - rodando testes ao salvar...${NC}"
    pytest tests/ -v --looponfail
}

# Se nenhum argumento, roda todos
if [ $# -eq 0 ]; then
    run_all
else
    case "$1" in
        all)
            run_all
            ;;
        unit)
            run_unit
            ;;
        integration)
            run_integration
            ;;
        quick)
            run_quick
            ;;
        coverage)
            run_coverage
            ;;
        watch)
            run_watch
            ;;
        help|-h|--help)
            usage
            ;;
        *)
            # Se não é um dos comandos acima, trata como arquivo
            if [[ "$1" == tests/* ]]; then
                echo -e "${BLUE}🧪 Rodando teste: $1${NC}"
                pytest "$1" -v
            else
                echo -e "${RED}✗ Opção desconhecida: $1${NC}"
                usage
                exit 1
            fi
            ;;
    esac
fi

# Mostrar status final
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Testes PASSARAM!${NC}\n"
else
    echo -e "\n${RED}❌ Testes FALHARAM!${NC}\n"
    exit 1
fi
