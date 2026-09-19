"""Run: python3 tests/check_nvim_lazy.py. Requires installed plugins and parsers.

Uses the repository config with isolated dpp state, data and test buffers.
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
data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
with tempfile.TemporaryDirectory(prefix="nvim-lazy-") as temporary:
    work = Path(temporary)
    config = work / "config/nvim"
    shutil.copytree(source / "dot_config/nvim", config)
    shutil.copytree(data / "nvim/site", work / "data/nvim/site")
    for toml in config.glob("toml/*.toml"):
        for plugin in tomllib.loads(toml.read_text())["plugins"]:
            for relative in (plugin["repo"], "github.com/" + plugin["repo"]):
                installed = cache / "dpp/repos" / relative
                if not installed.is_dir():
                    continue
                target = work / "cache/dpp/repos" / relative
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to(installed, target_is_directory=True)
            assert (work / "cache/dpp/repos/github.com" / plugin["repo"]).is_dir(), plugin["repo"]
    env = dict(
        os.environ,
        XDG_CONFIG_HOME=str(work / "config"),
        XDG_CACHE_HOME=str(work / "cache"),
        XDG_DATA_HOME=str(work / "data"),
        XDG_STATE_HOME=str(work / "state"),
        DENO_DIR=os.environ.get("DENO_DIR", str(cache / "deno")),
        NVIM_LOG_FILE=str(work / "nvim.log"),
    )

    def nvim(*args):
        result = subprocess.run(
            ["nvim", "--headless", "-i", "NONE", *args],
            cwd=work, env=env, text=True, capture_output=True, timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    nvim("-c", "DppMakeState")
    (work / "sample.txt").write_text("hello x world x more\n")
    check = work / "check.lua"

    def run(before, keys, after, *args):
        check.write_text("""
local function loaded(name)
    local sourced = vim.fn['dpp#get'](name).sourced
    return sourced == true or sourced == 1
end
local function checked(fn)
    local ok, err = pcall(fn)
    if not ok then print(err); vim.cmd('cquit') end
end
vim.defer_fn(function()
    checked(function()
""" + before + """
        vim.defer_fn(function()
            checked(function()
""" + after + """
                local messages = vim.api.nvim_exec2('messages', { output = true }).output
                assert(not messages:match('E%d+:') and not messages:find('Error'), messages)
                vim.cmd('qall!')
            end)
        end, 500)
        vim.api.nvim_input(vim.api.nvim_replace_termcodes(""" + json.dumps(keys) + """, true, false, true))
    end)
end, 100)
""")
        nvim(*args, "-c", "lua dofile(" + json.dumps(str(check)) + ")")

    run("", "", """
assert(loaded('gitsigns.nvim'), 'Gitsigns must retain its own lazy-loading behavior')
for _, name in ipairs({'flash.nvim', 'nvim-surround', 'ddu.vim', 'ddc.vim'}) do
    assert(not loaded(name), name .. ' loaded without being used')
end
assert(#vim.api.nvim_get_autocmds({event='FileType', pattern='ddu-ff'}) == 0)
assert(#vim.api.nvim_get_autocmds({event='FileType', pattern='ddu-filer'}) == 0)
""")

    # Each operation starts in a fresh process, exercising the first-use loader.
    for keys, expected in [
        ("fx;,", "assert(vim.api.nvim_win_get_cursor(0)[2] == 6)"),
        ("2fx", "assert(vim.api.nvim_win_get_cursor(0)[2] == 14)"),
        ("dfx", "assert(vim.api.nvim_get_current_line() == ' world x more')"),
        ("cfxZ<Esc>", "assert(vim.api.nvim_get_current_line() == 'Z world x more')"),
        ("vfx", "assert(vim.fn.mode() == 'v' and vim.api.nvim_win_get_cursor(0)[2] == 6)"),
        ("swo<CR>", "assert(vim.api.nvim_win_get_cursor(0)[2] == 8)"),
    ]:
        run("assert(not loaded('flash.nvim'))", keys,
            "assert(loaded('flash.nvim'))\n" + expected, "sample.txt")

    for keys, expected in [
        ("ysiw)", "(hello) x world x more"),
        ("viwS)", "(hello) x world x more"),
        ("i<C-g>s)A<Esc>", "(A)hello x world x more"),
    ]:
        run("assert(not loaded('nvim-surround'))", keys,
            "assert(loaded('nvim-surround'))\n"
            "assert(vim.api.nvim_get_current_line() == " + json.dumps(expected) + ")", "sample.txt")

    for key, name, ft in [
        ("e", "filer", "ddu-filer"),
        ("ff", "ff_file", "ddu-ff"),
        ("fg", "ff_grep", "ddu-ff"),
        ("fb", "ff_buffer", "ddu-ff"),
        ("fh", "ff_help", "ddu-ff"),
        ("ld", "lsp_definition", "ddu-ff"),
        ("ls", "lsp_documentSymbol", "ddu-ff"),
    ]:
        run("assert(not loaded('ddu.vim'))", " " + key, f"""
assert(vim.wait(10000, function() return vim.bo.filetype == '{ft}' end), '{name} did not open')
assert(vim.b.ddu_ui_name == '{name}')
local close = vim.fn.maparg('q', 'n', false, true)
assert(close.buffer == 1, 'First picker missed its buffer mappings')
vim.api.nvim_feedkeys('q', 'xt', false)
assert(vim.wait(5000, function() return vim.bo.filetype ~= '{ft}' end), '{name} did not close')
""", "sample.txt")

print("OK: lazy first-use mappings preserve Flash motions, surround modes and all DDU pickers")
