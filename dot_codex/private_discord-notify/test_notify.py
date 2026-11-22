import io
import json
import os
import shlex
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import install
import notify


class NotificationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        codex_home = patch.dict(os.environ, {"CODEX_HOME": str(self.root)})
        codex_home.start()
        self.addCleanup(codex_home.stop)
        self.default_config_path = notify.CONFIG_PATH
        shared_config = patch.object(notify, "CONFIG_PATH", self.root / "config.json")
        shared_config.start()
        self.addCleanup(shared_config.stop)
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

    def run_turn(self, seconds: float, **complete_fields: object) -> None:
        notify.handle("start", self.start, self.root)
        self.advance(seconds)
        notify.handle("complete", self.complete | complete_fields, self.root)

    def sent_payload(self) -> dict:
        return json.loads(self.network.call_args.args[0].data)


class ThresholdTests(NotificationTestCase):
    def test_turn_shorter_than_threshold_does_not_notify(self) -> None:
        self.run_turn(299.999)
        self.network.assert_not_called()

    def test_turn_exactly_at_threshold_notifies(self) -> None:
        self.run_turn(300)
        self.network.assert_called_once()

    def test_turn_over_threshold_notifies(self) -> None:
        self.run_turn(301)
        self.network.assert_called_once()

    def test_duplicate_completion_notifies_once(self) -> None:
        self.run_turn(600)
        notify.handle("complete", self.complete, self.root)
        self.network.assert_called_once()

    def test_followup_does_not_reset_start(self) -> None:
        notify.handle("start", self.start, self.root)
        self.advance(400)
        notify.handle("start", self.start, self.root)
        self.advance(200)
        notify.handle("complete", self.complete, self.root)
        self.network.assert_called_once()

    def test_concurrent_sessions_and_turns_are_independent(self) -> None:
        notify.handle("start", self.start, self.root)
        self.advance(400)
        for event in (
            {"session_id": "session-b", "turn_id": "turn-a"},
            {"session_id": "session-a", "turn_id": "turn-b"},
        ):
            notify.handle("start", event, self.root)
        self.advance(200)
        notify.handle("complete", self.complete, self.root)
        for fields in ({"thread-id": "session-b"}, {"turn-id": "turn-b"}):
            notify.handle("complete", self.complete | fields, self.root)
        self.network.assert_called_once()

    def test_completion_without_start_does_not_notify(self) -> None:
        notify.handle("complete", self.complete, self.root)
        self.network.assert_not_called()

    def test_events_other_than_turn_completion_do_not_notify(self) -> None:
        self.run_turn(301, type="approval-requested")
        self.network.assert_not_called()

    def test_interrupted_turn_does_not_notify(self) -> None:
        notify.handle("start", self.start, self.root)
        self.advance(301)
        notify.handle("interrupt", self.start, self.root)
        notify.handle("complete", self.complete, self.root)
        self.network.assert_not_called()


