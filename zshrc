# zsh-autocomplete
source ~/git/zsh-autocomplete/zsh-autocomplete.plugin.zsh

# Lines configured by zsh-newuser-install
HISTFILE=~/.histfile
HISTSIZE=1000
SAVEHIST=1000
# End of lines configured by zsh-newuser-install

alias ls='ls -clhos --color=auto --group-directories-first'
alias feh='feh -Fd'
alias free='free -h'

function cd {
    builtin cd "$@" && ls
}

export HISTZSIZE=1000
export SAVEHIST=100000
setopt hist_ignore_dups
setopt EXTENDED_HISTORY
export WORDCHAR='*?_.[]~-=&;:#$%^(){}<>'
export PATH=~/.npm-global/bin:$PATH
export PATH=~/.cargo/bin:$PATH

# starship
eval "$(starship init zsh)"

# zsh-autosuggestions
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
