#!/bin/bash
set -euo pipefail

if ! command -v python3 &>/dev/null; then
  echo "Error: python3 is required but not found." >&2
  echo "Install python3 and try again." >&2
  exit 1
fi

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "$DIR" > "$HOME/.robots_repo"

ROBOT=$(cat <<'ROBOT_EOF'
░░        ░
                          ▓▓▓▓▒        ░░░░░░░      ░░░     ▒
                            ░░░░░░░▓▓▓▓▓▓▓▓▓▓▒     ░░      ░░░
                        ░░░░░░   ▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░
                                 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
                      ▒▒▒▒░░░▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▓▓▓▓▓▓▓▓░    ░▒░░░ ░░░░░
              ░▒▓ ▓▓▒▓░    ▓▓▓▓▓▓▓▒▒░▒▓▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
                ▓░    ░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒▒▒▒▒▓▓▓░    ░░░░░░░
                ▒░    ░░▒▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░  ░▒░ ░░░░░
                ▒░    ░▒▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░ ░▒▒
                ▒░  ░ ▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▒▒░░▒░▒░░▒▒▒▒▒▒░▒▒░    ░▒▒▒░░░░
                ▒░   ▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒░░░░░░░▒▒▒▒▒▒░▓▓▒▒▒▒▒▒▒▒▓▒▒▒▒▒
                ▒░ ░░░▒▒▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒░░░░░░░░▒░░░░░▒   ░░▒ ░▓▓▒  ░░░░░░░░░░  ░
        ░░      ▒░   ▓▓▓▓▓▓▓▓▓▓▓░▒▓▓▒   ▒▒▒▒▒▒▒▒▒▓░░░░▒        ▒▒       ░░
              ░░  ▓▓▓▒▒▒▒▓▓▓▓▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░░       ░▒▓ ░     ▒
                ▓░  ░▓▓▓▓▓▓▓▓▓▓▓▓▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▓       ▓▓▓▓▓▒    ▓░
                ▓░  ░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒▒▓▓▓▓░   ▓▓      ░▓░
       ░   ░░ ░ ▓░▓▓░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒░░░        ▓▓ ▓▒▓▒ ▒▓
        ▒ ▓ ▒▓  ░░▓░ ▓▓▓▓▓▓▒▒░░▒▒▒░░▒░░░░░░░░░░░░░░░           ░░ ░▒▒▒ ░▒▒
              ▒▒▓▓▓░ ▓▓▓▓░           ▒▒▒░░▒░░░░░▒           ▒░░▒▒ ░░▒▓▒▓▓▓▒░▒ ▒▓▓▒ ▒
            ▒▒▓▓▓▓▓  ▓▓▓░            ▓▓▒▒▒▒▒▒▒▒░             ░▒▓▓ ░▒▒▓▒▓░░░
             ░▓▓▒▓▓░ ▓▓▓    ░░▒▒▒░    ▓▓▒▒▒▒▒▒▒     ░▒▒▒░░     ▒▓ ░▒▒▓░▓▓▓░░
     ░       ░▓▓▒▓▒░ ▓▓▒░░▓▓▓█████▓▓▓▓▓▓▒▒▒▒▒▒▓  ▓▓▓█████▓▓▓▓▓▓▓▓▓▓▓▒▓░▓░ ▒▒ ▒▒▒▒░
              ░▓░▒▒░ ▓▓▓     ░░░░    ░▓▓▒▒▒▒▒░░     ░░░░░    ░▒▓▓ ░▒▒▒ ▒░
              ▒░ ░▒░ ░▓▓▓           ░▓▓▒▒▒▒▒▒▒▒▓            ░░▓▓   ▒░▒ ▒
               ░▒░░   ▒▓▓▓▒      ░▒▒▓▒▒▒▒▒▒▒▒▒▒▒▒▒        ░░░▒▒▒   ░░░░░
              ░░░░░   ░▓▓▓▒▒▓▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒  ▒▒▒░▒▒▓▓▓▓▒▒▒▓▓▓      ░▒    ░░ ░░░░░
                  ▒      ▓▓▓▓▒▒░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓░░   ▒
                ░░░░▒  ▓░░ ░▒▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓   ░▒▒▒▒░   ▒▒   ░░▒▒▒▒▒░ ▒▒ ░▒▒
                   ░░░░▓▓░   ░▒ ▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░        ░░ ░
                       ▓▓░  ▒ ▓░░▒░  ░░░░▒▒▓▓▓▒▒▒▒▒░  ▓ ░░ ░░▒▓
                      ▒▒▓▓▓ ░ ░░░▒░░░░░░░░░░░░░░ ░░   ░    ░░░   ░░ ░░░░░ ░░░
                ▒▒▒░  ▓▓▓▓░    ▓▓▒░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░ ▒      ▒▒░▒▓    ░░ ░
                      ░░░▓▓▒   ░▒▒▒               ░▒ ░   ░░░░░░░░░░░▒
         ░ ▒░ ▒▒▒▒░▓▒ ░▒  ▓▓▓░  ▒▒  ░▓▓▓▓▓▓▓▓▓▓▓▒  ░░░  ░░▒▒▓▒▓▒▒
                       ░▒▒ ░▓▒▓░▒ ░░ ▓░░░░░░░░░░▒    ░░ ░░░    ░
              ▒░░▒           ▓▓▓▓░▓░░▓▒▒▒▒░▒▒░▒    ░  ░▒
                           ░░░░▓▓▒▓▒░▓▒▒▒▒▒▒▒▒▒▒▒░░▒░░░ ▒▓░  ▒▓▒▒ ▓ ░░▓░
                   ▓▓▒░░▓ ░▒░   ░░▓▒░▓▓▒▒▒▒▒▒▒▒▓▒░▒▒     ░
                                  ▒▓░▓▓▓▓▒▒▒▒▒▒▒░░▒    ░ ░░▒░ ░░░░
                          ▓▒▒░▓▒▒    ░░           ▒▒▒░
                             ░▒ ░░▒▒▒        ░░░░▒▒░ ░░
                                        ▓▓▓▓▓░▒▓
ROBOT_EOF
)

