local conditions = require("heirline.conditions")

return {
    condition = conditions.lsp_attached,
    update = { "LspAttach", "LspDetach", "BufEnter" },

    provider = function()
        local names = {}
        for _, server in pairs(vim.lsp.get_clients({ bufnr = 0 })) do
            table.insert(names, server.name)
        end
        return " [" .. table.concat(names, " ") .. "]"
    end,
    hl = { fg = "green", bold = true },
}
