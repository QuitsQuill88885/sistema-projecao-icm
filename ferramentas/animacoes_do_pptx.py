# -*- coding: utf-8 -*-
"""Refaz as telas animadas das CIAS a partir dos PowerPoints oficiais.

POR QUE EXISTE (medido em 05/10/2026):
  O pacote do Glorifica (PT_ColetaneaCIAS_2018_Gifs.pkr), de onde o Sistema
  importava, entrega 147 das 336 telas JA ACHATADAS (um quadro so: a animacao
  foi jogada fora na exportacao dele) e so cobre 110 dos 241 louvores — para
  no 142. Os PowerPoints da pasta "LOUVORES CIAS 4.3 - COM ANIMACOES" (do RAR
  "PROJECAO R.MS POWER POINT", achado pelo Samuel) trazem os 241, com todos os
  slides e os GIFs animados de verdade (o coracao que pulsa, a nota que gira).

COMO FUNCIONA — EM ANDARES (a 1a versao colava o GIF por cima de tudo e, no
louvor 39, o GIF do FUNDO teria APAGADO A LETRA; medido, nao suposto):
  1. Do XML de cada slide sai a pilha de formas, de baixo para cima. Ela e
     cortada em ANDARES: faixas de formas comuns separadas pelos GIFs.
  2. O PowerPoint (SEM JANELA: WithWindow=False) exporta, para cada andar de
     formas comuns, a camada sozinha sobre fundo PRETO e sobre fundo BRANCO.
     Com as duas sai a camada recortada exata, com a borda suave da letra
     (recorte por dois fundos: alfa = 1 - (branco - preto)/255).
     ARMADILHA: Slide.Export ESTOURA sem janela; Presentation.Export funciona.
  3. A tela e montada de baixo para cima: o andar de baixo (com o fundo do
     slide), depois cada GIF no seu quadro do momento, depois cada camada
     recortada por cima — o que estava sobre o GIF continua sobre o GIF.
  4. Cada GIF anda na propria velocidade; o laco dura o do GIF mais longo.
  5. CONFERENCIA DA TELA INTEIRA: o 1o quadro montado tem de ser igual ao slide
     que o proprio PowerPoint desenha com tudo junto. O que nao bater sai como
     SUSPEITO no relatorio, e a tela suspeita NAO vai para o indice.
  6. Os botoes de navegacao do PowerPoint ("INDICE"...) saem antes de exportar
     — so na memoria; o arquivo original nunca e salvo.

Grava LOUVOR POR LOUVOR e retoma de onde parou.

Uso:
    python animacoes_do_pptx.py <pasta_dos_pptx> <pasta_de_saida> [--so 38,97] [--refazer]
"""
import io
import json
import os
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
A = "{%s}" % NS["a"]
P = "{%s}" % NS["p"]
R = "{%s}" % NS["r"]

LARGURA = 1440                 # o mesmo das telas que o Sistema ja usa
QUALIDADE_ANIMADA = 72         # o mesmo do importar_animacoes.py
QUALIDADE_PARADA = 82
PASSO_MS = 60                  # amostragem do tempo da animacao
MAX_QUADROS = 40               # teto: acima disso o passo cresce
# conferencia da tela inteira (diferenca de 0 a 255)
LIMITE_MEDIA = 2.0             # media sobre a tela toda
LIMITE_PICO = 90.0             # 99,9% dos pixels abaixo disto
BOTOES = {"INDICE", "ÍNDICE", "VOLTAR", "MENU", "INICIO", "INÍCIO", "PROXIMO", "PRÓXIMO"}
GRUPO = 6                      # msoGroup


# ================================================================== XML
def _xfrm(el):
    x = el.find(A + "off")
    e = el.find(A + "ext")
    if x is None or e is None:
        return None
    r = [int(x.get("x")), int(x.get("y")), int(e.get("cx")), int(e.get("cy"))]
    co, ce = el.find(A + "chOff"), el.find(A + "chExt")
    if co is not None and ce is not None:
        r += [int(co.get("x")), int(co.get("y")), int(ce.get("cx")), int(ce.get("cy"))]
    return r


