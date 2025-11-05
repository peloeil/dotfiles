-- 検索
vim.opt.ignorecase = true
vim.opt.smartcase = true

-- インデント
vim.opt.expandtab = true
vim.opt.shiftround = true
vim.opt.shiftwidth = 4
vim.opt.smartindent = true
vim.opt.list = true
vim.opt.listchars = { tab = "|->", trail = "-" }
vim.api.nvim_create_autocmd({ "BufNewFile", "BufRead" }, {
    group = vim.api.nvim_create_augroup("__42projects_norm", { clear = true }),
    pattern = {
        vim.fn.expand("~") .. "/**/42cursus/**/*",
        vim.fn.expand("~") .. "/**/minishell/**/*",
        vim.fn.expand("~") .. "/**/minirt/**/*",
        vim.fn.expand("~") .. "/**/Makefile",
    },
    callback = function(args)
        vim.bo[args.buf].expandtab = false
        vim.bo[args.buf].tabstop = 4
    end
})

-- エンコード
vim.opt.encoding = "utf-8"
vim.opt.fileencoding = "utf-8"
vim.opt.fileencodings = "utf-8"

-- その他
vim.opt.number = true
vim.opt.scrolloff = 5
vim.opt.sidescrolloff = 10
vim.opt.cursorline = true
vim.opt.showbreak = "> "
vim.opt.termguicolors = true
vim.opt.undofile = true
vim.opt.wrap = false
vim.opt.wildignorecase = true
vim.g.mapleader = " "
vim.opt.winblend = 20
vim.opt.pumblend = 20
