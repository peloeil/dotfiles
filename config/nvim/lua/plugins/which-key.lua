return {
    "folke/which-key.nvim",
    cmd = {
        "WhichKey",
    },
    opts = {
        -- your configuration comes here
        -- or leave it empty to use the default settings
        -- refer to the configuration section below
    },
    config = function()
        require("which-key").setup()
        require("which-key").register({
            ["<leader>xx"] = "toggle trouble",
            ["<leader>xw"] = "toggle workspace diagnostics Quickfix",
            ["<leader>xd"] = "toggle document diagnostics Quickfix",
            ["<leader>xq"] = "toggle Quickfix",
            ["<leader>xl"] = "toggle loclist",
            ["gR"] = "toggle LSP references",
        })
    end
}
