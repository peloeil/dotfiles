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

local function command(bufnr)
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
    return cmd
end

return {
    on_init = function(client)
        if not client.root_dir or client.config.cmd[1] == "uvx" then
            return
        end
        local venv_python = client.root_dir .. "/.venv/bin/python"
        if vim.uv.fs_stat(venv_python) then
            client.settings = vim.tbl_deep_extend("force", client.settings, {
                python = { pythonPath = venv_python },
            })
        end
    end,
    reuse_client = function(client, config, bufnr)
        return client.name == config.name
            and not client:is_stopped()
            and client.root_dir == config.root_dir
            and vim.deep_equal(client.config.cmd, command(bufnr))
    end,
    cmd = function(dispatchers, config)
        -- Retain the resolved command so reuse checks include the script path.
        config.cmd = command(vim.api.nvim_get_current_buf())
        return vim.lsp.rpc.start(config.cmd, dispatchers)
    end,
}
