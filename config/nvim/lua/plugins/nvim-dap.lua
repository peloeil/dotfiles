return {
    "mfussenegger/nvim-dap",
    keys = {
        "<leader>db",
    },
    dependencies = {
        "theHamsta/nvim-dap-virtual-text",
        {
            "rcarriga/nvim-dap-ui",
            opts = {
                icons = {
                    expanded = "",
                    collapsed = "",
                },
                layouts = {
                    {
                        elements = {
                            { id = "watches", size = 0.20 },
                            { id = "stacks", size = 0.20 },
                            { id = "breakpoints", size = 0.20 },
                            { id = "scopes", size = 0.20 },
                        },
                        size = 64,
                        position = "left",
                    },
                    {
                        elements = {
                            "repl",
                            "console",
                        },
                        size = 0.20,
                        position = "bottom",
                    },
                },
            },
        }
    },
    config = function()
        local dap = require("dap")
        vim.fn.sign_define("DapBreakpoint", { text = "", texthl = "DapBreakpointTextHl" })
        vim.fn.sign_define("DapStopped", { text = "", texthl = "DapStoppedTextHl" })
        dap.adapters = {
            codelldb = {
                type = "server",
                port = "${port}",
                executable = {
                    command = vim.fn.stdpath("data") .. "/mason/packages/codelldb/extension/adapter/codelldb",
                    args = {"--port", "${port}"},
                },
            },
            debugpy = {
                type = "executable",
                command = vim.fn.stdpath("data") .. "/mason/packages/debugpy/venv/bin/python3",
                args = { "-m", "debugpy.adapter" },
            },
        }
        dap.configurations = {
            cpp = {
                {
                    name = "Launch file",
                    type = "codelldb",
                    request = "launch",
                    program = function()
                        return vim.fn.input("Path to executable: ", vim.fn.getcwd() .. "/", "file")
                    end,
                    cwd = "${fileDirname}",
                    stopOnEntry = false,
                },
            },
            rust = {
                {
                    name = "Launch file",
                    type = "codelldb",
                    request = "launch",
                    program = function()
                        return vim.fn.input("Path to executable: ", vim.fn.getcwd() .. "/", "file")
                    end,
                    cwd = "${fileDirname}",
                    stopOnEntry = false,
                },
            },
            python = {
                {
                    name = "Launch file",
                    type = "debugpy",
                    request = "launch",
                    program = function()
                        return vim.fn.input("Path to executable: ", vim.fn.getcwd() .. "/", "file")
                    end,
                    pythonPath = function()
                        return vim.fn.input("Path to python interpreter: ", vim.fn.getcwd() .. "/", "file")
                    end,
                },
            },
        }
        dap.configurations.c = dap.configurations.cpp
        require("nvim-dap-virtual-text").setup()
        -- set keymaps
        local bufnr = vim.api.nvim_get_current_buf()
        local opt = { buffer = bufnr, noremap = true, silent = true }
        local debug_begin = function()
            vim.keymap.set("n", "<F4>", function() require("dap").toggle_breakpoint() end, opt)
            vim.keymap.set("n", "<F5>", function() require("dap").continue() end, opt)
            vim.keymap.set("n", "<F10>", function() require("dap").step_over() end, opt)
            vim.keymap.set("n", "<F11>", function() require("dap").step_into() end, opt)
            vim.keymap.set("n", "<F12>", function() require("dap").step_out() end, opt)
            vim.keymap.set("n", "<leader>b", function() require("dap").toggle_breakpoint() end, opt)
            vim.api.nvim_set_hl(0, "DapBreakpointTextHl", { fg = "#AA0000" })
            vim.api.nvim_set_hl(0, "DapStoppedTextHl", { fg = "#00C853" })
            require("dapui").open()
        end
        vim.keymap.set("n", "<leader>db", debug_begin, opt)
        -- delete keymaps
        local debug_end = function()
            vim.keymap.del("n", "<F4>", { buffer = bufnr })
            vim.keymap.del("n", "<F5>", { buffer = bufnr })
            vim.keymap.del("n", "<F10>", { buffer = bufnr })
            vim.keymap.del("n", "<F11>", { buffer = bufnr })
            vim.keymap.del("n", "<F12>", { buffer = bufnr })
            vim.keymap.del("n", "<leader>b", { buffer = bufnr })
            require("dapui").close()
            require("dap").clear_breakpoints()
            require("dap").disconnect()
        end
        vim.keymap.set("n", "<leader>de", debug_end, opt)
    end
}
