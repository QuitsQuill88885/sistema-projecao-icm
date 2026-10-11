# -*- coding: utf-8 -*-
"""A ANIMACAO DENTRO DA MESMA TELA — o (4/5) do lote 2, 3.0.7 (ordem dele 11/10/2026 17h20: "vai la, pode fazer").

Ate a 3.0.6 cada clique de animacao do PowerPoint virava uma TELA a mais (o barco 6->7, o coracao 16->17): o
movimento sumia e o slide parecia duplicado. Aqui o slide vira um PALCO: o fundo parado + cada peca animada
recortada em camada (com transparencia, e com o GIF andando se ela tiver GIF), e a linha do tempo EXATA do
PowerPoint (efeito, duracao, atraso, gatilho), lida do p:timing. O telao (projecao.html) toca isso com animacao
de navegador; a seta do operador passa pelos cliques de dentro do slide antes de ir ao proximo.

Uso:
    python movimento_do_pptx.py <pptx> <pasta da apresentacao> 6 8 10 11 12 15 19 21   [--so-ler]

Grava <pasta>/_movimento/sNN_*.webp e <pasta>/movimento.json. Os slides sao os numeros do PPTX (1 = primeiro),
que tem de ser os mesmos da pasta (SlideNNN.webp). O SlideNNN.webp continua sendo a miniatura e o que o telao
mostra num Sistema que nao saiba ler o movimento.

Recorte por dois fundos (o mesmo _matte das CIAS): cada camada e exportada pelo PowerPoint sozinha sobre preto e
sobre branco; a diferenca da a transparencia. CONFERENCIA: todas as camadas empilhadas na posicao original tem de
dar o slide exportado inteiro (media <= 2,0 e 99,9% dos pixels <= 90, as mesmas reguas das CIAS).

Efeitos que o telao sabe tocar: esmaecer, aparecer, revelar (wipe, 4 lados), girar, crescer/encolher e caminho
de movimento (linhas e curvas). Efeito desconhecido NAO some calado: vira esmaecer e sai no relatorio como aviso.
Os ACRESCIMOS NOSSOS (ordem dele 17h21: "e se nao tiver, voce poe animacoes decentes") vao em EXTRAS, com
"nosso": true, e nunca mudam um efeito oficial.
"""
import io
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animacoes_do_pptx as AP  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
P, A = AP.P, AP.A
W, H = 1920, 1080
QUALIDADE = 82
PASSO_GIF_MS = 60
MAX_QUADROS = 40

# --- os acrescimos nossos, por slide do PPTX (ordem dele 17h21). Cada um vai marcado "nosso" no json e na nota.
# alvo = id da forma no slide; "depois_de" = comeca quando termina o ultimo efeito oficial deste alvo.
EXTRAS = {
    15: [{"alvo": 23, "efeito": "pulsar", "depois_de": 23, "dur": 1100, "escala": 1.08,
          "porque": "o coracao vermelho 'cheio de alegria e pulsando' (pedido dele; o pptx oficial nao pulsa)"},
         {"alvo": 17, "efeito": "pop", "junto_de": 17, "de": 0.85,
          "porque": "o balao de Jesus cresce um tico junto com o esmaecer (o oficial so esmaece)"}],
    6: [{"alvo": 2, "efeito": "pop", "junto_de": 2, "de": 0.85,
         "porque": "o balao dos discipulos cresce um tico junto com o esmaecer (o oficial so esmaece)"}],
}


# ======================================================== a linha do tempo
def _num(s, padrao=0):
    try:
        return int(s)
    except (TypeError, ValueError):
        return padrao


def _atraso(ctn):
    c = ctn.find(P + "stCondLst/" + P + "cond")
    return _num(c.get("delay")) if c is not None and c.get("delay") not in (None, "indefinite") else 0


def _caminho(path):
    """'M 0 0 L 0.1 0.2 C ... E' -> [(x, y)...] em fracao do slide, curvas amostradas em 12 pedacos."""
    t = re.findall(r"[MLCZEmlcze]|-?[\d.]+(?:[Ee]-?\d+)?", path or "")
    pts, i, cmd = [], 0, None
    while i < len(t):
        if t[i] in "MLCZEmlcze":
            cmd = t[i].upper(); i += 1
            if cmd in "ZE":
                continue
        if cmd in ("M", "L"):
            pts.append((float(t[i]), float(t[i + 1]))); i += 2
        elif cmd == "C":
            x0, y0 = pts[-1] if pts else (0.0, 0.0)
            (x1, y1), (x2, y2), (x3, y3) = [(float(t[i + k]), float(t[i + k + 1])) for k in (0, 2, 4)]
            i += 6
            for k in range(1, 13):
                u = k / 12.0; v = 1 - u
                pts.append((v ** 3 * x0 + 3 * v * v * u * x1 + 3 * v * u * u * x2 + u ** 3 * x3,
                            v ** 3 * y0 + 3 * v * v * u * y1 + 3 * v * u * u * y2 + u ** 3 * y3))
        else:
            i += 1
    return [(round(x, 5), round(y, 5)) for x, y in pts]


def _efeito(ctn, ini, avisos):
    """Um efeito do PowerPoint -> o dicionario que o telao toca."""
    cls, pid = ctn.get("presetClass"), _num(ctn.get("presetID"))
    alvo, dur, comp = None, 0, {}
    for x in ctn.iter():
        tag = x.tag.split("}")[1]
        if tag not in ("set", "animEffect", "animMotion", "animRot", "animScale", "anim", "animClr"):
            continue
        b = x.find(P + "cBhvr/" + P + "cTn")
        d = _num(b.get("dur")) if b is not None and b.get("dur") not in (None, "indefinite") else 0
        dur = max(dur, d + (_atraso(b) if b is not None else 0))
        sp = next((s.get("spid") for s in x.iter(P + "spTgt")), None)
        alvo = alvo or _num(sp)
        if tag == "animEffect":
            comp["filtro"] = x.get("filter") or ""
        elif tag == "animMotion":
            comp["caminho"] = _caminho(x.get("path"))
        elif tag == "animRot":
            comp["graus"] = round(_num(x.get("by")) / 60000.0, 2)
        elif tag == "animScale":
            by = x.find(P + "by")
            if by is not None:
                comp["escala"] = [_num(by.get("x"), 100000) / 100000.0, _num(by.get("y"), 100000) / 100000.0]
    ef = {"alvo": alvo, "classe": cls, "preset": pid, "ini": ini, "dur": dur,
          "suave": bool(_num(ctn.get("accel")) or _num(ctn.get("decel")))}
    f = comp.get("filtro", "")
    if cls in ("entr", "exit"):
        if f.startswith("fade"):
            ef["efeito"] = "esmaecer"
        elif f.startswith("wipe"):
            ef["efeito"] = "revelar"; ef["lado"] = re.sub(r"wipe\(?(\w*)\)?", r"\1", f) or "up"
        elif not f and pid == 1:
            ef["efeito"] = "aparecer"
        elif "escala" in comp:
            ef["efeito"] = "esmaecer"
            avisos.append("efeito %s/%s com escala: tocado como esmaecer" % (cls, pid))
        else:
            ef["efeito"] = "esmaecer"
            avisos.append("efeito %s/%s filtro=%r desconhecido: tocado como esmaecer" % (cls, pid, f))
    elif cls == "emph":
        if "graus" in comp:
            ef["efeito"] = "girar"; ef["graus"] = comp["graus"]
        elif "escala" in comp:
            ef["efeito"] = "crescer"; ef["escala"] = comp["escala"]
        else:
            ef["efeito"] = "nada"; avisos.append("enfase %s sem giro/escala: ignorada" % pid)
    elif cls == "path":
        ef["efeito"] = "caminho"; ef["caminho"] = comp.get("caminho") or [(0, 0)]
    else:
        ef["efeito"] = "nada"; avisos.append("classe %s desconhecida" % cls)
    return ef


