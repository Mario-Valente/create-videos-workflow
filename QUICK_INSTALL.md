# Quick Install - Instalação Rápida (Mac)

Se o `setup.sh` tiver problemas, siga estes passos manualmente:

## 1️⃣ Setup Básico (5 minutos)

```bash
cd /Users/mario.valente/my-projects/create-videos-workflows

# Criar virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências simples
pip install --upgrade pip
pip install -r requirements.txt
```

## 2️⃣ Instalar Piper TTS (5 minutos)

### ⭐ Opção A: Binário Pré-compilado (RECOMENDADO para Mac)

```bash
# Criar diretório
mkdir -p ~/piper-bin

# Download do binário macOS
cd ~/piper-bin
curl -L -o piper.tar.gz "https://github.com/rhasspy/piper/releases/download/2024.01.30/piper_macos_arm64.tar.gz"

# Extrair
tar -xzf piper.tar.gz

# Adicionar ao PATH
export PATH="$HOME/piper-bin/piper/bin:$PATH"
echo 'export PATH="$HOME/piper-bin/piper/bin:$PATH"' >> ~/.zshrc

# Verificar
piper --version
```

### Opção B: Via pip (menos recomendado, pode ter conflitos)
```bash
# Só tenta se Opção A não funcionar
pip install piper-tts
```

## 3️⃣ Baixar Modelos de Voz (5 minutos)

```bash
# Criar diretório
mkdir -p ~/.local/share/piper
cd ~/.local/share/piper

# Baixar modelo português (via curl no Mac)
echo "Baixando modelo de voz..."
curl -L -o pt_BR-faber-medium.onnx \
  "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx"

curl -L -o pt_BR-faber-medium.onnx.json \
  "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json"

echo "✓ Pronto!"
```

## 4️⃣ Instalar Resto das Dependências (1 minuto)

```bash
source venv/bin/activate  # Se não estiver ativo

pip install librosa Pillow pyyaml requests -q
```

## 5️⃣ Testar Tudo

```bash
# Terminal 1: Inicie Ollama
ollama serve

# Terminal 2: Verifique instalação
source venv/bin/activate
python -c "import ollama; print('✓ Ollama OK')"
python -c "import yaml; print('✓ YAML OK')"
piper --version
ffmpeg -version | head -1

# Terminal 3: Teste Piper
echo "Olá mundo" | piper --model pt_BR-faber-medium --output_file /tmp/test.wav
file /tmp/test.wav  # Deve retormar "WAV audio"
```

## 6️⃣ Executar Pipeline

```bash
source venv/bin/activate

# Teste rápido
python orchestrator.py --topic "Teste rápido" --fast

# Verificar output
ls -lh output/*/video_final.mp4
```

---

## ⚠️ Se tiver erros:

### Erro: "piper: command not found"
```bash
# Tente adicionar ao PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

# Ou verifique localização
find ~ -name piper -type f 2>/dev/null
```

### Erro: "Modelo não encontrado"
```bash
# Verificar se modelo foi baixado
ls -lh ~/.local/share/piper/pt_BR*

# Se não existe, baixar novamente
cd ~/.local/share/piper
curl -L -O "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx"
curl -L -O "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json"
```

### Erro: "Ollama não conecta"
```bash
# Terminal novo:
ollama serve

# Testar conexão
curl http://localhost:11434/api/tags
```

### Erro: "FFmpeg not found"
```bash
brew install ffmpeg
which ffmpeg
```

---

## ✅ Checklist Final

- [ ] Python 3.11 instalado (`python3.11 --version`)
- [ ] Virtual environment criado (`ls venv/`)
- [ ] Ollama rodando (`ollama serve`)
- [ ] Ollama tem modelos (`ollama list`)
- [ ] Piper CLI funciona (`piper --version`)
- [ ] Modelo português existe (`ls ~/.local/share/piper/pt_BR*`)
- [ ] FFmpeg funciona (`ffmpeg -version`)
- [ ] `orchestrator.py` existe (`ls orchestrator.py`)

Se tudo estiver OK, execute:

```bash
source venv/bin/activate
python orchestrator.py --topic "Seu tema aqui"
```

---

**Pronto! Seu primeiro vídeo deve ser gerado em 15-25 minutos.** 🎬
