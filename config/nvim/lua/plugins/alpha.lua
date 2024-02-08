return {
    "goolord/alpha-nvim",
    event = "BufWinEnter",
    dependencies = {
        "nvim-tree/nvim-web-devicons"
    },
    config = function()
        require("alpha").setup(require("alpha.themes.startify").config)
    end
}
