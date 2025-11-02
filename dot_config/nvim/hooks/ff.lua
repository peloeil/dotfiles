-- lua_add {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-ff",
    group = vim.api.nvim_create_augroup("__ddu_ff", { clear = true }),
    callback = function(arg)
        local opts = { noremap = true, silent = true, buffer = arg.buf }
        vim.keymap.set("n", "<cr>", [[<cmd>call ddu#ui#do_action("itemAction", {}, "file_recursive")<cr>]], opts)
        vim.keymap.set("n", "q", [[<cmd>call ddu#ui#do_action("quit", {}, "file_recursive")<cr>]], opts)
        vim.keymap.set("n", "i", [[<cmd>call ddu#ui#do_action("openFilterWindow", {}, "file_recursive")<cr>]], opts)
        vim.keymap.set("n", "a", [[<cmd>call ddu#ui#do_action("openFilterWindow", {}, "file_recursive")<cr>]], opts)
    end
})
-- }}}

-- lua_post_source {{{
vim.fn["ddu#custom#patch_local"]("file_recursive", {
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
    sources = { "file_rec" },
    sourceOptions = {
        file_rec = {
            ignoreCase = true,
            matchers = { "matcher_fzf" },
            sorters = { "sorter_fzf" },
        },
    },
    sourceParams = {
        file_rec = {
            ignoreDirectories = {
                ".git",
                ".venv",
                ".vscode",
                "__pycache__",
                "node_modules",
            },
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
    "<leader>f",
    [[<cmd>call ddu#start(#{name:"file_recursive"})<cr>]],
    opts
)
-- }}}