def _id(no):
    c = no.find(".//" + P + "cNvPr")
    return int(c.get("id")) if c is not None and c.get("id", "").isdigit() else None


def _gif(no, rels, transf, avisos):
    """Se `no` e figura .gif, devolve o dicionario dela (posicao no slide)."""
    blip = no.find(".//" + A + "blip")
    if blip is None:
        return None
    alvo = rels.get(blip.get(R + "embed") or "")
    if not alvo or not alvo.lower().endswith(".gif"):
        return None
    xf = no.find(P + "spPr/" + A + "xfrm")
    g = _xfrm(xf) if xf is not None else None
    if not g:
        avisos.append("gif sem posicao propria: %s" % alvo)
        return None
    # giro em 60000 avos de grau, no sentido do relogio; espelho antes do giro
    giro = int(xf.get("rot") or 0) / 60000.0
    espelho_h, espelho_v = xf.get("flipH") == "1", xf.get("flipV") == "1"
    if no.find(".//" + A + "effectLst/*") is not None:
        avisos.append("gif com SOMBRA/BRILHO (efeito que nao se refaz quadro a quadro): %s" % alvo)
    corte = (0, 0, 0, 0)
    sr = no.find(".//" + A + "srcRect")
    if sr is not None:   # l/t/r/b em milesimos de por cento
        corte = tuple(int(sr.get(k) or 0) / 100000.0 for k in ("l", "t", "r", "b"))
    x, y, cx, cy = transf(*g[:4])
    midia = os.path.normpath(os.path.join("ppt/slides", alvo)).replace("\\", "/")
    return {"id": _id(no), "midia": midia, "x": x, "y": y, "cx": cx, "cy": cy, "corte": corte,
            "giro": giro, "espelho_h": espelho_h, "espelho_v": espelho_v}


def _gifs_dentro(no, rels, transf, avisos):
    """Todos os GIFs dentro de um grupo (com a transformacao dos subgrupos)."""
    saida = []
    for filho in no:
        if filho.tag == P + "pic":
            g = _gif(filho, rels, transf, avisos)
            if g:
                saida.append(g)
        elif filho.tag == P + "grpSp":
            saida += _gifs_dentro(filho, rels, _transf_grupo(filho, transf), avisos)
    return saida


def _transf_grupo(grupo, transf):
    gx = grupo.find(P + "grpSpPr/" + A + "xfrm")
    g = _xfrm(gx) if gx is not None else None
    if not g or len(g) != 8:
        return transf
    if gx.get("rot") not in (None, "0") or gx.get("flipH") == "1" or gx.get("flipV") == "1":
        # grupo girado/espelhado: a posicao dos filhos sai errada; a conferencia
        # da tela inteira pega, e a tela cai no render parado do PowerPoint
        pass
    ox, oy, ocx, ocy, chx, chy, chcx, chcy = g
    sx = ocx / float(chcx) if chcx else 1.0
    sy = ocy / float(chcy) if chcy else 1.0

    def novo(x, y, cx, cy):
        return transf(ox + (x - chx) * sx, oy + (y - chy) * sy, cx * sx, cy * sy)
    return novo


