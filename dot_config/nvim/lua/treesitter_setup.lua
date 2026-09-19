local bundled = { "c", "lua", "markdown", "markdown_inline", "query", "vim", "vimdoc" }
local queries_added = false

vim.api.nvim_create_autocmd("FileType", {
    group = vim.api.nvim_create_augroup("__treesitter_highlight", { clear = true }),
    -- Starting inside FileType can suppress the enclosing BufReadPost (Git signs).
    callback = vim.schedule_wrap(function(event)
        if not vim.api.nvim_buf_is_loaded(event.buf) then
            return
        end
        local ft = vim.bo[event.buf].filetype
        if ft == "" or ft == "text" then
            return
        end
        if not queries_added then
            local manager = vim.fn["dpp#get"]("tree-sitter-manager.nvim")
            if manager.path then
                -- Queries are data; keep them available without executing the manager.
                vim.opt.runtimepath:append(manager.path .. "/runtime")
                queries_added = true
            end
        end
        if pcall(vim.treesitter.start, event.buf) then
            return
        end
        local lang = vim.treesitter.language.get_lang(ft)
        if vim.bo[event.buf].buftype ~= "" or vim.list_contains(bundled, lang) then
            return
        end
        -- Installed parsers need no manager UI, installer, or repository catalogue.
        require("tree-sitter-manager")
        if require("tree-sitter-manager.config").effective_repos[lang] then
            vim.cmd.TSInstall(lang)
        end
    end),
})
