"""Guard against silent or destructive setup failures in an isolated home."""

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
CHEZMOI = shutil.which("chezmoi")


def run(*args, **kwargs):
    result = subprocess.run(args, text=True, capture_output=True, check=False, **kwargs)
    if result.returncode:
        raise AssertionError(f"{args}:\n{result.stdout}{result.stderr}")
    return result.stdout


def mock(path, body):
    path.write_text("#!/bin/sh\n" + body + "\n")
    path.chmod(0o755)


class SetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CHEZMOI:
            raise unittest.SkipTest("chezmoi is required")
        cls.temp = tempfile.TemporaryDirectory(prefix="chezmoi-check-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.home = cls.work / "home with spaces"
        cls.home.mkdir()
        cls.local_bin = cls.home / ".local/bin"
        cls.local_bin.mkdir(parents=True)
        cls.data = {
            "chezmoi": {"homeDir": str(cls.home), "os": "linux", "hostname": "test"},
            "desktop": True,
            "denopsSharedServer": False,
            "denopsServerPort": 32123,
            "zennPreview": False,
            "email": "personal@example.invalid",
            "researchEmail": "research@example.invalid",
            "researchDir": str(cls.home / "workspace/university/laboratory/research"),
            "name": "Test User",
        }
        cls.clis = {}
        for desktop in (True, False):
            directory = cls.work / f"desktop-{desktop}"
            directory.mkdir()
            cli = (
                CHEZMOI, "--source", str(SOURCE), "--destination", str(cls.home),
                "--config", str(directory / "chezmoi.toml"),
                "--cache", str(directory / "cache"),
                "--persistent-state", str(directory / "state.boltdb"), "--no-tty",
            )
            run(*cli, "init", "--promptDefaults", "--promptString",
                "Enter your research Git email address=research@example.invalid",
                *([] if desktop else ["--promptBool", "Install desktop environment=false"]))
            cls.clis[desktop] = cli

    def render(self, relative, **overrides):
        return run(
            CHEZMOI, "--config", "/dev/null", "--config-format", "toml",
            "--source", str(SOURCE), "execute-template", "--override-data",
            json.dumps({**self.data, **overrides}), "--file", str(SOURCE / relative),
        )

    def test_desktop_targets_are_managed_only_when_enabled(self):
        gui = (
            ".xinitrc", ".xprofile", ".config/alacritty", ".config/fcitx5",
            ".config/flameshot", ".config/i3", ".config/picom", ".config/polybar",
            ".config/sunshine", ".chezmoiscripts/20_install_hack_nerd_font.sh",
        )
        for desktop in (True, False):
            with self.subTest(desktop=desktop):
                cli = self.clis[desktop]
                managed = set(run(*cli, "managed").splitlines())
                for target in gui:
                    self.assertEqual(target in managed, desktop, target)
                    if not desktop:
                        self.assertFalse(any(p.startswith(target + "/") for p in managed), target)
                self.assertNotIn(".config/opencode/plugins/discord-notify/config.json", managed)
                run(*cli, "diff")
                run(*cli, "apply", "--dry-run")

    def test_scripts_render_and_pass_shell_syntax_for_both_desktop_modes(self):
        for desktop in (True, False):
            for script in (SOURCE / ".chezmoiscripts").iterdir():
                with self.subTest(desktop=desktop, script=script.name):
                    content = (self.render(script.relative_to(SOURCE), desktop=desktop)
                               if script.suffix == ".tmpl" else script.read_text())
                    run("/bin/sh", "-n", input=content)

    def test_bash_profile_starts_x_only_on_desktop(self):
        for desktop in (True, False):
            with self.subTest(desktop=desktop):
                profile = self.render("dot_bash_profile.tmpl", desktop=desktop)
                run("bash", "-n", input=profile)
                self.assertEqual("exec startx" in profile, desktop)

    def test_codex_config_preserves_local_state_and_is_idempotent(self):
        config = self.home / ".codex/config.toml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            'service_tier = "fast"\n'
            '[features]\nfast_mode = true\nhooks = false\n'
            '[projects."/local/project"]\ntrust_level = "untrusted"\n'
            '[hooks.state.local]\ntrusted_hash = "sha256:test"\n'
            '[plugins."local@example"]\nenabled = false\n'
            '[tui]\nfullscreen_transcript = true\nscreen_reader_detection_done = true\n'
            '[tui.model_availability_nux]\n"example-model" = 4\n'
        )
        cli = (*self.clis[True], "--override-data", json.dumps(self.data))
        run(*cli, "apply", str(config))
        codex = tomllib.loads(config.read_text())
        self.assertEqual(codex["features"], {"fast_mode": False, "hooks": True})
        self.assertEqual(codex["service_tier"], "fast")
        self.assertEqual(codex["projects"]["/local/project"]["trust_level"], "untrusted")
        self.assertEqual(codex["hooks"]["state"]["local"]["trusted_hash"], "sha256:test")
        self.assertIs(codex["plugins"]["local@example"]["enabled"], False)
        self.assertIs(codex["tui"]["fullscreen_transcript"], False)
        self.assertIs(codex["tui"]["screen_reader_detection_done"], True)
        hint = codex["tui"]["model_availability_nux"]["example-model"]
        self.assertIs(type(hint), int)
        self.assertEqual(hint, 4)
        self.assertEqual(config.stat().st_mode & 0o777, 0o600)
        applied = config.read_bytes()
        run(*cli, "apply", str(config))
        self.assertEqual(config.read_bytes(), applied)
        self.assertEqual(run(*cli, "diff", str(config)), "")

    def test_rtk_init_preserves_shared_codex_instructions_on_repeated_runs(self):
        shared = self.home / ".config/opencode/AGENTS.md"
        codex = self.home / ".codex/AGENTS.md"
        claude = self.home / ".claude/CLAUDE.md"
        cli = (*self.clis[True], "--override-data", json.dumps(self.data))
        run(*cli, "apply", "--parent-dirs", str(shared), str(codex), str(claude))
        expected = (SOURCE / "dot_config/opencode/AGENTS.md").read_bytes()
        mock(self.local_bin / "mise", f'printf "%s\\n" "{self.local_bin / "rtk"}"')
        mock(self.local_bin / "rtk", 'if [ "${3:-}" = --codex ]; then\n'
             '  printf "\\n@%s/.codex/RTK.md\\n" "$HOME" >> "$HOME/.codex/AGENTS.md"\n'
             '  chmod 600 "$HOME/.codex/AGENTS.md"\nfi')
        script = (SOURCE / ".chezmoiscripts/run_onchange_after_15_init_rtk.sh").read_text()
        for _ in range(2):
            run("/bin/sh", input=script, env={**os.environ, "HOME": str(self.home)})
            self.assertTrue(codex.is_symlink())
            self.assertEqual(codex.resolve(), shared)
            self.assertEqual(shared.read_bytes(), expected)
            self.assertEqual(codex.read_bytes(), expected)

    def test_zenn_units_never_listen_without_tailscale_address(self):
        service_bin = self.work / "service-bin"
        service_bin.mkdir(exist_ok=True)
        log = self.work / "zenn-calls"
        mock(self.local_bin / "mise", 'printf "%s\\n" "$@" >> "$CHECK_LOG"')
        env = {**os.environ, "PATH": str(service_bin), "CHECK_LOG": str(log)}
        for unit, expected in (
            ("zenn-preview", ["node", "node_modules/zenn-cli/dist/server/zenn.js",
                              "preview", "--host", "100.64.0.1", "--port", "8000"]),
            ("zenn-notes", ["node", "scripts/preview-notes.mjs", "100.64.0.1", "8001"]),
        ):
            rendered = self.render(f"dot_config/systemd/user/{unit}.service.tmpl")
            start = next(line.removeprefix("ExecStart=") for line in rendered.splitlines()
                         if line.startswith("ExecStart="))
            command = shlex.split(start.replace("$$", "$"))
            run("/bin/sh", "-n", "-c", command[-1])
            with self.subTest(unit=unit, tailscale="available"):
                mock(service_bin / "tailscale", 'printf "100.64.0.1\\n"')
                run(*command, env=env)
                self.assertEqual(log.read_text().splitlines(), ["exec", "--", *expected])
                log.unlink()
            for unavailable in ("exit 1", "exit 0", None):
                with self.subTest(unit=unit, tailscale=unavailable):
                    if unavailable is None:
                        (service_bin / "tailscale").unlink()
                    else:
                        mock(service_bin / "tailscale", unavailable)
                    result = subprocess.run(command, env=env, capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(log.exists())

    def test_git_email_follows_research_directory_changes(self):
        global_git = self.work / "git.config"
        global_git.write_text(self.render("dot_config/git/private_config.tmpl"))
        research_git = self.home / ".config/git/research.config"
        research_git.parent.mkdir(parents=True, exist_ok=True)
        research_git.write_text(self.render("dot_config/git/private_research.config.tmpl"))
        env = {**os.environ, "GIT_CONFIG_GLOBAL": str(global_git), "GIT_CONFIG_NOSYSTEM": "1"}
        research = Path(self.data["researchDir"]) / "project"
        outside = self.home / "elsewhere"
        for repo in (research, outside):
            repo.mkdir(parents=True, exist_ok=True)
            run("git", "init", "--quiet", str(repo), env=env)
        def email(repo):
            return run("git", "-C", str(repo), "config", "user.email", env=env).strip()
        self.assertEqual(email(research), "research@example.invalid")
        self.assertEqual(email(outside), "personal@example.invalid")
        global_git.write_text(self.render("dot_config/git/private_config.tmpl", researchDir=str(outside) + "/"))
        self.assertEqual(email(outside), "research@example.invalid")
        self.assertEqual(email(research), "personal@example.invalid")


if __name__ == "__main__":
    unittest.main()
