vim.filetype.add({
    extension = {
        h = "c",
        hpp = "cpp",
    },
})

vim.opt.ignorecase = true
vim.opt.smartcase = true

vim.opt.expandtab = true
vim.opt.shiftround = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.softtabstop = -1
vim.opt.autoindent = true
vim.opt.list = true
vim.opt.listchars = { tab = "|->", trail = "-" }

vim.opt.cmdheight = 0
vim.opt.messagesopt:remove("progress:c")
vim.api.nvim_create_autocmd({ "CmdlineEnter", "CmdlineLeave" }, {
    group = vim.api.nvim_create_augroup("__cmdheight", { clear = true }),
    callback = function(event)
        vim.opt.cmdheight = (event.event == "CmdlineEnter" or vim.v.event.cmdlevel > 1) and 1 or 0
    end,
})

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
