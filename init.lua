if vim.loader then
    vim.loader.enable()
end
vim.opt.number = true
vim.opt.wrap = false

vim.env.XDG_CONFIG_HOME = vim.fs.joinpath(vim.env.HOME, ".config")
vim.env.XDG_CACHE_HOME = vim.fs.joinpath(vim.env.HOME, ".cache")

local function install_plugin(repo_name)
    local dpp_repos = vim.fs.joinpath(vim.env.XDG_CACHE_HOME, "dpp", "repos")
    local url = "https://github.com/" .. repo_name
    local repo_dir = vim.fs.joinpath(dpp_repos, repo_name)

    if vim.fn.isdirectory(repo_dir) ~= 1 then
        os.execute("git clone " .. url .. " " .. repo_dir)
    end
    vim.opt.runtimepath:prepend(repo_dir)
end

local function all_config_files()
    local config_dir = vim.fs.joinpath(vim.env.XDG_CONFIG_HOME, "nvim")
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
    local dpp_base = vim.fs.joinpath(vim.env.XDG_CACHE_HOME, "dpp")
    local dpp_config = vim.fs.joinpath(vim.env.XDG_CONFIG_HOME, "nvim", "config.ts")
    local dpp_autocmds = vim.api.nvim_create_augroup("__dpp_autocmds", { clear = true })

    if vim.fn.isdirectory(dpp_base) ~= 1 then
        os.execute("mkdir -p " .. dpp_base)
    end

    local dpp = require("dpp")
    vim.api.nvim_create_autocmd("User", {
        pattern = "Dpp:makeStatePost",
        group = dpp_autocmds,
        callback = function()
            vim.notify("dpp make_state() is done", vim.log.levels.INFO)
        end
    })
    if dpp.load_state(dpp_base) then
        vim.api.nvim_create_autocmd("User", {
            pattern = "Dpp:makeStatePost",
            group = dpp_autocmds,
            once = true,
            nested = true,
            callback = function()
                dpp.load_state(dpp_base)
            end
        })
        vim.fn["denops#server#wait_async"](function()
            dpp.make_state(dpp_base, dpp_config)
        end)
    end
    vim.api.nvim_create_autocmd("BufWritePost", {
        pattern = all_config_files(),
        group = dpp_autocmds,
        callback = function()
            vim.notify("dpp check_files() is run", vim.log.levels.INFO)
            dpp.check_files()
        end
    })
end

dpp_init()
dpp_load()
