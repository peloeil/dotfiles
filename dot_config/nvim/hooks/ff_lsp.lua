-- lua_add {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-ff",
    group = vim.api.nvim_create_augroup("__ddu_lsp", { clear = true }),
    callback = function(arg)
        local opts = { noremap = true, silent = true, buffer = arg.buf }
        vim.keymap.set("n", "<cr>", [[<cmd>call ddu#ui#do_action("itemAction", {})<cr>]], opts)
        vim.keymap.set("n", "q", [[<cmd>call ddu#ui#do_action("quit", {})<cr>]], opts)
        vim.keymap.set("n", "i", [[<cmd>call ddu#ui#do_action("openFilterWindow", {})<cr>]], opts)
        vim.keymap.set("n", "a", [[<cmd>call ddu#ui#do_action("openFilterWindow", {})<cr>]], opts)
    end
})
-- }}}

-- lua_post_source {{{
vim.fn["ddu#custom#patch_global"]({
    kindOptions = {
        lsp = {
            defaultAction = "open",
        },
        lsp_codeAction = {
            defaultAction = "apply"
        },
    },
})
vim.fn["ddu#custom#patch_local"]("lsp_definition", {
    -- ddu-ui-ff
    ui = "ff",
    uiParams = {
        ff = {
            floatingTitle = "definition",
            immediateAction = "open",
        },
    },
    -- ddu-source-lsp_definition
    sources = { "lsp_definition" },
    sync = true,
})
vim.fn["ddu#custom#patch_local"]("lsp_documentSymbol", {
    -- ddu-ui-ff
    ui = "ff",
    uiParams = {
        ff = {
            floatingTitle = "symbols",
            ignoreEmpty = false,
        },
    },
    -- ddu-source-lsp_documentSymbol
    sources = { "lsp_documentSymbol" },
    sourceOptions = {
        lsp_documentSymbol = {
            volatile = true,
            matchers = { "matcher_fzf" },
            sorters = { "sorter_fzf" },
            converters = { "converter_lsp_symbol" },
        },
    },
})
vim.fn["ddu#custom#patch_local"]("lsp_diagnostic", {
    -- ddu-ui-ff
    ui = "ff",
    uiParams = {
        ff = {
            floatingTitle = "diagnostics",
            immediateAction = "open",
        },
    },
    -- ddu-source-lsp_diagnostic
    sources = { "lsp_diagnostic" },
    sourceOptions = {
        lsp_diagnostic = {
            converters = { "converter_lsp_diagnostic" },
        },
    },
    sourceParams = {
        buffer = 0,
    },
})

local opts = { noremap = true, silent = true }
vim.keymap.set("n", "<leader>ld", [[<cmd>call ddu#start(#{name:"lsp_definition"})<cr>]], opts)
vim.keymap.set("n", "<leader>ls", [[<cmd>call ddu#start(#{name:"lsp_documentSymbol"})<cr>]], opts)
vim.keymap.set("n", "<leader>xx", [[<cmd>call ddu#start(#{name:"lsp_diagnostic"})<cr>]], opts)
-- }}}
