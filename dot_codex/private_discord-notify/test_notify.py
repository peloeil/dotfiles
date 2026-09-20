import io
import json
import os
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import install
import notify


class NotificationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        codex_home = patch.dict(os.environ, {"CODEX_HOME": str(self.root)})
        codex_home.start()
        self.addCleanup(codex_home.stop)
        self.config = {
            "bot_token": "test-secret",
            "channel_id": "123",
            "mention_user_id": "456",
            "threshold_seconds": 300,
        }
        (self.root / "config.json").write_text(json.dumps(self.config))
        self.start = {"session_id": "session-a", "turn_id": "turn-a"}
        self.complete = {
            "type": "agent-turn-complete",
            "thread-id": "session-a",
            "turn-id": "turn-a",
            "cwd": "/workspace/project",
            "input-messages": ["最初の指示", "直前の指示"],
        }
        clock = patch("notify.time.monotonic_ns", return_value=1_000_000_000_000)
        self.clock = clock.start()
        self.addCleanup(clock.stop)
        network = patch("notify.urlopen")
        self.network = network.start()
        self.addCleanup(network.stop)

    def advance(self, seconds: float) -> None:
        self.clock.return_value += int(seconds * 1_000_000_000)

    def test_threshold_mentions_and_duplicate_completion(self) -> None:
        for seconds, expected in ((299.999, 0), (300, 1), (301, 1)):
            with self.subTest(seconds=seconds):
                self.network.reset_mock()
                notify.handle("start", self.start, self.root)
                self.advance(seconds)
                notify.handle("complete", self.complete, self.root)
                notify.handle("complete", self.complete, self.root)
                self.assertEqual(self.network.call_count, expected)
                if expected:
                    request = self.network.call_args.args[0]
                    payload = json.loads(request.data)
                    self.assertEqual(
                        payload["allowed_mentions"],
                        {"parse": [], "users": ["456"]},
                    )
                    self.assertTrue(payload["content"].startswith("<@456>"))
                    self.assertIn("/workspace/project", payload["content"])
                    self.assertIn("直前のプロンプト:\n直前の指示", payload["content"])
                    self.assertNotIn("最初の指示", payload["content"])
                    self.assertNotIn("test-secret", payload["content"])
                    self.assertEqual(request.get_method(), "POST")
                    self.assertEqual(
                        request.full_url,
                        "https://discord.com/api/v10/channels/123/messages",
                    )
                    self.assertEqual(
                        request.get_header("Authorization"), "Bot test-secret"
                    )
                    self.assertEqual(self.network.call_args.kwargs["timeout"], 10)

    def test_followup_does_not_reset_start(self) -> None:
        notify.handle("start", self.start, self.root)
        self.advance(200)
        notify.handle("start", self.start, self.root)
        self.advance(100)
        notify.handle("complete", self.complete, self.root)
        self.network.assert_called_once()

    def test_latest_session_name_and_missing_or_damaged_index(self) -> None:
        self.assertEqual(notify.session_name("session-a"), "session-a")
        index = self.root / "session_index.jsonl"
        rows = [
            {"id": "session-a", "thread_name": "古い名前"},
            {"id": "session-b", "thread_name": "別の会話"},
            {"id": "session-a", "thread_name": "通知機能の追加"},
        ]
        index.write_text("\n".join(json.dumps(row) for row in rows) + '\n{"partial":')
        self.assertEqual(notify.session_name("session-a"), "通知機能の追加")
        notify.handle("start", self.start, self.root)
        self.advance(300)
        notify.handle("complete", self.complete, self.root)
        payload = json.loads(self.network.call_args.args[0].data)
        self.assertIn("セッション: 通知機能の追加", payload["content"])
        index.write_text("not JSON\n[]\n")
        self.assertEqual(notify.session_name("session-a"), "session-a")

    def test_long_prompt_is_truncated_without_expanding_mentions(self) -> None:
        event = self.complete | {"input-messages": ["@everyone <@789> " + "😀" * 3000]}
        notify.handle("start", self.start, self.root)
        self.advance(300)
        notify.handle("complete", event, self.root)
        payload = json.loads(self.network.call_args.args[0].data)
        self.assertLessEqual(len(payload["content"].encode("utf-16-le")) // 2, 2000)
        self.assertTrue(payload["content"].endswith("…"))
        self.assertIn("@everyone <@789>", payload["content"])
        self.assertEqual(payload["allowed_mentions"], {"parse": [], "users": ["456"]})

    def test_concurrent_sessions_and_turns_are_independent(self) -> None:
        notify.handle("start", self.start, self.root)
        self.advance(200)
        for event in (
            {"session_id": "session-b", "turn_id": "turn-a"},
            {"session_id": "session-a", "turn_id": "turn-b"},
        ):
            notify.handle("start", event, self.root)
        self.advance(100)
        notify.handle("complete", self.complete, self.root)
        for fields in ({"thread-id": "session-b"}, {"turn-id": "turn-b"}):
            notify.handle("complete", self.complete | fields, self.root)
        self.network.assert_called_once()

    def test_missing_start_interruption_and_other_events_do_not_notify(self) -> None:
        notify.handle("complete", self.complete, self.root)
        notify.handle("complete", {"type": "approval-requested"}, self.root)
        notify.handle("start", self.start, self.root)
        self.advance(301)
        notify.handle("interrupt", self.start, self.root)
        notify.handle("complete", self.complete, self.root)
        self.network.assert_not_called()

    def test_config_rejects_invalid_ids_threshold_and_token(self) -> None:
        for key, value in (
            ("channel_id", "../123"),
            ("mention_user_id", "@everyone"),
            ("mention_user_id", "\uff11\uff12\uff13"),
            ("threshold_seconds", True),
            ("threshold_seconds", -1),
            ("bot_token", "secret\nheader"),
        ):
            with self.subTest(key=key, value=value):
                (self.root / "config.json").write_text(
                    json.dumps(self.config | {key: value})
                )
                with self.assertRaises(ValueError):
                    notify.load_settings(self.root)

    def test_delivery_failure_does_not_block_codex_or_retry(self) -> None:
        notify.handle("start", self.start, self.root)
        self.advance(300)
        self.network.side_effect = HTTPError(
            "https://discord.com", 403, "Forbidden", Message(), None
        )
        original_handle = notify.handle
        with (
            patch("notify.sys.stderr", new_callable=io.StringIO) as stderr,
            patch(
                "notify.handle",
                side_effect=lambda mode, event: original_handle(mode, event, self.root),
            ),
        ):
            self.assertEqual(notify.main(["complete", json.dumps(self.complete)]), 0)
            self.assertIn("403", stderr.getvalue())
            self.assertNotIn("test-secret", stderr.getvalue())
        notify.handle("complete", self.complete, self.root)
        self.network.assert_called_once()

    def test_install_preserves_config_and_hooks_and_is_idempotent(self) -> None:
        codex_dir = self.root / "codex"
        codex_dir.mkdir()
        config_path = codex_dir / "config.toml"
        original = 'model = "existing-model"\n\n[hooks.state.example]\nenabled = true\n'
        config_path.write_text(original)
        hooks_path = codex_dir / "hooks.json"
        other = {"hooks": [{"type": "command", "command": "other-hook"}]}
        hooks_path.write_text(json.dumps({"hooks": {"SessionStart": [other]}}))
        install.install(codex_dir, self.root)
        result = config_path.read_text()
        install.install(codex_dir, self.root)
        self.assertEqual(config_path.read_text(), result)
        self.assertTrue(result.endswith(original))
        self.assertEqual(
            (codex_dir / "config.toml.before-discord-notify").read_text(), original
        )
        hooks = json.loads(hooks_path.read_text())["hooks"]
        self.assertEqual(hooks["SessionStart"], [other])
        self.assertEqual(len(hooks["UserPromptSubmit"]), 1)
        self.assertEqual(len(hooks["Interrupt"]), 1)
        self.assertEqual((self.root / "config.json").stat().st_mode & 0o777, 0o600)

    def test_install_keeps_conflicting_notify_untouched(self) -> None:
        codex_dir = self.root / "codex"
        codex_dir.mkdir()
        config = codex_dir / "config.toml"
        original = 'notify = ["existing-notifier"]\n'
        config.write_text(original)
        with self.assertRaises(ValueError):
            install.install(codex_dir, self.root)
        self.assertEqual(config.read_text(), original)
        self.assertFalse((codex_dir / "hooks.json").exists())


if __name__ == "__main__":
    unittest.main()
