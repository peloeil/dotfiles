-- lua_post_source {{{
vim.fn["ddu#custom#patch_global"]({
    uiParams = {
        ff = {
            split = "floating",
            floatingBorder = "rounded",
            previewFloating = true,
            previewFloatingBorder = "rounded",
            previewFloatingTitle = "preview",
            previewSplit = "horizontal",
        },
        filer = {
            winWidth = vim.o.columns * 0.2,
            split = "vertical",
            splitDirection = "topleft",
        },
    },
})
-- }}}
