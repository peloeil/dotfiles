-- 検索
vim.opt.ignorecase = true
vim.opt.smartcase = true

-- インデント
vim.opt.expandtab = true
vim.opt.shiftround = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.softtabstop = -1
vim.opt.autoindent = true
vim.opt.list = true
vim.opt.listchars = { tab = "|->", trail = "-" }

-- エンコード
vim.opt.fileencoding = "utf-8"
vim.opt.fileencodings = "utf-8"

-- その他
vim.opt.number = true
vim.opt.scrolloff = 5
vim.opt.sidescrolloff = 10
vim.opt.cursorline = true
vim.opt.showbreak = "> "
vim.opt.fillchars:append({ eob = " " })
vim.opt.termguicolors = true
vim.opt.undofile = true
vim.opt.wrap = false
vim.opt.wildignorecase = true
vim.opt.winblend = 20
vim.opt.pumblend = 20