def le_slide(z, n):
    """A pilha do slide, de baixo para cima: [{"id", "gifs": [...]}],
    onde "gifs" vazio = forma comum. E mais avisos, oculto, efeitos."""
    raiz = ET.fromstring(z.read("ppt/slides/slide%d.xml" % n))
    cam = "ppt/slides/_rels/slide%d.xml.rels" % n
    rels = {}
    if cam in z.namelist():
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read(cam))}
    avisos, pilha = [], []
    ident = lambda x, y, cx, cy: (x, y, cx, cy)   # noqa: E731
    arvore = raiz.find(P + "cSld/" + P + "spTree")
    if arvore is not None:
        for f in arvore:
            if f.tag in (P + "nvGrpSpPr", P + "grpSpPr"):
                continue
            if f.tag == P + "pic":
                g = _gif(f, rels, ident, avisos)
                pilha.append({"id": _id(f), "gifs": [g] if g else [], "grupo": False})
            elif f.tag == P + "grpSp":
                gs = _gifs_dentro(f, rels, _transf_grupo(f, ident), avisos)
                pilha.append({"id": _id(f), "gifs": gs, "grupo": True})
            else:
                pilha.append({"id": _id(f), "gifs": [], "grupo": False})
    # GIF apontado mas AUSENTE no arquivo (o 168 aponta para image3.gif, que nao
    # existe): vira forma comum — quem desenha e o PowerPoint, como estiver
    nomes = set(z.namelist())
    for it in pilha:
        faltam = [g for g in it["gifs"] if g["midia"] not in nomes]
        if faltam:
            avisos += ["gif AUSENTE no arquivo: %s" % g["midia"] for g in faltam]
            it["gifs"] = [g for g in it["gifs"] if g["midia"] in nomes]
    tm = raiz.find(P + "timing")
    efeitos = 0
    if tm is not None:
        efeitos = sum(1 for e in tm.iter() if e.tag in (
            P + "anim", P + "animEffect", P + "animMotion", P + "animRot", P + "animScale"))
    return pilha, avisos, raiz.get("show") == "0", efeitos


def andares(pilha):
    """Corta a pilha em andares: [("O", [idx...]) | ("G", [idx...])], de baixo p/ cima."""
    saida = []
    for i, item in enumerate(pilha):
        tipo = "G" if item["gifs"] else "O"
        if saida and saida[-1][0] == tipo:
            saida[-1][1].append(i)
        else:
            saida.append((tipo, [i]))
    return saida


def ordem_dos_slides(z):
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    rels = {r.get("Id"): r.get("Target")
            for r in ET.fromstring(z.read("ppt/_rels/presentation.xml.rels"))}
    saida = []
    for s in pres.iter(P + "sldId"):
        m = re.search(r"slide(\d+)\.xml$", rels.get(s.get(R + "id")) or "")
        if m:
            saida.append(int(m.group(1)))
    return saida


def tamanho(z):
    sz = ET.fromstring(z.read("ppt/presentation.xml")).find(P + "sldSz")
    return int(sz.get("cx")), int(sz.get("cy"))


# =========================================================== PowerPoint
_PP = None


def esquece_powerpoint():
    """O PowerPoint caiu (ou alguem fechou o dele, que e o MESMO programa: ele
    roda uma vez so na maquina). Esquece o objeto morto; o proximo pedido sobe outro."""
    global _PP
    _PP = None


def powerpoint():
    global _PP
    if _PP is None:
        import win32com.client
        _PP = win32com.client.Dispatch("PowerPoint.Application")
        try:
            _PP.DisplayAlerts = 1          # ppAlertsNone: nada de caixa de dialogo
        except Exception:
            pass
    return _PP


def fecha_os_meus(pasta_origem):
    """Fecha (sem salvar) apresentacoes da MINHA pasta que um lote interrompido
    deixou abertas. Nunca toca em apresentacao dele."""
    pp = powerpoint()
    alvo = os.path.abspath(pasta_origem).lower()
    for i in range(pp.Presentations.Count, 0, -1):
        try:
            p = pp.Presentations(i)
            if p.FullName.lower().startswith(alvo):
                p.Close()
        except Exception:
            pass


def _tira_botoes(pres):
    tirados = []
    for i in range(1, pres.Slides.Count + 1):
        formas = pres.Slides(i).Shapes
        for k in range(formas.Count, 0, -1):
            f = formas(k)
            try:
                if not f.HasTextFrame:
                    continue
                t = (f.TextFrame.TextRange.Text or "").strip().upper()
            except Exception:
                continue
            if t in BOTOES:
                tirados.append("slide %d: %s" % (i, t))
                f.Delete()
    return tirados


def _mostra_so(slide, visiveis):
    """Deixa visivel so o que esta em `visiveis` (ids). Grupo fica visivel se
    algum filho estiver; dentro dele, so os filhos pedidos."""
    for k in range(1, slide.Shapes.Count + 1):
        sh = slide.Shapes(k)
        if sh.Type == GRUPO:
            filhos = [sh.GroupItems(j) for j in range(1, sh.GroupItems.Count + 1)]
            algum = sh.Id in visiveis or any(f.Id in visiveis for f in filhos)
            sh.Visible = -1 if algum else 0
            if algum and sh.Id not in visiveis:
                for f in filhos:
                    f.Visible = -1 if f.Id in visiveis else 0
        else:
            sh.Visible = -1 if sh.Id in visiveis else 0


