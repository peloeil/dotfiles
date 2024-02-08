return {
    "nvim-treesitter/nvim-treesitter-context",
    event = {
        "BufReadPre",
        "BufNewFile",
    },
    keys = {
        { "[c", function() require("treesitter-context").go_to_context() end, { noremap = true, silent = true }}
    },
}
