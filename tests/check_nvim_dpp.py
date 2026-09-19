"""Run: python3 tests/check_nvim_dpp.py. Requires installed dpp/Denops plugins.

Uses isolated configuration/state and existing plugin checkouts; installs nothing.
"""

import json
import os
from pathlib import Path
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

print("OK: dpp state generation can retry after errors through saves and DppMakeState")
