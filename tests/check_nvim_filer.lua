-- Run: nvim --headless -u NONE -i NONE -l tests/check_nvim_filer.lua
-- Requires installed ddu/Denops plugins; uses temporary files and no dpp state.
local source = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h:h")
local cache = vim.env.XDG_CACHE_HOME or vim.env.HOME .. "/.cache"
for _, repo in ipairs({
    "vim-denops/denops.vim",
    "Shougo/ddu.vim",
    "Shougo/ddu-ui-filer",
    "Shougo/ddu-source-file",
    "Shougo/ddu-kind-file",
    "Shougo/ddu-filter-sorter_alpha",
    "ryota2357/ddu-column-icon_filename",
}) do
    vim.opt.runtimepath:append(cache .. "/dpp/repos/github.com/" .. repo)
end
vim.g.denops_server_addr = ""
vim.cmd("runtime plugin/denops.vim")
vim.fn["denops#server#connect_or_start"]()
dofile(source .. "/dot_config/nvim/hooks/ddu.lua")
dofile(source .. "/dot_config/nvim/hooks/filer.lua")
assert(vim.wait(15000, function()
    return vim.fn["denops#plugin#is_loaded"]("ddu") == 1
end), "ddu did not load")

local work = vim.fn.tempname()
local cwd = vim.fn.getcwd()
local ok, err = pcall(function()
    vim.fn.mkdir(work .. "/src/nested", "p")
    vim.fn.mkdir(work .. "/other/deep", "p")
    vim.cmd.cd(vim.fn.fnameescape(work))
    -- Reopening and switching buffers must both reveal the current file.
    for _, relative in ipairs({ "src/nested/current.lua", "src/nested/current.lua", "other/deep/next.lua" }) do
        local path = work .. "/" .. relative
        vim.fn.writefile({ "sample" }, path)
        vim.cmd.edit(vim.fn.fnameescape(path))
        vim.api.nvim_feedkeys("\\e", "xt", false)
        assert(vim.wait(10000, function()
            return vim.bo.filetype == "ddu-filer" and vim.fn["ddu#get_context"]("filer").doneUi == true
        end), "filer did not finish drawing")
        -- Let queued redraws settle: the regression briefly reveals, then collapses.
        vim.wait(300, function() return false end)
        local item = vim.fn["ddu#ui#get_item"]("filer")
        assert((item.action or {}).path == path, "Current file was not revealed: " .. relative)
        assert(item.__level == 2, "Ancestor directories were not expanded")
        assert(vim.fn.getcwd() == work, "Opening filer changed the working directory")
        vim.api.nvim_feedkeys("q", "xt", false)
        assert(vim.wait(5000, function() return vim.bo.filetype ~= "ddu-filer" end), "filer did not close")
    end
end)
vim.cmd.cd(vim.fn.fnameescape(cwd))
vim.fn.delete(work, "rf")
assert(ok, err)
print("OK: filer reveals the current file on first open, reopen, and buffer switch")
