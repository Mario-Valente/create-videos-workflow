#!/usr/bin/env python3
"""
orchestrator.py - Orquestrador central da pipeline

Executa todas as 7 etapas da geração de vídeos de forma sequencial
"""

import argparse
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class VideoOrchestrator:
    """Coordena toda a pipeline de geração de vídeos"""

    STEPS = [
        {
            "num": 1,
            "nome": "Planejamento",
            "script": "scripts/01_plan.py",
            "icon": "📋",
            "descricao": "Planejamento do conteúdo"
        },
        {
            "num": 2,
            "nome": "Roteiro",
            "script": "scripts/02_script.py",
            "icon": "📝",
            "descricao": "Criação do roteiro"
        },
        {
            "num": 3,
            "nome": "Narração",
            "script": "scripts/03_voice.py",
            "icon": "🎙️",
            "descricao": "Geração de narração (TTS)"
        },
        {
            "num": 4,
            "nome": "Prompts",
            "script": "scripts/04_image_prompts.py",
            "icon": "🎨",
            "descricao": "Geração de prompts para imagens"
        },
        {
            "num": 5,
            "nome": "Imagens",
            "script": "scripts/05_generate_images_lowmem.py",
            "icon": "🖼️",
            "descricao": "Geração de imagens (Stable Diffusion)"
        },
        {
            "num": 6,
            "nome": "Composição",
            "script": "scripts/07_compose_video.py",
            "icon": "🎬",
            "descricao": "Composição do vídeo final"
        }
    ]

    def __init__(self, topic: str, output_dir: str = None):
        self.topic = topic
        self.start_time = datetime.now()

        # Criar diretório de saída
        if output_dir is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = f"output/{timestamp}_{topic[:20].replace(' ', '_')}"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.output_dir / "pipeline.log"
        self.results = {
            "tema": topic,
            "inicio": self.start_time.isoformat(),
            "etapas": {}
        }

    def log(self, message: str):
        """Registra mensagem em log"""
        logger.info(message)
        with open(self.log_file, "a") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")

    def run_step(self, step: dict) -> bool:
        """Executa um step da pipeline"""

        step_num = step["num"]
        step_icon = step["icon"]
        step_nome = step["nome"]
        script_path = step["script"]

        self.log(f"\n{step_icon} ETAPA {step_num}/7: {step_nome}")
        self.log(f"{'=' * 50}")

        try:
            # Construir comando
            cmd = [
                "python3",
                script_path
            ]
            
            # Argumentos específicos por step
            if step_num == 7:  # Composição de vídeo usa --project
                cmd.extend(["--project", str(self.output_dir)])
            else:  # Outros steps usam --output
                cmd.extend(["--output", str(self.output_dir)])

            if step_num == 1:  # Planejamento
                cmd.extend(["--topic", self.topic])

            elif step_num == 5:  # Imagens - permitir modo rápido
                if hasattr(self, 'fast_mode') and self.fast_mode:
                    cmd.append("--fast")

            # Executar script
            logger.info(f"\n$ python3 {' '.join(cmd[1:])}\n")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hora por step
            )

            if result.returncode != 0:
                self.log(f"✗ Erro no step {step_num}: {result.stderr}")
                logger.error(result.stderr)
                return False

            # Registrar sucesso
            self.log(f"✓ Step {step_num} concluído com sucesso")
            self.results["etapas"][step_num] = {
                "nome": step_nome,
                "status": "sucesso",
                "timestamp": datetime.now().isoformat()
            }

            return True

        except subprocess.TimeoutExpired:
            self.log(f"✗ Timeout no step {step_num} (limite 1 hora)")
            return False
        except Exception as e:
            self.log(f"✗ Erro no step {step_num}: {e}")
            return False

    def execute_pipeline(self, skip_steps: list = None) -> bool:
        """Executa pipeline completa"""

        skip_steps = skip_steps or []

        logger.info("\n" + "=" * 60)
        logger.info(f"🎬 GERADOR DE VÍDEOS - PIPELINE COMPLETA")
        logger.info(f"{'=' * 60}")
        logger.info(f"Tema: {self.topic}")
        logger.info(f"Saída: {self.output_dir}")
        logger.info(f"Início: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60 + "\n")

        self.log(f"Tema: {self.topic}")
        self.log(f"Diretório: {self.output_dir}")

        # Executar steps
        for step in self.STEPS:
            step_num = step["num"]

            if step_num in skip_steps:
                logger.info(f"⏭️  Step {step_num} pulado")
                continue

            if not self.run_step(step):
                logger.error(f"\n❌ Pipeline interrompida no step {step_num}")
                self.log(f"Pipeline interrompida no step {step_num}")
                self.results["status"] = "erro"
                self.save_results()
                return False

        # Sucesso!
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        logger.info("\n" + "=" * 60)
        logger.info("✓ PIPELINE COMPLETA COM SUCESSO!")
        logger.info("=" * 60)
        logger.info(f"Vídeo final: {self.output_dir / 'video_final.mp4'}")
        logger.info(f"Duração total: {duration:.0f}s ({duration/60:.1f} min)")
        logger.info("=" * 60)

        self.log(f"\n✓ Pipeline concluída com sucesso!")
        self.log(f"Duração total: {duration:.0f}s")

        self.results["status"] = "sucesso"
        self.results["fim"] = end_time.isoformat()
        self.results["duracao_segundos"] = duration

        self.save_results()

        return True

    def save_results(self):
        """Salva resultados em JSON"""
        results_file = self.output_dir / "pipeline_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Orquestrador da pipeline de geração de vídeos"
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Tema/conceito do vídeo"
    )
    parser.add_argument(
        "--output",
        help="Diretório de saída (auto-gerado se não fornecido)"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Modo rápido (menos steps em geração de imagens)"
    )
    parser.add_argument(
        "--skip",
        nargs='+',
        type=int,
        default=[],
        help="Steps para pular (números 1-7)"
    )

    args = parser.parse_args()

    # Criar e executar orquestrador
    orchestrator = VideoOrchestrator(args.topic, args.output)
    orchestrator.fast_mode = args.fast

    success = orchestrator.execute_pipeline(skip_steps=args.skip)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
