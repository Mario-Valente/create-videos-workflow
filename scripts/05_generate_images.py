#!/usr/bin/env python3
"""
05_generate_images.py - Geração de imagens (Etapa 5)

Input: image_prompts.json
Output: PNG images (scene_001.png, scene_002.png, etc)
"""

import argparse
import sys
import json
import base64
import requests
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

from utils import FileManager, logger


class StableDiffusionGenerator:
    """Integração com Stable Diffusion local"""

    def __init__(self, api_url: str = "http://127.0.0.1:7860"):
        self.api_url = api_url
        self.txt2img_endpoint = f"{api_url}/api/v1/txt2img"

    def check_connection(self) -> bool:
        """Verifica se Stable Diffusion está rodando"""
        try:
            response = requests.get(f"{self.api_url}/config", timeout=5)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "low quality, blurry, distorted",
        steps: int = 25,
        width: int = 1920,
        height: int = 1080,
        guidance_scale: float = 7.5,
        sampler: str = "DPM++ 2M Karras"
    ) -> bytes:
        """Gera imagem usando Stable Diffusion WebUI"""

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "width": width,
            "height": height,
            "cfg_scale": guidance_scale,
            "sampler_name": sampler,
            "seed": -1,
            "n_iter": 1,
            "batch_size": 1,
        }

        try:
            logger.info(f"  ⏳ Gerando imagem (steps={steps}, {width}x{height})...")

            response = requests.post(
                self.txt2img_endpoint,
                json=payload,
                timeout=600  # 10 minutos de timeout
            )

            response.raise_for_status()

            result = response.json()

            if "images" not in result or not result["images"]:
                logger.error("Nenhuma imagem na resposta")
                raise ValueError("Resposta vazia do Stable Diffusion")

            # Decodificar primeira imagem
            img_data = base64.b64decode(result["images"][0])

            return img_data

        except requests.exceptions.Timeout:
            logger.error("Timeout ao gerar imagem (limite 10min)")
            raise
        except requests.exceptions.ConnectionError:
            logger.error("Stable Diffusion não está rodando!")
            logger.error("Execute: ./webui-user.sh (na pasta da WebUI)")
            raise
        except Exception as e:
            logger.error(f"Erro ao gerar imagem: {e}")
            raise


def generate_images(prompts_file: str, output_dir: str, fast_mode: bool = False):
    """Gera todas as imagens baseado nos prompts"""

    logger.info("🖼️  Geração de imagens")

    files = FileManager(output_dir)

    # Configurações por modo
    if fast_mode:
        steps = 15
        logger.info("⚡ Modo rápido (steps=15)")
    else:
        steps = 25
        logger.info("🎨 Modo qualidade (steps=25)")

    try:
        # Conectar ao Stable Diffusion
        sd = StableDiffusionGenerator()

        if not sd.check_connection():
            logger.error("❌ Stable Diffusion WebUI não está rodando!")
            logger.info("\nPara iniciar Stable Diffusion no Mac:")
            logger.info("  cd ~/stable-diffusion-webui")
            logger.info("  ./webui-user.sh")
            logger.info("\nEsperando por http://127.0.0.1:7860")
            raise RuntimeError("Stable Diffusion não acessível")

        logger.info("✓ Conectado ao Stable Diffusion")

        # Carregar prompts
        prompts_data = files.load_json("image_prompts.json")

        total_scenes = len(prompts_data["cenas"])
        logger.info(f"📋 {total_scenes} cenas para gerar\n")

        # Gerar imagem para cada cena
        for i, scene in enumerate(prompts_data["cenas"], 1):
            try:
                logger.info(f"[{i}/{total_scenes}] Cena {scene['numero']}:")
                logger.info(f"  Prompt: {scene['prompt_otimizado'][:60]}...")

                # Gerar imagem
                image_bytes = sd.generate_image(
                    prompt=scene['prompt_otimizado'],
                    steps=steps
                )

                # Salvar imagem
                output_path = files.get_image_path(scene['numero'])

                with open(output_path, 'wb') as f:
                    f.write(image_bytes)

                logger.info(f"  ✓ Salvo: {output_path.name}")

            except Exception as e:
                logger.error(f"  ✗ Erro na cena {scene['numero']}: {e}")
                logger.info("  (Continuando com próxima cena...)\n")
                continue

        logger.info(f"\n✓ Geração de imagens concluída!")
        logger.info(f"  Pasta: {files.dirs['images']}")

    except Exception as e:
        logger.error(f"✗ Erro fatal: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Etapa 5: Geração de imagens com Stable Diffusion"
    )
    parser.add_argument(
        "--input",
        default="image_prompts.json",
        help="Arquivo de prompts"
    )
    parser.add_argument(
        "--output",
        default="output/default",
        help="Diretório de saída"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Modo rápido (menos steps, menos qualidade)"
    )

    args = parser.parse_args()
    generate_images(args.input, args.output, fast_mode=args.fast)


if __name__ == "__main__":
    main()
