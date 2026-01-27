#!/usr/bin/env python3
"""
01_plan.py - Planejamento do conteúdo (Etapa 1)

Input: Tema/conceito fornecido pelo usuário
Output: plan.json com estrutura do vídeo
"""

import argparse
import sys
from pathlib import Path

# Adiciona diretório de scripts ao path
sys.path.insert(0, str(Path(__file__).parent))

from utils import OllamaClient, FileManager, ConfigManager, logger


PLAN_PROMPT = """Você é um especialista em criação de conteúdo para YouTube Shorts.

Tema: {topic}

Estruture um plano para vídeo curto (60 segundos) com as seguintes informações em JSON:

{{"
  "tema": "string - o tema do vídeo",
  "publico": "string - descrição do público-alvo",
  "tom": "string - tom de voz (educativo, divertido, inspirador, etc)",
  "duracao_segundos": 60,
  "pontos_chave": ["ponto 1", "ponto 2", "ponto 3", "ponto 4"],
  "num_cenas": 5,
  "hook_inicial": "string - primeira frase impactante (máx 15 palavras)",
  "call_to_action": "string - última frase com CTA"
}}

Seja direto. Retorne APENAS JSON válido, sem explicações."""


def create_plan(topic: str, output_dir: str):
    """Cria plano do vídeo usando Ollama"""

    logger.info(f"📋 Planejamento: {topic}")

    # Inicializar clients
    ollama = OllamaClient()
    files = FileManager(output_dir)

    try:
        # Gerar plano com Ollama
        prompt = PLAN_PROMPT.format(topic=topic)
        logger.info("⏳ Gerando plano com Ollama...")

        plan = ollama.generate_json(prompt, model="mistral")

        # Validar estrutura básica
        required_fields = ["tema", "publico", "tom", "pontos_chave"]
        for field in required_fields:
            if field not in plan:
                logger.error(f"Campo obrigatório faltando: {field}")
                raise ValueError(f"Resposta inválida do Ollama: falta {field}")

        # Salvar plano
        files.save_json("plan.json", plan)

        # Exibir resumo
        logger.info(f"✓ Plano criado com sucesso!")
        logger.info(f"  Tema: {plan['tema']}")
        logger.info(f"  Público: {plan['publico']}")
        logger.info(f"  Tom: {plan['tom']}")
        logger.info(f"  Cenas: {plan.get('num_cenas', 5)}")
        logger.info(f"  Hook: {plan.get('hook_inicial', 'N/A')}")

        return plan

    except Exception as e:
        logger.error(f"✗ Erro ao criar plano: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Etapa 1: Planejamento do conteúdo"
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Tema/conceito do vídeo"
    )
    parser.add_argument(
        "--output",
        default="output/default",
        help="Diretório de saída"
    )

    args = parser.parse_args()

    create_plan(args.topic, args.output)


if __name__ == "__main__":
    main()
