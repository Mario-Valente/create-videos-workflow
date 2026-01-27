"""
utils.py - Funções compartilhadas da pipeline de vídeos
"""

import json
import os
import sys
import requests
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class OllamaClient:
    """Cliente para interagir com Ollama local"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/generate"

    def generate(self, prompt: str, model: str = "mistral", temperature: float = 0.7) -> str:
        """Gera texto usando modelo Ollama"""
        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature
                },
                timeout=300
            )
            response.raise_for_status()
            return response.json()["response"].strip()
        except requests.exceptions.ConnectionError:
            logger.error(f"Erro: Ollama não está rodando em {self.base_url}")
            logger.error("Execute: ollama serve")
            raise
        except Exception as e:
            logger.error(f"Erro ao gerar com Ollama: {e}")
            raise

    def generate_json(self, prompt: str, model: str = "mistral") -> Dict[str, Any]:
        """Gera JSON usando Ollama"""
        response_text = self.generate(prompt, model)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.error(f"Resposta não é JSON válido: {response_text}")
            raise


class FileManager:
    """Gerencia estrutura de arquivos do projeto"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Criar subdirs
        self.dirs = {
            "root": self.output_dir,
            "images": self.output_dir / "images",
            "audio": self.output_dir / "audio",
        }

        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    def save_json(self, filename: str, data: Dict[str, Any]):
        """Salva JSON com indentação"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Salvo: {filename}")
        return filepath

    def load_json(self, filename: str) -> Dict[str, Any]:
        """Carrega JSON"""
        filepath = self.output_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_text(self, filename: str, content: str):
        """Salva arquivo de texto"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"✓ Salvo: {filename}")
        return filepath

    def load_text(self, filename: str) -> str:
        """Carrega arquivo de texto"""
        filepath = self.output_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def get_image_path(self, scene_num: int) -> Path:
        """Retorna caminho para imagem de cena"""
        return self.dirs["images"] / f"scene_{scene_num:03d}.png"

    def get_audio_path(self) -> Path:
        """Retorna caminho para áudio de narração"""
        return self.dirs["audio"] / "narration.wav"


class ConfigManager:
    """Gerencia configurações do projeto"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.prompts = self._load_yaml("prompts.yaml")
        self.models = self._load_yaml("models.yaml")

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Carrega arquivo YAML"""
        filepath = self.config_dir / filename
        if not filepath.exists():
            logger.warning(f"Config não encontrado: {filename}")
            return {}

        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def get_prompt(self, prompt_key: str) -> str:
        """Retorna template de prompt"""
        prompts = self.prompts.get("prompts", {})
        return prompts.get(prompt_key, "")

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Retorna configuração do modelo"""
        models = self.models.get("models", {})
        return models.get(model_name, {})


class ScriptParser:
    """Parseia scripts em markdown para extrair cenas e timing"""

    @staticmethod
    def parse_script(script_content: str) -> list[Dict[str, Any]]:
        """Parseia script markdown e extrai cenas"""
        scenes = []
        current_scene = None

        lines = script_content.split('\n')
        for line in lines:
            # Detectar cabeçalho de cena
            if line.startswith('## CENA'):
                if current_scene:
                    scenes.append(current_scene)

                # Extrair número da cena e timing
                parts = line.split('(')
                scene_num = int(''.join(filter(str.isdigit, parts[0].split()[-1])))
                timing = parts[1].rstrip(')') if len(parts) > 1 else "0-10s"

                current_scene = {
                    "numero": scene_num,
                    "timing": timing,
                    "naracao": "",
                    "visual": ""
                }

            # Extrair narração
            elif line.startswith('**Narração:**') and current_scene:
                current_scene["naracao"] = line.replace('**Narração:**', '').strip()

            # Extrair visual
            elif line.startswith('**Visual:**') and current_scene:
                current_scene["visual"] = line.replace('**Visual:**', '').strip()

        if current_scene:
            scenes.append(current_scene)

        return scenes


class TimestampExtractor:
    """Extrai timestamps de áudio"""

    @staticmethod
    def extract_from_audio(audio_path: str) -> Dict[str, Any]:
        """Extrai duração e calcula timestamps (aproximado)"""
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)

            return {
                "duration_seconds": duration,
                "sample_rate": sr,
                "num_samples": len(y)
            }
        except Exception as e:
            logger.error(f"Erro ao extrair timestamp: {e}")
            return {"duration_seconds": 0, "error": str(e)}


class VideoComposer:
    """Ferramentas para composição de vídeo com FFmpeg"""

    @staticmethod
    def build_ffmpeg_command(
        image_pattern: str,
        audio_path: str,
        subtitle_path: str,
        output_path: str,
        fps: int = 30,
        crf: int = 18
    ) -> str:
        """Constrói comando FFmpeg para composição de vídeo"""

        cmd = [
            "ffmpeg",
            "-framerate", str(fps),
            "-i", image_pattern,
            "-i", audio_path,
        ]

        # Adicionar legendas se fornecidas
        if subtitle_path and Path(subtitle_path).exists():
            cmd.extend(["-vf", f"subtitles={subtitle_path}"])

        # Codec e qualidade
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", str(crf),
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",  # Overwrite output
            output_path
        ])

        return " ".join(cmd)


def validate_dependencies():
    """Valida se todas as dependências estão instaladas"""

    required_tools = {
        "ollama": "Ollama",
        "ffmpeg": "FFmpeg",
        "piper": "Piper TTS"
    }

    missing = []

    for tool, name in required_tools.items():
        if not _command_exists(tool):
            missing.append(name)

    if missing:
        logger.error(f"Dependências não instaladas: {', '.join(missing)}")
        logger.error("Execute: brew install ollama ffmpeg && pip install piper-tts")
        return False

    return True


def _command_exists(command: str) -> bool:
    """Verifica se comando está disponível"""
    from shutil import which
    return which(command) is not None


def timestamp_to_srt_time(seconds: float) -> str:
    """Converte segundos para formato SRT (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def extract_timing(timing_str: str) -> tuple[float, float]:
    """Extrai start e end de string como '0-10s'"""
    try:
        parts = timing_str.replace('s', '').split('-')
        return float(parts[0]), float(parts[1])
    except (ValueError, IndexError):
        logger.warning(f"Timing inválido: {timing_str}, usando 0-10")
        return 0.0, 10.0
