if vim.loader then
    vim.loader.enable()
end

vim.g.mapleader = " "

require("builtin_plugins")
require("options")
require("keymaps")
require("dpp_setup")
require("treesitter_setup")
