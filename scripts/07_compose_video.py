#!/usr/bin/env python3
"""
07_compose_video.py - Composição do vídeo final (Etapa 6)

Input: Images (scene_*.png) + Audio (narration.wav)  
Output: video_final.mp4
"""

import argparse
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import FileManager, VideoComposer, logger


def check_ffmpeg():
    """Verifica se FFmpeg está instalado"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def compose_video(project_dir: str, fps: int = 30, crf: int = 18, quality: str = "high"):
    """Compõe vídeo final com FFmpeg"""

    logger.info("🎬 Composição do vídeo final")

    files = FileManager(project_dir)

    # Configurar quality
    if quality == "fast":
        crf = 23  # Mais rápido, maior arquivo
        logger.info("⚡ Modo rápido")
    elif quality == "balanced":
        crf = 20
        logger.info("⚖️  Modo equilibrado")
    else:
        crf = 18
        logger.info("🎨 Modo alta qualidade")

    try:
        # Verificar FFmpeg
        if not check_ffmpeg():
            logger.error("❌ FFmpeg não encontrado!")
            logger.error("Execute: brew install ffmpeg")
            raise RuntimeError("FFmpeg não disponível")

        # Verificar arquivos necessários
        images_dir = files.dirs["images"]
        audio_file = files.get_audio_path()
        subtitle_file = files.output_dir / "subtitles.srt"

        if not images_dir.exists() or not list(images_dir.glob("scene_*.png")):
            logger.error("❌ Nenhuma imagem encontrada!")
            raise FileNotFoundError(f"Imagens não encontradas em {images_dir}")

        if not audio_file.exists():
            logger.error("❌ Arquivo de áudio não encontrado!")
            raise FileNotFoundError(f"Áudio não encontrado: {audio_file}")

        if not subtitle_file.exists():
            logger.warning("⚠️  Legendas não encontradas (prosseguindo sem)")
            subtitle_file = None

        # Verificar e corrigir formato das imagens
        first_image = images_dir / "scene_001.png"
        if first_image.exists():
            # Detectar se imagens são JPEG com extensão PNG
            result = subprocess.run(["file", str(first_image)], capture_output=True, text=True)
            if "JPEG" in result.stdout:
                logger.warning("⚠️  Imagens são JPEG com extensão .png, convertendo...")
                # Converter todas as imagens
                for img_file in images_dir.glob("scene_*.png"):
                    temp_jpg = img_file.with_suffix(".temp.jpg")
                    subprocess.run(["mv", str(img_file), str(temp_jpg)], check=True)
                    subprocess.run(["ffmpeg", "-y", "-i", str(temp_jpg), str(img_file)], 
                                 capture_output=True, check=True)
                    temp_jpg.unlink()
                logger.info("✅ Imagens convertidas para PNG")

        # Contar imagens
        num_images = len(list(images_dir.glob("scene_*.png")))
        logger.info(f"📋 {num_images} imagens encontradas")

        # Obter duração do áudio
        result = subprocess.run([
            "ffprobe", "-i", str(audio_file), 
            "-show_entries", "format=duration", 
            "-v", "quiet", "-of", "csv=p=0"
        ], capture_output=True, text=True, check=True)
        audio_duration = float(result.stdout.strip())
        
        # Calcular duração ideal por imagem (10-15 segundos cada)
        ideal_duration_per_image = 12.0  # segundos
        ideal_num_images = max(1, int(audio_duration / ideal_duration_per_image))
        
        logger.info(f"🎬 Duração total: {audio_duration:.1f}s")
        logger.info(f"📸 {num_images} imagens disponíveis")
        logger.info(f"🎯 Ideal: {ideal_num_images} imagens ({ideal_duration_per_image}s cada)")
        
        # Usar as imagens disponíveis, repetindo se necessário
        if num_images < ideal_num_images:
            duration_per_image = audio_duration / num_images
            logger.info(f"⚡ Usando {num_images} imagens ({duration_per_image:.1f}s cada)")
        else:
            duration_per_image = ideal_duration_per_image
            logger.info(f"✨ Usando {ideal_num_images} primeiras imagens")

        # Construir comando FFmpeg
        image_pattern = str(images_dir / "scene_%03d.png")
        output_file = str(files.output_dir / "video_final.mp4")

        logger.info(f"⏳ Compilando vídeo (fps={fps}, crf={crf})...")
        logger.info("(Este processo pode levar alguns minutos)\n")

        # Usar todas as imagens em loop para cobrir toda a duração do áudio
        cmd = [
            "ffmpeg",
            "-stream_loop", "-1",  # Loop infinito das imagens
            "-r", f"{num_images/audio_duration}",  # Taxa para que as 5 imagens cubram todo o áudio
            "-i", image_pattern,
            "-i", str(audio_file),
            "-vf", f"scale=1280:720:flags=lanczos",  # Apenas escalar para HD
            "-c:v", "libopenh264",  # Encoder
            "-crf", str(crf),
            "-c:a", "aac", 
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-t", str(audio_duration),  # Duração exata do áudio
            "-y",  # Sobrescrever
            output_file
        ]

        # Executar FFmpeg
        logger.info(f"$ {' '.join(cmd[:8])}... (continuado)")
        logger.info("")

        result = subprocess.run(cmd, capture_output=False, timeout=3600)

        if result.returncode != 0:
            logger.error("❌ FFmpeg falhou!")
            raise RuntimeError("Erro ao compilar vídeo com FFmpeg")

        # Verificar output
        if not Path(output_file).exists():
            logger.error("❌ Arquivo de saída não foi criado!")
            raise FileNotFoundError("Vídeo não foi gerado")

        # Obter tamanho do arquivo
        file_size_mb = Path(output_file).stat().st_size / (1024 * 1024)

        logger.info(f"\n✓ Vídeo compilado com sucesso!")
        logger.info(f"  Arquivo: {Path(output_file).name}")
        logger.info(f"  Tamanho: {file_size_mb:.1f} MB")
        logger.info(f"  Localização: {files.output_dir}")

        return output_file

    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout ao gerar vídeo (limite 1 hora)")
        raise
    except Exception as e:
        logger.error(f"✗ Erro ao compor vídeo: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Etapa 7: Composição do vídeo final"
    )
    parser.add_argument(
        "--project",
        default="output/default",
        help="Diretório do projeto"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Frames por segundo (30 ou 60)"
    )
    parser.add_argument(
        "--quality",
        choices=["fast", "balanced", "high"],
        default="high",
        help="Qualidade da compressão"
    )

    args = parser.parse_args()
    compose_video(args.project, fps=args.fps, quality=args.quality)


if __name__ == "__main__":
    main()
