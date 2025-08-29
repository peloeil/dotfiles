-- lua_add {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-ff",
    group = vim.api.nvim_create_augroup("__ddu_ff", { clear = true }),
    callback = function()
        local opts = { noremap = true, silent = true, buffer = true }
        vim.keymap.set("n", "q", [[<cmd>call ddu#ui#async_action("quit")<cr>]], opts)
        vim.keymap.set("n", "<cr>", [[<cmd>call ddu#ui#async_action("itemAction")<cr>]], opts)
        vim.keymap.set("n", "i", [[<cmd>call ddu#ui#async_action("openFilterWindow")<cr>]], opts)
    end
})
-- }}}

-- lua_post_source {{{
vim.fn["ddu#custom#patch_local"]("file_recursive", {
    ui = "ff",
    uiParams = {
        ff = {
            split = "floating",
            floatingBorder = "rounded",
            floatingTitle = "files",
            previewFloating = true,
            previewFloatingBorder = "rounded",
            previewFloatingTitle = "preview",
            previewSplit = "horizontal",
            startAutoAction = true,
            autoAction = {
                name = "preview",
            },
        },
    },
    sources = {
        {
            name = { "file_rec" },
            options = {
                matchers = {
                    "matcher_fzf",
                },
                sorters = {
                    "sorter_fzf",
                },
            },
            params = {
                ignoreDirectories = {
                    ".git",
                    ".venv",
                    ".vscode",
                    "__pycache__",
                    "node_modules",
                },
            }
        },
    },
    kindOptions = {
        file = {
            defaultAction = "open",
        }
    },
})
vim.keymap.set(
    "n",
    "<leader>ff",
    [[<cmd>call ddu#start(#{name:"file_recursive"})<cr>]],
    opts
)
vim.api.nvim_create_autocmd("User", {
    pattern = "Ddu:uiDone",
    group = vim.api.nvim_create_augroup("__ddu_ui_done", { clear = true }),
    nested = true,
    command = [[call ddu#ui#async_action("openFilterWindow")]],
})
-- }}}
