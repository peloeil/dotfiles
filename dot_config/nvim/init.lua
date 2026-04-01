if vim.loader then
    vim.loader.enable()
end

vim.g.mapleader = " "

require("options")
require("keymaps")
require("dpp_setup")