def _ids_do_item(slide, item):
    """Ids de TUDO o que o item da pilha desenha, menos os GIFs."""
    gif_ids = set(g["id"] for g in item["gifs"])
    for k in range(1, slide.Shapes.Count + 1):
        sh = slide.Shapes(k)
        if sh.Id != item["id"]:
            continue
        if sh.Type == GRUPO and gif_ids:
            return set(sh.GroupItems(j).Id for j in range(1, sh.GroupItems.Count + 1)
                       if sh.GroupItems(j).Id not in gif_ids)
        return set() if gif_ids else {sh.Id}
    return set()


def exporta_camadas(pptx, pasta, W, H, plano):
    """plano[pos] = {"base": [idx], "andares": [[idx]...], "pilha": pilha} para
    slides com GIF. Exporta: tudo, base, e cada andar em preto e em branco.
    Devolve {estado: [png por posicao]} e os botoes tirados."""
    pp = powerpoint()
    max_andar = max([len(p["andares"]) for p in plano.values()] or [0])
    estados = ["tudo", "base"] + ["a%d_%s" % (j, c) for j in range(max_andar) for c in ("preto", "branco")]
    if not plano:
        estados = ["tudo"]
    saida, tirados = {}, []
    for est in estados:
        dest = os.path.join(pasta, est)
        if os.path.isdir(dest):
            for n in os.listdir(dest):
                try:
                    os.remove(os.path.join(dest, n))
                except OSError:
                    pass
        os.makedirs(dest, exist_ok=True)
        pres = None
        try:
            pres = pp.Presentations.Open(os.path.abspath(pptx), True, False, False)
            t = _tira_botoes(pres)
            if est == "tudo":
                tirados = t
            for pos, pl in plano.items():
                s = pres.Slides(pos + 1)
                if est == "tudo":
                    continue
                if est == "base":
                    vis = set()
                    for i in pl["base"]:
                        vis |= _ids_do_item(s, pl["pilha"][i])
                    _mostra_so(s, vis)
                    continue
                m = re.match(r"a(\d+)_(preto|branco)", est)
                j, cor = int(m.group(1)), m.group(2)
                vis = set()
                if j < len(pl["andares"]):
                    for i in pl["andares"][j]:
                        vis |= _ids_do_item(s, pl["pilha"][i])
                _mostra_so(s, vis)
                s.FollowMasterBackground = 0
                s.DisplayMasterShapes = 0
                s.Background.Fill.Solid()
                s.Background.Fill.ForeColor.RGB = 0 if cor == "preto" else 0xFFFFFF
            pres.Export(os.path.abspath(dest), "PNG", W, H)
        finally:
            if pres is not None:
                try:
                    pres.Close()                 # NUNCA salva: o original fica intacto
                except Exception:
                    pass

        def num(n):
            mm = re.findall(r"(\d+)", n)
            return int(mm[-1]) if mm else 0
        pngs = sorted([n for n in os.listdir(dest) if n.lower().endswith(".png")], key=num)
        saida[est] = [os.path.join(dest, n) for n in pngs]
    return saida, tirados


