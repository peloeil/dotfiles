local opts = { noremap = true, silent = true }

vim.api.nvim_create_user_command('DppInstall', [[call dpp#async_ext_action("installer", "install")]], {})
vim.api.nvim_create_user_command(
    'DppUpdate',
    function(opts)
        vim.fn['dpp#async_ext_action']('installer', 'update', { names = opts.fargs })
    end,
    { nargs = '*' }
)
