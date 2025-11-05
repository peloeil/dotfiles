-- lua_source {{{
vim.diagnostic.config({
    virtual_text = true,
    signs = {
        text = {
            [vim.diagnostic.severity.ERROR] = '',
            [vim.diagnostic.severity.WARN] = '',
            [vim.diagnostic.severity.INFO] = '󰋇',
            [vim.diagnostic.severity.HINT] = '󰌵',
        },
    },
})
vim.lsp.config("*", {
    capabilities = require("ddc_source_lsp").make_client_capabilities(),
})

local server_langs = {
    lua_ls = { "lua" },
    stylua = { "lua" },
    clangd = { "c", "cpp" },
}
local gid = vim.api.nvim_create_augroup("__lsp_config", { clear = true })
for server, langs in pairs(server_langs) do
    vim.api.nvim_create_autocmd("FileType", {
        group = gid,
        pattern = langs,
        callback = function(arg)
            vim.lsp.enable(server)
            local opts = { noremap = true, silent = true, buffer = arg.buf }
            vim.keymap.set("n", "<leader>ln", vim.lsp.buf.rename, opts)
        end
    })
end
-- }}}