def linha_do_tempo(raiz, avisos):
    """[passo 0 (sozinho ao entrar), clique 1, clique 2, ...]; cada passo = [efeitos com ini/dur em ms]."""
    passos = [[]]
    tm = raiz.find(P + "timing")
    if tm is None:
        return passos
    seq = next((c for c in tm.iter(P + "cTn") if c.get("nodeType") == "mainSeq"), None)
    if seq is None:
        return passos
    for clique in seq.findall(P + "childTnLst/" + P + "par"):
        efs = []
        for sub in clique.findall(P + "cTn/" + P + "childTnLst/" + P + "par"):
            d1 = _atraso(sub.find(P + "cTn"))
            for e in sub.findall(P + "cTn/" + P + "childTnLst/" + P + "par"):
                c = e.find(P + "cTn")
                if c is not None and c.get("presetClass"):
                    efs.append((c.get("nodeType"), _efeito(c, d1 + _atraso(c), avisos)))
        if not efs:
            continue
        primeiro = efs[0][0]
        lista = [ef for _, ef in efs]
        if primeiro == "clickEffect":
            passos.append(lista)
        else:   # "com/apos o anterior" no comeco: emenda no passo atual (no passo 0 = roda sozinho ao entrar)
            fim = max([f["ini"] + f["dur"] for f in passos[-1]] or [0]) if primeiro == "afterEffect" else 0
            for f in lista:
                f["ini"] += fim
            passos[-1] += lista
    return passos


def extras_do_slide(n, passos):
    saida = []
    for x in EXTRAS.get(n, []):
        x = dict(x, nosso=True)
        todos = [(k, f) for k, p in enumerate(passos) for f in p]
        if "depois_de" in x:
            k, f = max(((k, f) for k, f in todos if f["alvo"] == x["depois_de"]), key=lambda kf: (kf[0], kf[1]["ini"] + kf[1]["dur"]))
            x.update(passo=k, ini=f["ini"] + f["dur"])
        else:
            k, f = next((k, f) for k, f in todos if f["alvo"] == x["junto_de"])
            x.update(passo=k, ini=f["ini"], dur=f["dur"])
        x.pop("depois_de", None); x.pop("junto_de", None)
        saida.append(x)
    return saida


# ========================================================= as camadas
def _caixa_xml(raiz, sid, LX, LY):
    for c in raiz.iter(P + "cNvPr"):
        if _num(c.get("id")) == sid:
            el = c.getparent() if hasattr(c, "getparent") else None
    # ElementTree nao tem getparent: procura a forma de cima que tem esse id
    arv = raiz.find(P + "cSld/" + P + "spTree")
    for f in arv:
        if AP._id(f) == sid:
            xf = f.find(P + "spPr/" + A + "xfrm")
            if xf is None:
                xf = f.find(P + "grpSpPr/" + A + "xfrm")
            g = AP._xfrm(xf) if xf is not None else None
            if g:
                return [g[0] / LX, g[1] / LY, g[2] / LX, g[3] / LY]
    return None


def faixas(pilha, alvos):
    """A pilha cortada em camadas: cada alvo sozinho; o que nao anima, junto, entre um alvo e outro.
    A primeira faixa sem alvo vai com o FUNDO (opaca)."""
    saida = []
    for i, it in enumerate(pilha):
        anima = it["id"] in alvos
        if anima or not saida or saida[-1]["alvo"] is not None:
            saida.append({"alvo": it["id"] if anima else None, "itens": [i]})
        else:
            saida[-1]["itens"].append(i)
    return saida


