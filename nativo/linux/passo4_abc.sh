#!/bin/bash
# Roda NO VAIO (08/11): o PASSO 4, A/B/C das animações das CIAS no MESMO slide (211), Nativo com o telão no HDMI forçado
# (tampa "aberta", como na igreja), 30 s cada, dados na cópia de teste. A = WebP animado (o padrão), B = folha de sprites
# (NATIVO_ANIM_FORMATO=B, protótipo), C = MP4 pela placa (NATIVO_COM_VIDEO=1, EGL). HDMI desfeito no fim, com prova.
set -u
OUT="${1:-/tmp/passo4}"; mkdir -p "$OUT"
export DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority XDG_RUNTIME_DIR=/run/user/$(id -u)
D="$HOME/Sistema-ICM/med_dados"
MD=~/.config/nemo/desktop-metadata; cp -p "$MD" "$OUT/desktop-metadata.antes"
xrandr | grep -E " connected|HDMI" > "$OUT/xrandr.antes"
xrandr --addmode HDMI-0 1366x768 2>>"$OUT/erros.txt"; xrandr --output HDMI-0 --mode 1366x768 --right-of LVDS 2>>"$OUT/erros.txt"; sleep 8
export MEDIR_SITU=CIAS MEDIR_CIAS=211 MEDIR_SAIR=90
for f in A B C; do
  while [ $(cat /sys/class/thermal/thermal_zone0/temp) -gt 60000 ]; do sleep 10; done
  unset NATIVO_ANIM_FORMATO NATIVO_COM_VIDEO
  [ $f = B ] && export NATIVO_ANIM_FORMATO=B
  [ $f = C ] && export NATIVO_COM_VIDEO=1
  echo "== forma $f $(date +%H:%M:%S)"
  MEDIR_ROTULO=_$f python3 "$OUT/medir_culto_vaio.py" nativo "$D" "$OUT/forma_$f.json" | grep -E "CIAS|subiu|servidor"
  grep -E "telão:" /tmp/medir_culto_nativo.log | head -1
done
xrandr --output LVDS --primary; xrandr --output HDMI-0 --off; xrandr --delmode HDMI-0 1366x768 2>/dev/null; sleep 8
xrandr | grep -E " connected|HDMI" > "$OUT/xrandr.depois"
diff "$OUT/xrandr.antes" "$OUT/xrandr.depois" && echo "HDMI DESFEITO: igual ao antes"
cmp -s "$MD" "$OUT/desktop-metadata.antes" || { echo "a mesa mudou: devolvo"; cp -p "$OUT/desktop-metadata.antes" "$MD"; }
echo "sobrou rodando:"; pgrep -af "sistema_nativo|sistema.py" | grep -v -e pgrep -e passo4 || echo nada
echo "fim $(date +%H:%M:%S) $(cat /sys/class/thermal/thermal_zone0/temp)"
