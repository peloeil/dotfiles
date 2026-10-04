"""Run with python3 tests/check_setup.py; installers and desktop tools are mocked."""

import json
import os
import shlex
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

    # Both startup paths must expose shims without hiding standalone tools.
    shutil.copyfile(SOURCE / "dot_bashrc", test_home / ".bashrc")
    (test_home / ".bash_profile").write_text(render("dot_bash_profile.tmpl"))
    shims = test_home / ".local/share/mise/shims"
    shims.mkdir(parents=True)
    for executable in (shims / "setup-tool", shims / "standalone", local_bin / "standalone"):
        mock(executable, "exit 0")
    shell_calls = work / "shell-calls"
    mock(
        local_bin / "mise",
        'printf "%s\\n" "$*" >> "$CHECK_LOG"\n'
        'if [ "$2" = bash ]; then\n'
        '  printf \'export PATH="$HOME/.local/share/mise/shims:$PATH"\\n\'\n'
        'fi',
    )
    shell_env = {
        "HOME": str(test_home), "PATH": os.defpath, "DISPLAY": ":test", "TERM": "xterm",
        "CHECK_LOG": str(shell_calls),
    }
    for startup in (".bashrc", ".bash_profile"):
        for interactive in (False, True):
            output = run(
                "bash", "--noprofile", "--norc", "-ic" if interactive else "-c",
                '. "$1"; command -v setup-tool; command -v standalone',
                "check-shell", str(test_home / startup), env=shell_env,
            )
            assert output.splitlines() == [str(shims / "setup-tool"), str(local_bin / "standalone")]
            assert shell_calls.read_text().splitlines() == [
                "activate bash" if interactive else "activate bash --shims"
            ]
            shell_calls.unlink()

    # Assemble concurrently and clean up temporary objects on success and failure.
    if all(shutil.which(tool) for tool in ("fish", "as", "objcopy", "hexdump")):
        sc_tmp = work / "shellcode objects"
        sc_tmp.mkdir()
        fish_cli = [shutil.which("fish"), "--no-config", "-c"]
        fish_config = str(SOURCE / "dot_config/private_fish/config.fish")
        fish_env = {**shell_env, "TMPDIR": str(sc_tmp)}
        processes = [
            subprocess.Popen(
                [*fish_cli, 'source "$argv[1]"; sc "$argv[2]"', fish_config, instruction],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=fish_env,
            )
            for instruction in ("nop", "ret")
        ]
        for process, expected in zip(processes, ("\\x90\n", "\\xc3\n")):
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0 and stdout == expected, (stdout, stderr)
        for command in (
            "sc invalid_instruction",
            "function objcopy; return 23; end; sc nop",
            "function mktemp; return 1; end; sc nop",
        ):
            failed = subprocess.run(
                [*fish_cli, 'source "$argv[1]"; ' + command, fish_config],
                text=True, capture_output=True, env=fish_env,
            )
            assert failed.returncode != 0, failed.stdout + failed.stderr
            assert not list(sc_tmp.iterdir())
    else:
        print("SKIP: shellcode checks need fish, as, objcopy and hexdump")

    containers = tomllib.loads(render("dot_config/containers/containers.conf.tmpl"))
    assert containers["engine"]["compose_providers"] == [
        str(test_home / ".local/share/mise/shims/podman-compose")
    ]
    assert all(
        path.startswith(str(test_home))
        for path in containers["engine"]["helper_binaries_dir"][:2]
    )
    externals = tomllib.loads((SOURCE / ".chezmoiexternal.toml").read_text())
    assert externals[".gef/source"] == {
        "type": "git-repo",
        "url": "https://github.com/bata24/gef.git",
        "refreshPeriod": "24h",
        "clone": {"args": ["--branch", "dev", "--depth", "1"]},
        "pull": {"args": ["--ff-only"]},
    }
    assert (SOURCE / "dot_gef/symlink_gef.py").read_text() == "source/gef.py\n"
    assert (SOURCE / "dot_gdbinit").read_text() == "source ~/.gef/gef.py\n"
    i3 = render("dot_config/i3/config.tmpl")
    assert "/home/sota" not in i3
    for target in (
        "media/pictures/wallpapers/neko.jpg",
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
    repo = test_home / "workspace/university/laboratory/research/project"
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

    denops_script = ".chezmoiscripts/run_onchange_after_26_configure_denops_server.sh.tmpl"
    denops_unit = "dot_config/systemd/user/denops-shared-server.service.tmpl"
    denops_config = "dot_config/nvim/denops-settings.vim.tmpl"
    assert "denops_server_addr" not in render(denops_config)
    service_calls = work / "service-calls"
    service_bin = work / "service-bin"
    service_bin.mkdir()
    mock(service_bin / "systemctl", 'printf "%s\\n" "$*" >> "$CHECK_LOG"')
    service_env = {**os.environ, "PATH": str(service_bin), "CHECK_LOG": str(service_calls)}
    for enabled in (True, False):
        data["denopsSharedServer"] = enabled
        data["denopsServerPort"] = 32124
        script = render(denops_script)
        run("/bin/sh", "-n", input=script)
        run("/bin/sh", input=script, env=service_env)
        calls = service_calls.read_text()
        assert ("enable denops-shared-server.service" in calls) == enabled
        assert ("restart denops-shared-server.service" in calls) == enabled
        assert ("disable --now denops-shared-server.service" in calls) != enabled
        assert ("127.0.0.1:32124" in render(denops_config)) == enabled
        assert '--port=32124' in render(denops_unit)
        assert f'"{test_home}/.local/bin/mise"' in render(denops_unit)
        service_calls.unlink()
    previous = render(denops_script)
    data["denopsServerPort"] = 32125
    assert render(denops_script) != previous  # A hash of the unit template alone misses port changes.
    mock(service_bin / "systemctl", 'exit 1')
    assert 'Skipping Denops service' in run("/bin/sh", input=previous, env=service_env)
    for invalid_port in (0, 70000):
        data["denopsServerPort"] = invalid_port
        invalid = subprocess.run(
            [CHEZMOI, "--config", "/dev/null", "--config-format", "toml", "--source", str(SOURCE),
             "execute-template", "--override-data", json.dumps(data), "--file", str(SOURCE / denops_unit)],
            text=True, capture_output=True,
        )
        assert invalid.returncode != 0 and "denopsServerPort must be" in invalid.stderr
    del data["denopsSharedServer"], data["denopsServerPort"]

    zenn_script = ".chezmoiscripts/run_onchange_after_27_configure_zenn_preview.sh.tmpl"
    default_zenn_script = render(zenn_script)
    mock(service_bin / "systemctl", 'printf "%s\\n" "$*" >> "$CHECK_LOG"')
    for enabled in (True, False):
        data["zennPreview"] = enabled
        script = render(zenn_script)
        assert (script == default_zenn_script) != enabled
        run("/bin/sh", "-n", input=script)
        run("/bin/sh", input=script, env=service_env)
        assert service_calls.read_text().splitlines() == [
            "--user show-environment", "--user daemon-reload",
            *(["--user enable zenn-preview.service", "--user restart zenn-preview.service"]
              if enabled else ["--user disable --now zenn-preview.service"]),
        ]
        service_calls.unlink()
    data["zennPreview"] = True
    mock(service_bin / "systemctl", 'exit 1')
    assert 'Skipping Zenn preview service' in run("/bin/sh", input=render(zenn_script), env=service_env)
    (service_bin / "systemctl").unlink()
    assert 'Skipping Zenn preview service' in run("/bin/sh", input=render(zenn_script), env=service_env)
    del data["zennPreview"]

    # A missing Tailscale IP must never turn into a wildcard preview listener.
    zenn_unit = render("dot_config/systemd/user/zenn-preview.service.tmpl")
    zenn_start = next(line.removeprefix("ExecStart=") for line in zenn_unit.splitlines()
                      if line.startswith("ExecStart="))
    zenn_command = shlex.split(zenn_start.replace("$$", "$"))
    run("/bin/sh", "-n", "-c", zenn_command[-1])
    mock(local_bin / "mise", 'printf "%s\\n" "$@" >> "$CHECK_LOG"')
    mock(service_bin / "tailscale", 'printf "100.64.0.1\\n"')
    run(*zenn_command, env=service_env)
    assert service_calls.read_text().splitlines() == [
        "exec", "--", "node", "node_modules/zenn-cli/dist/server/zenn.js",
        "preview", "--host", "100.64.0.1", "--port", "8000",
    ]
    service_calls.unlink()
    for unavailable in ("exit 1", "exit 0"):
        mock(service_bin / "tailscale", unavailable)
        failed = subprocess.run(zenn_command, env=service_env, capture_output=True)
        assert failed.returncode != 0 and not service_calls.exists()
    (service_bin / "tailscale").unlink()
    failed = subprocess.run(zenn_command, env=service_env, capture_output=True)
    assert failed.returncode != 0 and not service_calls.exists()

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
    notification_script = ".chezmoiscripts/run_onchange_after_31_configure_codex_discord_notify.sh.tmpl"
    notification = render(notification_script)
    assert "skipped" in run("/bin/sh", input=notification, env=env)
    assert not log.exists()
    notification_dir = test_home / ".codex/discord-notify"
    notification_dir.mkdir(parents=True)
    notification_config = notification_dir / "config.json"
    notification_config.write_text("{}")
    mock(commands / "python3", 'printf "%s\\n" "$*" >> "$CHECK_LOG"')
    run("/bin/sh", input=notification, env=env)
    assert log.read_text().splitlines() == [str(notification_dir / "install.py")]
    log.unlink()
    notification_config.unlink()
    (commands / "python3").unlink()
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

    for relative in (
        Path(notification_script),
        Path("dot_codex/private_discord-notify/notify.py"),
        Path("dot_codex/private_discord-notify/install.py"),
    ):
        (changed_source / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / relative, changed_source / relative)
    original_notification = render(notification_script, changed_source)
    with (changed_source / "dot_codex/private_discord-notify/notify.py").open("a") as stream:
        stream.write("\n# Changed notification code\n")
    assert render(notification_script, changed_source) != original_notification

    zenn_unit_source = Path("dot_config/systemd/user/zenn-preview.service.tmpl")
    for relative in (Path(zenn_script), zenn_unit_source):
        (changed_source / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / relative, changed_source / relative)
    original_zenn = render(zenn_script, changed_source)
    with (changed_source / zenn_unit_source).open("a") as stream:
        stream.write("\n# Changed service definition\n")
    assert render(zenn_script, changed_source) != original_zenn

    # Use the same .xprofile before and after picom appears; no template re-render.
    xprofile = "fcitx5() { :; }\nxinput() { return 1; }\nsleep() { :; }\n"
    xprofile += (SOURCE / "dot_xprofile").read_text() + "\nwait\n"
    run("/bin/sh", input=xprofile, env=env)
    assert not log.exists()
    mock(commands / "picom", 'printf "%s\\n" "$*" >> "$CHECK_LOG"')
    run("/bin/sh", input=xprofile, env=env)
    assert log.read_text().strip() == "-b"
    log.unlink()

    # Missing desktop data must keep the existing desktop configuration.
    prereqs = ".chezmoiscripts/run_once_before_00_install_prereqs.sh.tmpl"
    desktop_sources = (
        ".chezmoiignore",
        "dot_bash_profile.tmpl",
        prereqs,
    )
    defaults = {relative: render(relative) for relative in desktop_sources}
    managed = {}
    mock(commands / "sudo", 'if [ "$1" != -v ]; then "$@"; fi')
    for desktop in (True, False):
        data["desktop"] = desktop
        rendered = {relative: render(relative) for relative in desktop_sources}
        if desktop:
            assert rendered == defaults
        assert ("exec startx" in rendered["dot_bash_profile.tmpl"]) == desktop

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
            assert all(package in calls for package in ("curl", "gdb", "git", "binutils"))
            if manager == "pacman":
                assert calls.startswith("-S --noconfirm --needed ")
            assert (desktop_package in calls) == desktop
            assert ("xclip" in calls) == desktop
            assert ("fcitx" in calls) == desktop
            log.unlink()
            (commands / manager).unlink()

        # Test the documented init flag, persistence, and real target selection.
        desktop_work = work / f"desktop-{desktop}"
        desktop_work.mkdir()
        config_path = desktop_work / "chezmoi.toml"
        cli = (
            CHEZMOI,
            "--source",
            str(SOURCE),
            "--destination",
            str(test_home),
            "--config",
            str(config_path),
            "--cache",
            str(desktop_work / "cache"),
            "--persistent-state",
            str(desktop_work / "state.boltdb"),
            "--no-tty",
        )
        run(
            *cli,
            "init",
            "--promptDefaults",
            *(
                ["--promptBool", "Install desktop environment=false"]
                if not desktop
                else []
            ),
            "--promptString",
            "Enter your research Git email address=research@example.invalid",
        )
        assert tomllib.loads(config_path.read_text())["data"]["desktop"] is desktop
        assert tomllib.loads(config_path.read_text())["data"]["denopsSharedServer"] is False
        assert tomllib.loads(config_path.read_text())["data"]["zennPreview"] is False
        run(*cli, "init", "--promptDefaults")
        assert tomllib.loads(config_path.read_text())["data"]["desktop"] is desktop
        original_config = config_path.read_text()
        config_path.write_text(original_config.replace("denopsSharedServer = false", "denopsSharedServer = true")
                               .replace("denopsServerPort = 32123", "denopsServerPort = 32124")
                               .replace("zennPreview = false", "zennPreview = true"))
        run(*cli, "init", "--promptDefaults")
        saved_data = tomllib.loads(config_path.read_text())["data"]
        assert saved_data["denopsSharedServer"] is True and saved_data["denopsServerPort"] == 32124
        assert saved_data["zennPreview"] is True
        config_path.write_text(original_config)
        managed[desktop] = set(run(*cli, "managed").splitlines())
        assert ".codex/discord-notify/config.json" not in managed[desktop]

        run(*cli, "diff")
        run(*cli, "apply", "--dry-run")

    # Shared defaults must preserve local state, including integer-valued UI records.
    codex_config = test_home / ".codex/config.toml"
    codex_cli = (*cli, "--override-data", json.dumps(data))
    codex_config.write_text('[tui]\nfullscreen_transcript = true\n')
    run(*codex_cli, "apply", str(codex_config))
    codex = tomllib.loads(codex_config.read_text())
    assert codex["features"]["fast_mode"] is False and "service_tier" not in codex
    assert codex["approval_policy"] == "never" and codex["sandbox_mode"] == "danger-full-access"
    assert codex["tui"]["fullscreen_transcript"] is False
    assert codex["notify"] == ["python3", str(test_home / ".codex/discord-notify/notify.py"), "complete"]
    assert "/home/sota" not in codex_config.read_text()
    assert codex_config.stat().st_mode & 0o777 == 0o600
    assert not run(*codex_cli, "diff", str(codex_config))

    codex_config.write_text(
        'service_tier = "fast"\n'
        '[features]\nfast_mode = true\nhooks = false\n'
        '[projects."/local/project"]\ntrust_level = "untrusted"\n'
        '[hooks.state.local]\ntrusted_hash = "sha256:test"\n'
        '[plugins."local@example"]\nenabled = false\n'
        '[tui]\nfullscreen_transcript = true\nscreen_reader_detection_done = true\n'
        '[tui.model_availability_nux]\n"example-model" = 4\n'
    )
    run(*codex_cli, "apply", str(codex_config))
    codex = tomllib.loads(codex_config.read_text())
    assert codex["features"] == {"fast_mode": False, "hooks": True}
    assert codex["service_tier"] == "fast"
    assert codex["projects"]["/local/project"]["trust_level"] == "untrusted"
    assert codex["hooks"]["state"]["local"]["trusted_hash"] == "sha256:test"
    assert codex["plugins"]["local@example"]["enabled"] is False
    assert codex["tui"]["fullscreen_transcript"] is False
    assert codex["tui"]["screen_reader_detection_done"] is True
    hint = codex["tui"]["model_availability_nux"]["example-model"]
    assert type(hint) is int and hint == 4
    applied = codex_config.read_bytes()
    run(*codex_cli, "apply", str(codex_config))
    assert codex_config.read_bytes() == applied
    assert not run(*codex_cli, "diff", str(codex_config))

    # Migrate the old file-only link and keep supporting documents reachable.
    shared_skill = test_home / ".agents/skills/commit"
    claude_skill = test_home / ".claude/skills/commit"
    claude_skill.mkdir(parents=True)
    (claude_skill / "SKILL.md").symlink_to("../../../.agents/skills/commit/SKILL.md")
    run(*cli, "apply", "--parent-dirs", str(shared_skill), str(claude_skill))
    assert claude_skill.is_symlink() and claude_skill.resolve() == shared_skill
    for relative in (
        "SKILL.md",
        "references/examples.md",
        "references/research.md",
        "evals/cases.md",
    ):
        assert (claude_skill / relative).read_bytes() == (
            SOURCE / "dot_agents/skills/commit" / relative
        ).read_bytes()
    run(*cli, "apply", str(shared_skill), str(claude_skill))
    assert not run(*cli, "diff", str(shared_skill), str(claude_skill))

    # Retire only the two distributed sandbox files, preserving local siblings.
    retired = [test_home / relative for relative in (
        ".local/bin/claude-sandbox", ".local/share/claude-sandbox/Dockerfile",
    )]
    for path in retired:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("old sandbox file\n")
    local_note = retired[1].with_name("local-note")
    local_note.write_text("keep\n")
    run(*cli, "apply", "--include", "remove")
    assert not any(path.exists() for path in retired)
    assert local_note.read_text() == "keep\n"
    run(*cli, "apply", "--include", "remove")

    for invalid_desktop in ("false", 0, None):
        invalid = subprocess.run(
            (*cli, "--override-data", json.dumps({"desktop": invalid_desktop}), "managed"),
            text=True,
            capture_output=True,
            check=False,
        )
        assert invalid.returncode != 0 and "desktop must be true or false" in invalid.stderr

    gui_targets = (
        ".xinitrc",
        ".xprofile",
        ".config/alacritty",
        ".config/fcitx5",
        ".config/flameshot",
        ".config/i3",
        ".config/picom",
        ".config/polybar",
        ".config/sunshine",
        ".chezmoiscripts/20_install_hack_nerd_font.sh",
    )
    assert managed[False] == {
        path
        for path in managed[True]
        if not any(path == gui or path.startswith(gui + "/") for gui in gui_targets)
    }
    assert all(gui in managed[True] for gui in gui_targets)
    assert {
        ".config/mise/config.toml",
        ".gdbinit",
        ".gef/gef.py",
        ".config/nvim/init.lua",
        ".config/containers/containers.conf",
        ".codex/AGENTS.md",
        ".claude/settings.json",
        ".chezmoiscripts/25_install_nvim_plugins.sh",
        ".chezmoiscripts/30_install_ai_plugins.sh",
        ".chezmoiscripts/31_configure_codex_discord_notify.sh",
        ".codex/discord-notify/notify.py",
        ".codex/discord-notify/config.example.json",
    } <= managed[False]

print(
    "OK: shell startup, shellcode cleanup, sandbox removal, home paths, repository email, CLI detection, mise changes, GDB/GEF setup, picom startup, desktop setup, shared commit skill"
)
