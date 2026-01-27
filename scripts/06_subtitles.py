#!/usr/bin/env python3
"""
06_subtitles.py - Geração de legendas (Etapa 6)

Input: script.md + timestamps.json
Output: subtitles.srt + subtitles.vtt
"""

import argparse
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import FileManager, ScriptParser, timestamp_to_srt_time, logger


def extract_scenes_with_timing(script_content: str) -> list[dict]:
    """Extrai cenas com timing do script"""

    scenes = []
    lines = script_content.split('\n')
    current_scene = None

    for line in lines:
        # Detectar cabeçalho de cena (## CENA X (Y-Zs))
        match = re.search(r'## CENA (\d+) \((\d+)-(\d+)s\)', line)
        if match:
            if current_scene:
                scenes.append(current_scene)

            current_scene = {
                "numero": int(match.group(1)),
                "start_seconds": int(match.group(2)),
                "end_seconds": int(match.group(3)),
                "naracao": ""
            }

        # Extrair narração
        if line.startswith('**Narração:**') and current_scene:
            current_scene["naracao"] = line.replace('**Narração:**', '').strip()

    if current_scene:
        scenes.append(current_scene)

    return scenes


def format_srt_time(seconds: float) -> str:
    """Converte segundos para formato SRT (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_vtt_time(seconds: float) -> str:
    """Converte segundos para formato VTT (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def split_text_into_lines(text: str, max_chars: int = 42) -> list[str]:
    """Divide texto em linhas para legendas (máx 42 chars por linha)"""

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def create_subtitles(script_path: str, output_dir: str):
    """Cria legendas em formato SRT e VTT"""

    logger.info("📝 Geração de legendas")

    files = FileManager(output_dir)

    try:
        # Carregar script
        script_content = files.load_text("script.md")

        # Extrair cenas com timing
        scenes = extract_scenes_with_timing(script_content)

        if not scenes:
            logger.error("Nenhuma cena encontrada!")
            raise ValueError("Script inválido")

        logger.info(f"📄 Processando {len(scenes)} cenas...")

        # Gerar SRT
        srt_content = ""
        vtt_content = "WEBVTT\n\n"

        for i, scene in enumerate(scenes, 1):
            # Dividir narração em linhas
            naracao = scene["naracao"]
            lines = split_text_into_lines(naracao)

            # Calcular timing para cada linha (dividir o tempo da cena)
            start_sec = scene["start_seconds"]
            end_sec = scene["end_seconds"]
            total_duration = end_sec - start_sec

            if len(lines) > 0:
                time_per_line = total_duration / len(lines)

                for j, line in enumerate(lines):
                    line_start = start_sec + (j * time_per_line)
                    line_end = start_sec + ((j + 1) * time_per_line)

                    # Formato SRT
                    srt_content += f"{i * 10 + j}\n"
                    srt_content += f"{format_srt_time(line_start)} --> {format_srt_time(line_end)}\n"
                    srt_content += f"{line}\n\n"

                    # Formato VTT
                    vtt_content += f"{format_vtt_time(line_start)} --> {format_vtt_time(line_end)}\n"
                    vtt_content += f"{line}\n\n"

        # Salvar arquivos
        files.save_text("subtitles.srt", srt_content)
        files.save_text("subtitles.vtt", vtt_content)

        logger.info(f"✓ Legendas criadas com sucesso!")
        logger.info(f"  SRT: subtitles.srt")
        logger.info(f"  VTT: subtitles.vtt")
        logger.info(f"  Total de linhas: {len(vtt_content.split(chr(10))) // 3}")

        return srt_content

    except Exception as e:
        logger.error(f"✗ Erro ao gerar legendas: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Etapa 6: Geração de legendas")
    parser.add_argument(
        "--voice",
        default="audio/narration.wav",
        help="Arquivo de áudio"
    )
    parser.add_argument(
        "--script",
        default="script.md",
        help="Arquivo de script"
    )
    parser.add_argument(
        "--output",
        default="output/default",
        help="Diretório de saída"
    )

    args = parser.parse_args()
    create_subtitles(args.script, args.output)


if __name__ == "__main__":
    main()
