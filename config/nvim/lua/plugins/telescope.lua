return {
    "nvim-telescope/telescope.nvim",
    branch = "0.1.x",
    keys = {
        { "<leader>ff", function() require("telescope.builtin").find_files() end },
        { "<leader>fg", function() require("telescope.builtin").live_grep() end },
        { "<leader>fb", function() require("telescope.builtin").buffers() end },
        { "<leader>fh", function() require("telescope.builtin").help_tags() end },
        { "<leader>fc", function() require("telescope.builtin").oldfiles() end },
        { "<leader>ft", function()
            vim.cmd.tabnew()
            require("telescope.builtin").find_files()
        end },
    },
    dependencies = {
        "nvim-lua/plenary.nvim",
        "nvim-tree/nvim-web-devicons",
        {
            "nvim-telescope/telescope-fzf-native.nvim",
            build = "cmake -S. -Bbuild -DCMAKE_BUILD_TYPE=Release && cmake --build build --config Release && cmake --install build --prefix build",
            config = function()
                require("telescope").load_extension("fzf")
            end
        },
    },
    -- TODO: complete configurations
    config = function()
        local telescopeConfig = require("telescope.config")
        -- Clone the default Telescope configuration
        local vimgrep_arguments = { unpack(telescopeConfig.values.vimgrep_arguments) }
        -- I want to search in hidden/dot files.
        table.insert(vimgrep_arguments, "--hidden")
        -- I don't want to search in the `.git` directory.
        table.insert(vimgrep_arguments, "--glob")
        table.insert(vimgrep_arguments, "!**/.git/*")
        require("telescope").setup({
            defaults = {
                -- `hidden = true` is not supported in text grep commands.
                vimgrep_arguments = vimgrep_arguments,
                mapping = {
                    n = {
                        ["q"] = require("telescope.actions").close,
                    },
                },
            },
            pickers = {
                find_files = {
                    -- `hidden = true` will still show the inside of `.git/` as it's not `.gitignore`d.
                    find_command = { "rg", "--files", "--hidden", "--glob", "!**/.git/*" },
                    mappings = {
                        n = {
                            ["cd"] = function(prompt_bufnr)
                                local selection = require("telescope.actions.state").get_selected_entry()
                                local dir = vim.fn.fnamemodify(selection.path, ":p:h")
                                require("telescope.actions").close(prompt_bufnr)
                                -- depending on what you want put `cd`, `lcd`, `tcd`
                                vim.cmd(string.format("silent tcd %s", dir))
                                require("telescope.builtin").find_files()
                            end,
                        },
                    },
                },
            },
        })
    end
}