def _render(pres, pos, vis, cor, pasta, nome):
    """Exporta o slide `pos` (1-based) so com `vis` visivel; cor None = fundo de verdade."""
    s = pres.Slides(pos)
    AP._mostra_so(s, vis)
    if cor is not None:
        s.FollowMasterBackground = 0
        s.DisplayMasterShapes = 0
        s.Background.Fill.Solid()
        s.Background.Fill.ForeColor.RGB = 0 if cor == "preto" else 0xFFFFFF
    arq = os.path.join(pasta, nome)
    s.Export(arq, "PNG", W, H)
    return arq


def monta(pptx, pasta_ap, slides, so_ler=False):
    import numpy as np
    from PIL import Image
    rel = {"pptx": os.path.basename(pptx), "slides": {}, "avisos": [], "suspeitos": []}
    saida = os.path.join(pasta_ap, "_movimento")
    tmp = os.path.join(os.environ.get("TEMP", "."), "movimento_png")
    os.makedirs(tmp, exist_ok=True)
    with zipfile.ZipFile(pptx) as z:
        LX, LY = AP.tamanho(z)
        ordem = AP.ordem_dos_slides(z)
        planos = {}
        for n in slides:
            raiz = ET.fromstring(z.read("ppt/slides/slide%d.xml" % ordem[n - 1]))
            av = []
            passos = linha_do_tempo(raiz, av)
            pilha, av2, _, _ = AP.le_slide(z, ordem[n - 1])
            av += av2
            alvos = {f["alvo"] for p in passos for f in p}
            topo = {it["id"] for it in pilha}
            fora = alvos - topo
            if fora:
                av.append("alvo DENTRO de grupo (nao sei recortar): %s" % sorted(fora))
            fx = faixas(pilha, alvos)
            caixas = {a: _caixa_xml(raiz, a, LX, LY) for a in alvos}
            planos[n] = {"passos": passos, "pilha": pilha, "faixas": fx, "caixas": caixas,
                         "extras": extras_do_slide(n, passos)}
            rel["avisos"] += ["slide %d: %s" % (n, a) for a in av]
            print("slide %d: %d passos (%s), %d camadas, alvos %s" % (
                n, len(passos), "/".join(str(len(p)) for p in passos), len(fx), sorted(alvos)))
            for k, p in enumerate(passos):
                for f in p:
                    print("   passo %d  %-8s %-9s alvo=%-5s ini=%5d dur=%5d %s" % (
                        k, f["classe"], f["efeito"], f["alvo"], f["ini"], f["dur"],
                        {c: f[c] for c in ("graus", "lado", "caminho", "escala") if c in f}))
            for x in planos[n]["extras"]:
                print("   NOSSO passo %d %-8s alvo=%s ini=%s" % (x["passo"], x["efeito"], x["alvo"], x["ini"]))
        if rel["avisos"]:
            print("AVISOS:", *rel["avisos"], sep="\n  ")
        if so_ler:
            return rel

        os.makedirs(saida, exist_ok=True)
        pp = AP.powerpoint()
        pres = pp.Presentations.Open(os.path.abspath(pptx), True, False, False)
        try:
            AP._tira_botoes(pres)
            renders = {}
            for n, pl in planos.items():
                s = pres.Slides(n)
                ids = [AP._ids_do_item(s, it) for it in pl["pilha"]]
                tudo = _render(pres, n, set().union(*ids) if ids else set(), None, tmp, "s%02d_tudo.png" % n)
                r = {"tudo": tudo, "faixas": []}
                for j, fx in enumerate(pl["faixas"]):
                    vis = set().union(*[ids[i] for i in fx["itens"]])
                    if j == 0 and fx["alvo"] is None:
                        r["faixas"].append({"fundo": _render(pres, n, vis, None, tmp, "s%02d_f0.png" % n)})
                    else:
                        r["faixas"].append({c: _render(pres, n, vis, c, tmp, "s%02d_f%d_%s.png" % (n, j, c))
                                            for c in ("preto", "branco")})
                if pl["faixas"] and pl["faixas"][0]["alvo"] is not None:
                    r["so_fundo"] = _render(pres, n, set(), None, tmp, "s%02d_fundo.png" % n)
                renders[n] = r
        finally:
            pres.Close()     # NUNCA salva: o original fica intacto

        mov = {"versao": 1, "pptx": os.path.basename(pptx), "largura": W, "altura": H, "slides": {}}
        for n, pl in planos.items():
            r = renders[n]
            abre = lambda p: Image.open(p).convert("RGB").resize((W, H))  # noqa: E731
            camadas, pilha_conf = [], []
            fx0 = pl["faixas"][0]
            if fx0["alvo"] is None:
                base_rgb = np.asarray(abre(r["faixas"][0]["fundo"]), dtype=np.float32)
                base_gifs = [g for i in fx0["itens"] for g in pl["pilha"][i]["gifs"]]
                resto = list(enumerate(pl["faixas"]))[1:]
            else:
                base_rgb = np.asarray(abre(r["so_fundo"]), dtype=np.float32)
                base_gifs = []
                resto = list(enumerate(pl["faixas"]))
            # o FUNDO (opaco), com os GIFs da primeira faixa andando
            nome_base = "s%02d_base.webp" % n
            cg = [AP._camada_gif(z, g, LX, LY, W, H) for g in base_gifs]
            _grava(os.path.join(saida, nome_base), base_rgb, np.ones(base_rgb.shape[:2] + (1,), np.float32), cg,
                   opaco=True)
            # a conferencia e SEM os GIFs: o "tudo" do PowerPoint tambem sai sem eles (_ids_do_item os tira)
            conf = base_rgb.copy()
            for j, fx in resto:
                cor, alfa = AP._matte(abre(r["faixas"][j]["preto"]), abre(r["faixas"][j]["branco"]))
                gifs = [AP._camada_gif(z, g, LX, LY, W, H) for i in fx["itens"] for g in pl["pilha"][i]["gifs"]]
                cx = pl["caixas"].get(fx["alvo"]) if fx["alvo"] is not None else None
                nome = "s%02d_c%d.webp" % (n, j)
                caixa = _grava(os.path.join(saida, nome), cor, alfa, gifs, caixa_forma=cx)
                if caixa is None:
                    continue
                conf = cor + (1.0 - alfa) * conf
                camadas.append({"id": fx["alvo"], "src": "_movimento/" + nome,
                                "x": caixa[0], "y": caixa[1], "w": caixa[2], "h": caixa[3],
                                # centro do giro/escala = centro da FORMA no PowerPoint, em fracao da camada
                                "cx": round(((cx[0] + cx[2] / 2) - caixa[0]) / caixa[2], 4) if cx else 0.5,
                                "cy": round(((cx[1] + cx[3] / 2) - caixa[1]) / caixa[3], 4) if cx else 0.5})
            # CONFERENCIA: camadas empilhadas x o slide exportado inteiro
            tudo = np.asarray(abre(r["tudo"]), dtype=np.int16)
            q = np.clip(conf + 0.5, 0, 255).astype(np.int16)
            dif = np.abs(q - tudo).max(axis=2)
            media, pico = float(dif.mean()), float(np.percentile(dif, 99.9))
            ok = media <= AP.LIMITE_MEDIA and pico <= AP.LIMITE_PICO
            if not ok:
                rel["suspeitos"].append({"slide": n, "media": round(media, 2), "pico": round(pico, 1)})
            Image.fromarray(np.clip(conf, 0, 255).astype(np.uint8)).save(os.path.join(tmp, "s%02d_conf.png" % n))
            mov["slides"][str(n)] = {"base": "_movimento/" + nome_base, "camadas": camadas,
                                     "passos": pl["passos"], "extras": pl["extras"],
                                     "confere": {"media": round(media, 2), "pico": round(pico, 1)}}
            rel["slides"][n] = {"camadas": len(camadas), "confere_media": round(media, 2),
                                "confere_pico": round(pico, 1), "ok": ok}
            print("slide %d: %d camadas, confere media %.2f pico %.1f %s" % (
                n, len(camadas), media, pico, "OK" if ok else "SUSPEITO"))
        with open(os.path.join(pasta_ap, "movimento.json"), "w", encoding="utf-8") as f:
            json.dump(mov, f, ensure_ascii=False, indent=1)
    return rel


