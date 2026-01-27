#!/usr/bin/env python3
"""
05_generate_images.py - Geração de imagens (Etapa 5)

Input: image_prompts.json
Output: PNG images (scene_001.png, scene_002.png, etc)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import FileManager, logger


class StableDiffusionGenerator:
    """Integração com Stable Diffusion via diffusers (local)"""

    def __init__(self, device: str = "cpu"):
        self.device = device
        self.pipe = None

    def _init_pipeline(self):
        """Inicializa pipeline Stable Diffusion (lazy load)"""
        if self.pipe is not None:
            return

        try:
            from diffusers import StableDiffusionPipeline
            import torch

            logger.info("⏳ Carregando modelo Stable Diffusion...")
            logger.info("   (primeira vez leva alguns minutos)")

            model_id = "runwayml/stable-diffusion-v1-5"

            # Detectar device melhor
            if torch.cuda.is_available():
                self.device = "cuda"
                dtype = torch.float16
                logger.info("   GPU detectada (CUDA)")
            else:
                self.device = "cpu"
                dtype = torch.float32
                logger.info("   Usando CPU")

            self.pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=dtype
            )
            self.pipe = self.pipe.to(self.device)

            logger.info("✓ Modelo carregado")

        except ImportError:
            logger.error("Dependências não instaladas!")
            logger.error("Execute: pip install diffusers transformers torch accelerate")
            raise
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            raise

    def check_connection(self) -> bool:
        """Verifica se é possível gerar imagens"""
        try:
            self._init_pipeline()
            return True
        except Exception:
            return False

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "low quality, blurry, distorted",
        steps: int = 25,
        width: int = 1920,
        height: int = 1080,
        guidance_scale: float = 7.5,
        sampler: str = None  # Não usado em diffusers
    ) -> bytes:
        """Gera imagem usando Stable Diffusion via diffusers"""

        try:
            self._init_pipeline()

            logger.info(f"  ⏳ Gerando imagem (steps={steps}, {width}x{height})...")

            # Gerar imagem
            with torch.no_grad():
                image = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    height=height,
                    width=width,
                    num_inference_steps=steps,
                    guidance_scale=guidance_scale,
                ).images[0]

            # Converter para bytes
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            return img_byte_arr.getvalue()

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
        # Inicializar Stable Diffusion
        sd = StableDiffusionGenerator()

        logger.info("✓ Stable Diffusion pronto")

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
