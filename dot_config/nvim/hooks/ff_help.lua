-- lua_add {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-ff",
    group = vim.api.nvim_create_augroup("__ddu_ff_help", { clear = true }),
    callback = function(arg)
        local opts = { noremap = true, silent = true, buffer = arg.buf }
        vim.keymap.set("n", "<cr>", [[<cmd>call ddu#ui#do_action("itemAction", {}, "ff_help")<cr>]], opts)
        vim.keymap.set("n", "q", [[<cmd>call ddu#ui#do_action("quit", {}, "ff_help")<cr>]], opts)
        vim.keymap.set("n", "i", [[<cmd>call ddu#ui#do_action("openFilterWindow", {}, "ff_help")<cr>]], opts)
        vim.keymap.set("n", "a", [[<cmd>call ddu#ui#do_action("openFilterWindow", {}, "ff_help")<cr>]], opts)
    end,
})
-- }}}

-- lua_post_source {{{
vim.fn["ddu#custom#patch_local"]("ff_help", {
    -- ddu-ui-ff
    ui = "ff",
    uiParams = {
        ff = {
            floatingTitle = "help",
            startAutoAction = true,
            autoAction = {
                name = "preview",
            },
        },
    },
    -- ddu-source-help
    sources = { "help" },
    sourceOptions = {
        help = {
            ignoreCase = true,
            matchers = { "matcher_fzf" },
            sorters = { "sorter_fzf" },
        },
    },
    -- ddu-kind-help
    kindOptions = {
        help = {
            defaultAction = "open",
        },
    },
})

local opts = { noremap = true, silent = true }
vim.keymap.set("n", "<leader>fh", [[<cmd>call ddu#start(#{name:"ff_help"})<cr>]], opts)
-- }}}
