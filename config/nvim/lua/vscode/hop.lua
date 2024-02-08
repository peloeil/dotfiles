return {
    "smoka7/hop.nvim",
    keys = {
        { "f", function() require("hop").hint_char1() end, { remap = true } },
        { "t", function() require("hop").hint_lines() end, { remap = true } },
    },
    version = "*",
    config = function()
        require("hop").setup() -- required
    end
}
