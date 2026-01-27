#!/usr/bin/env python3
"""
02_script.py - Criação do roteiro (Etapa 2)

Input: plan.json
Output: script.md com cenas, narração e timing
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import OllamaClient, FileManager, logger


SCRIPT_PROMPT = """Você é um roteirista especializado em conteúdo educativo para redes sociais.

Plano do vídeo:
Tema: {tema}
Público: {publico}
Tom: {tom}
Duração: 60 segundos
Pontos-chave: {pontos_chave}
Número de cenas: {num_cenas}

Crie um roteiro em Markdown com esta estrutura:
- Divisão em {num_cenas} cenas
- Cada cena com narração (máx 30 palavras)
- Descrição visual clara e visual (1 linha)
- Timing em segundos (0-10s, 10-25s, etc)

Use este formato para cada cena:

## CENA 1 (0-10s)
**Narração:** Sua narração aqui

**Visual:** Descrição visual concisa

---

## CENA 2 (10-25s)
...

Seja direto. Mantenha o tom especificado. Maximize o impacto visual."""


def create_script(plan_file: str, output_dir: str):
    """Cria script do vídeo baseado no plano"""

    logger.info("📝 Geração de roteiro")

    files = FileManager(output_dir)
    ollama = OllamaClient()

    try:
        # Carregar plano
        plan = files.load_json("plan.json")

        # Gerar script com Ollama
        prompt = SCRIPT_PROMPT.format(
            tema=plan["tema"],
            publico=plan["publico"],
            tom=plan["tom"],
            pontos_chave=", ".join(plan["pontos_chave"]),
            num_cenas=plan.get("num_cenas", 5)
        )

        logger.info("⏳ Gerando script com Ollama...")
        script = ollama.generate(prompt, model="mistral")

        # Salvar script
        files.save_text("script.md", script)

        # Contar cenas
        num_scenes = script.count("## CENA")
        logger.info(f"✓ Script criado com sucesso!")
        logger.info(f"  Cenas geradas: {num_scenes}")

        return script

    except Exception as e:
        logger.error(f"✗ Erro ao criar script: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Etapa 2: Criação do roteiro")
    parser.add_argument(
        "--input",
        default="plan.json",
        help="Arquivo de plano (dentro do output dir)"
    )
    parser.add_argument(
        "--output",
        default="output/default",
        help="Diretório de saída"
    )

    args = parser.parse_args()
    create_script(args.input, args.output)


if __name__ == "__main__":
    main()
