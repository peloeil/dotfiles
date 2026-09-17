-- Run: nvim --headless -u NONE -i NONE -l tests/check_nvim_cmdheight.lua
local source = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h:h")
local child = vim.fn.jobstart({ vim.v.progpath, "--embed", "--headless", "-u", "NONE", "-i", "NONE" }, { rpc = true })
local function request(method, ...)
    return vim.rpcrequest(child, method, ...)
end

local ok, err = pcall(function()
    request("nvim_ui_attach", 80, 24, {})
    request("nvim_exec_lua", "dofile(...)", { source .. "/dot_config/nvim/lua/options.lua" })
    request("nvim_command", "set laststatus=2 statusline=VISIBLE_FILENAME")

    local function check(keys, mode, height)
        request("nvim_input", keys)
        assert(vim.wait(1000, function()
            return request("nvim_get_mode").mode == mode
                and request("nvim_eval", "&cmdheight") == height
        end), "Unexpected mode or command-line height after " .. keys)
        request("nvim_command", "redraw")
        local row = 24 - height
        local line = request("nvim_eval", ("join(map(range(1, 80), 'screenstring(%d, v:val)'), '')"):format(row))
        assert(line:find("VISIBLE_FILENAME", 1, true), "Statusline hidden after " .. keys)
    end

    check("", "n", 0)
    check(":", "c", 1)
    check("<C-r>=", "c", 1)
    check("1<CR>", "c", 1)
    check("<Esc>", "n", 0)
    check("/filename", "c", 1)
    check("<Esc>", "n", 0)
    check(":let g:cmdheight_test = 1", "c", 1)
    check("<CR>", "n", 0)
    assert(request("nvim_eval", "g:cmdheight_test") == 1)
end)
vim.fn.jobstop(child)
assert(ok, err)
print("OK: statusline stays visible during command/search input and nested expressions")
