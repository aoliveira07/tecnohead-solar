"""Static release guardrails that do not contain customer-specific secrets."""

from __future__ import annotations

import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_EXTENSIONS = {".md", ".yaml", ".yml", ".py", ".sh", ".txt", ".toml", ".js", ".css", ".html"}


def main() -> int:
    failures: list[str] = []
    config = ROOT / "tecnohead_solar" / "config.yaml"
    repository = ROOT / "repository.yaml"
    if not config.exists() or not repository.exists():
        failures.append("repository.yaml/config.yaml ausente")
    config_text = config.read_text(encoding="utf-8") if config.exists() else ""
    for required in ("slug: \"tecnohead_solar\"", "image:", "ingress: true", "backup: cold", "panel_icon:"):
        if required not in config_text:
            failures.append(f"config.yaml sem {required}")
    if (ROOT / "tecnohead_solar" / "build.yaml").exists():
        failures.append("build.yaml legado não deve existir")
    if not (ROOT / "tecnohead_solar" / "icon.png").exists() or not (ROOT / "tecnohead_solar" / "logo.png").exists():
        failures.append("icon.png/logo.png ausente")

    private_tokens = [token for token in os.getenv("PRIVATE_SCAN_TOKENS", "").splitlines() if token]
    ip_pattern = re.compile(r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b")
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or path.suffix.lower() not in PUBLIC_EXTENSIONS
            or any(part in {".git", ".venv", ".pytest_cache", ".ruff_cache"} for part in path.parts)
        ):
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if ip_pattern.search(content):
            failures.append(f"endereço 192.168.x.x encontrado em {path.relative_to(ROOT)}")
        for token in private_tokens:
            if token in content:
                failures.append(f"token de varredura encontrado em {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("TecnoHead Solar release guardrails: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

