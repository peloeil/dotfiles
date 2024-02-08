vim.g.mapleader = " "
vim.g.maplocalleader = " "

local opt = { noremap = true, silent = true }
-- terminal mode keymap
vim.api.nvim_create_augroup("terminal_config", {})
vim.api.nvim_create_autocmd("TermOpen", {
    group = "terminal_config",
    callback = function()
        vim.cmd.startinsert()
        vim.wo.relativenumber = false
        vim.wo.number = false
    end
})
vim.keymap.set("t", "<leader><Esc>", "<C-\\><C-n>", opt)
vim.keymap.set("t", "<C-w><C-h>", "<Cmd>wincmd h<CR>", opt)
vim.keymap.set("t", "<C-w><C-j>", "<Cmd>wincmd j<CR>", opt)
vim.keymap.set("t", "<C-w><C-k>", "<Cmd>wincmd k<CR>", opt)
vim.keymap.set("t", "<C-w><C-l>", "<Cmd>wincmd l<CR>", opt)
vim.keymap.set("t", "<C-w>h", "<Cmd>wincmd h<CR>", opt)
vim.keymap.set("t", "<C-w>j", "<Cmd>wincmd j<CR>", opt)
vim.keymap.set("t", "<C-w>k", "<Cmd>wincmd k<CR>", opt)
vim.keymap.set("t", "<C-w>l", "<Cmd>wincmd l<CR>", opt)

-- normal mode keymap
vim.keymap.set("n", "<C-h>", "<Cmd>tabp<CR>", opt)
vim.keymap.set("n", "<C-l>", "<Cmd>tabn<CR>", opt)
vim.keymap.set("n", "<Esc><Esc>", "<Cmd>nohlsearch<CR>", opt)
vim.api.nvim_create_augroup("IMEoff", {})
vim.api.nvim_create_autocmd("InsertLeave", {
    group = "IMEoff",
    callback = function()
        vim.cmd("silent !fcitx5-remote -c")
    end
})

-- insert mode keymap
vim.keymap.set("i", "[", "[]<Left>", opt)
vim.keymap.set("i", "{", "{}<Left>", opt)
vim.keymap.set("i", "{<Enter>", "{}<Left><Enter><Esc>O", opt)
vim.keymap.set("i", "jj", "<Esc>", opt)
vim.keymap.set("i", "kk", "<Esc>", opt)
