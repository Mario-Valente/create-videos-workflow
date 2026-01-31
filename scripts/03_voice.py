#!/usr/bin/env python3
"""
03_voice.py - Criação de narração (Etapa 3)

Input: script.md
Output: narration.wav + timestamps.json
"""

import argparse
import sys
import os
import re
import subprocess
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import FileManager, ScriptParser, TimestampExtractor, logger


def extract_narration_text(script_content: str) -> str:
    """Extrai apenas o texto de narração do script"""

    lines = script_content.split('\n')
    narration_lines = []

    for line in lines:
        if line.startswith('**Narração:**'):
            text = line.replace('**Narração:**', '').strip()
            narration_lines.append(text)

    return ' '.join(narration_lines)


def generate_voice(narration_text: str, output_file: str, language: str = "pt_BR", model: str = "faber-medium"):
    """Gera áudio usando Piper TTS"""

    # Tentar encontrar o executável piper
    piper_cmd = None
    possible_paths = [
        "piper",  # Se estiver no PATH
        "/home/valente/.local/bin/piper",  # Instalação local
        "/usr/local/bin/piper",  # Instalação global
        "/usr/bin/piper"  # Instalação do sistema
    ]
    
    for piper_path in possible_paths:
        try:
            result = subprocess.run(
                [piper_path, "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                piper_cmd = piper_path
                logger.info(f"Piper encontrado em: {piper_path}")
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    if not piper_cmd:
        logger.error("Piper TTS não foi encontrado!")
        logger.error("Execute: pip install piper-tts")
        logger.error("E certifique-se de que ~/.local/bin está no PATH")
        raise RuntimeError("Piper TTS não encontrado")

    try:
        # Criar arquivo temporário com o texto
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp.write(narration_text)
            tmp_path = tmp.name

        try:
            # Executar Piper
            logger.info(f"⏳ Gerando áudio com Piper ({language}-{model})...")
            
            # Caminho completo para o modelo
            model_path = os.path.expanduser(f"~/.local/share/piper/{language}-{model}.onnx")
            
            if not os.path.exists(model_path):
                logger.error(f"Modelo não encontrado: {model_path}")
                logger.error("Execute o setup para baixar os modelos de voz")
                raise RuntimeError(f"Modelo {language}-{model} não encontrado")

            cmd = [
                piper_cmd,
                "--model", model_path,
                "--input_file", tmp_path,
                "--output_file", output_file,
                "--speaker", "0"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.error(f"Erro do Piper: {result.stderr}")
                raise RuntimeError(f"Piper falhou: {result.stderr}")

            logger.info(f"✓ Áudio gerado: {output_file}")

        finally:
            # Limpar arquivo temporário
            Path(tmp_path).unlink(missing_ok=True)

    except subprocess.TimeoutExpired:
        logger.error("Timeout ao gerar áudio (limite de 5 minutos)")
        raise
    except Exception as e:
        logger.error(f"✗ Erro ao gerar voz: {e}")
        raise


def extract_scene_timing(script_content: str) -> list[dict]:
    """Extrai timing de cada cena do script"""

    scenes_data = []
    lines = script_content.split('\n')

    current_scene = None

    for line in lines:
        # Detectar cabeçalho de cena (## CENA X (Y-Zs))
        match = re.search(r'## CENA (\d+) \((\d+)-(\d+)s\)', line)
        if match:
            current_scene = {
                "numero": int(match.group(1)),
                "start": int(match.group(2)),
                "end": int(match.group(3)),
                "naracao": ""
            }
            scenes_data.append(current_scene)

        # Extrair narração
        if line.startswith('**Narração:**') and current_scene:
            current_scene["naracao"] = line.replace('**Narração:**', '').strip()

    return scenes_data


def create_voice(script_path: str, output_dir: str, language: str = "pt_BR"):
    """Cria narração baseada no script"""

    logger.info("🎙️  Geração de narração")

    files = FileManager(output_dir)

    try:
        # Carregar script
        script_content = files.load_text("script.md")

        # Extrair texto de narração
        logger.info("📄 Extraindo narração...")
        narration_text = extract_narration_text(script_content)

        if not narration_text.strip():
            logger.error("Nenhum texto de narração encontrado no script!")
            raise ValueError("Script não contém narração")

        # Gerar áudio
        audio_output = str(files.get_audio_path())
        generate_voice(narration_text, audio_output, language=language)

        # Extrair timing de cenas
        scenes_timing = extract_scene_timing(script_content)

        # Extrair informações de áudio
        audio_info = TimestampExtractor.extract_from_audio(audio_output)

        # Criar estrutura de timestamps
        timestamps_data = {
            "narration_file": "audio/narration.wav",
            "total_duration": audio_info.get("duration_seconds", 0),
            "scenes": scenes_timing,
            "text": narration_text[:100] + "..." if len(narration_text) > 100 else narration_text
        }

        # Salvar timestamps
        files.save_json("timestamps.json", timestamps_data)

        logger.info(f"✓ Narração criada com sucesso!")
        logger.info(f"  Duração: {audio_info.get('duration_seconds', 0):.1f}s")
        logger.info(f"  Cenas: {len(scenes_timing)}")

        return audio_output

    except Exception as e:
        logger.error(f"✗ Erro ao criar narração: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Etapa 3: Criação de narração")
    parser.add_argument(
        "--input",
        default="script.md",
        help="Arquivo de script (dentro do output dir)"
    )
    parser.add_argument(
        "--output",
        default="output/default",
        help="Diretório de saída"
    )
    parser.add_argument(
        "--language",
        default="pt_BR",
        help="Código de idioma para Piper (pt_BR, en_US, es_ES, etc)"
    )

    args = parser.parse_args()
    create_voice(args.input, args.output, args.language)


if __name__ == "__main__":
    main()
