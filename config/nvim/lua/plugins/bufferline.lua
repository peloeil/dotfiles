return {
    "akinsho/bufferline.nvim",
    event = {
        "BufReadPre",
        "BufNewFile",
    },
    version = "*",
    dependencies = {
        "nvim-tree/nvim-web-devicons",
    },
    cond = false,
    config = function()
        require("bufferline").setup({
            options = {
                diagnostics = "nvim_lsp",
                custom_filter = function(bufnr)
                    return vim.api.nvim_buf_get_name(bufnr):find(vim.fn.getcwd(), 0, true)
                end,
            },
        })
        vim.keymap.set("n", "<A-h>", "<cmd>BufferLineCyclePrev<CR>", { noremap = true, silent = true })
        vim.keymap.set("n", "<A-l>", "<cmd>BufferLineCycleNext<CR>", { noremap = true, silent = true })
        vim.keymap.set("n", "<A-b>", "<cmd>BufferLinePickClose<CR>", { noremap = true, silent = true })
    end
}
