"""Run with python3 tests/check_setup.py; installers and desktop tools are mocked."""

import json
import os
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
CHEZMOI = shutil.which("chezmoi")
assert CHEZMOI, "chezmoi is required"


def run(*args, **kwargs):
    result = subprocess.run(args, text=True, capture_output=True, check=False, **kwargs)
    assert result.returncode == 0, f"{args}:\n{result.stdout}{result.stderr}"
    return result.stdout


def mock(path, body):
    path.write_text("#!/bin/sh\n" + body + "\n")
    path.chmod(0o755)


with tempfile.TemporaryDirectory(prefix="chezmoi-check-") as temporary:
    work = Path(temporary)
    test_home = work / "home with spaces"
    local_bin = test_home / ".local/bin"
    local_bin.mkdir(parents=True)
    data = {
        "chezmoi": {"homeDir": str(test_home), "os": "linux", "hostname": "test"},
        "email": "personal@example.invalid",
        "researchEmail": "research@example.invalid",
        "name": "Test User",
    }

    def render(relative, source=SOURCE):
        return run(
            CHEZMOI,
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(source),
            "execute-template",
            "--override-data",
            json.dumps(data),
            "--file",
            str(source / relative),
        )

    containers = tomllib.loads(render("dot_config/containers/containers.conf.tmpl"))
    assert containers["engine"]["compose_providers"] == [
        str(test_home / ".local/share/mise/shims/podman-compose")
    ]
    assert all(
        path.startswith(str(test_home))
        for path in containers["engine"]["helper_binaries_dir"][:2]
    )
    i3 = render("dot_config/i3/config.tmpl")
    assert "/home/sota" not in i3
    for target in (
        "pictures/neko.jpg",
        ".config/i3/polybar.sh",
        ".config/i3/monitor-hotplug.sh",
    ):
        assert f'"{test_home / target}"' in i3
    if i3_binary := shutil.which("i3"):
        i3_config = work / "i3.config"
        i3_config.write_text(i3)
        run(i3_binary, "-C", "-c", str(i3_config))

    global_git = work / "git.config"
    global_git.write_text(render("dot_config/git/private_config.tmpl"))
    research_git = test_home / ".config/git/research.config"
    research_git.parent.mkdir(parents=True)
    research_git.write_text(render("dot_config/git/private_research.config.tmpl"))
    git_env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": str(global_git),
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    repo = test_home / "workspace/univ/lab/research/project"
    repo.mkdir(parents=True)
    run("git", "init", "--quiet", str(repo), env=git_env)
    assert (
        run("git", "-C", str(repo), "config", "user.email", env=git_env).strip()
        == "research@example.invalid"
    )
    moved_repo = test_home / "elsewhere"
    repo.rename(moved_repo)
    assert (
        run("git", "-C", str(moved_repo), "config", "user.email", env=git_env).strip()
        == "personal@example.invalid"
    )
    data["researchDir"] = str(moved_repo) + "/"
    global_git.write_text(render("dot_config/git/private_config.tmpl"))
    assert (
        run("git", "-C", str(moved_repo), "config", "user.email", env=git_env).strip()
        == "research@example.invalid"
    )

    commands = work / "commands"
    commands.mkdir()
    (commands / "sh").symlink_to("/bin/sh")
    log = work / "calls"
    env = {**os.environ, "PATH": str(commands), "CHECK_LOG": str(log)}
    mock(local_bin / "mise", "exit 1")  # No mise-managed Codex or Claude.
    mock(local_bin / "codex", 'printf "%s\\n" "$*" >> "$CHECK_LOG"')
    plugins = render(".chezmoiscripts/run_onchange_after_30_install_ai_plugins.sh.tmpl")
    run("/bin/sh", input=plugins, env=env)
    assert log.read_text().splitlines() == [
        "plugin marketplace add DietrichGebert/ponytail",
        "plugin add ponytail@ponytail",
    ]
    log.unlink()
    (local_bin / "codex").unlink()
    run("/bin/sh", input=plugins, env=env)
    assert not log.exists()

    install_mise = render(".chezmoiscripts/run_once_before_01-install-mise.sh.tmpl")
    run("/bin/sh", input=install_mise, env=env)
    (local_bin / "mise").unlink()
    mock(
        commands / "mise", "exit 0"
    )  # Another mise on PATH must not hide the missing local binary.
    mock(commands / "curl", 'printf "%s\\n" "$*" >> "$CHECK_LOG"\nprintf "true\\n"')
    run("/bin/sh", input=install_mise, env=env)
    assert log.read_text().strip() == "-fsSL https://mise.run"
    log.unlink()

    changed_source = work / "source"
    installer = Path(".chezmoiscripts/run_onchange_after_10_install_mise_tools.sh.tmpl")
    config = Path("dot_config/mise/config.toml")
    for relative in (installer, config):
        (changed_source / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / relative, changed_source / relative)
    original = render(installer, changed_source)
    with (changed_source / config).open("a") as stream:
        stream.write("\n# Changed configuration\n")
    assert render(installer, changed_source) != original

    # Use the same .xprofile before and after picom appears; no template re-render.
    xprofile = "fcitx5() { :; }\nxinput() { return 1; }\nsleep() { :; }\n"
    xprofile += (SOURCE / "dot_xprofile").read_text() + "\nwait\n"
    run("/bin/sh", input=xprofile, env=env)
    assert not log.exists()
    mock(commands / "picom", 'printf "%s\\n" "$*" >> "$CHECK_LOG"')
    run("/bin/sh", input=xprofile, env=env)
    assert log.read_text().strip() == "-b"
    log.unlink()

    # Missing profile data must keep the existing full configuration.
    prereqs = ".chezmoiscripts/run_once_before_00_install_prereqs.sh.tmpl"
    profile_sources = (
        ".chezmoiignore",
        "dot_bash_profile.tmpl",
        "dot_config/tmux/tmux.conf.tmpl",
        prereqs,
    )
    legacy = {relative: render(relative) for relative in profile_sources}
    managed = {}
    mock(commands / "sudo", 'if [ "$1" != -v ]; then "$@"; fi')
    for profile in ("full", "minimal"):
        data["profile"] = profile
        rendered = {relative: render(relative) for relative in profile_sources}
        if profile == "full":
            assert rendered == legacy
        assert ("exec startx" in rendered["dot_bash_profile.tmpl"]) == (
            profile == "full"
        )
        assert ("xclip" in rendered["dot_config/tmux/tmux.conf.tmpl"]) == (
            profile == "full"
        )
        run("bash", "-n", input=rendered["dot_bash_profile.tmpl"])
        for script in (SOURCE / ".chezmoiscripts").iterdir():
            content = (
                render(script.relative_to(SOURCE))
                if script.suffix == ".tmpl"
                else script.read_text()
            )
            run("/bin/sh", "-n", input=content)

        # Exercise each distro branch without sudo, package installs, or network.
        for manager, desktop_package in (
            ("apt-get", "xserver-xorg"),
            ("pacman", "xorg-server"),
            ("emerge", "x11-base/xorg-server"),
        ):
            mock(commands / manager, 'printf "%s\\n" "$*" >> "$CHECK_LOG"')
            run("/bin/sh", input=rendered[prereqs], env=env)
            calls = log.read_text()
            assert "curl" in calls and "git" in calls and "binutils" in calls
            assert (desktop_package in calls) == (profile == "full")
            assert ("xclip" in calls) == (profile == "full")
            assert ("fcitx" in calls) == (profile == "full")
            log.unlink()
            (commands / manager).unlink()

        # Test the documented init flag, persistence, and real target selection.
        profile_work = work / profile
        profile_work.mkdir()
        config_path = profile_work / "chezmoi.toml"
        cli = (
            CHEZMOI,
            "--source",
            str(SOURCE),
            "--destination",
            str(test_home),
            "--config",
            str(config_path),
            "--cache",
            str(profile_work / "cache"),
            "--persistent-state",
            str(profile_work / "state.boltdb"),
            "--no-tty",
        )
        run(
            *cli,
            "init",
            "--promptDefaults",
            *(
                ["--promptChoice", "Install profile=minimal"]
                if profile == "minimal"
                else []
            ),
            "--promptString",
            "Enter your research Git email address=research@example.invalid",
        )
        assert tomllib.loads(config_path.read_text())["data"]["profile"] == profile
        run(*cli, "init", "--promptDefaults")
        assert tomllib.loads(config_path.read_text())["data"]["profile"] == profile
        managed[profile] = set(run(*cli, "managed").splitlines())
        run(*cli, "diff")
        run(*cli, "apply", "--dry-run")

    invalid = subprocess.run(
        (*cli, "--override-data", '{"profile":"typo"}', "managed"),
        text=True,
        capture_output=True,
        check=False,
    )
    assert (
        invalid.returncode != 0 and "profile must be full or minimal" in invalid.stderr
    )

    gui_targets = (
        ".xinitrc",
        ".xprofile",
        ".config/alacritty",
        ".config/fcitx5",
        ".config/i3",
        ".config/picom",
        ".config/polybar",
        ".config/sunshine",
        ".chezmoiscripts/20_install_hack_nerd_font.sh",
    )
    assert managed["minimal"] == {
        path
        for path in managed["full"]
        if not any(path == gui or path.startswith(gui + "/") for gui in gui_targets)
    }
    assert all(gui in managed["full"] for gui in gui_targets)
    assert {
        ".config/mise/config.toml",
        ".config/nvim/init.lua",
        ".config/containers/containers.conf",
        ".codex/AGENTS.md",
        ".claude/settings.json",
        ".local/bin/claude-sandbox",
        ".chezmoiscripts/25_install_nvim_plugins.sh",
        ".chezmoiscripts/30_install_ai_plugins.sh",
    } <= managed["minimal"]

print(
    "OK: home paths, repository email, CLI detection, mise changes, picom startup, full/minimal setup"
)