# ============================================================= montagem
def _camada_gif(z, g, LX, LY, W, H):
    from PIL import Image
    im = Image.open(io.BytesIO(z.read(g["midia"])))
    px, py = int(round(W * g["x"] / float(LX))), int(round(H * g["y"] / float(LY)))
    pcx = max(1, int(round(W * g["cx"] / float(LX))))
    pcy = max(1, int(round(H * g["cy"] / float(LY))))
    gw, gh = im.size
    l, t_, r, b = g["corte"]
    caixa = (int(round(gw * l)), int(round(gh * t_)),
             int(round(gw * (1 - r))), int(round(gh * (1 - b))))
    if caixa[2] <= caixa[0] or caixa[3] <= caixa[1]:
        caixa = (0, 0, gw, gh)
    girado = abs(g.get("giro") or 0) > 0.01
    quadros, fim, t = [], [], 0
    pos = (px, py)
    for k in range(getattr(im, "n_frames", 1)):
        im.seek(k)
        q = im.convert("RGBA").crop(caixa).resize((pcx, pcy), Image.LANCZOS)
        if g.get("espelho_h"):
            q = q.transpose(Image.FLIP_LEFT_RIGHT)
        if g.get("espelho_v"):
            q = q.transpose(Image.FLIP_TOP_BOTTOM)
        if girado:
            # PIL gira no sentido anti-horario; o PowerPoint, no horario.
            # Gira em volta do centro da caixa, e a imagem cresce para caber.
            q = q.rotate(-g["giro"], resample=Image.BICUBIC, expand=True)
            pos = (int(round(px + pcx / 2.0 - q.size[0] / 2.0)),
                   int(round(py + pcy / 2.0 - q.size[1] / 2.0)))
        quadros.append(q)
        d = im.info.get("duration") or 100
        if d < 20:                       # navegador trata <20 ms como 100 ms
            d = 100
        t += d
        fim.append(t)
    return {"q": quadros, "fim": fim, "laco": t, "pos": pos}


def _quadro_em(c, t):
    if len(c["q"]) == 1:
        return c["q"][0]
    t = t % c["laco"]
    for k, f in enumerate(c["fim"]):
        if t < f:
            return c["q"][k]
    return c["q"][-1]


def _matte(preto, branco):
    """Recorte por dois fundos: devolve (cor ja multiplicada, alfa)."""
    import numpy as np
    kb = np.asarray(preto, dtype=np.float32)
    kw = np.asarray(branco, dtype=np.float32)
    alfa = 1.0 - (kw - kb).mean(axis=2) / 255.0
    return kb, np.clip(alfa, 0.0, 1.0)[..., None]


