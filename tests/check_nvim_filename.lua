-- Run: nvim --headless -u NONE -i NONE -l tests/check_nvim_filename.lua
-- Requires the installed Heirline and devicons plugins.
local source = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h:h")
local cache = vim.env.XDG_CACHE_HOME or vim.env.HOME .. "/.cache"
vim.opt.runtimepath:prepend(source .. "/dot_config/nvim")
for _, repo in ipairs({ "rebelot/heirline.nvim", "nvim-tree/nvim-web-devicons" }) do
    vim.opt.runtimepath:append(cache .. "/dpp/repos/github.com/" .. repo)
end

require("heirline").setup({ statusline = require("heirline.filename") })
for _, filename in ipairs({ "normal.txt", "100%done.txt", "test%{1+1}.txt" }) do
    vim.api.nvim_buf_set_name(0, vim.fn.getcwd() .. "/" .. filename)
    local rendered = vim.api.nvim_eval_statusline(vim.o.statusline, { maxwidth = 180 }).str
    assert(rendered:find(filename, 1, true), "Filename was interpreted: " .. rendered)
end
print("OK: filenames containing statusline syntax are displayed literally")
