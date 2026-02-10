-- lua_post_source {{{
local conditions = require("heirline.conditions")

local space_block = { provider = " " }
local align_block = { provider = "%=" }

local vimode_block = require("heirline.vimode")
local filename_block = require("heirline.filename")
local ruler_block = { provider = "%7(%l/%3L%):%2c %P" }
local scrollbar_block = require("heirline.scrollbar")
local active_lsp_block = require("heirline.lsp")
local diagnostics_block = require("heirline.diagnostics")
local git_block = require("heirline.git")

local default_statusline = {
    vimode_block,
    space_block,
    filename_block,
    space_block,
    git_block,
    space_block,
    diagnostics_block,
    align_block,
    active_lsp_block,
    ruler_block,
    space_block,
    scrollbar_block,
}

local inactive_statusline = {
    condition = conditions.is_not_active,
    filename_block,
    align_block,
}

local utils = require("heirline.utils")
local colors = {
    bright_bg = utils.get_highlight("Folded").bg,
    bright_fg = utils.get_highlight("Folded").fg,
    red = utils.get_highlight("DiagnosticError").fg,
    dark_red = utils.get_highlight("DiffDelete").bg,
    green = utils.get_highlight("String").fg,
    blue = utils.get_highlight("Function").fg,
    gray = utils.get_highlight("NonText").fg,
    orange = utils.get_highlight("Constant").fg,
    purple = utils.get_highlight("Statement").fg,
    cyan = utils.get_highlight("Special").fg,
    diag_warn = utils.get_highlight("DiagnosticWarn").fg,
    diag_error = utils.get_highlight("DiagnosticError").fg,
    diag_hint = utils.get_highlight("DiagnosticHint").fg,
    diag_info = utils.get_highlight("DiagnosticInfo").fg,
    git_del = utils.get_highlight("diffRemoved").fg,
    git_add = utils.get_highlight("diffAdded").fg,
    git_change = utils.get_highlight("diffChanged").fg,
}

local statusline = {
    hl = function()
        if conditions.is_active() then
            return "StatusLine"
        else
            return "StatusLineNC"
        end
    end,
    fallthrough = false,
    inactive_statusline,
    default_statusline,
}

require("heirline").setup({
    statusline = statusline,
    opts = {
        colors = colors,
    },
})
-- }}}
