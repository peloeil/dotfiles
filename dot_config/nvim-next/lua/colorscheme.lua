vim.g.everforest_background = "hard"
vim.g.everforest_transparent_background = 2
vim.g.everforest_better_performance = 1

-- transparent_background = 2 でもフロート、カーソル行、補完ポップアップ、タブラインには背景色が残る。
-- :colorscheme の直後に1回消すだけでは、読み直したときに戻るので autocmd にする
local function clear_backgrounds()
    -- PmenuThumb はスクロールバーのつまみを背景色だけで描くので、消すと見えなくなる
    local groups = {
        "NormalFloat",
        "FloatBorder",
        "FloatTitle",
        "CursorLine",
        "CursorLineNr",
        "Pmenu",
        "PmenuExtra",
        "PmenuKind",
        "PmenuSbar",
        "TabLine",
    }
    for _, name in ipairs(groups) do
        local hl = vim.api.nvim_get_hl(0, { name = name, link = false })
        hl.bg, hl.ctermbg = nil, nil
        vim.api.nvim_set_hl(0, name, hl)
    end

    -- 選択中の項目は明るい背景に暗い文字で示されるので、背景を消すだけでは文字が見えなくなる。
    -- 背景色を文字色に移して、選択中であることを色で残す
    for _, name in ipairs({ "PmenuSel", "PmenuExtraSel", "PmenuKindSel", "TabLineSel" }) do
        local hl = vim.api.nvim_get_hl(0, { name = name, link = false })
        if hl.bg then
            hl.fg, hl.ctermfg = hl.bg, hl.ctermbg
            hl.bg, hl.ctermbg = nil, nil
            vim.api.nvim_set_hl(0, name, hl)
        end
    end
end
vim.api.nvim_create_autocmd("ColorScheme", {
    group = vim.api.nvim_create_augroup("__transparent_highlights", { clear = true }),
    callback = clear_backgrounds,
})

vim.pack.add({ "https://github.com/sainnhe/everforest" })
vim.cmd.colorscheme("everforest")
