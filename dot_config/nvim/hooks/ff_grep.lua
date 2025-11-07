-- lua_add {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-ff",
    group = vim.api.nvim_create_augroup("__ddu_ff_grep", { clear = true }),
    callback = function(arg)
        local opts = { noremap = true, silent = true, buffer = arg.buf }
        vim.keymap.set("n", "<cr>", [[<cmd>call ddu#ui#do_action("itemAction", {}, "ff_grep")<cr>]], opts)
        vim.keymap.set("n", "q", [[<cmd>call ddu#ui#do_action("quit", {}, "ff_grep")<cr>]], opts)
        vim.keymap.set("n", "i", [[<cmd>call ddu#ui#do_action("openFilterWindow", {}, "ff_grep")<cr>]], opts)
        vim.keymap.set("n", "a", [[<cmd>call ddu#ui#do_action("openFilterWindow", {}, "ff_grep")<cr>]], opts)
    end
})
-- }}}

-- lua_post_source {{{
vim.fn["ddu#custom#patch_local"]("ff_grep", {
    -- ddu-ui-ff
    ui = "ff",
    uiParams = {
        ff = {
            floatingTitle = "grep",
            startAutoAction = true,
            autoAction = {
                name = "preview",
            },
            ignoreEmpty = false,
            autoResize = false,
        },
    },
    -- ddu-source-rg
    sources = { "rg" },
    sourceOptions = {
        rg = {
            volatile = true,
            matchers = {},
        },
    },
    -- ddu-kind-file
    kindOptions = {
        file = {
            defaultAction = "open",
        },
    },
})

local opts = { noremap = true, silent = true }
vim.keymap.set(
    "n",
    "<leader>fg",
    [[<cmd>call ddu#start(#{name:"ff_grep"})<cr>]],
    opts
)
-- }}}


