if test -f "$HOME/.cargo/env.fish"
    source "$HOME/.cargo/env.fish"
end

# Fish 4.3 moved fish_key_bindings from universal to global scope.
# Tide renders prompts in a non-interactive `fish -c`, so this must not be
# gated on `status is-interactive`.
set -g fish_key_bindings fish_default_key_bindings

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
