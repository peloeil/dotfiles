"""Run: python3 tests/check_nvim_lazy.py. Requires plugins, parsers, Lua LS and Pyright.

Uses the repository config with isolated dpp state, data and test buffers.
"""

import json
import os
import select
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
    # Old installations may link queries into a dpp runtime that was regenerated.
    shutil.copytree(data / "nvim/site", work / "data/nvim/site", ignore_dangling_symlinks=True)
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
    (work / "sample.lua").write_text("local answer = { 42 }\nreturn answer\n")
    (work / "sample.py").write_text("answer: int = 42\n")
    (work / "sample.css").write_text("body { color: #ff0000; }\n")
    (work / "colors.txt").write_text("#ff0000\n")
    (work / "sample.md").write_text("# Example\n\nbefore\n")
    for args in [
        ("init", "--quiet"), ("add", "sample.md"),
        ("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
         "commit", "--quiet", "-m", "Initial"),
    ]:
        subprocess.run(["git", *args], cwd=work, check=True, capture_output=True)
    (work / "sample.md").write_text("# Example\n\nafter\n")
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
assert(not loaded('gitsigns.nvim'), 'Unnamed buffers must not initialize Git monitoring')
assert(not package.loaded['gitsigns.actions'], 'Preview mapping must not defeat internal lazy loading')
for _, name in ipairs({
    'flash.nvim', 'nvim-surround', 'ddu.vim', 'ddc.vim',
    'nvim-lspconfig', 'ddc-source-lsp', 'fidget.nvim', 'tree-sitter-manager.nvim',
    'rainbow-delimiters.nvim', 'indentmini.nvim', 'nvim-colorizer.lua',
}) do
    assert(not loaded(name), name .. ' loaded without being used')
