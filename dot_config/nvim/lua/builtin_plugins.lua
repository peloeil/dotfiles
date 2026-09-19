-- These runtime plugins provide commands/file handlers we do not use.
-- loaded_shada_plugin only disables editing *.shada; history still persists.
for _, name in ipairs({
    "remote_plugins", "man", "tutor_mode_plugin", "spellfile_plugin",
    "shada_plugin", "nvim_net_plugin",
}) do
    vim.g["loaded_" .. name] = 1
end

-- Keep directory and remote-file browsing available after startup, too.
vim.g.loaded_netrwPlugin = 1
local group = vim.api.nvim_create_augroup("__netrw_lazy", { clear = true })
local function load_netrw()
    vim.api.nvim_del_augroup_by_id(group)
    vim.g.loaded_netrwPlugin = nil
    vim.cmd.packadd("netrw")
    if vim.v.vim_did_enter == 1 then
        -- netrw initializes its directory handlers at VimEnter.
        vim.api.nvim_exec_autocmds("VimEnter", { group = "FileExplorer", modeline = false })
    end
end

vim.api.nvim_create_autocmd("BufEnter", {
    group = group,
    callback = function(event)
        if vim.bo[event.buf].buftype == "" and vim.fn.isdirectory(event.file) == 1 then
            load_netrw()
        end
    end,
})
vim.api.nvim_create_autocmd("CmdUndefined", {
    group = group,
    pattern = {
        "Ex*", "[SHVTLNP]ex*", "Nread", "Nwrite", "Nsource", "Ntree", "NetUserPass",
    },
    callback = load_netrw,
})
vim.api.nvim_create_autocmd({ "BufReadCmd", "FileReadCmd", "BufWriteCmd", "FileWriteCmd", "SourceCmd" }, {
    group = group,
    pattern = { "file://*", "ftp://*", "rcp://*", "scp://*", "dav://*", "davs://*", "rsync://*", "sftp://*" },
    nested = true,
    callback = function(event)
        load_netrw()
        vim.api.nvim_exec_autocmds(event.event, { group = "Network", pattern = event.match, modeline = false })
    end,
})
