return {
    "chomosuke/typst-preview.nvim",
    event = {
        "BufReadPre",
        "BufNewFile",
    },
    ft = {
        "typst",
    },
    version = "0.1.1",
    build = function()
        require("typst-preview").update()
    end,
    config = function()
        vim.keymap.set("n", "<leader>tp", "<cmd>TypstPreview<CR>")
        vim.api.nvim_create_augroup("typst_compile", {})
        vim.api.nvim_create_autocmd({ "BufWritePost" }, {
            pattern = { "*.typst" },
            group = "typst_compile",
            callback = function()
                vim.cmd("!typst compile %")
            end
        })
    end
}
