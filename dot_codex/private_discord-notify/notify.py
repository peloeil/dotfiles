#!/usr/bin/env python3
"""Notify Discord after a long Codex turn, using only the standard library."""

import argparse
import hashlib
import json
import os
import socket
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str = field(repr=False)
    channel_id: str
    mention_user_id: str
    threshold_seconds: int


def required_string(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a nonempty string")
    return value


def load_settings(root: Path) -> Settings:
    data = json.loads((root / "config.json").read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config.json must contain an object")
    token = required_string(data, "bot_token")
    if any(char.isspace() for char in token):
        raise ValueError("bot_token must not contain whitespace")
    for key in ("channel_id", "mention_user_id"):
        value = required_string(data, key)
        if not value.isascii() or not value.isdecimal() or not 0 < int(value) < 2**64:
            raise ValueError(f"{key} must be a Discord snowflake ID")
    threshold = data.get("threshold_seconds", 600)
    if type(threshold) is not int or threshold <= 0:
        raise ValueError("threshold_seconds must be a positive integer")
    return Settings(token, data["channel_id"], data["mention_user_id"], threshold)


def state_path(root: Path, session_id: str, turn_id: str) -> Path:
    key = json.dumps([session_id, turn_id]).encode()
    return root / "state" / hashlib.sha256(key).hexdigest()


def session_name(session_id: str) -> str:
    codex_dir = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    name = session_id
    # ponytail: read Codex's local name cache; use thread/read if its format changes.
    try:
        with (codex_dir / "session_index.jsonl").open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if isinstance(entry, dict) and entry.get("id") == session_id:
                    value = entry.get("thread_name")
                    name = (
                        value
                        if isinstance(value, str) and value.strip()
                        else session_id
                    )
    except (OSError, UnicodeError):
        pass
    return name


def truncate(text: str, limit: int) -> str:
    encoded = text.encode("utf-16-le")
    if len(encoded) <= limit * 2:
        return text
    return encoded[: (limit - 1) * 2].decode("utf-16-le", errors="ignore") + "…"


def send_notification(
    settings: Settings, cwd: str, elapsed: float, name: str, prompt: str
) -> None:
    minutes, seconds = divmod(int(elapsed), 60)
    content = (
        f"<@{settings.mention_user_id}> Codex の回答が完了した。\n"
        f"マシン: {socket.gethostname()[:128]}\n"
        f"作業場所: {truncate(cwd, 300)}\n"
        f"セッション: {truncate(name, 160)}\n"
        f"所要時間: {minutes} 分 {seconds} 秒\n\n"
        f"直前のプロンプト:\n{prompt}"
    )
    payload = {
        "content": truncate(content, 2000),
        "allowed_mentions": {"parse": [], "users": [settings.mention_user_id]},
    }
    request = Request(
        f"https://discord.com/api/v10/channels/{settings.channel_id}/messages",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bot {settings.bot_token}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "CodexDiscordNotify/1.0",
        },
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        response.read()


def handle(mode: str, event: Mapping[str, object], root: Path = ROOT) -> None:
    complete = mode == "complete"
    if complete and event.get("type") != "agent-turn-complete":
        return
    session_id = required_string(event, "thread-id" if complete else "session_id")
    turn_id = required_string(event, "turn-id" if complete else "turn_id")
    path = state_path(root, session_id, turn_id)
    if mode == "start":
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return
        with os.fdopen(descriptor, "w") as stream:
            stream.write(str(time.monotonic_ns()))
        return
    if mode == "interrupt":
        path.unlink(missing_ok=True)
        return
    try:
        started = int(path.read_text())
        path.unlink()
    except FileNotFoundError:
        return
    elapsed = (time.monotonic_ns() - started) / 1_000_000_000
    settings = load_settings(root)
    if elapsed >= settings.threshold_seconds:
        messages = event.get("input-messages")
        prompt = messages[-1] if isinstance(messages, list) and messages else None
        if not isinstance(prompt, str) or not prompt.strip():
            prompt = "テキストなし"
        # ponytail: one delivery attempt; add an outbox if retries become necessary.
        send_notification(
            settings,
            required_string(event, "cwd"),
            elapsed,
            session_name(session_id),
            prompt,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("start", "complete", "interrupt"))
    parser.add_argument("event", nargs="?")
    args = parser.parse_args(argv)
    try:
        event = json.loads(args.event if args.event is not None else sys.stdin.read())
        if not isinstance(event, dict):
            raise ValueError("event must be a JSON object")
        handle(args.mode, event)
    except (OSError, ValueError) as error:
        print(f"Codex Discord notification failed: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
