#!/bin/bash
# Roda NO VAIO (08/11): o PASSO 8, a prova de que o "carregando" não fica preto e a tela não se rearruma. Abre o Nativo
# de verdade na tela do notebook (dados na cópia de teste, servidor só local, fecha sozinho) e FILMA a tela a 10 quadros
# por segundo (ffmpeg x11grab). Depois: a régua (brilho do meio da tela em cada quadro) e uma folha com os quadros.
# uso: bash passo8_filme_subida.sh /tmp/passo8
set -u
OUT="${1:-/tmp/passo8}"; rm -rf "$OUT/q"; mkdir -p "$OUT/q"
export DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority XDG_RUNTIME_DIR=/run/user/$(id -u)
echo "== $(date +%H:%M:%S) $(cat /sys/class/thermal/thermal_zone0/temp)"
nice -n 5 ffmpeg -loglevel error -y -f x11grab -framerate 10 -video_size 1366x768 -i :0+0,0 -t 16 "$OUT/q/%03d.png" &
FF=$!
sleep 1
cd "$HOME/Sistema-ICM/nativo"
APPDATA="$HOME/Sistema-ICM/med_dados" SISTEMA_APP="$HOME/Sistema-ICM/sistema-projecao-3.0.12" NATIVO_SO_LOCAL=1 \
  NATIVO_SAIR_EM=14 NATIVO_TAMPA=aberta NATIVO_TEMPOS=1 PYTHONIOENCODING=utf-8 \
  "$HOME/.sistema-nativo/venv69/bin/python" sistema_nativo.py > "$OUT/log.txt" 2>&1
wait $FF
grep -E "de pé|tela de carregamento|QML carregado|telão:" "$OUT/log.txt" | head -6
ls "$OUT/q" | wc -l
echo "sobrou rodando:"; pgrep -af "sistema_nativo" | grep -v -e pgrep -e passo8 || echo nada
