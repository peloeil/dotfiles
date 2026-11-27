vim.o.autocomplete = true
-- 前にある出どころほど時間を多く割り当てられるので、応答の遅い LSP（o）を先頭に置く
vim.o.complete = "o,.,w,b"
-- 'autocomplete' が自動で付ける noselect は、LSP が非同期に呼ぶ complete() には効かず、
-- 1つ目の候補が勝手に挿入されるので明示する
vim.opt.completeopt:append({ "menuone", "noselect", "fuzzy" })

vim.keymap.set("i", "<CR>", function()
    local selected = vim.fn.pumvisible() == 1 and vim.fn.complete_info({ "selected" }).selected ~= -1
    return selected and "<C-y>" or "<CR>"
end, { expr = true })

local function lsp_item(item)
    return vim.tbl_get(item, "user_data", "nvim", "lsp", "completion_item")
end

local scores = {}
local function fuzzy_score(item)
    local before_cursor = vim.api.nvim_get_current_line():sub(1, vim.fn.col(".") - 1)
    local prefix = vim.fn.matchstr(before_cursor, [[\k*$]])
    if scores.prefix ~= prefix then
        scores = { prefix = prefix, texts = {} }
    end
    if prefix == "" then
        return 0
    end
    -- LSP の候補は word で比べない。rust-analyzer の iter().partition(…) のような候補は
    -- word が "iter" になり、本命の iter() より上に来てしまう
    local lsp = lsp_item(item)
    local text = lsp and (lsp.filterText or lsp.label) or item.word
    if scores.texts[text] == nil then
        scores.texts[text] = vim.fn.matchfuzzypos({ text }, prefix)[3][1] or -math.huge
    end
    return scores.texts[text]
end

-- 標準の並べ替えは、サーバーが isIncomplete を返すと（rust-analyzer など）あいまい一致の
-- スコアを使わず sortText の順になり、".it" で iter より split_off が上に来る。
-- 同じ単語は LSP の候補を前に置く。LSP の候補は dup = 1 なので、complete() の重複除去で
-- 落ちるのは後ろのバッファの単語になる
local function compare(a, b)
    local score_a, score_b = fuzzy_score(a), fuzzy_score(b)
    if score_a ~= score_b then
        return score_a > score_b
    end
    local lsp_a, lsp_b = lsp_item(a), lsp_item(b)
    if (lsp_a ~= nil) ~= (lsp_b ~= nil) then
        return lsp_a ~= nil
    end
    local key_a = lsp_a and (lsp_a.sortText or lsp_a.label) or a.word
    local key_b = lsp_b and (lsp_b.sortText or lsp_b.label) or b.word
    return key_a < key_b
end

-- 'complete' の o だけでは、"." や "->" のようなキーワード以外の文字で補完が始まらず、
-- <C-y> で確定したときの自動 import などの追加編集も適用されない
vim.api.nvim_create_autocmd("LspAttach", {
    group = vim.api.nvim_create_augroup("__lsp_completion", { clear = true }),
    callback = function(event)
        local client = assert(vim.lsp.get_client_by_id(event.data.client_id))
        if client:supports_method("textDocument/completion") then
            vim.lsp.completion.enable(true, client.id, event.buf, { autotrigger = true, cmp = compare })
        end
    end,
})
