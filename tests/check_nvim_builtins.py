"""Run: python3 tests/check_nvim_builtins.py. Tests real runtime file handlers."""

import gzip
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import zipfile


source = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="nvim-builtins-") as temporary:
    work = Path(temporary)
    init = work / "init.lua"
    init.write_text("dofile(" + json.dumps(str(source / "dot_config/nvim/lua/builtin_plugins.lua")) + ")\n")
    (work / "plain.txt").write_text("original\n")
    with gzip.open(work / "sample.txt.gz", "wt") as stream:
        stream.write("compressed\n")
    with tarfile.open(work / "sample.tar.gz", "w:gz") as archive:
        archive.add(work / "plain.txt", arcname="plain.txt")
    with zipfile.ZipFile(work / "sample.zip", "w") as archive:
        archive.write(work / "plain.txt", arcname="plain.txt")

    def check(body, *args):
        script = work / "check.lua"
        script.write_text("""
vim.defer_fn(function()
    local ok, err = pcall(function()
""" + body + """
    end)
    if not ok then print(err); vim.cmd('cquit') else vim.cmd('qa!') end
end, 20)
""")
        result = subprocess.run(
            ["nvim", "--headless", "-i", "NONE", "-u", str(init), *args,
             "-c", "luafile " + str(script)], cwd=work, capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    check("""
assert(vim.fn.exists('#FileExplorer') == 0)
for _, cmd in ipairs({'Man', 'Tutor', 'UpdateRemotePlugins'}) do assert(vim.fn.exists(':' .. cmd) == 0) end
assert(vim.o.shada ~= '')
vim.fn.setreg('a', 'saved register')
vim.cmd('wshada! history.shada')
vim.fn.setreg('a', '')
vim.cmd('rshada! history.shada')
assert(vim.fn.getreg('a') == 'saved register')
""")
    for args, action in [(('.',), ''), ((), "vim.cmd.edit('.')"), ((), "vim.cmd('Ex')"), ((), "vim.cmd('Vexplore')")]:
        check(action + "\nassert(vim.bo.filetype == 'netrw'); assert(vim.fn.search('plain.txt', 'nw') > 0)", *args)
    check("assert(vim.api.nvim_get_current_line() == 'original')", "file://" + str(work / "plain.txt"))
    check("vim.cmd.edit('file://" + str(work / "plain.txt") + "'); assert(vim.api.nvim_get_current_line() == 'original')")
    for name, ft in [('sample.tar.gz', 'tar'), ('sample.zip', 'zip')]:
        for args, action in [((name,), ''), ((), "vim.cmd.edit('" + name + "')")]:
            check(action + "\nassert(vim.bo.filetype == '" + ft + "'); assert(vim.fn.search('plain.txt', 'nw') > 0)", *args)
    check("assert(vim.api.nvim_get_current_line() == 'compressed')", 'sample.txt.gz')
    check("""
vim.cmd.edit('sample.txt.gz')
assert(vim.api.nvim_get_current_line() == 'compressed')
vim.api.nvim_set_current_line('changed')
vim.cmd.write()
""")
    with gzip.open(work / "sample.txt.gz", "rt") as stream:
        assert stream.read() == "changed\n"

print("OK: optional runtime plugins, ShaDa history, first directory/URL/archive opens and gzip writes")
