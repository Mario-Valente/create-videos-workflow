#!/bin/bash
# setup.sh - Script de instalação automática para Mac

set -e

echo "=================================="
echo "🎬 VIDEO GENERATOR - SETUP SCRIPT"
echo "=================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para printar com cor
print_step() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. Verificar Homebrew
echo ""
echo "Checking prerequisites..."
if ! command -v brew &> /dev/null; then
    print_error "Homebrew não encontrado"
    echo "Instale com: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi
print_step "Homebrew encontrado"

# 2. Instalar ferramentas
echo ""
echo "Installing system tools..."

if ! command -v python3.11 &> /dev/null; then
    print_warning "Instalando Python 3.11..."
    brew install python@3.11
fi
print_step "Python 3.11"

if ! command -v ollama &> /dev/null; then
    print_warning "Instalando Ollama..."
    brew install ollama
fi
print_step "Ollama"

if ! command -v ffmpeg &> /dev/null; then
    print_warning "Instalando FFmpeg..."
    brew install ffmpeg
fi
print_step "FFmpeg"

# 3. Criar virtual environment
echo ""
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    print_step "Virtual environment criado"
else
    print_step "Virtual environment já existe"
fi

source venv/bin/activate

# 4. Instalar dependências Python
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip --quiet
print_step "pip atualizado"

pip install -r requirements.txt --quiet
print_step "Dependências base instaladas"

pip install librosa Pillow pyyaml requests --quiet 2>/dev/null
print_step "Dependências opcionais (librosa, Pillow, etc)"

# 5. Instalar Piper CLI
echo ""
echo "Setting up Piper TTS..."

# Opção 1: Try to install from source
if [ ! -d "$HOME/piper" ]; then
    print_warning "Clonando Piper..."
    git clone https://github.com/rhasspy/piper.git ~/piper > /dev/null 2>&1
    cd ~/piper/src/python
    pip install . --quiet 2>/dev/null || print_warning "Piper CLI - instalação alternativa pode ser necessária"
    cd - > /dev/null
fi

if command -v piper &> /dev/null; then
    print_step "Piper TTS CLI"
else
    print_warning "Piper CLI não encontrado - será necessário instalar manualmente"
fi

# 5a. Download Piper voice models
echo ""
echo "Downloading Piper voice models..."
mkdir -p ~/.local/share/piper
cd ~/.local/share/piper

# Verificar se modelo já existe
if [ ! -f "pt_BR-faber-medium.onnx" ]; then
    print_warning "Baixando modelo de voz português..."
    echo "  (Isto pode levar alguns minutos - ~65MB)"

    # Usar curl ou wget
    if command -v wget &> /dev/null; then
        wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx 2>/dev/null &
        wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json 2>/dev/null &
        wait
    elif command -v curl &> /dev/null; then
        curl -L -o pt_BR-faber-medium.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx 2>/dev/null &
        curl -L -o pt_BR-faber-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json 2>/dev/null &
        wait
    fi
    print_step "Modelos de voz português"
else
    print_step "Modelos de voz já existem"
fi

# 5. Download de modelos Ollama
echo ""
echo "Downloading Ollama models..."
echo "(Isto pode levar alguns minutos na primeira vez)"

# Verificar se Ollama está rodando
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_warning "Iniciando Ollama em background..."
    ollama serve > /dev/null 2>&1 &
    OLLAMA_PID=$!
    sleep 3
fi

if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_step "Ollama rodando"

    # Download de modelos
    echo "Downloading Mistral..."
    ollama pull mistral > /dev/null 2>&1 &
    MISTRAL_PID=$!

    echo "Downloading Llama2..."
    ollama pull llama2 > /dev/null 2>&1 &
    LLAMA_PID=$!

    # Aguardar downloads
    wait $MISTRAL_PID
    print_step "Mistral baixado"

    wait $LLAMA_PID
    print_step "Llama2 baixado"
else
    print_warning "Ollama não conseguiu conectar"
    echo "   Execute depois: ollama serve &"
    echo "   Depois: ollama pull mistral && ollama pull llama2"
fi

# 6. Testes finais
echo ""
echo "Running tests..."

if python -c "import ollama" 2>/dev/null; then
    print_step "Ollama Python client"
else
    print_warning "Ollama Python client não encontrado (opcional)"
fi

if python -c "import yaml" 2>/dev/null; then
    print_step "YAML support"
else
    print_error "YAML support não encontrado"
fi

if command -v ffmpeg &> /dev/null; then
    print_step "FFmpeg"
else
    print_error "FFmpeg não encontrado"
fi

# 7. Resumo
echo ""
echo "=================================="
echo "✨ SETUP COMPLETO!"
echo "=================================="
echo ""
echo "Próximos passos:"
echo ""
echo "1. Ativar ambiente:"
echo "   source venv/bin/activate"
echo ""
echo "2. (OPCIONAL) Iniciar Stable Diffusion em outro terminal:"
echo "   cd ~/stable-diffusion-webui && ./webui-user.sh"
echo ""
echo "3. Executar pipeline:"
echo "   python orchestrator.py --topic 'Seu tema aqui'"
echo ""
echo "Ou use Makefile:"
echo "   make full TOPIC='Seu tema aqui'"
echo ""
