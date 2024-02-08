-- enable line numbers
--vim.opt.number = true
vim.opt.relativenumber = true

-- sync clipboard between OS and Neovim
vim.opt.clipboard:append({ 'unnamedplus' })

-- save undo histroy
vim.opt.undofile = true

-- search
vim.opt.hlsearch = true
vim.opt.ignorecase = true

-- indent shift width
vim.opt.shiftwidth = 4
vim.opt.smartindent = true
vim.opt.expandtab = true

-- enable transparency for a floating window and a popup window
vim.opt.winblend = 20
vim.opt.pumblend = 20

-- others
vim.opt.scrolloff = 5
vim.opt.sidescrolloff = 10
vim.opt.shell = "zsh"
vim.opt.termguicolors = true
vim.opt.fileencoding = "utf-8"
vim.opt.fileencodings = "utf-8,sjis"
vim.opt.wrap = false
vim.opt.foldcolumn = "auto"
vim.opt.foldlevel = 2
