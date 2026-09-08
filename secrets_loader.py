import os
import re
from pathlib import Path


SECRETS_FILE = Path(__file__).with_name("ключи апи")


def _load_file_secrets():
    if not SECRETS_FILE.is_file():
        return {}

    text = SECRETS_FILE.read_text(encoding="utf-8")
    secrets = {}
    for name in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "XAI_API_KEY"):
        match = re.search(rf"{name}\s*[:=]?\s*(\S+)", text)
        if match:
            secrets[name] = match.group(1)

    token_match = re.search(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b", text)
    if token_match:
        secrets["BOT_TOKEN"] = token_match.group(0)
    return secrets


_FILE_SECRETS = _load_file_secrets()


def get_secret(name, default=""):
    return os.environ.get(name) or _FILE_SECRETS.get(name) or default
