-- lua_post_source {{{
local vimode_block = require("hooks.heirline.vimode")
local filename_block = require("hooks.heirline.filename")
local ruler = { provider = "%7(%l/%3L%):%2c %P" }
local align_block = { provider = "%=" }
local scrollbar = require("hooks.heirline.scrollbar")
local lsp_active = require("hooks.heirline.lsp")

local statusline = {
    vimode_block,
    filename_block,
    lsp_active,
    align_block,
    ruler,
    scrollbar,
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
    git_del = utils.get_highlight("diffDeleted").fg,
    git_add = utils.get_highlight("diffAdded").fg,
    git_change = utils.get_highlight("diffChanged").fg,
}
require("heirline").setup({
    statusline = statusline,
    opts = {
        colors = colors
    }
})
-- }}}
