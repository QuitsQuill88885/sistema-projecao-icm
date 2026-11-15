#!/bin/bash
# Roda NO VAIO (08/11): a MEDIDA para encolher o venv69 na TELA REAL (:0), não no Xvfb (o Xvfb carrega outros plugins
# de desenho e o encolher tiraria os da tela de verdade). Duas voltas pelo medir_no_vaio.py (louvor, CIAS, Bíblia,
# apresentação animada; fecha sozinho): uma normal e uma com o vídeo ligado (a medida C do A/B/C usa o QtMultimedia).
# Em cada volta, aos 80 s, o encolher_venv.py medir lê o /proc/<pid>/maps e o QML_IMPORT_TRACE. Junta as duas.
# Não encolhe nada: só mede e faz o ENSAIO. uso: bash medir_para_encolher.sh <pasta de saída>
set -u
OUT="${1:-/tmp/encolher}"; mkdir -p "$OUT"
PROG="$HOME/Sistema-ICM/nativo"; PY="$HOME/.sistema-nativo/venv69/bin/python"; ENC="$OUT/encolher_venv.py"
export DISPLAY=:0 SISTEMA_APP="$HOME/Sistema-ICM/sistema-projecao-3.0.12" QML_IMPORT_TRACE=1 XDG_RUNTIME_DIR=/run/user/1000
for volta in normal video; do
  if [ "$volta" = video ]; then export NATIVO_COM_VIDEO=1; else unset NATIVO_COM_VIDEO; fi
  echo "== volta $volta $(date +%H:%M:%S) $(cat /sys/class/thermal/thermal_zone0/temp)"
  ( cd "$PROG" && MEDIR_SEG=110 "$PY" ferramentas/medir_no_vaio.py > "$OUT/medir_$volta.txt" 2>&1 ) &
  sleep 80
  ENCOLHER_LOG=/tmp/medir_no_vaio.log python3 "$ENC" medir "$OUT/medida_$volta.json"
  cp /tmp/medir_no_vaio.log "$OUT/log_$volta.txt"
  wait
  tail -5 "$OUT/medir_$volta.txt"
  sleep 20
done
python3 - "$OUT" <<'EOF'
import json, sys, os
o = sys.argv[1]
a = [json.load(open(os.path.join(o, "medida_%s.json" % v))) for v in ("normal", "video")]
j = {"so": sorted(set(a[0]["so"]) | set(a[1]["so"])), "qml": sorted(set(a[0]["qml"]) | set(a[1]["qml"]))}
json.dump(j, open(os.path.join(o, "medida.json"), "w"), indent=1)
print("juntas:", len(j["so"]), "bibliotecas,", len(j["qml"]), "módulos QML (normal %d/%d, video %d/%d)"
      % (len(a[0]["so"]), len(a[0]["qml"]), len(a[1]["so"]), len(a[1]["qml"])))
EOF
python3 "$ENC" ensaio "$OUT/medida.json" | tail -25
echo "fim $(date +%H:%M:%S) $(cat /sys/class/thermal/thermal_zone0/temp); sobrou rodando:"; pgrep -af sistema_nativo || echo nada
