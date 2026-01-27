# ARCHITECTURE.md - Arquitetura Técnica

## 📐 Visão Geral

Pipeline 100% local para geração automática de vídeos usando IA generativa:

```
Input (Tema)
    ↓
[1. Planejamento] → Ollama
    ↓
[2. Roteiro] → Ollama
    ↓
[3. Narração] → Piper TTS
    ↓
[4. Prompts] → Ollama
    ↓
[5. Imagens] → Stable Diffusion
    ↓
[6. Legendas] → Python (processamento de texto)
    ↓
[7. Composição] → FFmpeg
    ↓
Output (Vídeo MP4)
```

## 🏗️ Componentes Principais

### 1. **Orchestrator** (`orchestrator.py`)
- Coordena execução de todos os 7 steps
- Gerencia logging e resultados
- Permite skip de steps individuais
- Rastreia tempo de execução

### 2. **Utils** (`scripts/utils.py`)
Classes compartilhadas:

- **OllamaClient**: Interface com Ollama (POST requests)
- **FileManager**: Gerencia estrutura de arquivos de saída
- **ConfigManager**: Carrega configurações YAML
- **ScriptParser**: Parseia markdown para extrair cenas
- **TimestampExtractor**: Extrai duração de áudio
- **VideoComposer**: Constrói comandos FFmpeg
- **StableDiffusionGenerator**: Interface com WebUI

### 3. **Scripts de Processamento** (7 etapas)

```
01_plan.py
├── Input: Tema (string)
├── LLM: Ollama Mistral
├── Output: plan.json
│   ├── tema
│   ├── publico
│   ├── tom
│   ├── pontos_chave[]
│   └── hook_inicial
└── Tempo: 10-30s

02_script.py
├── Input: plan.json
├── LLM: Ollama Mistral
├── Output: script.md
│   ├── ## CENA 1 (0-10s)
│   ├── **Narração:** ...
│   └── **Visual:** ...
└── Tempo: 30-60s

03_voice.py
├── Input: script.md
├── TTS: Piper (pt_BR)
├── Output:
│   ├── audio/narration.wav
│   └── timestamps.json
└── Tempo: 5-15s

04_image_prompts.py
├── Input: script.md + plan.json
├── LLM: Ollama Mistral
├── Output: image_prompts.json
│   ├── cenas[]
│   ├── prompt_otimizado
│   └── duracao
└── Tempo: 30-60s

05_generate_images.py
├── Input: image_prompts.json
├── Image Gen: Stable Diffusion
├── Output: images/scene_001.png ... scene_N.png
│   ├── Resolução: 1920×1080
│   ├── Formato: PNG
│   └── Steps: 15-25
└── Tempo: 2-10 min por imagem

06_subtitles.py
├── Input: script.md
├── Processamento: Regex + split
├── Output:
│   ├── subtitles.srt
│   └── subtitles.vtt
└── Tempo: 5-10s

07_compose_video.py
├── Input:
│   ├── images/scene_*.png
│   ├── audio/narration.wav
│   └── subtitles.srt
├── Composição: FFmpeg
├── Output: video_final.mp4
│   ├── Codec: H.264
│   ├── FPS: 30
│   └── CRF: 18
└── Tempo: 1-3 min
```

## 🔄 Fluxo de Dados

### Estrutura de Diretórios

```
output/{timestamp}_tema/
├── plan.json                    # [01] Input: tema → Output: estrutura
├── script.md                    # [02] Output: roteiro em markdown
├── image_prompts.json           # [04] Output: prompts otimizados
├── timestamps.json              # [03] Output: timing de áudio
├── subtitles.srt               # [06] Output: legendas SRT
├── subtitles.vtt               # [06] Output: legendas VTT
├── audio/
│   └── narration.wav           # [03] Output: áudio narração
├── images/
│   ├── scene_001.png           # [05] Output: imagens geradas
│   ├── scene_002.png
│   └── ...
├── video_final.mp4             # [07] Output: vídeo final
├── pipeline.log                # Log detalhado de execução
└── pipeline_results.json       # Resumo de resultados
```

## 🔗 Dependências Externas

### **Ollama (LLM Local)**
```
POST http://localhost:11434/api/generate
{
  "model": "mistral",
  "prompt": "...",
  "stream": false,
  "temperature": 0.7
}
```

Modelos disponíveis:
- **mistral** (7B): Rápido, versátil → DEFAULT
- **llama2** (7B): Mais preciso
- **neural-chat** (7B): Conversacional

### **Piper TTS**
```bash
piper --model pt_BR-faber-medium \
      --input-file script.txt \
      --output-file narration.wav
```

Formatos suportados:
- pt_BR (português), en_US, es_ES, fr_FR, etc
- Vozes: faber-medium, faber-large, ljspeech-high

### **Stable Diffusion**
```
POST http://127.0.0.1:7860/api/v1/txt2img
{
  "prompt": "...",
  "steps": 25,
  "width": 1920,
  "height": 1080,
  "cfg_scale": 7.5
}
```

Resposta: Base64-encoded PNG

