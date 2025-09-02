-- lua_add {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-filer",
    group = vim.api.nvim_create_augroup("__ddu_filer", { clear = true }),
    callback = function()
        local opts = { noremap = true, silent = true, buffer = true }
        vim.keymap.set("n", "q", [[<cmd>call ddu#ui#do_action("quit", {}, "filer")<cr>]], opts)
        vim.keymap.set("n", "o", [[<cmd>call ddu#ui#do_action("expandItem", #{ mode: "toggle" }, "filer")<cr>]], opts)
        vim.keymap.set("n", "<cr>", [[<cmd>call ddu#ui#do_action("itemAction", {}, "filer")<cr>]], opts)
        vim.keymap.set("n", "<space>", [[<cmd>call ddu#ui#do_action("toggleSelectItem", {}, "filer")<cr>]], opts)
    end
})
-- }}}

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
            options = {
                columns = { "icon_filename" },
            },
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
    "<leader>e",
    [[<cmd>call ddu#start(#{name: "filer", searchPath: expand("%:p")})<cr>]],
    opts
)
-- }}}
