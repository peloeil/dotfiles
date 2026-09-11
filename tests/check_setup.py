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


print("OK: home paths, mise configuration, standalone Codex detection")
