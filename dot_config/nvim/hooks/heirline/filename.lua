local conditions = require("heirline.conditions")
local utils = require("heirline.utils")

local filename_block = {
    init = function(self)
        self.filename = vim.api.nvim_buf_get_name(0)
    end,
}
local fileicon = {
    init = function(self)
        local filename = self.filename
        local extension = vim.fn.fnamemodify(filename, ":e")
        self.icon, self.icon_color = require("nvim-web-devicons").get_icon_color(filename, extension, { default = true })
    end,
    provider = function(self)
        return self.icon and (self.icon .. " ")
    end,
    hl = function(self)
        return { fg = self.icon_color }
    end
}

local filename = {
    provider = function(self)
        local filename = vim.fn.fnamemodify(self.filename, ":.")
        if filename == "" then return "[No Name]" end
        if not conditions.width_percent_below(#filename, 0.25) then
            filename = vim.fn.pathshorten(filename)
        end
        return filename
    end,
    hl = { fg = utils.get_highlight("Directory").fg },
}

local fileflags = {
    {
        condition = function()
            return vim.bo.modified
        end,
        provider = "[+]",
        hl = { fg = "green" },
    },
    {
        condition = function()
            return not vim.bo.modifiable or vim.bo.readonly
        end,
        provider = "",
        hl = { fg = "orange" },
    },
}

local filename_modifier = {
    hl = function()
        if vim.bo.modified then
            return { fg = "cyan", bold = true, force = true }
        end
    end,
}

-- let's add the children to our FileNameBlock component
return utils.insert(filename_block,
    fileicon,
    utils.insert(filename_modifier, filename),
    fileflags,
    { provider = '%<'}
)
