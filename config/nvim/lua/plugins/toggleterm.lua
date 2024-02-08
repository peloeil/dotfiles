return {
    "akinsho/toggleterm.nvim",
    keys = {
        { "th", "<cmd>ToggleTerm direction=horizontal<CR>", { noremap = true, silent = true } },
        { "tj", "<cmd>2ToggleTerm direction=horizontal<CR>", { noremap = true, silent = true } },
        { "tv", "<cmd>ToggleTerm direction=vertical<CR>", { noremap = true, silent = true } },
        { "tb", "<cmd>2ToggleTerm direction=vertical<CR>", { noremap = true, silent = true } },
        { "tt", "<cmd>ToggleTerm direction=tab<CR>", { noremap = true, silent = true } },
        "<leader>g",
    },
    version = "*",
    opts = {
    },
    config = function()
        require("toggleterm").setup({
            size = function(term)
                if term.direction == "horizontal" then
                    return vim.o.lines * 0.4
                elseif term.direction == "vertical" then
                    return vim.o.columns * 0.4
                end
            end,
        })
        local Terminal = require("toggleterm.terminal").Terminal
        local lazygit = Terminal:new({ cmd = "lazygit", direction = "float", hidden = true })
        function _lazygit_toggle()
            lazygit:toggle()
        end
        vim.keymap.set("n", "<leader>g", _lazygit_toggle, { noremap = true, silent = true })
    end
}
