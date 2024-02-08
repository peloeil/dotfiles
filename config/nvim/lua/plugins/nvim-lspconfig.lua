return {
    "neovim/nvim-lspconfig",
    event = {
        "BufReadPre",
        "BufNewFile",
    },
    dependencies = {
        "williamboman/mason-lspconfig.nvim",
        dependencies = {
            "hrsh7th/cmp-nvim-lsp",
            "williamboman/mason.nvim",
        },
        config = function()
            local capabilities = require("cmp_nvim_lsp").default_capabilities()
            require("mason-lspconfig").setup_handlers({ function(server)
                local opt = {
                    -- -- Function executed when the LSP server startup
                    -- on_attach = function(client, bufnr)
                    --     local opts = { noremap=true, silent=true }
                    --     vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)
                    --     vim.cmd 'autocmd BufWritePre * lua vim.lsp.buf.formatting_sync(nil, 1000)'
                    -- end,
                    capabilities = capabilities,
                }
                require("lspconfig")[server].setup(opt)
            end })
        end
    },
    config = function()
        local opt = { noremap = true, silent = true }
        -- set buffer local keymap
        vim.keymap.set("n", "K", vim.lsp.buf.hover, opt)
        vim.keymap.set("n", "gd", vim.lsp.buf.definition, opt)
        vim.keymap.set("n", "gf", vim.lsp.buf.format, opt)
        vim.keymap.set("n", "gr", vim.lsp.buf.references, opt)
        vim.keymap.set("n", "gn", vim.lsp.buf.rename, opt)
        -- reference highlight
        vim.api.nvim_create_augroup("lsp_document_highlight", {})
        vim.api.nvim_create_autocmd({ "CursorHold", "CursorHoldI" }, {
            pattern = { "*.c", "*.cpp", "*.py", "*.rust", "*.lua" }, -- workaround
            group = "lsp_document_highlight",
            callback = function()
                vim.lsp.buf.document_highlight()
            end
        })
        vim.api.nvim_create_autocmd({ "CursorMoved", "CursorMovedI" }, {
            pattern = { "*.c", "*.cpp", "*.py", "*.rust", "*.lua" }, -- workaround
            group = "lsp_document_highlight",
            callback = function()
                vim.lsp.buf.clear_references()
            end
        })
        -- TODO: understand the arguments (see help)
        vim.opt.updatetime = 500
        vim.api.nvim_set_hl(0, "LspReferenceText", {
            bg = "#4a4a4a",
            underline = true,
        })
        vim.api.nvim_set_hl(0, "LspReferenceRead", {
            bg = "#4a4a4a",
            underline = true,
        })
        vim.api.nvim_set_hl(0, "LspReferenceWrite", {
            bg = "#4a4a4a",
            underline = true,
        })
    end
}
