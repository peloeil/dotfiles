-- lua_post_source {{{
vim.api.nvim_create_autocmd("FileType", {
    pattern = "ddu-filer",
    group = vim.api.nvim_create_augroup("__ddu_filer", { clear = true }),
    callback = function(arg)
        local opts = { noremap = true, silent = true, buf = arg.buf }
        vim.keymap.set("n", "<leader>e", [[<cmd>call ddu#ui#do_action("quit", {}, "filer")<cr>]], opts)
        vim.keymap.set("n", "q", [[<cmd>call ddu#ui#do_action("quit", {}, "filer")<cr>]], opts)
        vim.keymap.set("n", "o", [[<cmd>call ddu#ui#do_action("expandItem", #{ mode: "toggle" }, "filer")<cr>]], opts)
        vim.keymap.set("n", "r", [[<cmd>call ddu#ui#do_action("redraw", #{method: "refreshItems"}, "filer")<cr>]], opts)
        vim.keymap.set(
            "n",
            "..",
            [[<cmd>call ddu#ui#do_action("itemAction", #{name: "narrow", params: #{path: ".."}}, "filer")<cr>]],
            opts
        )
        vim.keymap.set("n", "mv", [[<cmd>call ddu#ui#do_action("itemAction", #{name: "rename"}, "filer")<cr>]], opts)
        vim.keymap.set("n", "dd", [[<cmd>call ddu#ui#do_action("itemAction", #{name: "delete"}, "filer")<cr>]], opts)
        vim.keymap.set("n", "c", [[<cmd>call ddu#ui#do_action("itemAction", #{name: "newFile"}, "filer")<cr>]], opts)
        vim.keymap.set("n", "<cr>", function()
            if vim.fn["ddu#ui#get_item"]().isTree then
                vim.fn["ddu#ui#do_action"]("itemAction", { name = "narrow" }, "filer")
            else
                vim.fn["ddu#ui#do_action"]("itemAction", { name = "open" }, "filer")
            end
        end, opts)
    end,
})
vim.fn["ddu#custom#patch_local"]("filer", {
    ui = "filer",
    -- Avoid a later async redraw collapsing the tree expanded by searchPath.
    sync = true,
    sources = { "file" },
    sourceOptions = {
        file = {
            sorters = { "sorter_alpha" },
            columns = { "icon_filename" },
            converters = { "converter_filer" },
        },
    },
    kindOptions = {
        file = {
            defaultAction = "open",
        },
    },
})

local opts = { noremap = true, silent = true }
vim.keymap.set("n", "<leader>e", [[<cmd>call ddu#start(#{name: "filer", searchPath: expand("%:p")})<cr>]], opts)
-- }}}
