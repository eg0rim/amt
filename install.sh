#!/usr/bin/env bash

# Install script for unix-based systems

echo "This script will install the article management tool and its dependencies."

echo "Do you want to continue? [y/n]"   
read answer
if [ "$answer" != "y" ]; then
    echo "Installation aborted."
    exit 1
fi

# Check if python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 is not installed. Please, install python3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null
then
    echo "Pip is not installed. Please, install pip and try again."
    exit 1
fi

# Define paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"
BINFILE_DIR="$SCRIPT_DIR/installation_files"
DESKTOPFILE_DIR="$SCRIPT_DIR/installation_files"
BIN_SCRIPT="$BINFILE_DIR/amt"
DESKTOP_FILE="$DESKTOPFILE_DIR/article-management-tool.desktop"
ENTRY_POINT="$SCRIPT_DIR/articlemanagementtool.py"

# Create the virtual environment
echo "Creating virtual environment..."
python3 -m venv $VENV_DIR

# Activate the virtual environment
source $VENV_DIR/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r REQUIREMENTS.txt

# Compile Qt resources and ui files
echo "Compiling Qt resources and ui files..."
make all

# Create dirs if they don't exist
mkdir -p $BINFILE_DIR
mkdir -p $DESKTOPFILE_DIR

# Generate bin file 
echo "Generating bin file..."
cat <<EOL > "$BIN_SCRIPT"
#!/bin/env bash

source $VENV_DIR/bin/activate
$SCRIPT_DIR/articlemanagementtool.py
deactivate
EOL

# Generate desktop file
# Extract version from __init__.py
VERSION=$(grep "__version__" "$SCRIPT_DIR/amt/__init__.py" | cut -d '"' -f 2)
echo "Generating desktop file..."
cat <<EOL > "$DESKTOP_FILE"
[Desktop Entry]
Version=$VERSION
Name=Article Management Tool
GenericName=Article Management Tool
Comment=Manage your articles efficiently
Exec=amt
Icon=$SCRIPT_DIR/amt/views/resources/files/logo.png
Type=Application
Terminal=false
Categories=Office;Utility;
StartupNotify=true
EOL

# Make files executable
chmod +x $BIN_SCRIPT
chmod +x $ENTRY_POINT

# Move files 
echo "Do you want to move bin file to $HOME/bin? [y/n]"
read answer
if [ "$answer" == "y" ]; then
    mkdir -p $HOME/bin
    mv $BIN_SCRIPT $HOME/bin
    echo "Bin file moved to $HOME/bin. Make sure $HOME/bin is in your PATH."
else
    echo "You can find the bin file in $BIN_SCRIPT. Move it to an appropriate location and add the location to PATH."
fi

echo "Do you want to move desktop file to $HOME/.local/share/applications? [y/n]"
read answer
if [ "$answer" == "y" ]; then
    mkdir -p $HOME/.local/share/applications
    mv $DESKTOP_FILE $HOME/.local/share/applications
    echo "Desktop file moved to $HOME/.local/share/applications. Make sure that amt executable is in your PATH."
else
    echo "You can find the desktop file in $DESKTOP_FILE. Move it to an appropriate location."
fi

echo "Installation completed."

