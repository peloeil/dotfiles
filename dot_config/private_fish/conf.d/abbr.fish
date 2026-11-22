function last_history_item
    echo $history[1]
end

function multicd
    echo (string repeat --count (math (string length -- $argv[1]) - 1) ../ | string trim --right --chars /)
end

abbr --add !! --position anywhere --function last_history_item
abbr --add dotdot --regex '^\.\.\.+$' --function multicd
# --position anywhere だと echo ... なども展開されるため、引数での展開は cd に限る
abbr --add dotdot_cd --regex '^\.\.\.+$' --command cd --function multicd
abbr --add co --command git commit
abbr --add st --command git status
abbr --add sw --command git switch
abbr --add swc --command git "switch -c"
abbr --add ll --command git "log --graph --oneline --all"
abbr --add ls lsd
abbr --add objdump "objdump -S -M intel -d"
