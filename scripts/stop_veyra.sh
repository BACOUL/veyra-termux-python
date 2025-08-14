#!/data/data/com.termux/files/usr/bin/bash
tmux kill-session -t veyra 2>/dev/null || true
pkill -f veyra_termux.py 2>/dev/null || true
termux-wake-unlock || true
echo "Veyra arrêté."
