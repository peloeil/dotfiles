if test -f "$HOME/.cargo/env.fish"
    source "$HOME/.cargo/env.fish"
end

# Fish 4.3 moved fish_key_bindings from universal to global scope.
# Tide renders prompts in a non-interactive `fish -c`, so this must not be
# gated on `status is-interactive`.
set -g fish_key_bindings fish_default_key_bindings

set -gx EDITOR nvim
set -gx VISUAL nvim

# Make mise available before activation.
fish_add_path --path "$HOME/.local/bin"

# miseの初期化
if command -v mise >/dev/null
    if status is-interactive
        mise activate fish | source
    else
        mise activate fish --shims | source
    end
end

# Prefer standalone tools over mise shims, including inherited PATH entries.
fish_add_path --path --move --prepend "$HOME/.local/bin"

function sc -d "Assemble x86_64 to shellcode"
    if test (count $argv) -eq 0
        echo "Usage: sc 'mov rax, 1'"
        return 1
    end

    set -l object_file (mktemp); or return 1
    printf '%s\n' ".intel_syntax noprefix; $argv" | as --64 -o "$object_file"
    set -l result $status

    if test $result -eq 0
        objcopy -O binary --only-section=.text "$object_file" /dev/stdout | \
        hexdump -v -e '"\\\" "x" /1 "%02x"'
        if test "$pipestatus" != "0 0"
            set result 1
        end
        echo "" # 改行
    end

    rm -f -- "$object_file"
    return $result
end
