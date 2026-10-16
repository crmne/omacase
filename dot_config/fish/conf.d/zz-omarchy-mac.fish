# Managed by Omacase. Personal config.fish remains untouched.
fish_add_path --global /opt/homebrew/bin /opt/homebrew/sbin $HOME/.local/bin
if status is-interactive
    set -g fish_greeting
    set -gx STARSHIP_CONFIG $HOME/.config/omarchy-mac/starship.toml
    starship init fish | source
    zoxide init fish | source
    mise activate fish | source
    direnv hook fish | source
    fzf --fish | source
    alias ls 'eza --icons --group-directories-first'
    alias ll 'eza --long --all --icons --git --group-directories-first'
    alias la 'eza --all --icons --group-directories-first'
    alias lt 'eza --tree --level=2 --icons'
    alias cat bat
    alias lg lazygit
    alias ld lazydocker
end
