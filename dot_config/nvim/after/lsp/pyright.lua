local function has_pep723_metadata(lines)
    local start_idx = nil

    for i, line in ipairs(lines) do
        if line == "# /// script" then
            start_idx = i + 1
            break
        end
    end

    if start_idx == nil then
        return false
    end

    for i = start_idx, #lines do
        if lines[i] == "# ///" then
            return true
        end
    end

    return false
end

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
        local uvx_exists = vim.fn.executable("uvx") == 1
        local has_metadata = has_pep723_metadata(lines)

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
