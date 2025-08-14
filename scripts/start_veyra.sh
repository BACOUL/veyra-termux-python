#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd ~/veyra-termux
termux-wake-lock || true

# stop anciens services
tmux kill-session -t veyra 2>/dev/null || true
pkill -f veyra_termux.py 2>/dev/null || true
: > tunnel.log

# lance Flask dans tmux (pane 0)
tmux new-session -d -s veyra "python app/veyra_termux.py"

# pane 1 : boucle de tunnel avec reconnexion automatique
tmux split-window -h -t veyra "bash -lc '
  while true; do
    echo \"[tunnel] starting...\" | tee -a tunnel.log
    ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:8787 nokey@localhost.run 2>&1 | tee -a tunnel.log
    echo \"[tunnel] disconnected, retry in 3s\" | tee -a tunnel.log
    sleep 3
  done
'"

tmux select-layout -t veyra even-horizontal

# essaie d'extraire l'URL en continu (arrière-plan)
( while true; do
    URL=$(grep -oE 'https://[a-zA-Z0-9.-]+(lhr\.life|localhost\.run)' tunnel.log | tail -n1 || true)
    if [ -n "$URL" ]; then echo "$URL" > tunnel_url.txt; fi
    sleep 2
  done ) >/dev/null 2>&1 &

sleep 5
[ -f tunnel_url.txt ] && echo "Veyra en ligne : $(cat tunnel_url.txt)" || echo "URL pas encore capturée. tail -f tunnel.log"
echo "Attache tmux :  tmux attach -t veyra   (Ctrl+b puis d pour détacher)"
