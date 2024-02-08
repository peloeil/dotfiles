return {
    "zbirenbaum/copilot.lua",
    event = {
        "InsertEnter",
    },
    config = function()
        require("copilot").setup({
            panel = {
                auto_refresh = true,
                keymap = {
                    open = "<leader>cp",
                },
                layout = {
                    position = "right",
                    ratio = 0.4,
                },
            },
            suggestion = {
                auto_trigger = true,
                keymap = {
                    accept = "<C-a>",
                    accept_word = "<C-k>",
                    accept_line = "<C-l>",
                },
            },
        })
    end
}
