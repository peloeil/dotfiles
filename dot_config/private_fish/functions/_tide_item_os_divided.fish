# Tide picks one separator style for every same-colored pair, so the line
# between the hostname and the OS icon has to come from a dedicated item.
function _tide_item_os_divided
    set -g prev_bg_color $tide_os_bg_color
    tide_left_prompt_separator_same_color='│' _tide_print_item os $tide_os_icon
end
