#!/bin/bash
# test_setup.sh - Verifica se tudo está instalado corretamente

echo "=================================="
echo "🔍 TESTANDO SETUP"
echo "=================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

# Função para testar
test_command() {
    local name=$1
    local cmd=$2

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $name"
        ((FAILED++))
    fi
}

# Testes
echo "Ferramentas do sistema:"
test_command "Python 3.11" "python3.11 --version"
test_command "FFmpeg" "ffmpeg -version"
test_command "Ollama" "ollama --version"
test_command "Git" "git --version"

echo ""
echo "Python packages:"
test_command "ollama" "python3.11 -c 'import ollama'"
test_command "yaml" "python3.11 -c 'import yaml'"
test_command "requests" "python3.11 -c 'import requests'"
test_command "tqdm" "python3.11 -c 'import tqdm'"

echo ""
echo "Piper TTS:"
test_command "piper CLI" "piper --version"

echo ""
echo "Modelos Piper:"
test_command "Modelo português" "test -f ~/.local/share/piper/pt_BR-faber-medium.onnx"

echo ""
echo "Ollama server:"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama server rodando"
    ((PASSED++))

    # Verificar modelos
    MODELS=$(ollama list 2>/dev/null | grep -c "mistral\|llama2")
    if [ "$MODELS" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Modelos Ollama instalados"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} Nenhum modelo Ollama encontrado (execute: ollama pull mistral)"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Ollama server não está rodando (execute: ollama serve)"
fi

echo ""
echo "Projeto:"
test_command "orchestrator.py" "test -f orchestrator.py"
test_command "scripts/" "test -d scripts"
test_command "config/" "test -d config"
test_command "docs/" "test -d docs"

echo ""
echo "=================================="
echo "RESULTADO: ${GREEN}${PASSED} OK${NC} / ${RED}${FAILED} FALHA${NC}"
echo "=================================="

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "✨ Tudo pronto! Execute:"
    echo ""
    echo "  source venv/bin/activate"
    echo "  python orchestrator.py --topic 'Seu tema aqui'"
    echo ""
    exit 0
else
    echo ""
    echo "⚠️  Existem problemas a resolver. Veja QUICK_INSTALL.md"
    exit 1
fi