def monta_louvor(pptx, destino, largura=LARGURA, nome=None, titulo=None):
    """nome: o prefixo dos arquivos ("38" -> 38-1.webp; "av-fui-lavado" -> av-fui-lavado-1.webp).
    Sem nome, sai do arquivo: "38 - TENHO UM CORACAO ALEGRE.pptx"."""
    import numpy as np
    from PIL import Image

    if nome is None:
        m = re.match(r"^(\d+)\s*-\s*(.+?)\.pptx?$", os.path.basename(pptx), re.I)
        louvor, titulo = int(m.group(1)), m.group(2)
    else:
        louvor = nome
    rel = {"louvor": louvor, "titulo": titulo, "telas": [], "botoes_tirados": [],
           "ocultos": [], "avisos": [], "suspeitos": [], "telas_com_efeito_ppt": []}

    with zipfile.ZipFile(pptx) as z:
        LX, LY = tamanho(z)
        W, H = largura, int(round(largura * LY / float(LX)))
        ordem = ordem_dos_slides(z)

        lidos, plano = [], {}
        for pos, num_xml in enumerate(ordem):
            pilha, avisos, oculto, efeitos = le_slide(z, num_xml)
            rel["avisos"] += ["slide %d: %s" % (pos + 1, a) for a in avisos]
            lidos.append((pilha, oculto, efeitos))
            if oculto or not any(it["gifs"] for it in pilha):
                continue
            an = andares(pilha)
            base = an[0][1] if an[0][0] == "O" else []
            resto = an[1:] if an[0][0] == "O" else an
            plano[pos] = {"pilha": pilha, "base": base,
                          "andares": [idx for tipo, idx in resto if tipo == "O"],
                          "seq": resto}

        pngs, rel["botoes_tirados"] = exporta_camadas(pptx, os.path.join(destino, "_png"), W, H, plano)
        if len(pngs["tudo"]) != len(ordem):
            rel["avisos"].append("PowerPoint exportou %d PNG para %d slides" % (len(pngs["tudo"]), len(ordem)))

        tela = 0
        for pos, (pilha, oculto, efeitos) in enumerate(lidos):
            if pos >= len(pngs["tudo"]):
                break
            if oculto:
                rel["ocultos"].append(pos + 1)
                continue
            tela += 1
            if efeitos:
                rel["telas_com_efeito_ppt"].append(tela)
            arq = "%s-%d.webp" % (louvor, tela)
            alvo = os.path.join(destino, arq)

            tudo = Image.open(pngs["tudo"][pos]).convert("RGB")
            if tudo.size != (W, H):
                tudo = tudo.resize((W, H), Image.LANCZOS)

            if pos not in plano:                        # slide sem GIF: o render e a tela
                tudo.save(alvo, "WEBP", quality=QUALIDADE_PARADA, method=6)
                rel["telas"].append({"arq": arq, "quadros": 1, "gifs": 0})
                continue

            pl = plano[pos]
            base = np.asarray(Image.open(pngs["base"][pos]).convert("RGB").resize((W, H)), dtype=np.float32)
            mattes = []
            for j in range(len(pl["andares"])):
                kb = Image.open(pngs["a%d_preto" % j][pos]).convert("RGB").resize((W, H))
                kw = Image.open(pngs["a%d_branco" % j][pos]).convert("RGB").resize((W, H))
                mattes.append(_matte(kb, kw))

            # a sequencia de andares acima da base, cada GIF ja preparado
            seq, j = [], 0
            for tipo, idx in pl["seq"]:
                if tipo == "O":
                    seq.append(("O", mattes[j]))
                    j += 1
                else:
                    gs = [g for i in idx for g in pl["pilha"][i]["gifs"]]
                    seq.append(("G", [_camada_gif(z, g, LX, LY, W, H) for g in gs]))

            def quadro(t):
                c = base.copy()
                for tipo, dado in seq:
                    if tipo == "G":
                        im = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8))
                        for cam in dado:
                            f = _quadro_em(cam, t)
                            im.paste(f, cam["pos"], f)
                        c = np.asarray(im, dtype=np.float32)
                    else:
                        cor, alfa = dado
                        c = cor + (1.0 - alfa) * c
                return np.clip(c + 0.5, 0, 255).astype(np.uint8)

            # CONFERENCIA DA TELA INTEIRA: quadro 0 montado x render do PowerPoint
            q0 = quadro(0)
            dif = np.abs(q0.astype(np.int16) - np.asarray(tudo, dtype=np.int16)).max(axis=2)
            media, pico = float(dif.mean()), float(np.percentile(dif, 99.9))
            ok = media <= LIMITE_MEDIA and pico <= LIMITE_PICO

            camadas = [c for tipo, d in seq if tipo == "G" for c in d]
            animadas = [c for c in camadas if len(c["q"]) > 1]
            info = {"arq": arq, "gifs": len(camadas), "andares": len(pl["andares"]),
                    "confere_media": round(media, 2), "confere_pico": round(pico, 1)}
            if not ok:
                rel["suspeitos"].append(dict(info, tela=tela))
                info["suspeito"] = True

            if not animadas or not ok:
                # sem animacao, ou suspeita: vai o render do PowerPoint, que e certo
                tudo.save(alvo, "WEBP", quality=QUALIDADE_PARADA, method=6)
                info["quadros"] = 1
                rel["telas"].append(info)
                continue

            laco = max(c["laco"] for c in animadas)
            passo = max(PASSO_MS, int(-(-laco // MAX_QUADROS)))
            n = max(2, int(round(laco / float(passo))))
            quadros = [Image.fromarray(q0)] + [Image.fromarray(quadro(k * passo)) for k in range(1, n)]
            quadros[0].save(alvo, "WEBP", save_all=True, append_images=quadros[1:],
                            duration=[passo] * n, loop=0, quality=QUALIDADE_ANIMADA, method=4)
            info.update({"quadros": n, "laco_ms": laco, "passo_ms": passo})
            rel["telas"].append(info)
    return rel


# ================================================================ lote
def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    origem, destino = sys.argv[1], sys.argv[2]
    so = None
    if "--so" in sys.argv:
        so = set(int(x) for x in sys.argv[sys.argv.index("--so") + 1].split(","))
    refazer = "--refazer" in sys.argv
    os.makedirs(destino, exist_ok=True)
    fecha_os_meus(origem)

    arq_rel = os.path.join(destino, "relatorio.json")
    relatorio = {}
    if os.path.exists(arq_rel) and not refazer:
        relatorio = json.load(io.open(arq_rel, encoding="utf-8"))

    pptxs = []
    for n in os.listdir(origem):
        m = re.match(r"^(\d+)\s*-", n)
        if m and n.lower().endswith(".pptx") and not n.startswith("~$"):
            pptxs.append((int(m.group(1)), os.path.join(origem, n)))
    pptxs.sort()
    if so:
        pptxs = [p for p in pptxs if p[0] in so]

    t0 = time.time()
    feitos = 0
    for i, (num, cam) in enumerate(pptxs, start=1):
        ja = relatorio.get(str(num))
        if ja and not ja.get("erro") and not refazer and not so:
            continue                               # retoma: so refaz o que faltou ou deu erro
        rel = None
        for tentativa in (1, 2):
            try:
                rel = monta_louvor(cam, destino)
                break
            except Exception as e:
                rel = {"louvor": num, "erro": "%s: %s" % (type(e).__name__, e), "telas": [],
                       "tentativas": tentativa}
                # PowerPoint caiu: esquece o morto e tenta UMA vez com um novo.
                # Se cair de novo no mesmo louvor, registra e segue com outro novo.
                esquece_powerpoint()
                try:
                    fecha_os_meus(origem)
                except Exception:
                    esquece_powerpoint()
                if isinstance(e, zipfile.BadZipFile):
                    break                          # arquivo estragado: tentar de novo nao adianta
        relatorio[str(num)] = rel
        tmp = arq_rel + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as g:
            json.dump(relatorio, g, ensure_ascii=False, indent=1)
        os.replace(tmp, arq_rel)                  # grava a cada louvor: retoma de onde parou
        feitos += 1
        anim = sum(1 for t in rel.get("telas", []) if t.get("quadros", 1) > 1)
        marca = ("ERRO " + rel["erro"]) if rel.get("erro") else (
            "%d telas, %d animadas%s" % (
                len(rel["telas"]), anim,
                ", %d SUSPEITA(S)" % len(rel["suspeitos"]) if rel.get("suspeitos") else ""))
        print("[%3d/%d] %4d  %-38s %s   (%.0fs)" % (
            i, len(pptxs), num, (rel.get("titulo") or "")[:38], marca, time.time() - t0))
        sys.stdout.flush()

    indice = escreve_indice(destino, relatorio)

    erros = [k for k, r in relatorio.items() if r.get("erro")]
    susp = sum(len(r.get("suspeitos", [])) for r in relatorio.values())
    telas = sum(len(r.get("telas", [])) for r in relatorio.values())
    anim = sum(1 for r in relatorio.values() for t in r.get("telas", []) if t.get("quadros", 1) > 1)
    print()
    print("PRONTO: %d louvores, %d telas (%d animadas), %d suspeitas (foram paradas, pelo render "
          "do PowerPoint), %d erros, %d feitos agora" % (len(indice), telas, anim, susp, len(erros), feitos))
    if erros:
        print("ERROS: %s" % ", ".join(sorted(erros, key=lambda x: (len(x), x))))


def escreve_indice(destino, relatorio):
    """indice.json no formato que o Sistema le:
       {"38": ["38-1.webp", ...], "chave:AV|FUI LAVADO...|...": ["av-fui-lavado-1.webp", ...]}
    CIA pelo numero; avulso pela CHAVE do louvor (num|TITULO|1a linha), que e unica."""
    indice = {}
    for k, rel in relatorio.items():
        telas = [t["arq"] for t in rel.get("telas", [])]
        if not telas:
            continue
        indice[k if k.startswith("chave:") else str(int(k))] = telas
    tmp = os.path.join(destino, "indice.json.tmp")
    with io.open(tmp, "w", encoding="utf-8") as g:
        json.dump(indice, g, ensure_ascii=False)
    os.replace(tmp, os.path.join(destino, "indice.json"))
    return indice


if __name__ == "__main__":
    main()
