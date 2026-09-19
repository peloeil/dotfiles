-- lua_post_source {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-ff",
    group = vim.api.nvim_create_augroup("__ddu_ff_grep", { clear = true }),
    callback = function(arg)
        if vim.b[arg.buf].ddu_ui_name ~= "ff_grep" then
            return
        end
        local opts = { noremap = true, silent = true, buf = arg.buf }
        vim.keymap.set("n", "<cr>", [[<cmd>call ddu#ui#do_action("itemAction", {}, "ff_grep")<cr>]], opts)
        vim.keymap.set("n", "q", [[<cmd>call ddu#ui#do_action("quit", {}, "ff_grep")<cr>]], opts)
        vim.keymap.set("n", "i", [[<cmd>call ddu#ui#do_action("openFilterWindow", {}, "ff_grep")<cr>]], opts)
        vim.keymap.set("n", "a", [[<cmd>call ddu#ui#do_action("openFilterWindow", {}, "ff_grep")<cr>]], opts)
    end,
})
vim.fn["ddu#custom#patch_local"]("ff_grep", {
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
    sources = { "rg" },
    sourceParams = {
        rg = {
            args = {
                "--column",
                "--no-heading",
                "--color",
                "never",
                "--hidden",
                "--no-ignore",
                "--glob",
                "!{.git,node_modules,.venv,venv,__pycache__}",
            },
        },
    },
    sourceOptions = {
        rg = {
            volatile = true,
            matchers = {},
        },
    },
    kindOptions = {
        file = {
            defaultAction = "open",
        },
    },
})

local opts = { noremap = true, silent = true }
vim.keymap.set("n", "<leader>fg", [[<cmd>call ddu#start(#{name:"ff_grep"})<cr>]], opts)
-- }}}
