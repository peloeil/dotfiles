vim.g.everforest_background = "hard"
vim.g.everforest_transparent_background = 2

-- transparent_background = 2 still paints floats and the cursor line, so drop their backgrounds.
local function clear_backgrounds()
    for _, name in ipairs({ "NormalFloat", "FloatBorder", "FloatTitle", "CursorLine", "CursorLineNr" }) do
        local hl = vim.api.nvim_get_hl(0, { name = name, link = false })
        hl.bg, hl.ctermbg = nil, nil
        vim.api.nvim_set_hl(0, name, hl)
    end
end
vim.api.nvim_create_autocmd("ColorScheme", {
    group = vim.api.nvim_create_augroup("__transparent_highlights", { clear = true }),
    callback = clear_backgrounds,
})

vim.pack.add({ "https://github.com/sainnhe/everforest" })
vim.cmd.colorscheme("everforest")