ROBOT2='  .%%%%%%..%%..%%...%%%%...%%%%%%...%%%%...%%......%%......%%%%%%..%%%%%..
  ...%%....%%%.%%..%%........%%....%%..%%..%%......%%......%%......%%..%%.
  ...%%....%%.%%%...%%%%.....%%....%%%%%%..%%......%%......%%%%....%%..%%.
  ...%%....%%..%%......%%....%%....%%..%%..%%......%%......%%......%%..%%.
  .%%%%%%..%%..%%...%%%%.....%%....%%..%%..%%%%%%..%%%%%%..%%%%%%..%%%%%..
  ........................................................................'

install_cli() {
  local dest="$1"
  cp "$DIR/cli/robots" "$dest"
  chmod +x "$dest"
  local dir; dir=$(dirname "$dest")
  cp "$DIR/cli/llm.py" "$dir/llm.py"
  chmod +x "$dir/llm.py" 2>/dev/null || true
}

if cp "$DIR/cli/robots" /usr/local/bin/robots 2>/dev/null; then
  install_cli /usr/local/bin/robots
  DEST="/usr/local/bin/robots"
else
  mkdir -p "$HOME/bin"
  install_cli "$HOME/bin/robots"
  DEST="$HOME/bin/robots"
  if ! echo "$PATH" | tr ':' '\n' | grep -qx "$HOME/bin"; then
    touch "$HOME/.bashrc"
    echo 'export PATH="$PATH:$HOME/bin"' >> "$HOME/.bashrc"
    export PATH="$PATH:$HOME/bin"
  fi
fi

echo "$ROBOT"
echo ""
echo "$ROBOT2"
echo ""
echo "  robots installed to $DEST"
echo ""
echo "  searching for robots.txt..."
FOUND=()
if [ -f "robots.txt" ]; then
  FOUND+=("$(cd "$(dirname "robots.txt")" && pwd)/robots.txt")
fi
if [ -f "../robots.txt" ]; then
  FOUND+=("$(cd .. && pwd)/robots.txt")
fi
if [ -f "../../robots.txt" ]; then
  FOUND+=("$(cd ../.. && pwd)/robots.txt")
fi
for d in */; do
  [ -d "$d" ] && [ -f "${d}robots.txt" ] && FOUND+=("$(cd "$d" && pwd)/robots.txt")
done
for d in */*/; do
  [ -d "$d" ] && [ -f "${d}robots.txt" ] && FOUND+=("$(cd "$d" && pwd)/robots.txt")
done

if [ ${#FOUND[@]} -gt 0 ]; then
  echo ""
  echo "  found ${#FOUND[@]} robots.txt:"
  for i in "${!FOUND[@]}"; do
    echo "    $((i+1))) ${FOUND[$i]}"
  done
  echo ""
  echo "  we need your robots.txt to post."
  read -r -p "  choose (1-${#FOUND[@]}, or enter a path): " choice
  if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -gt 0 ] && [ "$choice" -le "${#FOUND[@]}" ]; then
    idx=$((choice-1))
    "$DEST" -setup "${FOUND[$idx]}"
  else
    if [ -z "$choice" ]; then
      echo "  Error: no path provided." >&2
      echo "  Re-run install.sh and enter a path to your robots.txt." >&2
      exit 1
    fi
    "$DEST" -setup "$choice"
  fi
else
  echo ""
  echo "  none found."
  echo "  where is your robots.txt file?"
  echo ""
  "$DEST" -setup
fi
