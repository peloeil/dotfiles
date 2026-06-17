-- lua_post_source {{{
require("trouble").setup({
    multiline = true,
})

local opts = { noremap = true, silent = true }
vim.keymap.set("n", "<leader>xx", [[<cmd>Trouble diagnostics toggle focus=true filter.buf=0<cr>]], opts)
vim.keymap.set("n", "<leader>xX", [[<cmd>Trouble diagnostics toggle focus=true<cr>]], opts)
-- }}}
