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
GUI_TARGETS = (
    ".xinitrc", ".xprofile", ".config/alacritty", ".config/fcitx5",
    ".config/flameshot", ".config/i3", ".config/picom", ".config/polybar",
    ".config/sunshine", ".chezmoiscripts/20_install_hack_nerd_font.sh",
)
TAILNET_IP = "100.64.0.1"
ZENN_UNITS = {
    "zenn-preview": ["zenn", "preview", "--host", TAILNET_IP, "--port", "8000"],
    "zenn-notes": ["node", "scripts/preview-notes.mjs", TAILNET_IP, "8001"],
}


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
        # Only the prompted configs and the external download cache are shared:
        # neither is written by the tests, and re-running init per test is slow.
        shared = tempfile.TemporaryDirectory(prefix="chezmoi-check-shared-")
        cls.addClassCleanup(shared.cleanup)
        cls.cache = Path(shared.name) / "cache"
        cls.configs = {}
        for desktop in (True, False):
            config = Path(shared.name) / f"desktop-{desktop}.toml"
            run(CHEZMOI, "--source", str(SOURCE), "--config", str(config),
                "--cache", str(cls.cache), "--no-tty", "init", "--promptDefaults",
                "--promptString",
                "Enter your research Git email address=research@example.invalid",
                *([] if desktop else ["--promptBool", "Install desktop environment=false"]))
            cls.configs[desktop] = config

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="chezmoi-check-")
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        self.home = self.work / "home with spaces"
        self.local_bin = self.home / ".local/bin"
        self.local_bin.mkdir(parents=True)
        self.data = {
            "chezmoi": {"homeDir": str(self.home), "os": "linux", "hostname": "test"},
            "desktop": True,
            "denopsSharedServer": False,
            "denopsServerPort": 32123,
            "zennPreview": False,
            "email": "personal@example.invalid",
            "researchEmail": "research@example.invalid",
            "researchDir": str(self.home / "workspace/university/laboratory/research"),
            "name": "Test User",
        }

    def cli(self, desktop=True):
        return (
            CHEZMOI, "--source", str(SOURCE), "--destination", str(self.home),
            "--config", str(self.configs[desktop]), "--cache", str(self.cache),
            "--persistent-state", str(self.work / "state.boltdb"), "--no-tty",
        )

    def apply(self, *targets):
        run(*self.cli(), "--override-data", json.dumps(self.data), "apply", *map(str, targets))

    def render(self, relative, **overrides):
        return run(
            CHEZMOI, "--config", "/dev/null", "--config-format", "toml",
            "--source", str(SOURCE), "execute-template", "--override-data",
            json.dumps({**self.data, **overrides}), "--file", str(SOURCE / relative),
        )

    def managed(self, desktop):
        return set(run(*self.cli(desktop), "managed").splitlines())

    def test_desktop_targets_are_managed_when_desktop_is_enabled(self):
        self.assertLessEqual(set(GUI_TARGETS), self.managed(desktop=True))

    def test_desktop_targets_and_their_contents_are_unmanaged_without_desktop(self):
        managed = self.managed(desktop=False)
        leaked = [path for path in managed for target in GUI_TARGETS
                  if path == target or path.startswith(target + "/")]
        self.assertEqual(leaked, [])

    def test_discord_notify_config_is_never_managed(self):
        for desktop in (True, False):
            with self.subTest(desktop=desktop):
                self.assertNotIn(".config/opencode/plugins/discord-notify/config.json",
                                 self.managed(desktop))

    def test_diff_and_dry_run_succeed_in_a_fresh_home(self):
        for desktop in (True, False):
            with self.subTest(desktop=desktop):
                run(*self.cli(desktop), "diff")
                run(*self.cli(desktop), "apply", "--dry-run")

    def test_templated_scripts_render_to_valid_shell_for_both_desktop_modes(self):
        for desktop in (True, False):
            for script in (SOURCE / ".chezmoiscripts").glob("*.tmpl"):
                with self.subTest(desktop=desktop, script=script.name):
                    run("/bin/sh", "-n",
                        input=self.render(script.relative_to(SOURCE), desktop=desktop))

    def test_plain_scripts_are_valid_shell(self):
        for script in (SOURCE / ".chezmoiscripts").glob("*.sh"):
            with self.subTest(script=script.name):
                run("/bin/sh", "-n", script)

    def test_bash_profile_starts_x_only_on_desktop(self):
        for desktop in (True, False):
            with self.subTest(desktop=desktop):
                profile = self.render("dot_bash_profile.tmpl", desktop=desktop)
                run("bash", "-n", input=profile)
                self.assertEqual("exec startx" in profile, desktop)

    def write_local_codex_config(self):
        config = self.home / ".codex/config.toml"
        config.parent.mkdir(parents=True)
        config.write_text(
            'service_tier = "fast"\n'
            '[features]\nfast_mode = true\nhooks = false\n'
            '[projects."/local/project"]\ntrust_level = "untrusted"\n'
            '[hooks.state.local]\ntrusted_hash = "sha256:test"\n'
            '[plugins."local@example"]\nenabled = false\n'
            '[tui]\nfullscreen_transcript = true\nscreen_reader_detection_done = true\n'
            '[tui.model_availability_nux]\n"example-model" = 4\n'
        )
        return config

    def test_codex_config_keeps_local_state(self):
        config = self.write_local_codex_config()
        self.apply(config)
        codex = tomllib.loads(config.read_text())
        self.assertEqual(codex["service_tier"], "fast")
        self.assertEqual(codex["projects"]["/local/project"]["trust_level"], "untrusted")
        self.assertEqual(codex["hooks"]["state"]["local"]["trusted_hash"], "sha256:test")
        self.assertIs(codex["plugins"]["local@example"]["enabled"], False)
        self.assertIs(codex["tui"]["screen_reader_detection_done"], True)
        hint = codex["tui"]["model_availability_nux"]["example-model"]
        self.assertIs(type(hint), int)
        self.assertEqual(hint, 4)

    def test_codex_config_overrides_local_values_of_managed_settings(self):
        config = self.write_local_codex_config()
        self.apply(config)
        codex = tomllib.loads(config.read_text())
        self.assertEqual(codex["features"], {"fast_mode": False, "hooks": True})
        self.assertIs(codex["tui"]["fullscreen_transcript"], False)

    def test_codex_config_is_private(self):
        config = self.write_local_codex_config()
        self.apply(config)
        self.assertEqual(config.stat().st_mode & 0o777, 0o600)

    def test_codex_config_is_unchanged_by_a_second_apply(self):
        config = self.write_local_codex_config()
        self.apply(config)
        applied = config.read_bytes()
        self.apply(config)
        self.assertEqual(config.read_bytes(), applied)
        self.assertEqual(run(*self.cli(), "--override-data", json.dumps(self.data),
                             "diff", str(config)), "")

    def test_rtk_init_preserves_shared_codex_instructions_on_repeated_runs(self):
        shared = self.home / ".config/opencode/AGENTS.md"
        codex = self.home / ".codex/AGENTS.md"
        claude = self.home / ".claude/CLAUDE.md"
        self.apply("--parent-dirs", shared, codex, claude)
        expected = (SOURCE / "dot_config/opencode/AGENTS.md").read_bytes()
        mock(self.local_bin / "mise", f'printf "%s\\n" "{self.local_bin / "rtk"}"')
        mock(self.local_bin / "rtk", 'if [ "${3:-}" = --codex ]; then\n'
             '  printf "\\n@%s/.codex/RTK.md\\n" "$HOME" >> "$HOME/.codex/AGENTS.md"\n'
             '  chmod 600 "$HOME/.codex/AGENTS.md"\nfi')
        script = (SOURCE / ".chezmoiscripts/run_onchange_after_15_init_rtk.sh").read_text()
        for attempt in (1, 2):
            with self.subTest(attempt=attempt):
                run("/bin/sh", input=script, env={**os.environ, "HOME": str(self.home)})
                self.assertTrue(codex.is_symlink())
                self.assertEqual(codex.resolve(), shared)
                self.assertEqual(shared.read_bytes(), expected)
                self.assertEqual(codex.read_bytes(), expected)

    def start_zenn_unit(self, unit, service_mocks):
        """Run the unit's ExecStart with only ``service_mocks`` on PATH."""
        rendered = self.render(f"dot_config/systemd/user/{unit}.service.tmpl")
        start = next(line.removeprefix("ExecStart=") for line in rendered.splitlines()
                     if line.startswith("ExecStart="))
        command = shlex.split(start.replace("$$", "$"))
        run("/bin/sh", "-n", "-c", command[-1])
        service_bin = Path(tempfile.mkdtemp(dir=self.work))
        log = service_bin / "mise-calls"
        log.touch()
        mock(self.local_bin / "mise", 'printf "%s\\n" "$@" >> "$CHECK_LOG"')
        for name, body in service_mocks.items():
            mock(service_bin / name, body)
        env = {**os.environ, "PATH": str(service_bin), "CHECK_LOG": str(log)}
        result = subprocess.run(command, env=env, capture_output=True)
        return result.returncode, log.read_text().splitlines()

    def test_zenn_units_listen_on_the_tailscale_address(self):
        for unit, expected in ZENN_UNITS.items():
            with self.subTest(unit=unit):
                returncode, calls = self.start_zenn_unit(
                    unit, {"tailscale": f'printf "{TAILNET_IP}\\n"'})
                self.assertEqual(returncode, 0)
                self.assertEqual(calls, ["exec", "--", *expected])

    def test_zenn_units_never_listen_without_tailscale_address(self):
        for unit in ZENN_UNITS:
            for case, service_mocks in (
                ("tailscale fails", {"tailscale": "exit 1"}),
                ("tailscale prints nothing", {"tailscale": "exit 0"}),
                ("tailscale is missing", {}),
            ):
                with self.subTest(unit=unit, case=case):
                    returncode, calls = self.start_zenn_unit(unit, service_mocks)
                    self.assertNotEqual(returncode, 0)
                    self.assertEqual(calls, [])

    def git_email_env(self, research_dir):
        global_git = self.work / "git.config"
        global_git.write_text(self.render("dot_config/git/private_config.tmpl",
                                          researchDir=research_dir))
        research_git = self.home / ".config/git/research.config"
        research_git.parent.mkdir(parents=True, exist_ok=True)
        research_git.write_text(self.render("dot_config/git/private_research.config.tmpl"))
        return {**os.environ, "GIT_CONFIG_GLOBAL": str(global_git), "GIT_CONFIG_NOSYSTEM": "1"}

    def git_email(self, repo, env):
        repo.mkdir(parents=True, exist_ok=True)
        run("git", "init", "--quiet", str(repo), env=env)
        return run("git", "-C", str(repo), "config", "user.email", env=env).strip()

    def test_git_uses_research_email_inside_research_directory(self):
        env = self.git_email_env(self.data["researchDir"])
        repo = Path(self.data["researchDir"]) / "project"
        self.assertEqual(self.git_email(repo, env), "research@example.invalid")

    def test_git_uses_personal_email_outside_research_directory(self):
        env = self.git_email_env(self.data["researchDir"])
        self.assertEqual(self.git_email(self.home / "elsewhere", env),
                         "personal@example.invalid")

    def test_git_email_follows_a_changed_research_directory(self):
        moved = self.home / "elsewhere"
        env = self.git_email_env(f"{moved}/")
        self.assertEqual(self.git_email(moved, env), "research@example.invalid")
        self.assertEqual(self.git_email(Path(self.data["researchDir"]) / "project", env),
                         "personal@example.invalid")


if __name__ == "__main__":
    unittest.main()
