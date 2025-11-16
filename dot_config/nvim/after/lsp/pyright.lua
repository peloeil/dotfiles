return {
    cmd = function(dispatchers)
        local bufnr = vim.api.nvim_get_current_buf()
        local filename = vim.api.nvim_buf_get_name(bufnr)
        local lines = vim.api.nvim_buf_get_lines(bufnr, 0, 100, false)
        local content = table.concat(lines, "\n")

        local uvx_exists = vim.fn.executable("uvx") == 1
        local has_metadata = content:find("# /// script\n.*# ///") ~= nil

        local cmd
        if uvx_exists and has_metadata then
            cmd = {
                "uvx",
                "--with-requirements",
                filename,
                "--quiet",
                "--from",
                "pyright",
                "pyright-langserver",
                "--stdio",
            }
        else
            cmd = { "pyright-langserver", "--stdio" }
        end

        return vim.lsp.rpc.start(cmd, dispatchers)
    end,
}
