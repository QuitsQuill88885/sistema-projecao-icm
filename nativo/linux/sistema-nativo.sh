#!/bin/bash
# Abre o SISTEMA NATIVO (Python + Qt, sem navegador) no Vaio. 07/11/2026, ordem dele: "instala a versão Blaster no Vaio
# para eu testar". A 3.0.12 continua no ícone "Sistema ICM" (~/sistema-icm.sh), intocada: este é outro programa.
#  - Qt 6.9.3 (venv ~/.sistema-nativo/venv69): o 6.10 em diante exige SSE4.2/POPCNT, que o E-450 não tem
#    (o 6.12 morre com "invalid opcode" no libshiboken6, medido 07/11 02h11).
#  - os dados são os da 3.0.12 do Vaio (louvores, fundos, Bíblia, cifras): SISTEMA_APP aponta para ela.
#  - já aberto? traz para a frente em vez de abrir outro.
export DISPLAY="${DISPLAY:-:0}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"
# 08/11: pelo PROCESSO, não pelo título. O painel passou a se chamar "Sistema" (igual à 3.0.x) e a procura pelo título
# antigo "Sistema Nativo · painel" nunca achava: cada clique no ícone abria OUTRA cópia (ele viu duas às 08h13).
# Aberto (ou ainda carregando, sem janela): traz a janela dele para a frente, se já houver, e NÃO abre outro.
PID=$(pgrep -o -f "venv69/bin/python sistema_nativo[.]py")
if [ -n "$PID" ]; then
  JA=$(wmctrl -lp 2>/dev/null | awk -v p="$PID" '$3 == p { print $1; exit }')
  [ -n "$JA" ] && wmctrl -i -a "$JA"
  exit 0
fi
export SISTEMA_APP="$HOME/Sistema-ICM/sistema-projecao-3.0.12"
cd "$HOME/Sistema-ICM/nativo" || exit 1
# 12/11: o registro tem TETO (o ffmpeg escreve um bloco por vídeo aberto: ~600 KB por 1.160 trocas): passou de 2 MB,
# vira nativo.log.1 (o anterior se apaga) e começa outro
L="$HOME/.sistema-nativo/nativo.log"
[ -f "$L" ] && [ "$(stat -c %s "$L" 2>/dev/null || echo 0)" -gt 2097152 ] && mv -f "$L" "$L.1"
echo "=== $(date '+%F %T') abrindo" >> "$HOME/.sistema-nativo/nativo.log"
exec "$HOME/.sistema-nativo/venv69/bin/python" sistema_nativo.py >> "$HOME/.sistema-nativo/nativo.log" 2>&1
