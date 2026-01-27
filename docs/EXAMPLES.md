# EXAMPLES.md - Exemplos de Uso

## 🎬 Exemplo 1: Pipeline Completa com Tema Simples

### Situação
Você quer criar um vídeo sobre "Como funcionam buracos negros" em 5 minutos.

### Execução

```bash
# Ativar ambiente
source venv/bin/activate

# Executar pipeline completa
python orchestrator.py --topic "Como funcionam buracos negros"
```

### Saída esperada

```
============================================================
🎬 GERADOR DE VÍDEOS - PIPELINE COMPLETA
============================================================
Tema: Como funcionam buracos negros
Saída: output/20240127_153000_Como_funcionam_buracos_negros
Início: 2024-01-27 15:30:00
============================================================

📋 ETAPA 1/7: Planejamento
==================================================
[15:30:05] ✓ Plano criado com sucesso!
[15:30:05]   Tema: Como funcionam buracos negros
[15:30:05]   Público: Público geral, 13+
[15:30:05]   Tom: Educativo, acessível, com curiosidades
[15:30:05]   Cenas: 5

📝 ETAPA 2/7: Roteiro
==================================================
[15:30:45] ✓ Script criado com sucesso!
[15:30:45]   Cenas geradas: 5

🎙️ ETAPA 3/7: Narração
==================================================
[15:30:50] 🎙️ Geração de narração
[15:31:05] ✓ Narração criada com sucesso!
[15:31:05]   Duração: 58.2s
[15:31:05]   Cenas: 5

🎨 ETAPA 4/7: Prompts
==================================================
[15:31:10] 🎨 Geração de prompts para imagens
[15:31:45] ✓ Prompts gerados com sucesso!
[15:31:45]   Cenas: 5

🖼️ ETAPA 5/7: Imagens
==================================================
[15:31:50] 🖼️ Geração de imagens
[15:31:50] ✓ Conectado ao Stable Diffusion
[15:31:50] 📋 5 cenas para gerar

[1/5] Cena 1:
  Prompt: Space background with glowing stars...
  ✓ Salvo: scene_001.png

[2/5] Cena 2:
  Prompt: Scientific diagram of stellar collapse...
  ✓ Salvo: scene_002.png

... (3-5)

[15:37:30] ✓ Geração de imagens concluída!
[15:37:30]   Pasta: output/.../images

📄 ETAPA 6/7: Legendas
==================================================
[15:37:35] ✓ Legendas criadas com sucesso!
[15:37:35]   SRT: subtitles.srt
[15:37:35]   VTT: subtitles.vtt
[15:37:35]   Total de linhas: 12

🎬 ETAPA 7/7: Composição
==================================================
[15:37:40] 🎬 Composição do vídeo final
[15:37:40] ⚖️ Modo equilibrado
[15:37:40] 📋 5 imagens encontradas
[15:37:40] ⏳ Compilando vídeo (fps=30, crf=20)...

ffmpeg -framerate 30 ... (output de FFmpeg)

[15:39:15] ✓ Vídeo compilado com sucesso!
[15:39:15]   Arquivo: video_final.mp4
[15:39:15]   Tamanho: 145.3 MB

============================================================
✓ PIPELINE COMPLETA COM SUCESSO!
============================================================
Vídeo final: output/20240127_153000_.../video_final.mp4
Duração total: 525s (8.75 min)
============================================================
```

## 🎯 Exemplo 2: Executar Steps Individuais

### Situação
Você já tem um plano e script, mas quer regenerar as imagens com melhor qualidade.

```bash
source venv/bin/activate

# Diretório do projeto anterior
OUTPUT_DIR="output/20240127_153000_Como_funcionam_buracos_negros"

# Regenerar apenas as imagens (modo qualidade)
python scripts/05_generate_images.py --output $OUTPUT_DIR

# Depois recompor o vídeo com as novas imagens
python scripts/07_compose_video.py --project $OUTPUT_DIR
```

## 📝 Exemplo 3: Customizar Prompts

### Situação
Você quer gerar um vídeo mais artístico (menos realista).

#### Passo 1: Editar `config/prompts.yaml`

```yaml
prompts:
  image_prompt_optimizer:
    template: |
      Você é especialista em prompts para Stable Diffusion com foco em ART.

      Com base nesta descrição visual: "{visual_description}"

      Gere um prompt para ARTE DIGITAL/ILUSTRAÇÃO otimizado (NÃO fotografia):
      - Estilo artístico específico (oil painting, watercolor, digital art, vector)
      - Inspiração: Studio Ghibli, concept art, ilustração moderna
      - Cores vibrantes e composição interessante

      Retorne APENAS o prompt otimizado.
```

#### Passo 2: Executar

```bash
python scripts/04_image_prompts.py --output output/meu_video

# Isso vai regenerar os prompts com a nova template
# Depois gerar as imagens:
python scripts/05_generate_images.py --output output/meu_video --fast
```

## 🚀 Exemplo 4: Modo Rápido para Testes

### Situação
Você quer testar a pipeline rápido, sem esperar pelas imagens de alta qualidade.

