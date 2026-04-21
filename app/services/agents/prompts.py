from hashlib import sha256
from pathlib import Path

from app.core.config import settings

PROMPT_DIR = Path("app/agents/prompts")


def load_prompt(prompt_name: str, override_path: str | None = None) -> dict:
    if override_path:
        prompt_path = Path(override_path)
    elif prompt_name == "product_scout":
        prompt_path = Path(settings.product_scout_prompt_path) if settings.product_scout_prompt_path else PROMPT_DIR / "product_scout.txt"
    elif prompt_name == "supplier_check":
        prompt_path = Path(settings.supplier_check_prompt_path) if settings.supplier_check_prompt_path else PROMPT_DIR / "supplier_check.txt"
    else:
        raise ValueError(f"Unknown prompt: {prompt_name}")

    content = prompt_path.read_text(encoding="utf-8")
    version = sha256(content.encode("utf-8")).hexdigest()[:12]
    return {
        "name": prompt_name,
        "path": str(prompt_path),
        "version": version,
        "content": content,
    }
