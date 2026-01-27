#!/usr/bin/env python3
"""
04_image_prompts.py - Geração de prompts para imagens (Etapa 4)

Input: script.md
Output: image_prompts.json com prompts otimizados para Stable Diffusion
"""

import argparse
import sys
import re
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import OllamaClient, FileManager, ScriptParser, logger


PROMPT_OPTIMIZER = """Você é especialista em prompts para Stable Diffusion.

Com base nesta descrição visual: "{visual_description}"

Contexto: {context}

Gere um prompt otimizado para geração de imagem 4K seguindo estas diretrizes:
- Estilo visual específico e detalhado
- Qualidade e iluminação (cinematic, professional)
- Proporciona correta (16:9 para vídeo)
- Evite termos vagos e use palavras-chave específicas
- Evite negar coisas (no, not, without) - use apenas descrições positivas

Retorne APENAS o prompt otimizado, sem explicações ou aspas."""


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
    """Gera prompts otimizados para cada cena"""

    logger.info("🎨 Geração de prompts para imagens")

    files = FileManager(output_dir)
    ollama = OllamaClient()

    try:
        # Carregar script e plano
        script_content = files.load_text("script.md")
        plan = files.load_json("plan.json")

        # Extrair visuals
        logger.info("📄 Extraindo descrições visuais...")
        scenes_visuals = extract_visuals_from_script(script_content)

        if not scenes_visuals:
            logger.error("Nenhuma cena encontrada no script!")
            raise ValueError("Script inválido")

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
                "duracao": int(scene['timing'].split('-')[1].replace('s', ''))
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
