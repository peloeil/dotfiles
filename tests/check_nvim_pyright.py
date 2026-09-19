"""Run: python3 tests/check_nvim_pyright.py. Requires Pyright and nvim-lspconfig.

Uses the real language server; uvx is mocked to avoid installing script dependencies.
"""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile


source = Path(__file__).resolve().parents[1]
cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
pyright = shutil.which("pyright-langserver")
assert pyright, "pyright-langserver is required"
with tempfile.TemporaryDirectory(prefix="nvim-pyright-") as temporary:
    work = Path(temporary)
    commands = work / "bin"
    commands.mkdir()
    uvx = commands / "uvx"
    uvx.write_text("#!/bin/sh\nexec " + shlex.quote(pyright) + " --stdio\n")
    uvx.chmod(0o755)
    (work / "pyproject.toml").write_text('[project]\nname="review"\nversion="0.0.0"\n')
    venv = work / ".venv/bin"
    venv.mkdir(parents=True)
    (venv / "python").symlink_to(sys.executable)
    for name in ("plain", "other"):
        (work / f"{name}.py").write_text("answer: int = 42\n")
    for name in ("first", "second"):
        (work / f"{name}.py").write_text(
            f'# /// script\n# dependencies = ["{name}-package"]\n# ///\nanswer = 42\n'
        )
    init = work / "init.lua"
    init.write_text(
        "vim.opt.runtimepath:prepend(" + json.dumps(str(cache / "dpp/repos/github.com/neovim/nvim-lspconfig")) + ")\n"
        "vim.lsp.config('pyright', dofile(" + json.dumps(str(source / "dot_config/nvim/after/lsp/pyright.lua")) + "))\n"
        "vim.lsp.enable('pyright')\n"
    )
    check = work / "check.lua"
    for order in (["plain", "first", "second", "other"], ["second", "first", "other", "plain"]):
        check.write_text("local order = " + "{" + ",".join(map(json.dumps, order)) + "}\n" + """
vim.defer_fn(function()
    local ok, err = pcall(function()
        local clients = {}
        for _, name in ipairs(order) do
            vim.cmd('edit ' .. name .. '.py')
            assert(vim.wait(10000, function()
                local attached = vim.lsp.get_clients({ bufnr = 0 })
                return #attached == 1 and attached[1].initialized
            end), 'Pyright did not attach to ' .. name)
            clients[name] = vim.lsp.get_clients({ bufnr = 0 })[1]
        end
        assert(clients.plain.id == clients.other.id, 'Ordinary files must share their client')
        assert(clients.first.id ~= clients.second.id, 'Different scripts shared an environment')
        for _, name in ipairs({ 'first', 'second' }) do
            local client = clients[name]
            assert(client.id ~= clients.plain.id, 'A script reused the project environment')
            assert(client.config.cmd[1] == 'uvx')
            assert(client.config.cmd[3] == vim.fn.getcwd() .. '/' .. name .. '.py')
            assert(not client.settings.python.pythonPath, 'Project venv overrode script dependencies')
        end
        assert(clients.plain.config.cmd[1] == 'pyright-langserver')
        assert(clients.plain.settings.python.pythonPath == vim.fn.getcwd() .. '/.venv/bin/python')
        for _, name in ipairs(order) do
            vim.cmd('buffer ' .. name .. '.py')
            vim.api.nvim_exec_autocmds('FileType', { buffer = 0 })
            local attached = vim.lsp.get_clients({ bufnr = 0 })
            assert(#attached == 1 and attached[1].id == clients[name].id, 'Client was duplicated')
        end
    end)
    if not ok then print(err); vim.cmd('cquit') else vim.cmd('qall!') end
end, 100)
""")
        result = subprocess.run(
            ["nvim", "--headless", "-i", "NONE", "-u", str(init), "-c", "lua dofile(" + json.dumps(str(check)) + ")"],
            cwd=work, text=True, capture_output=True, timeout=30,
            env=dict(os.environ, PATH=str(commands) + os.pathsep + os.environ["PATH"],
                     XDG_STATE_HOME=str(work / "state"), NVIM_LOG_FILE=str(work / "nvim.log")),
        )
        assert result.returncode == 0, result.stdout + result.stderr

print("OK: Pyright separates script environments in both opening orders and reuses matching clients")
