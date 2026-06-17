vim.filetype.add({
    extension = {
        h = "c",
        hpp = "cpp",
    },
})

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

-- その他
vim.opt.number = true
vim.opt.scrolloff = 5
vim.opt.sidescrolloff = 10
vim.opt.cursorline = true
vim.opt.fillchars:append({ eob = " " })
vim.opt.termguicolors = true
vim.opt.undofile = true
vim.opt.wrap = false
vim.opt.wildignorecase = true
vim.opt.winblend = 20
vim.opt.pumblend = 20
