.PHONY: help setup install clean test full plan script voice images subtitles compose

# Variáveis
TOPIC ?= "Teste de pipeline"
OUTPUT_DIR ?= output/default
PYTHON := python3
PIP := pip3

help:
	@echo "🎬 Video Generator Pipeline - Makefile"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo ""
	@echo "  make setup          Instala todas as dependências"
	@echo "  make install        Mesmo que setup"
	@echo ""
	@echo "  make full TOPIC=\"seu tema\"     Executa pipeline completa"
	@echo "  make plan TOPIC=\"seu tema\"     Etapa 1: Planejamento"
	@echo "  make script          Etapa 2: Roteiro"
	@echo "  make voice          Etapa 3: Narração"
	@echo "  make prompts        Etapa 4: Prompts de imagens"
	@echo "  make images         Etapa 5: Geração de imagens"
	@echo "  make subtitles      Etapa 6: Legendas"
	@echo "  make compose        Etapa 7: Composição de vídeo"
	@echo ""
	@echo "  make clean          Remove outputs gerados"
	@echo "  make test           Testa dependências"
	@echo ""
	@echo "Exemplos:"
	@echo "  make full TOPIC=\"Como funcionam buracos negros\""
	@echo "  make plan TOPIC=\"Inteligência Artificial\""
	@echo ""

# Alvo padrão
.DEFAULT_GOAL := help

# Setup e instalação
setup: check-homebrew install-tools install-python-deps init-ollama
	@echo "✓ Setup completo!"

install: setup

check-homebrew:
	@command -v brew >/dev/null 2>&1 || \
		(echo "❌ Homebrew não instalado"; \
		echo "Execute: /bin/bash -c \"\$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""; \
		exit 1)
	@echo "✓ Homebrew encontrado"

install-tools:
	@echo "📦 Instalando ferramentas (FFmpeg, Ollama)..."
	@command -v ffmpeg >/dev/null 2>&1 || brew install ffmpeg
	@command -v ollama >/dev/null 2>&1 || brew install ollama
	@echo "✓ Ferramentas instaladas"

install-python-deps:
	@echo "📦 Instalando dependências Python..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "✓ Dependências Python instaladas"

init-ollama:
	@echo "📥 Baixando modelos Ollama..."
	@echo "   (Isso pode levar alguns minutos)"
	@command -v ollama >/dev/null 2>&1 && \
		(ollama pull mistral || echo "⚠️  ollama serve deve estar rodando") || \
		echo "⚠️  Ollama será necessário"
	@echo "✓ Modelos Ollama prontos"

# Teste de dependências
test:
	@echo "🔍 Testando dependências..."
	@command -v python3 >/dev/null 2>&1 && echo "✓ Python3" || (echo "✗ Python3 não encontrado" && exit 1)
	@command -v ffmpeg >/dev/null 2>&1 && echo "✓ FFmpeg" || (echo "⚠️  FFmpeg não encontrado" && exit 1)
	@command -v ollama >/dev/null 2>&1 && echo "✓ Ollama" || (echo "⚠️  Ollama não encontrado" && exit 1)
	@command -v piper >/dev/null 2>&1 && echo "✓ Piper TTS" || (echo "⚠️  Piper TTS não encontrado" && exit 1)
	@echo "✓ Todas as dependências presentes"

# Pipeline steps
plan:
	@$(PYTHON) scripts/01_plan.py --topic "$(TOPIC)" --output "$(OUTPUT_DIR)"

script: plan
	@$(PYTHON) scripts/02_script.py --output "$(OUTPUT_DIR)"

voice: script
	@$(PYTHON) scripts/03_voice.py --output "$(OUTPUT_DIR)"

prompts: script
	@$(PYTHON) scripts/04_image_prompts.py --output "$(OUTPUT_DIR)"

images: prompts
	@$(PYTHON) scripts/05_generate_images.py --output "$(OUTPUT_DIR)"

subtitles: voice
	@$(PYTHON) scripts/06_subtitles.py --output "$(OUTPUT_DIR)"

compose: voice images subtitles
	@$(PYTHON) scripts/07_compose_video.py --project "$(OUTPUT_DIR)"

# Pipeline completa
full:
	@$(PYTHON) orchestrator.py --topic "$(TOPIC)" --output "$(OUTPUT_DIR)"

# Limpeza
clean:
	@echo "🗑️  Limpando outputs..."
	@rm -rf output/
	@echo "✓ Limpeza concluída"

clean-cache:
	@echo "🗑️  Limpando cache Python..."
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "✓ Cache limpo"

# Desenvolvimento
lint:
	@echo "🔍 Linting..."
	@$(PYTHON) -m black scripts/ --check || true
	@$(PYTHON) -m flake8 scripts/ --max-line-length=100 || true

format:
	@echo "✨ Formatando código..."
	@$(PYTHON) -m black scripts/

# Documentação
docs:
	@echo "📚 Documentação disponível em:"
	@echo "   - docs/SETUP.md"
	@echo "   - docs/ARCHITECTURE.md"
	@echo "   - docs/EXAMPLES.md"

# Utilitários
check-server:
	@echo "🔍 Verificando Ollama..."
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "✓ Ollama rodando" || echo "✗ Ollama não está rodando (execute: ollama serve)"

check-sd:
	@echo "🔍 Verificando Stable Diffusion..."
	@curl -s http://127.0.0.1:7860/api/v1/txt2img > /dev/null 2>&1 && echo "✓ Stable Diffusion rodando" || echo "✗ Stable Diffusion não está rodando"

list-outputs:
	@echo "📁 Outputs gerados:"
	@find output -type f -name "video_final.mp4" -exec ls -lh {} \;

# Scripts de desenvolvimento
start-servers:
	@echo "🚀 Iniciando servidores..."
	@echo "  1. Ollama (em background)..."
	@ollama serve &
	@sleep 2
	@echo "  2. Lembre-se de iniciar Stable Diffusion WebUI:"
	@echo "     cd ~/stable-diffusion-webui && ./webui-user.sh"

.PHONY: check-server check-sd list-outputs start-servers lint format docs clean-cache check-homebrew install-tools install-python-deps init-ollama test