def _cola_gifs(cor, alfa, gifs, t):
    """cor ja multiplicada pelo alfa; cola os quadros dos GIFs no instante t (por cima, na ordem)."""
    import numpy as np
    from PIL import Image
    c = cor.copy()
    a = np.ones(c.shape[:2] + (1,), np.float32) if alfa is None else alfa.copy()
    for g in gifs:
        f = AP._quadro_em(g, t)
        x, y = g["pos"]
        fa = np.zeros(c.shape[:2] + (1,), np.float32)
        fc = np.zeros(c.shape, np.float32)
        lay = Image.new("RGBA", (c.shape[1], c.shape[0]), (0, 0, 0, 0))
        lay.paste(f, (x, y), f)
        arr = np.asarray(lay, dtype=np.float32)
        fa = arr[..., 3:4] / 255.0
        fc = arr[..., :3] * fa
        c = fc + (1.0 - fa) * c
        a = fa + (1.0 - fa) * a
    return c, a


def _grava(arq, cor, alfa, gifs, opaco=False, caixa_forma=None):
    """Grava a camada recortada na caixa do que aparece (e da forma). Devolve a caixa em fracao do slide."""
    import numpy as np
    from PIL import Image
    animados = [g for g in gifs if len(g["q"]) > 1]
    if animados:
        laco = max(g["laco"] for g in animados)
        passo = max(PASSO_GIF_MS, int(-(-laco // MAX_QUADROS)))
        tempos = [k * passo for k in range(max(2, int(round(laco / float(passo)))))]
    else:
        passo, tempos = 0, [0]
    quadros = []
    for t in tempos:
        c, a = (cor, alfa) if not gifs else _cola_gifs(cor, None if opaco else alfa, gifs, t)
        quadros.append((c, a))
    if opaco:
        caixa = (0, 0, W, H)
    else:
        soma = sum(q[1][..., 0] for q in quadros)
        ys, xs = np.where(soma > 0.02)
        if not len(xs):
            return None
        caixa = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        if caixa_forma:
            fx0, fy0 = int(caixa_forma[0] * W), int(caixa_forma[1] * H)
            fx1, fy1 = int((caixa_forma[0] + caixa_forma[2]) * W), int((caixa_forma[1] + caixa_forma[3]) * H)
            caixa = [max(0, min(caixa[0], fx0)), max(0, min(caixa[1], fy0)), min(W, max(caixa[2], fx1)),
                     min(H, max(caixa[3], fy1))]
    x0, y0, x1, y1 = caixa
    ims = []
    for c, a in quadros:
        if opaco:
            ims.append(Image.fromarray(np.clip(c + 0.5, 0, 255).astype(np.uint8)))
            continue
        rgb = np.where(a > 1e-3, c / np.maximum(a, 1e-3), 0)
        rgba = np.concatenate([np.clip(rgb + 0.5, 0, 255), np.clip(a * 255 + 0.5, 0, 255)], axis=2).astype(np.uint8)
        ims.append(Image.fromarray(rgba[y0:y1, x0:x1], "RGBA"))
    if len(ims) > 1:
        ims[0].save(arq, "WEBP", save_all=True, append_images=ims[1:], duration=[passo] * len(ims), loop=0,
                    quality=72, method=4)
    else:
        ims[0].save(arq, "WEBP", quality=QUALIDADE, method=6)
    return [round(x0 / W, 5), round(y0 / H, 5), round((x1 - x0) / W, 5), round((y1 - y0) / H, 5)]


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    r = monta(args[0], args[1], [int(a) for a in args[2:]], so_ler="--so-ler" in sys.argv)
    if r["suspeitos"]:
        print("SUSPEITOS:", r["suspeitos"])
