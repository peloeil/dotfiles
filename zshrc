source ~/AUR/zsh-autocomplete/zsh-autocomplete.plugin.zsh
eval "$(starship init zsh)"

alias ls='ls -lhsX --color=auto --group-directories-first'
function cd {
    builtin cd "$@" && ls
}

# 履歴ファイルの保存先
export HISTFILE=${HOME}/.zsh_history
# メモリに保存される履歴の件数
export HISTSIZE=1000
# 履歴ファイルに保存される履歴の件数
export SAVEHIST=100000
# zsh: do you wish to see all N possibilities ?
export LISTMAX=1000
# 重複を記録しない
setopt hist_ignore_dups
# 開始と終了を記録
setopt EXTENDED_HISTORY

export WORDCHARS='*?_.[]~-=&;!#$%^(){}<>'
export PATH=~/.npm-global/bin:$PATH

source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh

