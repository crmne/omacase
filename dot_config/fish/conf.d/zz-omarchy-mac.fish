# Managed by Omacase. Personal config.fish remains untouched.
fish_add_path --global /opt/homebrew/bin /opt/homebrew/sbin $HOME/.local/bin
if status is-interactive
    set -g fish_greeting
    # OMAfish owns mise, Starship, zoxide and its own shell functions.
    direnv hook fish | source
    fzf --fish | source
    alias ll 'eza --long --all --icons --git --group-directories-first'
    alias la 'eza --all --icons --group-directories-first'
    alias lt 'eza --tree --level=2 --icons'
    alias cat bat
    alias lg lazygit
    alias ld lazydocker
end
