# 🎬 Create Videos Workflows

Pipeline 100% local para geração automática de vídeos usando IA generativa.

**Sem APIs externas. Sem custos recorrentes. Roda localmente no seu Mac.**

## ✨ Características

- ✅ **100% Local**: Ollama (LLM) + Stable Diffusion (imagens) + Piper TTS (voz) + FFmpeg
- ✅ **Gratuito**: Open-source, sem APIs pagas
- ✅ **7 Etapas Bem Definidas**: Planejamento → Roteiro → Narração → Prompts → Imagens → Legendas → Composição
- ✅ **Rápido**: 15-25 minutos para vídeo 60s (M1/M2)
- ✅ **Extensível**: Configurável, scripts modulares, templates customizáveis
- ✅ **Mac Native**: Otimizado para macOS (M1/M2/M3)

## 🚀 Quick Start

### 1. Instalação (5 minutos)

```bash
# Clone e setup
cd create-videos-workflows
make setup

# Verificar instalação
make test
```

### 2. Gerar Primeiro Vídeo

```bash
# Ativar ambiente
source venv/bin/activate

# Executar pipeline
python orchestrator.py --topic "Inteligência Artificial em 2024"

# Ou use Makefile
make full TOPIC="Seu tema aqui"
```

### 3. Encontrar Vídeo

```bash
# Vídeo final em:
output/<timestamp>_tema/video_final.mp4

# Listar outputs
make list-outputs
```

## 📋 Pipeline em 7 Etapas

```
┌─────────────────────────────────────────────────────────┐
│ 1️⃣  PLANEJAMENTO (Ollama)                              │
│    Input: "Tema"                                         │
│    Output: plan.json (objetivo, público, tom, hook)     │
└─────────────┬───────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│ 2️⃣  ROTEIRO (Ollama)                                    │
│    Input: plan.json                                      │
│    Output: script.md (5 cenas com timing)                │
└─────────────┬───────────────────────────────────────────┘
              ↓
        ┌─────┴─────┐
        ↓           ↓
┌─────────────┐  ┌──────────────┐
│ 3️⃣ NARRAÇÃO │  │ 4️⃣ PROMPTS   │
│  (Piper)    │  │   (Ollama)   │
│ narration   │  │ image_       │
│ .wav        │  │ prompts.json │
└──────┬──────┘  └──────┬───────┘
       │                │
       └────────┬───────┘
                ↓
┌─────────────────────────────────────────────────────────┐
│ 5️⃣  IMAGENS (Stable Diffusion)                          │
│    Input: image_prompts.json                             │
│    Output: images/scene_001.png ... scene_N.png          │
└─────────────┬───────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│ 6️⃣  LEGENDAS (Python)                                   │
│    Input: script.md                                      │
│    Output: subtitles.srt, subtitles.vtt                  │
└─────────────┬───────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│ 7️⃣  COMPOSIÇÃO (FFmpeg)                                 │
│    Input: images/ + narration.wav + subtitles.srt       │
│    Output: video_final.mp4                               │
└─────────────┬───────────────────────────────────────────┘
              ↓
        VIDEO PRONTO! 🎉
```

## 💻 Requisitos

### Mínimo
- macOS 12+ (Intel ou Apple Silicon)
- 16GB RAM
- 50GB espaço livre
- Python 3.10+
- Homebrew

### Recomendado
- M1/M2/M3 Pro
- 32GB+ RAM
- 100GB+ espaço
- Rede rápida (para baixar modelos)

## 📦 Dependências Instaladas

| Ferramenta | Função | Instalação |
|------------|--------|------------|
| **Ollama** | LLM (texto) | `brew install ollama` |
| **Piper TTS** | Voz (narração) | `pip install piper-tts` |
| **Stable Diffusion** | Imagens | WebUI local |
| **FFmpeg** | Vídeo (composição) | `brew install ffmpeg` |
| **Python 3.11** | Runtime | `brew install python@3.11` |

## 📖 Documentação

- **[SETUP.md](docs/SETUP.md)** - Guia de instalação completo
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detalhes técnicos, fluxo de dados
- **[EXAMPLES.md](docs/EXAMPLES.md)** - 10+ exemplos práticos de uso

## 🎯 Exemplos de Uso

### Pipeline Completa (Forma Simples)
```bash
python orchestrator.py --topic "Como funcionam buracos negros"
```

### Com Opções
```bash
python orchestrator.py \
  --topic "Inteligência Artificial" \
  --output output/custom_dir \
  --fast  # Modo rápido (15 minutos)
```

