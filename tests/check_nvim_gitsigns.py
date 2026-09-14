"""Run after applying the Neovim config: python3 tests/check_nvim_gitsigns.py.

Requires the installed Neovim plugins and Markdown parser; uses a temporary Git repo.
"""

import subprocess
import tempfile
from pathlib import Path


with tempfile.TemporaryDirectory(prefix="nvim-gitsigns-") as temporary:
    repo = Path(temporary)

    def run(*args):
        result = subprocess.run(
            args, cwd=repo, text=True, capture_output=True, timeout=20
        )
        assert result.returncode == 0, f"{args}:\n{result.stdout}{result.stderr}"

    run("git", "init", "--quiet")
    document = repo / "sample.md"
    document.write_text("# Example\n\nbefore\n")
    run("git", "add", "sample.md")
    run(
        "git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
        "commit", "--quiet", "-m", "Initial",
    )
    document.write_text("# Example\n\nafter\n")

    check = """
        vim.defer_fn(function()
            local ok, err = pcall(function()
                assert(vim.wait(5000, function()
                    local status = vim.b.gitsigns_status_dict
                    return status and status.changed == 1
                        and vim.treesitter.highlighter.active[vim.api.nvim_get_current_buf()] ~= nil
                end), 'Expected Git change signs and Tree-sitter highlighting')
                assert(#require('gitsigns').get_hunks() == 1, 'Expected one change hunk')
            end)
            if not ok then
                print(err)
                vim.cmd('cquit')
            else
                vim.cmd('qall!')
            end
        end, 0)
    """
    for opening in (["sample.md"], ["-c", "edit sample.md"]):
        run("nvim", "--headless", "-i", "NONE", *opening, "-c", "lua " + check)
    print("OK: Git hunks and Tree-sitter highlighting on startup and :edit")
