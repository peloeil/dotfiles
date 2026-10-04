-- Run: timeout --kill-after=2s 30s nvim --headless -u NONE -i NONE -l tests/check_nvim_lsp.lua
-- Uses installed ddu/Denops plugins and fixed LSP responses; no language server or dpp state.
local source = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h:h")
local cache = vim.env.XDG_CACHE_HOME or vim.env.HOME .. "/.cache"
for _, repo in ipairs({
    "vim-denops/denops.vim",
    "Shougo/ddu.vim",
    "Shougo/ddu-ui-ff",
    "uga-rosa/ddu-source-lsp",
}) do
    vim.opt.runtimepath:append(cache .. "/dpp/repos/github.com/" .. repo)
end
vim.g.mapleader = " "
vim.g.denops_server_addr = ""
vim.cmd("runtime plugin/denops.vim")
vim.fn["denops#server#connect_or_start"]()
dofile(source .. "/dot_config/nvim/hooks/ddu.lua")
dofile(source .. "/dot_config/nvim/hooks/ff_lsp.lua")
assert(vim.wait(15000, function()
    return vim.fn["denops#plugin#is_loaded"]("ddu") == 1
end), "ddu did not load")

local work = vim.fn.tempname()
local ok, err = pcall(function()
    vim.fn.mkdir(work, "p")
    local origin = work .. "/origin.lua"
    local target = work .. "/target.lua"
    vim.fn.writefile({ "target()" }, origin)
    vim.fn.writefile({ "-- target", "local function target() end", "local function other() end" }, target)
    local count = 1
    package.loaded.ddu_nvim_lsp = {
        get_client_by_bufnr = function()
            return { { name = "nvim-lsp", id = 1, offsetEncoding = "utf-16" } }
        end,
        request = function(_, method)
            assert(method == "textDocument/definition")
            local locations = {}
            for line = 1, count do
                locations[#locations + 1] = {
                    uri = vim.uri_from_fname(target),
                    range = { start = { line = line, character = 15 },
                        ["end"] = { line = line, character = 21 } },
                }
            end
            return locations
        end,
    }

    -- A persisted immediate action used to wait on its own UI redraw lock.
    -- Repeat after selecting from a list to exercise reuse of the same UI.
    for _, candidates in ipairs({ 1, 2, 1, 0 }) do
        count = candidates
        vim.cmd.edit(vim.fn.fnameescape(origin))
        print("Checking definition candidates: " .. count)
        vim.api.nvim_feedkeys(" ld", "xt", false)
        if count == 1 then
            assert(vim.wait(5000, function()
                return vim.api.nvim_buf_get_name(0) == target
            end), "Single definition did not open")
            assert(vim.api.nvim_win_get_cursor(0)[1] == 2, "Wrong definition line")
            assert(#vim.api.nvim_list_wins() == 1, "Single definition opened a picker")
        else
            assert(vim.wait(5000, function()
                return vim.bo.filetype == "ddu-ff"
                    and #vim.fn["ddu#ui#get_items"]("lsp_definition") == count
            end), "Definition picker did not show the expected candidates")
            if count > 0 then
                vim.api.nvim_feedkeys(vim.keycode("<CR>"), "xt", false)
                assert(vim.wait(5000, function()
                    return vim.api.nvim_buf_get_name(0) == target and #vim.api.nvim_list_wins() == 1
                end), "Selecting a definition did not close the picker and jump")
            else
                vim.api.nvim_feedkeys("q", "xt", false)
                assert(vim.wait(5000, function() return #vim.api.nvim_list_wins() == 1 end),
                    "Empty picker did not close")
            end
        end
        -- Wait for the complete request, not just the buffer change before the deadlock.
        vim.fn["ddu#get_context"]("lsp_definition")
    end
end)
vim.fn.delete(work, "rf")
assert(ok, err)
print("OK: single definitions jump without freezing; multiple and empty results remain usable")
