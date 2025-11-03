-- lua_add {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-ff",
    group = vim.api.nvim_create_augroup("__ddu_ff_buffer", { clear = true }),
    callback = function(arg)
        local opts = { noremap = true, silent = true, buffer = arg.buf }
        vim.keymap.set("n", "<cr>", [[<cmd>call ddu#ui#do_action("itemAction", {}, "ff_buffer")<cr>]], opts)
        vim.keymap.set("n", "q", [[<cmd>call ddu#ui#do_action("quit", {}, "file_recursive")<cr>]], opts)
        vim.keymap.set("n", "i", [[<cmd>call ddu#ui#do_action("openFilterWindow", {}, "ff_buffer")<cr>]], opts)
        vim.keymap.set("n", "a", [[<cmd>call ddu#ui#do_action("openFilterWindow", {}, "ff_buffer")<cr>]], opts)
    end
})
-- }}}

-- lua_post_source {{{
vim.fn["ddu#custom#patch_local"]("ff_buffer", {
    -- ddu-ui-ff
    ui = "ff",
    uiParams = {
        ff = {
            startAutoAction = true,
            autoAction = {
                name = "preview",
            },
        },
    },
    -- ddu-source-file_rec
    sources = { "buffer" },
    sourceOptions = {
        buffer = {
            ignoreCase = true,
            matchers = { "matcher_fzf" },
            sorters = { "sorter_fzf" },
        },
    },
    -- ddu-kind-file
    kindOptions = {
        file = {
            defaultAction = "open",
        }
    },
})

local opts = { noremap = true, silent = true }
vim.keymap.set(
    "n",
    "<leader>fb",
    [[<cmd>call ddu#start(#{name:"ff_buffer"})<cr>]],
    opts
)
-- }}}

