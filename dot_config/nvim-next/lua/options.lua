-- 既定では .h を C++ と判定する
vim.filetype.add({ extension = { h = "c" } })

vim.opt.ignorecase = true
vim.opt.smartcase = true

vim.opt.expandtab = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.softtabstop = -1
vim.opt.shiftround = true

vim.opt.number = true
vim.opt.cursorline = true
vim.opt.wrap = false
vim.opt.scrolloff = 5
vim.opt.sidescrolloff = 10
vim.opt.list = true
vim.opt.listchars = { tab = "|->", trail = "-" }
vim.opt.fillchars:append({ eob = " " })
vim.opt.winblend = 20
vim.opt.pumblend = 20

vim.opt.undofile = true
vim.opt.wildignorecase = true
