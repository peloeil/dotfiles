if status is-interactive
    # Commands to run in interactive sessions can go here
end

# uv
fish_add_path "$HOME/.local/bin"

# miseの初期化
if command -v mise >/dev/null
    mise activate fish | source
end

function sc -d "Assemble x86_64 to shellcode"
    if test (count $argv) -eq 0
        echo "Usage: sc 'mov rax, 1'"
        return 1
    end

    echo ".intel_syntax noprefix; $argv" | as --64 -o /tmp/sc.o
    
    if test $status -eq 0
        objcopy -O binary --only-section=.text /tmp/sc.o /dev/stdout | \
        hexdump -v -e '"\\\" "x" /1 "%02x"'
        echo "" # 改行
        rm /tmp/sc.o
    else
        return 1
    end
end
