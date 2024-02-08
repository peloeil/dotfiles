return {
    "nvim-treesitter/nvim-treesitter",
    event = {
        "BufReadPre",
        "BufNewFile",
    },
    build = ":TSUpdate",
    config = function()
        require("nvim-treesitter.configs").setup({
            ensure_installed = {
                "c",
                "cpp",
                "python",
                "lua",
                "vim",
                "vimdoc",
                "rust",
            },
            highlight = {
                enable = true,
            }
        })
    end
}
