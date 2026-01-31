#!/usr/bin/env python3
"""
05_generate_images_lowmem.py - Versão otimizada para GPUs de 4GB
- Resolução: 512x512 
- Steps: 8
- Otimizações agressivas de memória
- Prompts truncados para 77 tokens
"""

import argparse
import sys
from pathlib import Path
import time
import gc

sys.path.insert(0, str(Path(__file__).parent))

from utils import FileManager, logger

try:
    import torch
    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
    import warnings
    warnings.filterwarnings("ignore")
    
    # Configurar fragmentação de memória
    import os
    os.environ['PYTORCH_ALLOC_CONF'] = 'expandable_segments:True'
    
    # Otimizar backends
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    
except ImportError as e:
    logger.error("Dependências não instaladas!")
    logger.error(f"Erro: {e}")
    sys.exit(1)


def truncate_prompt(prompt: str, max_tokens: int = 75) -> str:
    """Trunca prompt para evitar overflow do CLIP"""
    words = prompt.split()
    if len(words) <= max_tokens:
        return prompt
    
    truncated = " ".join(words[:max_tokens])
    logger.warning(f"⚠️  Prompt truncado: {len(words)} → {max_tokens} palavras")
    return truncated


def clear_memory():
    """Limpar memória agressivamente"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()


def generate_images_lowmem(prompts_file: str, output_dir: str):
    """Versão otimizada para GPU de 4GB"""

    logger.info("🔥 MODO LOW-MEMORY (512x512, 8 steps, otimizações agressivas)")
    
    files = FileManager(output_dir)
    
    # Verificar GPU
    if not torch.cuda.is_available():
        logger.error("❌ CUDA não disponível! Este script precisa de GPU.")
        return
        
    # Informações da GPU
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    logger.info(f"🖥️  GPU: {torch.cuda.get_device_name(0)} ({gpu_memory:.1f}GB)")
    
    clear_memory()
    
    device = "cuda"
    dtype = torch.float16
    
    start_time = time.time()
    logger.info("📥 Carregando modelo com otimizações extremas...")
    
    # Carregar modelo com configurações mínimas de memória
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
        variant="fp16"
    )
    
    # Scheduler mais eficiente
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    
    # Otimizações agressivas de memória
    pipe.enable_model_cpu_offload()  # Mais agressivo que attention_slicing
    pipe.enable_vae_slicing() 
    pipe.enable_vae_tiling()
    pipe.enable_attention_slicing(1)  # Slice máximo
    
    # Não mover para GPU ainda - deixar o cpu_offload gerenciar
    
    load_time = time.time() - start_time
    logger.info(f"✅ Modelo carregado em {load_time:.1f}s com otimizações extremas")
    
    # Carregar prompts
    try:
        prompts_data = files.load_json("image_prompts.json")
        total_scenes = len(prompts_data["cenas"])
    except Exception as e:
        logger.error(f"❌ Erro ao carregar prompts: {e}")
        return
    
    logger.info(f"📋 {total_scenes} cenas para gerar\n")
    
    # Gerar imagens
    total_start = time.time()
    
    for i, scene in enumerate(prompts_data["cenas"], 1):
        try:
            scene_start = time.time()
            logger.info(f"[{i}/{total_scenes}] Cena {scene['numero']}...")
            
            # Limpar memória antes de cada geração
            clear_memory()
            
            # Preparar prompt (truncar para evitar overflow)
            prompt = truncate_prompt(scene['prompt_otimizado'], max_tokens=75)
            negative_prompt = "low quality, blurry"
            
            # Monitorar memória
            if torch.cuda.is_available():
                memory_before = torch.cuda.memory_allocated() / 1024**3
                logger.info(f"  💾 Memória antes: {memory_before:.2f}GB")
            
            # Gerar com configurações mínimas
            with torch.no_grad():
                image = pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    height=512,              # Resolução mínima para qualidade aceitável
                    width=512,
                    num_inference_steps=8,   # Menos steps = menos memória
                    guidance_scale=7.5,      # Padrão
                    generator=torch.Generator(device).manual_seed(42),
                ).images[0]
            
            # Salvar imagem
            output_path = files.get_image_path(scene['numero'])
            image.save(output_path, "JPEG", quality=90, optimize=True)
            
            scene_time = time.time() - scene_start
            logger.info(f"  ✓ {output_path.name} ({scene_time:.1f}s)")
            
            # Limpar memória após cada geração
            clear_memory()
            
            if torch.cuda.is_available():
                memory_after = torch.cuda.memory_allocated() / 1024**3
                logger.info(f"  💾 Memória depois: {memory_after:.2f}GB")
                
        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"  ❌ CUDA Out of Memory na cena {scene['numero']}")
            logger.error("  💡 Tentando limpar memória e continuar...")
            
            # Limpeza agressiva
            clear_memory()
            
            try:
                # Tentar novamente com configurações ainda menores
                with torch.no_grad():
                    image = pipe(
                        prompt=truncate_prompt(scene['prompt_otimizado'], max_tokens=50),
                        height=384,              # Ainda menor
                        width=384,
                        num_inference_steps=6,   # Menos steps ainda
                        guidance_scale=6.0,      # Menor guidance
                    ).images[0]
                
                output_path = files.get_image_path(scene['numero'])
                image.save(output_path, "JPEG", quality=85)
                logger.info(f"  ✓ {output_path.name} (modo emergência 384x384)")
                
            except Exception as e2:
                logger.error(f"  ❌ Falha total na cena {scene['numero']}: {e2}")
                
        except Exception as e:
            logger.error(f"  ❌ Erro na cena {scene['numero']}: {e}")
    
    total_time = time.time() - total_start
    avg_time = total_time / total_scenes if total_scenes > 0 else 0
    
    logger.info(f"\n🎯 CONCLUÍDO!")
    logger.info(f"⏱️  Tempo total: {total_time:.1f}s")
    logger.info(f"📊 Média por imagem: {avg_time:.1f}s")
    logger.info(f"🖼️  Resolução: 512x512 (otimizado para GPU 4GB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador otimizado para GPU de 4GB")
    parser.add_argument("--output", default="output/default", help="Diretório de saída")
    parser.add_argument("--steps", type=int, default=8, help="Número de steps (padrão: 8)")
    parser.add_argument("--size", type=int, default=512, help="Tamanho da imagem (padrão: 512)")
    
    args = parser.parse_args()
    
    # Validar argumentos para GPU pequena
    if args.steps > 12:
        logger.warning("⚠️  Muitos steps para GPU 4GB. Usando máximo de 12.")
        args.steps = min(args.steps, 12)
    
    if args.size > 512:
        logger.warning("⚠️  Resolução alta demais para GPU 4GB. Usando 512x512.")
        args.size = 512
    
    generate_images_lowmem("image_prompts.json", args.output)