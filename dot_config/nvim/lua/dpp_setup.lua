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
        os.execute("git clone " .. url .. " " .. repo_dir)
    end
    vim.opt.runtimepath:prepend(repo_dir)
end

local function all_config_files()
    local config_dir = vim.fs.joinpath(xdg_config_home, "nvim")
    local globs = {
        "**/*.lua",
        "**/*.ts",
        "**/*.toml",
    }
    local files = {}
    for _, glob in pairs(globs) do
        table.insert(files, vim.fn.globpath(config_dir, glob, true, true))
    end
    return vim.iter(files):flatten():totable()
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
    local dpp_config = vim.fs.joinpath(xdg_config_home, "nvim", "config.ts")
    local dpp_autocmds = vim.api.nvim_create_augroup("__dpp_autocmds", { clear = true })

    if vim.fn.isdirectory(dpp_base) ~= 1 then
        os.execute("mkdir -p " .. dpp_base)
    end

    local dpp = require("dpp")
    if dpp.load_state(dpp_base) then
        vim.api.nvim_create_autocmd("User", {
            pattern = "Dpp:makeStatePost",
            group = dpp_autocmds,
            once = true,
            callback = function()
                dpp.load_state(dpp_base)
            end,
        })
        vim.fn["denops#server#wait_async"](function()
            dpp.make_state(dpp_base, dpp_config)
        end)
    end
    vim.api.nvim_create_autocmd("BufWritePost", {
        pattern = all_config_files(),
        group = dpp_autocmds,
        callback = function()
            vim.notify("dpp check_files() is run")
            if #dpp.check_files(dpp_base) == 0 then
                return
            end
            vim.fn["denops#server#wait_async"](function()
                dpp.make_state(dpp_base, dpp_config)
            end)
        end,
    })
end

dpp_init()
dpp_load()
