# -*- coding: utf-8 -*-
"""AS TELAS NO LINUX (o Vaio): o ligar_hdmi() da 3.0.12 (linux_nativo.py), a mesma regra, para o Sistema Nativo.

15/10/2026, palavra dele: "no Vaio a projeção pelo HDMI simplesmente não funciona". Com o HDMI plugado mas DESLIGADO ou
ESPELHADO no Cinnamon, o X só mostra uma tela (ou as duas em +0+0) e o telão não tem para onde ir. Na 3.0.12 isto roda no
"Procurar novamente" do cartão (estender_telas) e ao abrir a projeção (_abrir_projecao_linux). O HDMI FORÇADO (o que não
foi detectado, atrás de extensor) é do modo gestos (modo_gestos.forcar_hdmi) e não entra aqui, como lá.

`rodar` é o subprocess.run (as provas passam um falso: nada mexe nas telas de verdade)."""
import re
import subprocess

_GEO = re.compile(r"^\d+x\d+\+-?\d+\+-?\d+$")


def saidas_xrandr(rodar=subprocess.run):
    """[(nome, conectada, primaria, '1366x768+0+0' ou None)] de 'xrandr --query' (o _saidas_xrandr da 3.0.12)."""
    r = rodar(["xrandr", "--query"], capture_output=True, text=True, timeout=5)
    saidas = []
    for linha in (r.stdout or "").splitlines():
        if not linha or linha[0].isspace() or linha.startswith("Screen"):
            continue
        p = linha.split()
        if len(p) < 2:
            continue
        geo = next((x for x in p[2:] if _GEO.match(x)), None)
        saidas.append((p[0], p[1] == "connected", "primary" in p, geo))
    return saidas


def ligar_hdmi(rodar=subprocess.run):
    """HDMI plugado mas DESLIGADO ou ESPELHADO -> estende à direita da principal. Devolve o nome da saída ligada, ou None
    se não havia nada a fazer (uma tela só conectada, ou já estendida)."""
    try:
        ligadas = [s for s in saidas_xrandr(rodar) if s[1]]
    except Exception:
        return None
    if len(ligadas) < 2:
        return None
    prim = next((s for s in ligadas if s[2] and s[3]), None) or next((s for s in ligadas if s[3]), None)
    if prim is None:
        return None
    origem = prim[3].split("+", 1)[1]
    for s in ligadas:
        if s is prim:
            continue
        if s[3] is None or s[3].split("+", 1)[1] == origem:
            try:
                rodar(["xrandr", "--output", s[0], "--auto", "--right-of", prim[0]], capture_output=True, timeout=10)
                return s[0]
            except Exception:
                return None
    return None
