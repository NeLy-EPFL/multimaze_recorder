#!/bin/bash
# Install a desktop shortcut for Multimaze Recorder.
# Run once per user after uv sync.

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICON="$REPO_DIR/assets/icon.svg"
APP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$APP_DIR/multimaze_recorder.desktop"

mkdir -p "$APP_DIR"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Multimaze Recorder
GenericName=Maze Recording Software
Comment=High-throughput recording for the multimaze experimental setup
Exec=$REPO_DIR/RunGUI.sh
Icon=$ICON
Terminal=false
Categories=Science;
Keywords=maze;recorder;camera;imaging;
StartupWMClass=MainWindow
EOF

chmod +x "$DESKTOP_FILE"
echo "Shortcut installed: $DESKTOP_FILE"

# Also place on Desktop if the folder exists
if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP_FILE" "$HOME/Desktop/multimaze_recorder.desktop"
    chmod +x "$HOME/Desktop/multimaze_recorder.desktop"
    # Mark as trusted so GNOME allows launching it
    gio set "$HOME/Desktop/multimaze_recorder.desktop" metadata::trusted true 2>/dev/null || true
    echo "Also placed on Desktop."
fi

# Refresh the application menu
update-desktop-database "$APP_DIR" 2>/dev/null || true

echo "Done. You may need to log out and back in for the app menu entry to appear."
