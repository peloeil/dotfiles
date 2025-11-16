return {
    cmd = function(dispatchers)
        local bufnr = vim.api.nvim_get_current_buf()
        local filename = vim.api.nvim_buf_get_name(bufnr)
        local max_lines = 100

        local lines
        if vim.api.nvim_buf_is_loaded(bufnr) then
            lines = vim.api.nvim_buf_get_lines(bufnr, 0, max_lines, false)
        else
            local ok, disk_lines = pcall(vim.fn.readfile, filename, "", max_lines)
            lines = ok and disk_lines or {}
        end

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
