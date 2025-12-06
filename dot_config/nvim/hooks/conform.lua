-- lua_post_source {{{
require("conform").setup({
    formatters_by_ft = {
        c = { "clang-format" },
        cpp = { "clang-format" },
        lua = { "stylua" },
        python = { "ruff_organize_import", "ruff_format", "ruff_fix" },
        sh = { "shellcheck", "shfmt" },
        zig = { "zigfmt" },
    },
    formatters = {
        stylua = {
            prepend_args = { "--indent-type", "Spaces" },
        },
    },
})

local opts = { noremap = true, silent = true }
vim.keymap.set("n", "<leader>lf", function() require("conform").format() end, opts)
-- }}}
