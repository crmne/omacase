# Set paths and prompt configuration before OMAfish's init.fish runs.
fish_add_path --global /opt/homebrew/bin /opt/homebrew/sbin $HOME/.local/bin
set -gx STARSHIP_CONFIG $HOME/.config/omarchy-mac/starship.toml
