return {
    "nvimtools/none-ls.nvim",
    event = {
        "BufReadPre",
        "BufNewFile",
    },
    dependencies = {
        "nvim-lua/plenary.nvim",
    },
    -- TODO: decide if automated or not
    config = function()
        local null_ls = require("null-ls")
        null_ls.setup({
            sources = {
                null_ls.builtins.formatting.black,
                null_ls.builtins.formatting.rustfmt,
                null_ls.builtins.formatting.stylua,
            },
        })
    end
}