class MessageTests(NotificationTestCase):
    def test_notification_mentions_only_the_configured_user(self) -> None:
        self.run_turn(600)
        payload = self.sent_payload()
        self.assertTrue(payload["content"].startswith("<@456>"))
        self.assertEqual(payload["allowed_mentions"], {"parse": [], "users": ["456"]})

    def test_notification_shows_cwd_and_only_the_latest_prompt(self) -> None:
        self.run_turn(600)
        content = self.sent_payload()["content"]
        self.assertIn("/workspace/project", content)
        self.assertIn("直前のプロンプト:\n直前の指示", content)
        self.assertNotIn("最初の指示", content)

    def test_notification_is_posted_to_the_channel_with_the_bot_token(self) -> None:
        self.run_turn(600)
        request = self.network.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            request.full_url, "https://discord.com/api/v10/channels/123/messages"
        )
        self.assertEqual(request.get_header("Authorization"), "Bot test-secret")
        self.assertEqual(self.network.call_args.kwargs["timeout"], 10)

    def test_notification_content_does_not_contain_the_bot_token(self) -> None:
        self.run_turn(600)
        self.assertNotIn("test-secret", self.sent_payload()["content"])

    def test_long_prompt_is_truncated_without_expanding_mentions(self) -> None:
        self.run_turn(600, **{"input-messages": ["@everyone <@789> " + "😀" * 3000]})
        payload = self.sent_payload()
        self.assertLessEqual(len(payload["content"].encode("utf-16-le")) // 2, 2000)
        self.assertTrue(payload["content"].endswith("…"))
        self.assertIn("@everyone <@789>", payload["content"])
        self.assertEqual(payload["allowed_mentions"], {"parse": [], "users": ["456"]})

    def test_notification_shows_the_session_name(self) -> None:
        (self.root / "session_index.jsonl").write_text(
            json.dumps({"id": "session-a", "thread_name": "通知機能の追加"})
        )
        self.run_turn(600)
        self.assertIn("セッション: 通知機能の追加", self.sent_payload()["content"])


class SessionNameTests(NotificationTestCase):
    def test_falls_back_to_the_id_without_an_index(self) -> None:
        self.assertEqual(notify.session_name("session-a"), "session-a")

    def test_uses_the_latest_entry_and_skips_a_partial_line(self) -> None:
        rows = [
            {"id": "session-a", "thread_name": "古い名前"},
            {"id": "session-b", "thread_name": "別の会話"},
            {"id": "session-a", "thread_name": "通知機能の追加"},
        ]
        (self.root / "session_index.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows) + '\n{"partial":'
        )
        self.assertEqual(notify.session_name("session-a"), "通知機能の追加")

    def test_falls_back_to_the_id_with_a_damaged_index(self) -> None:
        (self.root / "session_index.jsonl").write_text("not JSON\n[]\n")
        self.assertEqual(notify.session_name("session-a"), "session-a")


class SettingsTests(NotificationTestCase):
    def test_codex_reads_the_settings_file_owned_by_the_opencode_notifier(self) -> None:
        # Contract with the OpenCode plugin: both notifiers share one settings file.
        self.assertEqual(
            self.default_config_path,
            Path("~/.config/opencode/plugins/discord-notify/config.json").expanduser(),
        )

    def test_config_rejects_invalid_ids_threshold_and_token(self) -> None:
        for key, value in (
            ("channel_id", "../123"),
            ("mention_user_id", "@everyone"),
            ("mention_user_id", "１２３"),
            ("threshold_seconds", True),
            ("threshold_seconds", -1),
            ("bot_token", "secret\nheader"),
        ):
            with self.subTest(key=key, value=value):
                (self.root / "config.json").write_text(
                    json.dumps(self.config | {key: value})
                )
                with self.assertRaises(ValueError):
                    notify.load_settings()


class DeliveryFailureTests(NotificationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.network.side_effect = HTTPError(
            "https://discord.com", 403, "Forbidden", Message(), None
        )
        notify.handle("start", self.start, self.root)
        self.advance(600)

    def complete_via_cli(self) -> tuple[int, str]:
        with patch("notify.sys.stderr", new_callable=io.StringIO) as stderr:
            status = notify.main(["complete", json.dumps(self.complete)], self.root)
        return status, stderr.getvalue()

    def test_failure_does_not_fail_codex(self) -> None:
        status, _ = self.complete_via_cli()
        self.assertEqual(status, 0)

    def test_failure_is_reported_without_the_bot_token(self) -> None:
        _, stderr = self.complete_via_cli()
        self.assertIn("403", stderr)
        self.assertNotIn("test-secret", stderr)

    def test_failed_delivery_is_not_retried(self) -> None:
        self.complete_via_cli()
        notify.handle("complete", self.complete, self.root)
        self.network.assert_called_once()


class InstallTests(NotificationTestCase):
    original_config = 'model = "existing-model"\n\n[hooks.state.example]\nenabled = true\n'
    other_hook = {"hooks": [{"type": "command", "command": "other-hook"}]}

    def setUp(self) -> None:
        super().setUp()
        self.codex_dir = self.root / "codex"
        self.codex_dir.mkdir()
        self.config_path = self.codex_dir / "config.toml"
        self.config_path.write_text(self.original_config)
        self.hooks_path = self.codex_dir / "hooks.json"
        self.hooks_path.write_text(
            json.dumps({"hooks": {"SessionStart": [self.other_hook]}})
        )

    def hook(self, mode: str, timeout: int) -> dict:
        command = shlex.join(["python3", str(self.root / "notify.py"), mode])
        return {"hooks": [{"type": "command", "command": command, "timeout": timeout}]}

    def installed_hooks(self) -> dict:
        return json.loads(self.hooks_path.read_text())["hooks"]

    def test_install_prepends_notify_command_to_the_existing_config(self) -> None:
        install.install(self.codex_dir, self.root)
        command = json.dumps(["python3", str(self.root / "notify.py"), "complete"])
        self.assertEqual(
            self.config_path.read_text(), f"notify = {command}\n\n{self.original_config}"
        )

    def test_install_backs_up_the_original_config(self) -> None:
        install.install(self.codex_dir, self.root)
        backup = self.codex_dir / "config.toml.before-discord-notify"
        self.assertEqual(backup.read_text(), self.original_config)

    def test_install_keeps_other_hooks(self) -> None:
        install.install(self.codex_dir, self.root)
        self.assertEqual(self.installed_hooks()["SessionStart"], [self.other_hook])

    def test_install_registers_start_and_interrupt_hooks(self) -> None:
        install.install(self.codex_dir, self.root)
        hooks = self.installed_hooks()
        self.assertEqual(hooks["UserPromptSubmit"], [self.hook("start", 5)])
        self.assertEqual(hooks["Interrupt"], [self.hook("interrupt", 3)])

    def test_install_twice_changes_nothing(self) -> None:
        install.install(self.codex_dir, self.root)
        config, hooks = self.config_path.read_bytes(), self.hooks_path.read_bytes()
        install.install(self.codex_dir, self.root)
        self.assertEqual(self.config_path.read_bytes(), config)
        self.assertEqual(self.hooks_path.read_bytes(), hooks)

    def test_install_makes_the_settings_file_private(self) -> None:
        install.install(self.codex_dir, self.root)
        self.assertEqual((self.root / "config.json").stat().st_mode & 0o777, 0o600)

    def test_install_keeps_conflicting_notify_untouched(self) -> None:
        original = 'notify = ["existing-notifier"]\n'
        self.config_path.write_text(original)
        self.hooks_path.unlink()
        with self.assertRaises(ValueError):
            install.install(self.codex_dir, self.root)
        self.assertEqual(self.config_path.read_text(), original)
        self.assertFalse(self.hooks_path.exists())


if __name__ == "__main__":
    unittest.main()
