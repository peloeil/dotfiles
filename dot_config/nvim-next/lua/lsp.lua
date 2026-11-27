vim.diagnostic.config({
    virtual_text = true,
    signs = {
        text = {
            [vim.diagnostic.severity.ERROR] = "",
            [vim.diagnostic.severity.WARN] = "",
            [vim.diagnostic.severity.INFO] = "󰋇",
            [vim.diagnostic.severity.HINT] = "󰌵",
        },
    },
})

vim.pack.add({ "https://github.com/neovim/nvim-lspconfig" })

vim.lsp.config("rust_analyzer", {
    settings = {
        ["rust-analyzer"] = {
            check = {
                command = "clippy",
            },
        },
    },
})

-- LSP の進捗は標準では進捗メッセージにならず、ステータスラインの進捗表示にも出ない
vim.api.nvim_create_autocmd("LspProgress", {
    group = vim.api.nvim_create_augroup("__lsp_progress", { clear = true }),
    callback = function(event)
        local value = event.data.params.value
        local client = vim.lsp.get_client_by_id(event.data.client_id)
        vim.api.nvim_echo({ { value.message or "done" } }, false, {
            id = ("lsp.%d.%s"):format(event.data.client_id, event.data.params.token),
            kind = "progress",
            source = client and client.name or "vim.lsp",
            title = value.title,
            status = value.kind == "end" and "success" or "running",
            percent = value.percentage,
        })
    end,
})

vim.lsp.enable({ "clangd", "lua_ls", "pyright", "rust_analyzer", "zls" })
