"""Run: python3 tests/check_nvim_dpp.py. Requires installed dpp/Denops plugins.

Uses isolated configuration/state and existing plugin checkouts; installs nothing.
"""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib


source = Path(__file__).resolve().parents[1]
cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
with tempfile.TemporaryDirectory(prefix="nvim-dpp-") as temporary:
    work = Path(temporary)
    config = work / "config/nvim"
    shutil.copytree(source / "dot_config/nvim", config)
    for name in ("no_lazy", "lazy", "ddu", "ddc"):
        (config / "toml" / f"{name}.toml").write_text("plugins = []\n")
    for plugin in tomllib.loads((config / "toml/dpp.toml").read_text())["plugins"]:
        for relative in (plugin["repo"], "github.com/" + plugin["repo"]):
            installed = cache / "dpp/repos" / relative
            assert installed.is_dir(), f"Missing installed plugin: {installed}"
            target = work / "cache/dpp/repos" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(installed, target_is_directory=True)
    env = dict(
        os.environ,
        XDG_CONFIG_HOME=str(work / "config"),
        XDG_CACHE_HOME=str(work / "cache"),
        XDG_STATE_HOME=str(work / "state"),
        DENO_DIR=os.environ.get("DENO_DIR", str(cache / "deno")),
        NVIM_LOG_FILE=str(work / "nvim.log"),
    )

    def run(*args):
        result = subprocess.run(
            ["nvim", "--headless", "-i", "NONE", *args],
            cwd=work, env=env, text=True, capture_output=True, timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result

    run("-c", "DppMakeState")
    check = work / "check.lua"
    check.write_text("""
vim.defer_fn(function()
    local ok, err = pcall(function()
        local config = vim.env.XDG_CONFIG_HOME .. '/nvim/config.ts'
        local original = vim.fn.readfile(config)
        local buffer = vim.fn.bufadd(config)
        local completed = 0
        vim.api.nvim_create_autocmd('User', {
            pattern = 'Dpp:makeStatePost',
            callback = function() completed = completed + 1 end,
        })
        local function save(lines)
            vim.fn.writefile(lines, config)
            vim.api.nvim_exec_autocmds('BufWritePost', { buffer = buffer })
        end
        local function fail_build(marker)
            save({ 'throw new Error("' .. marker .. '");' })
            assert(vim.wait(10000, function()
                return vim.api.nvim_exec2('messages', { output = true }).output:find(marker, 1, true)
            end), 'Expected the asynchronous config error')
        end
        fail_build('DPP_SAVE_RETRY_TEST')
        save(original)
        assert(vim.wait(10000, function() return completed == 1 end), 'Save did not retry')
        fail_build('DPP_COMMAND_RETRY_TEST')
        vim.fn.writefile(original, config)
        vim.cmd('DppMakeState')
    end)
    if not ok then print(err); vim.cmd('cquit') end
end, 100)
""")
    run("-c", "lua dofile(" + json.dumps(str(check)) + ")")
    assert (work / "cache/dpp/nvim/state.vim").is_file()

    # Run the installer's exact autocmds with Git failures confined to this cache.
    script = (source / ".chezmoiscripts/run_onchange_after_25_install_nvim_plugins.sh.tmpl").read_text()
    args = []
    for command in re.findall(r"--cmd '([^']+)'", script):
        args.extend(["--cmd", command])
    run(*args)  # Already installed: success without downloads.
    (config / "toml/no_lazy.toml").write_text(
        '[[plugins]]\nrepo = "audit-test/unavailable-plugin"\n'
    )
    run("-c", "DppMakeState")
    commands = work / "bin"
    commands.mkdir()
    git = commands / "git"
    git.write_text("#!/bin/sh\necho 'Simulated offline clone failure' >&2\nexit 23\n")
    git.chmod(0o755)
    env["PATH"] = str(commands) + os.pathsep + env["PATH"]
    result = subprocess.run(
        ["nvim", "--headless", "-i", "NONE", *args],
        cwd=work, env=env, text=True, capture_output=True, timeout=30,
    )
    assert "Failed plugins" in result.stdout + result.stderr
    assert result.returncode != 0, "Plugin installation failure was reported as success"
    assert not (work / "cache/dpp/repos/github.com/audit-test/unavailable-plugin").exists()

print("OK: dpp retries after config errors; installer distinguishes success and clone failure")
