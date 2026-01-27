# SETUP.md - Guia de Instalação

## ⚡ Instalação Rápida (Mac)

### 1. Pré-requisitos
- macOS 12+
- Homebrew instalado
- Python 3.10+

### 2. Instalação das Dependências

#### **Passo 1: Ferramentas do Sistema**

```bash
# Instalar com Homebrew
brew install ollama ffmpeg python@3.11
```

#### **Passo 2: Python Virtual Environment**

```bash
cd create-videos-workflows
python3.11 -m venv venv
source venv/bin/activate
```

#### **Passo 3: Dependências Python Base**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### **Passo 4: Piper TTS (CLI - Recomendado para Mac)**

**Opção A: Binário Pré-compilado (⭐ Recomendado)**
```bash
# Download do binário para macOS ARM64 (M1/M2/M3)
mkdir -p ~/piper-bin
cd ~/piper-bin
curl -L -o piper.tar.gz "https://github.com/rhasspy/piper/releases/download/2024.01.30/piper_macos_arm64.tar.gz"
tar -xzf piper.tar.gz

# Adicionar ao PATH
export PATH="$HOME/piper-bin/piper/bin:$PATH"
echo 'export PATH="$HOME/piper-bin/piper/bin:$PATH"' >> ~/.zshrc

# Verificar
piper --version
```

**Ou Opção B: Python package (menos recomendado)**
```bash
pip install piper-tts
# Pode ter warnings de dependências, mas CLI funcionará
```

#### **Passo 5: Modelos do Piper (Português)**

```bash
# Criar diretório para modelos
mkdir -p ~/.local/share/piper

# Baixar vozes português
cd ~/.local/share/piper

# Opção 1: Voz feminina mais natural (recomendado)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json

# Opção 2: Voz feminina com variações
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/high/pt_BR-faber-high.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/high/pt_BR-faber-high.onnx.json
```

#### **Passo 6: Dependências Opcionais**

```bash
pip install librosa Pillow pyyaml requests
```

#### **Passo 7: Modelos Ollama**

```bash
# Em outro terminal, inicie Ollama
ollama serve &

# Em outro terminal, baixe modelos
ollama pull mistral
ollama pull llama2
```

#### **Verificação Rápida**

```bash
# Verificar Piper
piper --version

# Verificar Ollama
curl http://localhost:11434/api/tags

# Verificar FFmpeg
ffmpeg -version | head -n 1
```

### 3. Configurar Stable Diffusion (Opcional mas recomendado)

```bash
# Clone a WebUI
cd ~
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui

# Baixe o modelo (este passo é demorado: 10-20GB)
# A WebUI vai fazer isso automaticamente na primeira execução

# Inicie em um terminal separado:
./webui-user.sh
# Acesse: http://127.0.0.1:7860
```

## 📋 Verificar Instalação

```bash
# Testar dependências
make test

# Verificar Ollama
make check-server

# Verificar Stable Diffusion
make check-sd
```

## 🚀 Uso Básico

### Executar Pipeline Completa

```bash
# Ativar venv
source venv/bin/activate

# Executar com tema específico
python orchestrator.py --topic "Inteligência Artificial"

# Ou usar Makefile
make full TOPIC="Inteligência Artificial"
```

### Executar Steps Individuais

```bash
# Step 1: Planejamento
python scripts/01_plan.py --topic "Seu tema" --output output/meu_video

# Step 2: Roteiro
python scripts/02_script.py --output output/meu_video

# Step 3: Narração
python scripts/03_voice.py --output output/meu_video

# Step 4: Prompts de Imagem
python scripts/04_image_prompts.py --output output/meu_video

# Step 5: Gerar Imagens
python scripts/05_generate_images.py --output output/meu_video

# Step 6: Legendas
python scripts/06_subtitles.py --output output/meu_video

# Step 7: Composição de Vídeo
python scripts/07_compose_video.py --project output/meu_video
```

## ⚙️ Configurações Importantes

### Modelos Ollama

Por padrão, usamos **Mistral** (rápido). Alternativas:

```yaml
# config/models.yaml - modifique para usar:
ollama_model: "llama2"      # Mais preciso, mais lento
ollama_model: "neural-chat" # Mais rápido, menor qualidade
```

### Qualidade de Imagens

**Modo Rápido** (15 steps, ~2-3 min por imagem):
```bash
python scripts/05_generate_images.py --output output/meu_video --fast
```

**Modo Qualidade** (25 steps, ~5-10 min):
```bash
python scripts/05_generate_images.py --output output/meu_video
```

### Velocidade de Narração

Edite em `scripts/03_voice.py`:
```python
# Padrão: "faber-medium" (~150 palavras/min)
# Opções: "faber-medium", "faber-large" (mais natural)
```

## 🔧 Troubleshooting

### Ollama não encontrado
```bash
# Instalado?
which ollama

# Se não: brew install ollama

# Se instalado, verificar se está rodando:
curl http://localhost:11434/api/tags

# Se erro, inicie: ollama serve
```

### Stable Diffusion não encontrado
```bash
# Verificar se está rodando:
curl http://127.0.0.1:7860/config

# Se erro, inicie em outro terminal:
cd ~/stable-diffusion-webui && ./webui-user.sh
```

### Erro de dependências Python
```bash
# Reativar venv e reinstalar
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Erro de timeout em geração de imagens
- Aumente timeout em `config/models.yaml` (timeouts.sd_generate)
- Use menos steps (--fast)
- Reduza resolução em `config/models.yaml`

## 📊 Requisitos de Hardware (Mac)

| Hardware | Tempo Total | Qualidade |
|----------|-------------|-----------|
| M1/M2    | 15-25 min   | Boa      |
| M1/M2 Pro| 10-15 min   | Muito Boa|
| M3/M3 Max| 5-10 min    | Excelente|

**Armazenamento**: Mínimo 50GB (especialmente para Stable Diffusion)

## 🔄 Atualizar Modelos

```bash
# Puxar novos modelos Ollama
ollama pull llama2
ollama pull neural-chat

# Listar modelos instalados
ollama list

# Remover modelo
ollama rm mistral
```

## 📝 Estrutura de Saída

```
output/
├── 20240127_153000_Seu_Tema/
│   ├── plan.json                  # Planejamento
│   ├── script.md                  # Roteiro
│   ├── image_prompts.json         # Prompts otimizados
│   ├── subtitles.srt              # Legendas (SRT)
│   ├── subtitles.vtt              # Legendas (VTT)
│   ├── images/
│   │   ├── scene_001.png
│   │   ├── scene_002.png
│   │   └── ...
│   ├── audio/
│   │   └── narration.wav
│   ├── video_final.mp4            # Vídeo final
│   ├── pipeline.log               # Log detalhado
│   └── pipeline_results.json      # Resumo dos resultados
```

## 🎯 Próximos Passos

1. Executar pipeline teste: `make full TOPIC="Teste"`
2. Verificar saída em `output/`
3. Customizar prompts em `config/prompts.yaml`
4. Ajustar timings de narração em scripts
5. Explorar diferentes modelos e qualidades

## 📚 Mais Informações

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detalhes técnicos
- [EXAMPLES.md](./EXAMPLES.md) - Exemplos de uso
- [config/models.yaml](../config/models.yaml) - Configurações de modelos
- [config/prompts.yaml](../config/prompts.yaml) - Templates de prompts
