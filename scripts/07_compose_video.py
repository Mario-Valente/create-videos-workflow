#!/usr/bin/env python3
"""
07_compose_video.py - Composição do vídeo final (Etapa 7)

Input: Images (scene_*.png) + Audio (narration.wav) + Subtitles (subtitles.srt)
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

        # Contar imagens
        num_images = len(list(images_dir.glob("scene_*.png")))
        logger.info(f"📋 {num_images} imagens encontradas")

        # Construir comando FFmpeg
        image_pattern = str(images_dir / "scene_%03d.png")
        output_file = str(files.output_dir / "video_final.mp4")

        logger.info(f"⏳ Compilando vídeo (fps={fps}, crf={crf})...")
        logger.info("(Este processo pode levar alguns minutos)\n")

        cmd = [
            "ffmpeg",
            "-framerate", str(fps),
            "-i", image_pattern,
            "-i", str(audio_file),
        ]

        # Adicionar legendas se existem
        if subtitle_file and subtitle_file.exists():
            cmd.extend(["-vf", f"subtitles={subtitle_file}"])

        # Finalizar comando
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", str(crf),
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",  # Usa duração mínima (áudio normalmente)
            "-y",  # Sobrescrever arquivo
            output_file
        ])

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
