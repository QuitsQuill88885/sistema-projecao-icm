#!/bin/bash
# Roda NO VAIO (08/11): o PASSO 3, CPU e RAM do Nativo x 3.0.12 nas 4 situações do culto, com o HDMI FORÇADO (sem TV,
# como o roteiro 270 da casa) e DESFEITO no fim, com prova. Os dados vão numa CÓPIA (o histórico da igreja não é tocado).
# uso: bash passo3_cpu_ram.sh /tmp/passo3
set -u
OUT="${1:-/tmp/passo3}"; mkdir -p "$OUT"
export DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority XDG_RUNTIME_DIR=/run/user/$(id -u)
D="$HOME/Sistema-ICM/med_dados"
echo "== $(date +%H:%M:%S) $(cat /sys/class/thermal/thermal_zone0/temp) disco livre: $(df -h $HOME | tail -1 | awk '{print $4}')"
if [ ! -d "$D/Sistema Projecao" ]; then mkdir -p "$D"; nice -n 19 cp -a "$HOME/Sistema Projecao" "$D/"; fi
echo "dados de teste: $(du -sh "$D" | cut -f1)"
MD=~/.config/nemo/desktop-metadata; cp -p "$MD" "$OUT/desktop-metadata.antes"; md5sum "$MD" | cut -c1-12
xrandr | grep -E " connected|HDMI" > "$OUT/xrandr.antes"
# o HDMI forçado (o mesmo da igreja: a TV vira a 2ª tela à direita)
xrandr --addmode HDMI-0 1366x768 2>>"$OUT/erros.txt"; xrandr --output HDMI-0 --mode 1366x768 --right-of LVDS 2>>"$OUT/erros.txt"
sleep 8; xrandr | grep -E " connected|HDMI" | tee "$OUT/xrandr.forcado"
PY=python3
$PY "$OUT/medir_culto_vaio.py" nativo "$D" "$OUT/nativo.json"
while [ $(cat /sys/class/thermal/thermal_zone0/temp) -gt 60000 ]; do sleep 10; done
$PY "$OUT/medir_culto_vaio.py" 312 "$D" "$OUT/312.json"
# DESFAZ o HDMI e PROVA
xrandr --output LVDS --primary; xrandr --output HDMI-0 --off; xrandr --delmode HDMI-0 1366x768 2>/dev/null
sleep 8; xrandr | grep -E " connected|HDMI" | tee "$OUT/xrandr.depois"
diff "$OUT/xrandr.antes" "$OUT/xrandr.depois" && echo "HDMI DESFEITO: igual ao antes"
if ! cmp -s "$MD" "$OUT/desktop-metadata.antes"; then echo "a mesa mudou: devolvo o desktop-metadata de antes"; cp -p "$OUT/desktop-metadata.antes" "$MD"; fi
md5sum "$MD" | cut -c1-12
echo "sobrou rodando:"; pgrep -af "sistema_nativo|sistema.py" | grep -v -e pgrep -e passo3 || echo nada
echo "fim $(date +%H:%M:%S) $(cat /sys/class/thermal/thermal_zone0/temp)"