### **FFmpeg**
```bash
ffmpeg -framerate 30 \
       -i images/scene_%03d.png \
       -i audio/narration.wav \
       -vf subtitles=subtitles.srt \
       -c:v libx264 -crf 18 \
       video_final.mp4
```

## 📊 Processamento por Step

### Step 1: Planejamento
**Input**: Tema (string)
**Processamento**:
```python
prompt = PLAN_PROMPT.format(topic=topic)
plan = ollama.generate_json(prompt, model="mistral")
# Validar campos obrigatórios
# Salvar JSON
```

### Step 2: Roteiro
**Input**: plan.json
**Processamento**:
```python
# Ler plan.json
# Construir prompt com contexto
# Gerar markdown com regex pattern: "## CENA (\d+) \((\d+)-(\d+)s\)"
# Extrair narração e visual de cada cena
```

### Step 3: Narração
**Input**: script.md
**Processamento**:
```python
# Regex: extrair **Narração:** lines
# Concatenar em texto único
# Executar Piper TTS
# Extrair duração com librosa
# Gerar timestamps.json
```

### Step 4: Prompts
**Input**: script.md + plan.json
**Processamento**:
```python
# Extrair descrições visuais (**Visual:** lines)
# Para cada visual:
#   - Construir prompt de otimização
#   - Chamar Ollama
#   - Salvar prompt otimizado
```

### Step 5: Imagens
**Input**: image_prompts.json
**Processamento**:
```python
# Para cada cena:
#   - Conectar ao Stable Diffusion
#   - POST txt2img com prompt
#   - Decodificar Base64
#   - Salvar PNG com padding (scene_001.png)
```

### Step 6: Legendas
**Input**: script.md
**Processamento**:
```python
# Extrair cenas e timing: ## CENA (\d+) \((\d+)-(\d+)s\)
# Para cada cena:
#   - Dividir narração em linhas (max 42 chars)
#   - Calcular timing por linha
#   - Formato SRT: index, timestamps, text
#   - Formato VTT: timestamps com ".mmm", text
```

### Step 7: Composição
**Input**: images/, audio/narration.wav, subtitles.srt
**Processamento**:
```bash
# Construir comando FFmpeg:
ffmpeg -framerate 30 \
       -i images/scene_%03d.png \  # Sequence of images
       -i audio/narration.wav \      # Audio file
       -vf subtitles=subtitles.srt \ # Subtitle filter
       -c:v libx264 -preset slow \   # Video codec
       -crf 18 -c:a aac -b:a 128k \  # Audio codec
       -shortest \                    # Use minimum duration
       video_final.mp4
```

## ⚡ Otimizações

### Paralelização Futura
Potencial para paralelizar:
- **Step 5** (Imagens): Gerar múltiplas imagens simultaneamente
- Criar um job queue com reutilização de conexão Stable Diffusion

### Caching
Implementar em versão futura:
- Cache de prompts gerados
- Cache de imagens por prompt hash
- Reuso de modelos Ollama em memória

### Performance
**Gargalos atuais**:
1. Geração de imagens (Stable Diffusion) → ~50% do tempo total
2. Composição com FFmpeg → ~20% do tempo

**Melhorias possíveis**:
- GPU mais potente (NVIDIA RTX 4090)
- Usar modelos menores do Stable Diffusion
- Paralelizar geração de imagens

## 🛡️ Validações

**Step 1 (Planejamento)**:
```python
required_fields = ["tema", "publico", "ton", "pontos_chave"]
for field in required_fields:
    if field not in plan:
        raise ValueError(f"Campo obrigatório faltando: {field}")
```

**Step 2 (Roteiro)**:
```python
num_scenes = script.count("## CENA")
if num_scenes < 3 or num_scenes > 8:
    raise ValueError(f"Número de cenas inválido: {num_scenes}")
```

**Step 5 (Imagens)**:
```python
if not sd.check_connection():
    raise RuntimeError("Stable Diffusion não acessível")
```

**Step 7 (Composição)**:
```python
if not Path(output_file).exists():
    raise FileNotFoundError("Vídeo não foi gerado")
```

## 📈 Métricas

**Saídas por step**:
- Step 1: 1 arquivo JSON (~2KB)
- Step 2: 1 arquivo Markdown (~1-2KB)
- Step 3: 1 arquivo WAV (~500KB-2MB) + 1 JSON (~1KB)
- Step 4: 1 arquivo JSON (~5-10KB)
- Step 5: N PNGs (~500KB-2MB cada)
- Step 6: 2 arquivos (SRT + VTT, ~5KB cada)
- Step 7: 1 arquivo MP4 (~50-200MB)

**Tempo total esperado**:
- Padrão: 15-25 minutos
- Rápido: 10-15 minutos
- Qualidade: 30-45 minutos

## 🔐 Segurança

**Validações contra injection**:
- Prompts escapados antes de passar para Ollama
- Paths sanitizados antes de usar em FFmpeg
- Sem execução de shell arbitrário (uso de subprocess.run com args separados)

**Permissões de arquivo**:
- Criação automática de diretórios necessários
- Escritura em output/ apenas
- Leitura de config/ apenas
