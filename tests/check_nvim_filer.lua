-- Run: nvim --headless -u NONE -i NONE -l tests/check_nvim_filer.lua
-- Requires installed ddu/Denops plugins and Git; uses temporary files and no dpp state.
local source = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h:h")
local cache = vim.env.XDG_CACHE_HOME or vim.env.HOME .. "/.cache"
vim.opt.runtimepath:prepend(source .. "/dot_config/nvim")
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
        local icon = assert(item.highlights[1], "File icon lost its highlight")
        assert(icon.col == 6, "File icon must follow two spaces per level and padding")
        assert(item.display:match("^ +"):len() == 5, "Non-Git files must retain aligned indentation")
        assert(vim.fn.getcwd() == work, "Opening filer changed the working directory")
        vim.api.nvim_feedkeys("q", "xt", false)
        assert(vim.wait(5000, function() return vim.bo.filetype ~= "ddu-filer" end), "filer did not close")
    end

    local repo = work .. "/repo"
    local checkout = work .. "/linked worktree"
    vim.fn.mkdir(repo .. "/src", "p")
    vim.fn.mkdir(repo .. "/removed", "p")
    for _, file in ipairs({ "src/modified file.lua", "src/staged.lua", "src/clean.lua", "old 日本語.txt", "removed/file.lua" }) do
        vim.fn.writefile({ "before" }, repo .. "/" .. file)
    end
    local function git(dir, ...)
        local result = vim.system({ "git", "-C", dir, ... }, { text = true }):wait()
        assert(result.code == 0, result.stderr)
    end
    git(repo, "init", "--quiet")
    git(repo, "add", ".")
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "commit", "--quiet", "-m", "Initial")
    git(repo, "worktree", "add", "--quiet", "--detach", checkout)
    vim.fn.writefile({ "after" }, checkout .. "/src/modified file.lua")
    vim.fn.writefile({ "after" }, checkout .. "/src/staged.lua")
    git(checkout, "add", "src/staged.lua")
    git(checkout, "mv", "old 日本語.txt", "renamed 日本語.txt")
    vim.fn.writefile({ "staged" }, checkout .. "/src/added.lua")
    git(checkout, "add", "src/added.lua")
    vim.fn.writefile({ "edited again" }, checkout .. "/src/added.lua")
    vim.fn.delete(checkout .. "/removed/file.lua")
    vim.fn.mkdir(checkout .. "/new", "p")
    vim.fn.writefile({ "new" }, checkout .. "/new/untracked 日本語.lua")
    local long_name = "long_" .. string.rep("filename_", 8) .. "日本語.lua"
    vim.fn.writefile({ "new" }, checkout .. "/src/" .. long_name)
    vim.fn.writefile({ "new" }, checkout .. "/src/no_icon.unknown_extension")

    local function draw()
        assert(vim.wait(10000, function()
            return vim.bo.filetype == "ddu-filer" and vim.fn["ddu#get_context"]("filer").doneUi == true
        end), "Git filer did not finish drawing")
    end
    -- The displayed path, rather than Neovim/Denops cwd, determines the repository.
    vim.fn["ddu#start"]({ name = "filer", sourceOptions = { file = { path = checkout } },
        searchPath = checkout .. "/src/modified file.lua" })
    draw()
    vim.api.nvim_win_set_width(0, 24)
    local function check_status(relative, expected, group)
        local found
        for _, item in ipairs(vim.fn["ddu#ui#get_items"]("filer")) do
            if (item.action or {}).path == checkout .. "/" .. relative then found = item; break end
        end
        assert(found, "Missing filer item: " .. relative)
        local filename = vim.fs.basename(relative) .. (found.isTree and "/" or "")
        local ending = " " .. filename
        assert(found.display:sub(-#ending) == ending, relative .. ": " .. found.display)
        local icon = found.highlights[1]
        assert(icon.col == 2 + 2 * found.__level + (expected and 5 or 0), "Icon highlight is misaligned")
        local highlight = vim.iter(found.highlights):find(function(hl) return hl.name == "filer_git_status" end)
        assert((highlight and highlight.hl_group) == group, "Wrong Git highlight: " .. relative)
        if highlight then
            assert(highlight.col == 2 + 2 * found.__level and highlight.width == 4,
                "Git highlight must follow indentation and precede the icon: " .. relative)
            assert(found.display:sub(highlight.col, highlight.col + 3) == "[" .. expected .. "]",
                "Git highlight is misaligned before the icon: " .. relative)
            if relative == "src/" .. long_name then
                local width = vim.api.nvim_win_get_width(0)
                assert(not vim.wo.wrap and vim.fn.strdisplaywidth(found.display) > width,
                    "The long filename must exceed the filer window")
                assert(vim.fn.strdisplaywidth(found.display:sub(1, highlight.col + 3)) <= width,
                    "Git status must remain visible when the filename is clipped")
            end
        end
    end
    check_status("src/modified file.lua", " M", "DiagnosticWarn")
    check_status("src/staged.lua", "M ", "DiagnosticOk")
    check_status("src/added.lua", "AM", "DiagnosticWarn")
    check_status("src/clean.lua", nil, nil)
    check_status("src/" .. long_name, "??", "DiagnosticInfo")
    check_status("src/no_icon.unknown_extension", "??", "DiagnosticInfo")
    check_status("src", " *", "DiagnosticWarn")
    check_status("removed", " *", "DiagnosticWarn")
    check_status("renamed 日本語.txt", "R ", "DiagnosticOk")
    check_status("new", " *", "DiagnosticWarn")
    assert(vim.fn.getcwd() == work, "Git status changed the working directory")

    -- Refresh must observe index changes, and expanding must retain indentation.
    git(checkout, "add", "src/modified file.lua")
    vim.api.nvim_feedkeys("r", "xt", false)
    -- The redraw action returns before its refresh finishes.
    assert(vim.wait(10000, function()
        return vim.iter(vim.fn["ddu#ui#get_items"]("filer")):any(function(item)
            return (item.action or {}).path == checkout .. "/src/modified file.lua"
                and item.display:find("[M ]", 1, true) ~= nil
        end)
    end), "Refreshed Git status did not appear")
    check_status("src/modified file.lua", "M ", "DiagnosticOk")
    vim.fn["ddu#ui#do_action"]("quit", vim.empty_dict(), "filer")
    vim.fn["ddu#start"]({ name = "filer", sourceOptions = { file = { path = checkout .. "/new" } },
        searchPath = checkout .. "/new/untracked 日本語.lua" })
    draw()
    check_status("new/untracked 日本語.lua", "??", "DiagnosticInfo")
    vim.fn["ddu#ui#do_action"]("quit", vim.empty_dict(), "filer")
end)
vim.cmd.cd(vim.fn.fnameescape(cwd))
vim.fn.delete(work, "rf")
assert(ok, err)
print("OK: filer reveals files with two-space indentation and refreshed Git status, including linked worktrees")
