"""Configuración central: rutas, modelo Claude y parámetros de reintento."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
LOGS_DIR = DATA_DIR / "logs"
SCHEMAS_DIR = BASE_DIR / "schemas"
PROMPTS_DIR = BASE_DIR / "prompts"

CHANNEL_FILE = DATA_DIR / "channel.json"
METHODS_JSONL = DATA_DIR / "methods.jsonl"
REPORT_MD = DATA_DIR / "report.md"
NO_TRANSCRIPT_LOG = LOGS_DIR / "no_transcript.log"
PIPELINE_LOG = LOGS_DIR / "pipeline.log"

LANG_PRIORITY = ["es", "en"]

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:14b")
OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "40960"))
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "qwen3-embedding:8b")

MAX_RETRIES = int(os.environ.get("PIPELINE_MAX_RETRIES", "4"))
BACKOFF_BASE = float(os.environ.get("PIPELINE_BACKOFF_BASE", "2.0"))

YT_COOKIES_FROM_BROWSER = os.environ.get("YT_COOKIES_FROM_BROWSER") or None
