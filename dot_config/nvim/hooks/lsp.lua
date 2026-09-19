-- lua_source {{{
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
vim.lsp.config("*", {
    capabilities = require("ddc_source_lsp").make_client_capabilities(),
})
vim.lsp.config("rust_analyzer", {
    settings = {
        ["rust-analyzer"] = {
            check = {
                command = "clippy",
            },
        },
    },
})

local servers = {
    "clangd",
    "lua_ls",
    "pyright",
    "rust_analyzer",
    "zls",
}

local opts = { noremap = true, silent = true }
vim.keymap.set("n", "<leader>ln", vim.lsp.buf.rename, opts)
for _, server in ipairs(servers) do
    vim.lsp.enable(server)
end
-- }}}
