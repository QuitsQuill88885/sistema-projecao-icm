#!/bin/bash
# INSTALA o Sistema Nativo num Linux (o caminho feito à mão no Vaio em 07/11/2026, escrito para refazer igual).
# Pré-requisito: a 3.0.12 já instalada em ~/Sistema-ICM/sistema-projecao-3.0.12 (os dados vêm dela) e o código do nativo
# copiado em ~/Sistema-ICM/nativo (a pasta Nativo do PC de casa). Não mexe na 3.0.12 nem no ícone "Sistema ICM".
# uso:  bash ~/Sistema-ICM/nativo/linux/instalar.sh
set -e
VENV="$HOME/.sistema-nativo/venv69"
# 1. o que o Qt precisa do sistema: o plugin xcb do Qt >= 6.5 exige o libxcb-cursor0; wmctrl = "já aberto? traz pra frente"
sudo apt-get install -y libxcb-cursor0 wmctrl python3-venv
# 2. o Python do nativo. Qt 6.9.3 de propósito: do 6.10 em diante as rodas exigem SSE4.2/POPCNT, e processador antigo
#    (o AMD E-450 do Vaio) morre com "invalid opcode" no libshiboken6. pypdfium2 = abrir PDF como apresentação.
mkdir -p "$HOME/.sistema-nativo"
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install -q "PySide6-Essentials==6.9.3" "PySide6-Addons==6.9.3" pypdfium2 "qrcode==8.2"   # 22/11: sem ele o QR do celular saía vazio no Vaio (qr_png engole o erro)
# 3. o lançador e o menu ("Sistema Nativo")
cp "$HOME/Sistema-ICM/nativo/linux/sistema-nativo.sh" "$HOME/sistema-nativo.sh"; chmod +x "$HOME/sistema-nativo.sh"
mkdir -p "$HOME/.local/share/applications"
cp "$HOME/Sistema-ICM/nativo/linux/sistema-nativo.desktop" "$HOME/.local/share/applications/"
# 4. a PLACA (12/11/2026): placa AMD antiga (driver radeon) recebe o conserto do verdão e do congelamento do vídeo, como
#    pacote DKMS (sobrevive às atualizações do kernel). Máquina com outra placa: nada muda.
CONSERTO="$HOME/Sistema-ICM/nativo/ferramentas/radeon_uvd/instalar_conserto_radeon.sh"
if lspci -k 2>/dev/null | grep -A3 -iE "vga|display" | grep -q "radeon"; then
    if /usr/sbin/dkms status radeon-uvd 2>/dev/null | grep -q "$(uname -r).*installed"; then
        echo "placa: conserto do radeon já instalado"
    elif [ -f "$CONSERTO" ]; then
        sudo bash "$CONSERTO" && echo "placa: conserto do radeon instalado (vale depois de reiniciar)"
    else
        echo "AVISO: placa radeon sem o conserto e sem $CONSERTO (o pacote de dados não veio?)"
    fi
fi
# 5. confere: abre a janela de verdade 8 s e fecha sozinho (o Qt 6.9.3 do pip não traz o modo sem tela "offscreen";
#    medido 12/11). Sem tela gráfica (só SSH), pula.
cd "$HOME/Sistema-ICM/nativo"
if [ -n "$DISPLAY" ]; then
    SISTEMA_APP="$HOME/Sistema-ICM/sistema-projecao-3.0.12" QT_QPA_PLATFORM=xcb NATIVO_SO_LOCAL=1 NATIVO_SAIR_EM=8 \
      "$VENV/bin/python" sistema_nativo.py --janela 2>&1 | grep -E "de pé em|Traceback|Error" || true
else
    echo "sem tela gráfica: a conferência de 8 s fica para depois (abra pelo menu)"
fi
echo "pronto: menu > Sistema Nativo"
