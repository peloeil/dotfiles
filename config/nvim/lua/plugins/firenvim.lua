return {
    "glacambre/firenvim",
    -- Explanation: https://github.com/folke/lazy.nvim/discussions/463#discussioncomment-4819297
    lazy = not vim.g.started_by_firenvim,
    cond = false,
    build = function()
        vim.fn["firenvim#install"](0)
        vim.g.firenvim_config.localSettings['.*'] = { selector = 'textarea' }
        vim.api.nvim_create_autocmd({ 'BufEnter' }, {
            pattern = "github.com_*.txt",
            cmd = "set filetype=markdown"
        })
    end
}