### Steps Individuais
```bash
# Apenas planejamento
python scripts/01_plan.py --topic "Seu tema" --output output/meu_video

# Apenas narração + legendas
python scripts/03_voice.py --output output/meu_video
python scripts/06_subtitles.py --output output/meu_video

# Apenas recompor vídeo
python scripts/07_compose_video.py --project output/meu_video
```

### Makefile
```bash
# Setup completo
make setup

# Executar pipeline
make full TOPIC="Seu tema aqui"

# Teste de dependências
make test

# Verificar servidores
make check-server  # Ollama
make check-sd      # Stable Diffusion
```

## ⚙️ Configuração

### Customizar Modelos
Editar `config/models.yaml`:
```yaml
models:
  ollama:
    mistral:        # Rápido (DEFAULT)
    llama2:         # Mais preciso
    neural-chat:    # Mais conversacional
```

### Customizar Prompts
Editar `config/prompts.yaml`:
- Templates de planejamento
- Templates de roteiro
- Templates de otimização de imagens
- Templates de legendas

### Ajustar Qualidade
```bash
# Rápido (15 steps, ~3 min por imagem)
python scripts/05_generate_images.py --output output/meu_video --fast

# Qualidade (25 steps, ~8 min)
python scripts/05_generate_images.py --output output/meu_video

# Modo desenvolvimento (alterar crf em 07_compose_video.py)
```

## 📊 Tempos Esperados (M1/M2)

| Etapa | Tempo |
|-------|-------|
| 1. Planejamento | 20s |
| 2. Roteiro | 45s |
| 3. Narração | 10s |
| 4. Prompts | 45s |
| 5. Imagens (5x) | 10-25 min |
| 6. Legendas | 5s |
| 7. Composição | 2 min |
| **TOTAL** | **15-25 min** |

## 🔧 Troubleshooting

### Ollama não encontrado
```bash
brew install ollama
ollama serve  # Em terminal separado
```

### Stable Diffusion não conecta
```bash
cd ~/stable-diffusion-webui
./webui-user.sh  # Em terminal separado
```

### Timeout em geração de imagens
Aumentar em `config/models.yaml`:
```yaml
timeouts:
  sd_generate: 900  # 15 minutos
```

Mais ajuda em [SETUP.md](docs/SETUP.md#-troubleshooting)

## 📁 Estrutura do Projeto

```
create-videos-workflows/
├── scripts/
│   ├── 01_plan.py           # Planejamento
│   ├── 02_script.py         # Roteiro
│   ├── 03_voice.py          # Narração
│   ├── 04_image_prompts.py  # Prompts
│   ├── 05_generate_images.py # Imagens
│   ├── 06_subtitles.py      # Legendas
│   ├── 07_compose_video.py  # Composição
│   └── utils.py             # Funções compartilhadas
├── config/
│   ├── prompts.yaml         # Templates de prompts
│   └── models.yaml          # Config de modelos
├── docs/
│   ├── SETUP.md             # Instalação
│   ├── ARCHITECTURE.md      # Arquitetura
│   └── EXAMPLES.md          # Exemplos
├── orchestrator.py          # Orquestrador central
├── Makefile                 # Automação
├── requirements.txt         # Dependências Python
└── README.md                # Este arquivo
```

## 🎨 Customizações Comuns

### Mudar Idioma de Narração
Em `scripts/03_voice.py`:
```python
generate_voice(narration_text, audio_output,
               language="en_US")  # pt_BR, en_US, es_ES, etc
```

### Mudar Resolução de Imagens
Em `scripts/05_generate_images.py`:
```python
image_bytes = sd.generate_image(
    ...,
    width=2560,      # Default 1920
    height=1440      # Default 1080
)
```

### Adicionar Efeitos ao Vídeo
Em `scripts/07_compose_video.py`, adicionar FFmpeg filters:
```bash
-vf "subtitles=..., scale=1920:-1, fps=30"
```

## 🚀 Próximos Passos

1. **[Setup](docs/SETUP.md)** - Instalar dependências
2. **[Quick Start](docs/SETUP.md#-uso-básico)** - Executar primeiro vídeo
3. **[Examples](docs/EXAMPLES.md)** - Explorar 10+ exemplos
4. **[Customize](docs/EXAMPLES.md#-exemplo-3-customizar-prompts)** - Adaptar para seus temas

## 📝 Licença

MIT - Livre para usar, modificar e distribuir

## 🤝 Contribuindo

Bugs, sugestões ou melhorias? Issues e PRs são bem-vindos!

## 📞 Suporte

- 📚 Documentação: [docs/](docs/)
- ❓ FAQ: [docs/SETUP.md#troubleshooting](docs/SETUP.md#-troubleshooting)
- 💬 Discussões: Issues no repositório

---

**Made with ❤️ para criadores locais**

Gerado com Claude Code - https://claude.com/claude-code
