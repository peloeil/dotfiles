function last_history_item
    echo $history[1]
end

abbr --add !! --position anywhere --function last_history_item
abbr --add co --command git commit
abbr --add st --command git status
abbr --add sw --command git switch
abbr --add swc --command git "switch -c"
abbr --add ls lsd
abbr --add objdump "objdump -d -S -M intel"
