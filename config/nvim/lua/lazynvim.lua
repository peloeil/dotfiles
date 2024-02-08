local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
    vim.fn.system({
        "git",
        "clone",
        "--filter=blob:none",
        "https://github.com/folke/lazy.nvim.git",
        "--branch=stable",
        lazypath,
    })
end
vim.opt.rtp:prepend(lazypath)

local opt = {
    defaults = {
        lazy = true,
    },
    performance = {
        cache = {
            enabled = true,
        },
    },
}

if vim.g.vscode then
    require("lazy").setup("vscode", opt)
else
    require("lazy").setup("plugins", opt)
end
