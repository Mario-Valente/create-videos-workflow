#!/usr/bin/env python3
"""
04_image_prompts.py - Geração de prompts para imagens (Etapa 4)

Input: script.md + narration.wav
Output: image_prompts.json com prompts otimizados (quantidade baseada na duração do áudio)
"""

import argparse
import sys
import re
import json
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import OllamaClient, FileManager, ScriptParser, logger


PROMPT_OPTIMIZER = """Você é especialista em prompts para Stable Diffusion.

Com base nesta descrição visual: "{visual_description}"

Contexto: {context}

Gere um prompt otimizado para geração de imagem 4K seguindo estas diretrizes:
- Estilo visual específico e detalhado
- Qualidade e iluminação (cinematic, professional)
- Proporção correta (16:9 para vídeo)
- Evite termos vagos e use palavras-chave específicas
- Evite negar coisas (no, not, without) - use apenas descrições positivas

Retorne APENAS o prompt otimizado, sem explicações ou aspas."""


def get_audio_duration(audio_file: Path) -> float:
    """Obtém duração do áudio em segundos"""
    try:
        result = subprocess.run([
            "ffprobe", "-i", str(audio_file), 
            "-show_entries", "format=duration", 
            "-v", "quiet", "-of", "csv=p=0"
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Erro ao obter duração do áudio: {e}")
        return 60.0  # fallback para 1 minuto


def calculate_optimal_scenes(audio_duration: float) -> int:
    """Calcula quantidade ideal de cenas baseado na duração"""
    # 1 imagem a cada 12-15 segundos
    if audio_duration <= 30:
        return 2  # Mínimo 2 imagens
    elif audio_duration <= 60:
        return max(3, int(audio_duration / 15))
    elif audio_duration <= 120:
        return max(5, int(audio_duration / 12))
    else:
        return max(8, int(audio_duration / 10))  # Máximo detalhamento para vídeos longos


def redistribute_scenes(original_scenes: list, target_count: int, audio_duration: float) -> list:
    """Redistribui cenas para atingir quantidade ideal"""
    if len(original_scenes) == target_count:
        return original_scenes
    
    time_per_scene = audio_duration / target_count
    new_scenes = []
    
    for i in range(target_count):
        start_time = int(i * time_per_scene)
        end_time = int((i + 1) * time_per_scene)
        
        # Pegar cena original mais próxima como base
        base_idx = min(i, len(original_scenes) - 1)
        base_scene = original_scenes[base_idx]
        
        new_scene = {
            "numero": i + 1,
            "timing": f"{start_time}-{end_time}s",
            "naracao": base_scene.get("naracao", ""),
            "visual": base_scene.get("visual", ""),
            "duracao": int(time_per_scene)
        }
        new_scenes.append(new_scene)
    
    return new_scenes


def extract_visuals_from_script(script_content: str) -> list[dict]:
    """Extrai descrições visuais do script"""

    visuals = []
    lines = script_content.split('\n')

    current_scene = None

    for line in lines:
        # Detectar cabeçalho de cena
        match = re.search(r'## CENA (\d+) \((\d+)-(\d+)s\)', line)
        if match:
            current_scene = {
                "numero": int(match.group(1)),
                "timing": f"{match.group(2)}-{match.group(3)}s",
                "naracao": "",
                "visual": ""
            }
            visuals.append(current_scene)

        # Extrair narração
        if line.startswith('**Narração:**') and current_scene:
            current_scene["naracao"] = line.replace('**Narração:**', '').strip()

        # Extrair visual
        if line.startswith('**Visual:**') and current_scene:
            current_scene["visual"] = line.replace('**Visual:**', '').strip()

    return visuals


def generate_image_prompts(script_path: str, output_dir: str):
    """Gera prompts otimizados para cada cena baseado na duração do áudio"""

    logger.info("🎨 Geração de prompts para imagens")

    files = FileManager(output_dir)
    ollama = OllamaClient()

    try:
        # Verificar se áudio existe
        audio_file = files.output_dir / "audio" / "narration.wav"
        if not audio_file.exists():
            logger.error(f"Áudio não encontrado: {audio_file}")
            raise FileNotFoundError("Execute primeiro o step de narração!")

        # Obter duração do áudio
        audio_duration = get_audio_duration(audio_file)
        optimal_scenes = calculate_optimal_scenes(audio_duration)
        
        logger.info(f"🎬 Duração do áudio: {audio_duration:.1f}s")
        logger.info(f"📊 Cenas ideais: {optimal_scenes}")

        # Carregar script e plano
        script_content = files.load_text("script.md")
        plan = files.load_json("plan.json")

        # Extrair visuals originais
        logger.info("📄 Extraindo descrições visuais...")
        original_scenes = extract_visuals_from_script(script_content)

        if not original_scenes:
            logger.error("Nenhuma cena encontrada no script!")
            raise ValueError("Script inválido")

        # Redistribuir cenas baseado na duração
        scenes_visuals = redistribute_scenes(original_scenes, optimal_scenes, audio_duration)
        logger.info(f"🔄 Redistribuído: {len(original_scenes)} → {len(scenes_visuals)} cenas")

        # Gerar prompts otimizados
        logger.info("⏳ Otimizando prompts com Ollama...")

        optimized_prompts = []

        for scene in scenes_visuals:
            logger.info(f"  Cena {scene['numero']}/{len(scenes_visuals)}...")

            context = f"Tema: {plan['tema']}, Tom: {plan['tom']}"

            prompt = PROMPT_OPTIMIZER.format(
                visual_description=scene['visual'],
                context=context
            )

            optimized = ollama.generate(prompt, model="mistral", temperature=0.5)

            optimized_prompts.append({
                "numero": scene['numero'],
                "timing": scene['timing'],
                "visual_original": scene['visual'],
                "prompt_otimizado": optimized,
                "duracao": scene.get('duracao', int(scene['timing'].split('-')[1].replace('s', '')))
            })

        # Estrutura final
        image_prompts_data = {
            "tema": plan['tema'],
            "total_scenes": len(optimized_prompts),
            "cenas": optimized_prompts
        }

        # Salvar prompts
        files.save_json("image_prompts.json", image_prompts_data)

        logger.info(f"✓ Prompts gerados com sucesso!")
        logger.info(f"  Cenas: {len(optimized_prompts)}")

        # Exibir exemplo
        if optimized_prompts:
            logger.info(f"\n  Exemplo (Cena 1):")
            logger.info(f"  {optimized_prompts[0]['prompt_otimizado'][:80]}...")

        return image_prompts_data

    except Exception as e:
        logger.error(f"✗ Erro ao gerar prompts: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Etapa 4: Geração de prompts para imagens"
    )
    parser.add_argument(
        "--input",
        default="script.md",
        help="Arquivo de script"
    )
    parser.add_argument(
        "--output",
        default="output/default",
        help="Diretório de saída"
    )

    args = parser.parse_args()
    generate_image_prompts(args.input, args.output)


if __name__ == "__main__":
    main()
