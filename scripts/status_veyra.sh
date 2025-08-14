#!/data/data/com.termux/files/usr/bin/bash
tmux ls 2>/dev/null | grep veyra && echo "tmux OK" || echo "tmux: non démarré"
[ -f ~/veyra-termux/tunnel_url.txt ] && echo "URL: $(cat ~/veyra-termux/tunnel_url.txt)" || echo "URL: inconnue"
