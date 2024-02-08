return {
    "kat0h/bufpreview.vim",
    ft = {
        "markdown",
    },
    event = {
        "BufReadPre",
        "BufNewFile",
    },
    build = "deno task prepare",
    dependencies = {
        "vim-denops/denops.vim",
    },
    config = function()
        vim.keymap.set("n", "<leader>mp", function()
            vim.cmd("!firefox")
            vim.cmd("PreviewMarkdown")
        end, { noremap = true, silent = true })
    end
}
