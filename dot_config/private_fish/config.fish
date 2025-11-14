if status is-interactive
    # Commands to run in interactive sessions can go here
end

# uv
fish_add_path "/home/sota/.local/bin"

# miseの初期化
if command -v mise >/dev/null
    mise activate fish | source
end