end
assert(#vim.api.nvim_get_autocmds({event='FileType', pattern='ddu-ff'}) == 0)
assert(#vim.api.nvim_get_autocmds({event='FileType', pattern='ddu-filer'}) == 0)
""")

    run("vim.api.nvim_exec_autocmds('UIEnter', {modeline=false})", "", """
local status = vim.api.nvim_eval_statusline(vim.o.statusline, {winid=0})
assert(status.str:find('[No Name]', 1, true), 'Transparent theme broke statusline rendering')
""")

    for opening in [("sample.md",), ("-c", "edit sample.md")]:
        run("", "", """
assert(not loaded('tree-sitter-manager.nvim'), 'Installed parsers need no management UI')
assert(not loaded('nvim-lspconfig') and not loaded('fidget.nvim'))
assert(not loaded('indentmini.nvim'), 'Markdown is excluded from indent guides')
assert(vim.wait(5000, function()
    return vim.treesitter.highlighter.active[vim.api.nvim_get_current_buf()] ~= nil
        and (vim.b.gitsigns_status_dict or {}).changed == 1
end), 'First file lost highlighting or Git signs')
""", *opening)

    run("", "", """
assert(not loaded('tree-sitter-manager.nvim'))
assert(vim.treesitter.highlighter.active[vim.api.nvim_get_current_buf()])
assert(vim.treesitter.query.get('css', 'highlights'), 'Manager queries must remain available')
""", "sample.css")

    run("""
assert(vim.wait(5000, function() return (vim.b.gitsigns_status_dict or {}).changed == 1 end))
vim.api.nvim_win_set_cursor(0, {3, 0})
""", " hp", """
assert(vim.iter(vim.api.nvim_list_wins()):any(function(win)
    return vim.api.nvim_win_get_config(win).relative ~= ''
end), 'First hunk preview did not open')
""", "sample.md")

    for action in [
        "vim.cmd.edit('sample.md')",
        "vim.cmd.edit('new-git.txt')",
        "vim.cmd('file renamed.txt')",
        "vim.api.nvim_buf_set_lines(0, 0, -1, false, {'new'}); vim.cmd('write written.txt')",
    ]:
        run("assert(vim.v.vim_did_enter == 1); assert(not loaded('gitsigns.nvim')); " + action,
            "", """
assert(loaded('gitsigns.nvim'))
assert(vim.wait(5000, function() return vim.b.gitsigns_head ~= nil end), 'Git did not attach')
""")
    for action in ["vim.cmd('Gitsigns toggle_current_line_blame')",
                   "vim.fn.maparg(' hp', 'n', false, true).callback()"]:
        run("assert(not loaded('gitsigns.nvim')); " + action, "", "assert(loaded('gitsigns.nvim'))")

    run("assert(not loaded('tree-sitter-manager.nvim'))", ":TSManager<CR>", """
assert(loaded('tree-sitter-manager.nvim'), 'TSManager must work before opening a file')
""")

    # Mock installation so this check cannot download or build a missing parser.
    parser = work / "data/nvim/site/parser/python.so"
    hidden_parser = work / "python.so.disabled"
    parser.rename(hidden_parser)
    try:
        run("""
package.preload['tree-sitter-manager.installer'] = function()
    return { setup = function() end, install = function(languages)
        if vim.list_contains(languages, 'python') then vim.g.requested_python_parser = true end
    end }
end
vim.cmd.edit('sample.py')
""", "", """
assert(loaded('tree-sitter-manager.nvim'))
assert(vim.g.requested_python_parser, 'Missing parser did not request installation')
""")
    finally:
        hidden_parser.rename(parser)

    run("", "", """
assert(not loaded('rainbow-delimiters.nvim'))
assert(not loaded('indentmini.nvim') and not loaded('nvim-colorizer.lua'))
""", "-c", "help help")

    run("", "", """
assert(not loaded('indentmini.nvim'), 'Plain text is excluded from indent guides')
assert(not loaded('nvim-colorizer.lua') and not loaded('rainbow-delimiters.nvim'))
""", "sample.txt")

    color_check = """
assert(loaded('nvim-colorizer.lua'))
assert(require('colorizer').is_buffer_attached(0))
local ns = vim.api.nvim_get_namespaces().colorizer
assert(vim.wait(3000, function()
    return #vim.api.nvim_buf_get_extmarks(0, ns, 0, -1, {}) > 0
end), 'First buffer is missing color highlights')
"""
    run("", "", color_check, "sample.css")
    run("assert(not loaded('nvim-colorizer.lua'))", "i#ff0000<Esc>", color_check, "new.css")
    run("assert(not loaded('nvim-colorizer.lua'))", ":ColorizerAttachToBuffer<CR>", color_check, "colors.txt")
    run("", "", """
assert(require('colorizer').is_buffer_attached(0))
vim.cmd.edit('sample.txt')
assert(not require('colorizer').is_buffer_attached(0), 'Later plain text must remain excluded')
""", "sample.css")
    run("", "", """
assert(loaded('rainbow-delimiters.nvim') and loaded('indentmini.nvim'))
assert(require('rainbow-delimiters').is_enabled(0), 'Unnamed Lua buffer missed delimiter highlighting')
assert(vim.treesitter.highlighter.active[vim.api.nvim_get_current_buf()])
""", "-c", "lua vim.api.nvim_buf_set_lines(0, 0, -1, false, {'local t = { 1 }'})",
        "-c", "setfiletype lua")

    run("", ":IndentToggle<CR>", "assert(loaded('indentmini.nvim'))")

    for filename, server in [("sample.lua", "lua_ls"), ("sample.py", "pyright")]:
        for opening in [(filename,), ("-c", "edit " + filename)]:
            run("", "", f"""
assert(loaded('nvim-lspconfig') and loaded('fidget.nvim'))
assert(not loaded('ddc.vim'), 'LSP setup must not start completion')
assert(vim.wait(10000, function()
    local clients = vim.lsp.get_clients({{bufnr=0, name='{server}'}})
    return #clients == 1 and clients[1].initialized
end), '{server} did not attach to the first file')
local client = vim.lsp.get_clients({{bufnr=0, name='{server}'}})[1]
assert(client.config.capabilities.textDocument.completion.completionItem.snippetSupport)
""", *opening)

    run("", "i(<Esc>", """
assert(loaded('ddc.vim') and loaded('ddc-source-lsp'))
assert(not loaded('nvim-lspconfig'), 'Completion alone must not configure LSP servers')
assert(vim.api.nvim_get_current_line() == '()', 'First pair insertion failed')
""")

    # Reusing one process would skip the lazy loader after the first motion.
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

    filer_check = """
assert(vim.wait(10000, function() return vim.bo.filetype == 'ddu-filer' end), 'First filer did not open')
"""
    local_check = "assert(vim.fn['denops#_internal#server#proc#is_started']() ~= 0)"
    run("", " e", filer_check + local_check)
    denops = cache / "dpp/repos/vim-denops/denops.vim/denops/@denops-private"
    with (work / "shared-server.log").open("w+") as log:
        server = subprocess.Popen(
            ["deno", "run", "-A", "--no-lock", "--config", str(denops / "deno.jsonc"),
             str(denops / "cli.ts"), "--quiet", "--identity", "--hostname=127.0.0.1", "--port=0"],
            env=env, cwd=work, stdout=subprocess.PIPE, stderr=log, text=True,
        )
        try:
            assert select.select([server.stdout], [], [], 15)[0], 'Shared server did not listen'
            address = server.stdout.readline().strip()
            assert address.startswith('127.0.0.1:'), address
            settings = subprocess.run(
                ["chezmoi", "--source", str(source), "execute-template", "--override-data",
                 json.dumps({"denopsSharedServer": True, "denopsServerPort": int(address.split(':')[1])}),
                 "--file", str(source / "dot_config/nvim/denops-settings.vim.tmpl")],
                check=True, capture_output=True, text=True,
            ).stdout
            (config / "denops-settings.vim").write_text(settings)
            nvim("-c", "DppMakeState")
            run("", " e", filer_check + """
assert(vim.fn['denops#_internal#server#proc#is_started']() == 0, 'Shared connection spawned a local server')
""")
        finally:
            server.terminate()
            server.wait(timeout=10)
        run("", " e", filer_check + local_check)

print("OK: first-use mappings, pickers, syntax/Git display and Lua/Python LSP capabilities")
