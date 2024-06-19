#!/bin/bash

# Absolute path to the project root
PROJECT_ROOT="$(pwd)"

# Create a command script
echo "#!/bin/bash

# Navigate to the project root
cd $PROJECT_ROOT

# Run the main shell script
./snakeman_execute.sh
" > $PROJECT_ROOT/run_snakeman.sh

# Make the command script executable
chmod +x $PROJECT_ROOT/run_snakeman.sh

# Create an alias in the shell configuration
SHELL_CONFIG="$HOME/.bashrc"
if [ "$SHELL" == "/bin/zsh" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
fi

# Check if the alias already exists
if ! grep -q "alias snakeman='$PROJECT_ROOT/run_snakeman.sh'" $SHELL_CONFIG; then
    echo "alias snakeman='$PROJECT_ROOT/run_snakeman.sh'" >> $SHELL_CONFIG
    echo "Alias 'snakeman' added to $SHELL_CONFIG"
else
    echo "Alias 'snakeman' already exists in $SHELL_CONFIG"
fi

# Reload the shell configuration
source $SHELL_CONFIG

echo "Setup complete. You can now use the command 'snakeman' to run the project."
