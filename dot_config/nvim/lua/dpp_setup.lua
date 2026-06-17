local function resolve_xdg_dir(env_name, fallback_dir)
    local dir = vim.env[env_name]
    if dir == nil or dir == "" then
        dir = vim.fs.joinpath(vim.env.HOME, fallback_dir)
        vim.env[env_name] = dir
    end

    return dir
end

local xdg_config_home = resolve_xdg_dir("XDG_CONFIG_HOME", ".config")
local xdg_cache_home = resolve_xdg_dir("XDG_CACHE_HOME", ".cache")

local function install_plugin(repo_name)
    local dpp_repos = vim.fs.joinpath(xdg_cache_home, "dpp", "repos")
    local url = "https://github.com/" .. repo_name
    local repo_dir = vim.fs.joinpath(dpp_repos, repo_name)

    if vim.fn.isdirectory(repo_dir) ~= 1 then
        vim.system({ "git", "clone", url, repo_dir }):wait()
    end
    vim.opt.runtimepath:prepend(repo_dir)
end

local config_dir = vim.fs.joinpath(xdg_config_home, "nvim")

local function is_dpp_config_file(path)
    local file = vim.fs.normalize(vim.fn.fnamemodify(path, ":p"))
    local dir = vim.fs.normalize(config_dir)

    return vim.startswith(file, dir .. "/")
        and (
            file:match("%.lua$") ~= nil
            or file:match("%.ts$") ~= nil
            or file:match("%.toml$") ~= nil
        )
end

local function dpp_init()
    install_plugin("Shougo/dpp-protocol-git")
    install_plugin("Shougo/dpp-ext-toml")
    install_plugin("Shougo/dpp-ext-lazy")
    install_plugin("Shougo/dpp-ext-installer")
    install_plugin("Shougo/dpp.vim")
    install_plugin("vim-denops/denops.vim")
end

local function dpp_load()
    local dpp_base = vim.fs.joinpath(xdg_cache_home, "dpp")
    local dpp_config = vim.fs.joinpath(config_dir, "config.ts")
    local dpp_autocmds = vim.api.nvim_create_augroup("__dpp_autocmds", { clear = true })

    if vim.fn.isdirectory(dpp_base) ~= 1 then
        vim.fn.mkdir(dpp_base, "p")
    end

    local dpp = require("dpp")

    local function make_state(message)
        if message ~= nil then
            vim.notify(message)
        end
        vim.fn["denops#server#wait_async"](function()
            dpp.make_state(dpp_base, dpp_config)
        end)
    end

    vim.api.nvim_create_user_command("DppMakeState", function()
        make_state("dpp make_state() is run")
    end, { desc = "Regenerate dpp state" })

    if dpp.load_state(dpp_base) then
        vim.api.nvim_create_autocmd("User", {
            pattern = "Dpp:makeStatePost",
            group = dpp_autocmds,
            once = true,
            callback = function()
                dpp.load_state(dpp_base)
            end,
        })
        make_state("dpp load_state() failed; make_state() is run")
    elseif #dpp.check_files(dpp_base) > 0 then
        make_state("dpp state is outdated; make_state() is run")
    end

    vim.api.nvim_create_autocmd("BufWritePost", {
        pattern = { "*.lua", "*.ts", "*.toml" },
        group = dpp_autocmds,
        callback = function(event)
            if not is_dpp_config_file(vim.api.nvim_buf_get_name(event.buf)) then
                return
            end
            make_state("dpp config file is saved; make_state() is run")
        end,
    })
end

dpp_init()
dpp_load()
