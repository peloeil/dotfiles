#!/usr/bin/env python3
"""Register the notifier in this machine's Codex user configuration."""

import json
import os
import shlex
import shutil
import sys
import tomllib
from pathlib import Path

from notify import ROOT, load_settings


def write_with_backup(path: Path, content: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    backup = path.with_name(path.name + ".before-discord-notify")
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
        backup.chmod(0o600)
    temporary = path.with_name(path.name + ".discord-notify.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)


def install(codex_dir: Path, root: Path = ROOT) -> None:
    load_settings(root)
    config_path = codex_dir / "config.toml"
    text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    config = tomllib.loads(text)
    notify = ["python3", str(root / "notify.py"), "complete"]
    if "notify" in config and config["notify"] != notify:
        raise ValueError("An existing notify command is configured; keep it intact.")
    hooks_config = config.get("hooks", {})
    if any(key != "state" for key in hooks_config):
        raise ValueError("Inline hooks already exist; merge the new hooks manually.")
    hooks_path = codex_dir / "hooks.json"
    hooks = (
        json.loads(hooks_path.read_text(encoding="utf-8"))
        if hooks_path.exists()
        else {"hooks": {}}
    )
    for event, mode, timeout in (
        ("UserPromptSubmit", "start", 5),
        ("Interrupt", "interrupt", 3),
    ):
        handler = {
            "hooks": [
                {
                    "type": "command",
                    "command": shlex.join(["python3", str(root / "notify.py"), mode]),
                    "timeout": timeout,
                }
            ]
        }
        handlers = hooks.setdefault("hooks", {}).setdefault(event, [])
        if handler not in handlers:
            handlers.append(handler)
    if "notify" not in config:
        text = f"notify = {json.dumps(notify)}\n\n{text}"
    tomllib.loads(text)
    codex_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    root.chmod(0o700)
    (root / "config.json").chmod(0o600)
    write_with_backup(hooks_path, json.dumps(hooks, indent=2) + "\n")
    write_with_backup(config_path, text)


if __name__ == "__main__":
    try:
        install(Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser().resolve())
    except (OSError, ValueError) as error:
        sys.exit(f"Installation failed: {error}")
    print("Installed. Restart Codex and review the two new hooks with /hooks.")
