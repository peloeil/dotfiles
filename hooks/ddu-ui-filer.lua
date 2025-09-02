-- lua_post_source {{{
vim.fn["ddu#custom#patch_local"]("filer", {
    ui = "filer",
    uiParams = {
        filer = {
            winWidth = vim.o.columns * 0.2,
            split = "vertical",
            splitDirection = "topleft",
        },
    },
    sources = {
        {
            name = "file",
            options = {},
            params = {},
        },
    },
    kindOptions = {
        file = {
            defaultAction = "open",
        },
    },
})
local opts = { noremap = true, silent = true }
vim.keymap.set(
    "n",
    "<C-n>",
    [[<cmd>call ddu#start(#{name:"filer"})<cr>]],
    opts
)
-- }}}