```bash
source venv/bin/activate

# Executar com modo rápido (menos steps em imagens)
python orchestrator.py --topic "Teste rápido" --fast

# Tempo esperado: ~10-15 minutos (vs 20-30 normal)
```

### Resultado
- Imagens com menos detalhes (15 steps vs 25)
- Vídeo final menor
- Qualidade aceitável para preview

## 🎨 Exemplo 5: Tema Educativo Completo

### Situação
Criar vídeo sobre "Fotossíntese" para YouTube Shorts educativo.

```bash
python orchestrator.py --topic "Fotossíntese: como as plantas criam alimento"
```

### Outputs que você vai receber

**plan.json:**
```json
{
  "tema": "Fotossíntese: como as plantas criam alimento",
  "publico": "Estudantes 10+, curiosos por biologia",
  "tom": "Educativo, divertido, com analogias",
  "num_cenas": 5,
  "pontos_chave": [
    "Definição básica de fotossíntese",
    "Ingredientes: luz, água, CO2",
    "Processo passo a passo",
    "Importância para o planeta"
  ],
  "hook_inicial": "As plantas são como pequenas fábricas solares!"
}
```

**script.md (excerpt):**
```markdown
## CENA 1 (0-12s)
**Narração:** Você sabia que as plantas são como pequenas
fábricas solares? Elas usam luz para criar seu próprio alimento!

**Visual:** Animação de planta em luz solar brilhante

---

## CENA 2 (12-25s)
**Narração:** O processo se chama fotossíntese. Precisa de três
ingredientes: luz solar, água e dióxido de carbono do ar.

**Visual:** Diagrama mostrando 3 ingredientes com ícones
```

## 🎬 Exemplo 6: Integrar com n8n (Futuro)

### Webhook para automação

```bash
# Webhook trigger em n8n
curl -X POST http://localhost:5678/webhook/video-generator \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Inteligência Artificial em 2024",
    "quality": "balanced",
    "language": "pt_BR"
  }'

# n8n executaria:
# python orchestrator.py --topic "..." --fast
# E notificaria quando terminar
```

## 📊 Exemplo 7: Processar Lista de Temas

### Script para gerar múltiplos vídeos

```bash
#!/bin/bash
# batch_generator.sh

TOPICS=(
  "Como funcionam buracos negros"
  "Fotossíntese explicada"
  "Machine Learning para iniciantes"
  "História da Internet"
  "O que é blockchain"
)

source venv/bin/activate

for topic in "${TOPICS[@]}"; do
  echo "🎬 Gerando vídeo: $topic"
  python orchestrator.py --topic "$topic" --fast
  echo "✓ Concluído!\n"

  # Aguardar entre execuções (Ollama pode ficar sobrecarregado)
  sleep 60
done

echo "✓ Todos os vídeos foram gerados!"
echo "Saídas em: output/"
```

```bash
chmod +x batch_generator.sh
./batch_generator.sh
```

## 🔧 Exemplo 8: Solucionar Problemas Comuns

### Problema 1: Stable Diffusion não gera imagens

```bash
# Verificar se está rodando
curl http://127.0.0.1:7860/config

# Se erro:
cd ~/stable-diffusion-webui
./webui-user.sh

# Esperar por "Running on http://127.0.0.1:7860"
```

### Problema 2: Narração muito rápida/lenta

Editar `scripts/03_voice.py`:

```python
# Mudar modelo de voz:
# Mais lento/natural: "faber-large"
# Mais rápido: "faber-medium"

generate_voice(narration_text, audio_output,
               language="pt_BR",
               model="faber-large")  # Mais natural
```

### Problema 3: Timeout em geração de imagens

Aumentar timeout em `config/models.yaml`:

```yaml
timeouts:
  sd_generate: 900  # 15 minutos (aumentado de 10)
```

## 📈 Exemplo 9: Monitorar Performance

```bash
# Ver outputs gerados
make list-outputs

# Ver último log
tail -f output/*/pipeline.log

# Verificar tamanho de arquivos
du -sh output/*/

# Contar imagens geradas
ls output/*/images/ | wc -l
```

## 🎯 Exemplo 10: Customização Avançada

### Mudar resolução de imagens

Em `scripts/05_generate_images.py`:

```python
image_bytes = sd.generate_image(
    prompt=scene['prompt_otimizado'],
    width=2560,    # De 1920
    height=1440,   # De 1080
    steps=steps
)
```

### Mudar codec de vídeo

Em `scripts/07_compose_video.py`:

```python
cmd.extend([
    "-c:v", "libx265",  # HEVC (melhor compressão)
    "-preset", "medium",
    "-crf", str(crf),
])
```

### Adicionar efeitos audio

```python
# Em 03_voice.py, após gerar narração:
# ffmpeg -i narration.wav -af "volume=1.2" narration_boosted.wav
```

## 📚 Próximos Passos

1. Executar: `make full TOPIC="Seu tema aqui"`
2. Conferir output em `output/`
3. Customizar `config/prompts.yaml` conforme necessário
4. Compartilhar feedback!
