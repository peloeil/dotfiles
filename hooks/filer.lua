-- lua_add {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-filer",
    group = vim.api.nvim_create_augroup("__ddu_filer", { clear = true }),
    callback = function()
        local opts = { noremap = true, silent = true, buffer = true }
        vim.keymap.set("n", "q", [[<cmd>call ddu#ui#do_action("quit", {}, "filer")<cr>]], opts)
        vim.keymap.set("n", "o", [[<cmd>call ddu#ui#do_action("expandItem", #{ mode: "toggle" }, "filer")<cr>]], opts)
        vim.keymap.set("n", "..", [[<cmd>call ddu#ui#do_action("itemAction", #{name: "narrow", params: #{path: ".."}})<cr>]], opts)
        vim.keymap.set("n", "mv", [[<cmd>call ddu#ui#do_action("itemAction", #{name: "rename"})<cr>]], opts)
        vim.keymap.set("n", "dd", [[<cmd>call ddu#ui#do_action("itemAction", #{name: "delete"})<cr>]], opts)
        vim.keymap.set("n", "c", [[<cmd>call ddu#ui#do_action("itemAction", #{name: "newFile"})<cr>]], opts)
        vim.keymap.set("n", "<cr>", function()
            if vim.fn["ddu#ui#get_item"]().isTree then
                vim.fn["ddu#ui#do_action"]("itemAction", { name = "narrow" }, "filer")
            else
                vim.fn["ddu#ui#do_action"]("itemAction", { name = "open" }, "filer")
            end
        end, opts)
    end
})
-- }}}

-- lua_post_source {{{
vim.fn["ddu#custom#patch_local"]("filer", {
    -- ddu-ui-filer
    ui = "filer",
    uiParams = {
        filer = {
            winWidth = vim.o.columns * 0.2,
            split = "vertical",
            splitDirection = "topleft",
        },
    },
    -- ddu-source-file
    sources = { "file" },
    sourceOptions = {
        file = {
            columns = { "icon_filename" },
        },
    },
    -- ddu-kind-file
    kindOptions = {
        file = {
            defaultAction = "open",
        },
    },
})

local opts = { noremap = true, silent = true }
vim.keymap.set(
    "n",
    "<leader>e",
    [[<cmd>call ddu#start(#{name: "filer", searchPath: expand("%:p")})<cr>]],
    opts
)
-- }}}
