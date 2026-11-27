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

vim.lsp.enable({ "clangd", "lua_ls", "pyright", "rust_analyzer", "zls" })
