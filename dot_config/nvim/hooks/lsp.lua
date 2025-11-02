-- lua_add {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-ff",
    group = vim.api.nvim_create_augroup("__ddu_lsp", { clear = true }),
    callback = function(arg)
        local opts = { noremap = true, silent = true, buffer = arg.buf }
        vim.keymap.set("n", "<cr>", [[<cmd>call ddu#ui#do_action("itemAction", {}, "lsp")<cr>]], opts)
    end
})
-- }}}

-- lua_post_source {{{
vim.fn["ddu#custom#patch_local"]("lsp", {
    -- ddu-ui-ff
    ui = "ff",
    uiParams = {
        ff = {
            immediateAction = "open",
        },
    },
    -- ddu-source-lsp_definition
    sources = {
        name = { "lsp_definition" },
    },
    -- ddu-kind-lsp, ddu-kind-lsp_codeAction
    kindOptions = {
        lsp = {
            defaultAction = "open",
        },
        lsp_codeAction = {
            defaultAction = "apply"
        },
    },
    sync = true,
})

local opts = { noremap = true, silent = true }
vim.keymap.set(
    "n",
    "<leader>l",
    [[<cmd>call ddu#start(#{name:"lsp"})<cr>]],
    opts
)
-- }}}
