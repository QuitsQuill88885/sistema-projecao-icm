# -*- coding: utf-8 -*-
"""O MOTOR DE ENTRADA: cada CLIQUE de animacao do PowerPoint vira uma tela a mais.

POR QUE EXISTE (medido em 11/10/2026, na aula "Voce sabe o que e Salvacao"):
  O animacoes_do_pptx exporta o slide PARADO, com TODAS as formas visiveis. No
  slide 6 o clique tira a tempestade (com a chuva em GIF) e poe o mar calmo: o
  render parado desenhava as duas cenas juntas, e o mar calmo nunca aparecia. No
  15, o clique traz o balao "Menina, a ti te digo" e troca o coracao cinza pelo
  vermelho, que ainda anda por um caminho. Referencia, palavra dele: o PowerPoint
  em MODO APRESENTACAO, clique a clique.

COMO FUNCIONA:
  1. Le a sequencia principal (mainSeq) de cada slide: entrada, saida, enfase e
     caminho, na ordem, cortada nos cliques.
  2. Estado inicial: quem tem ENTRADA como primeiro efeito comeca escondido. O
     que roda sozinho antes do 1o clique ja vale na 1a tela.
  3. Cada clique e uma tela: quem saiu e APAGADO do XML (esconder nao basta: o
     GIF da chuva estava dentro do grupo que sai, e o motor colaria o GIF de
     novo); o caminho desloca a forma para onde ela termina.
  4. Grava um .pptx NOVO com as telas como slides comuns, sem a temporizacao. O
     animacoes_do_pptx roda em cima dele sem mudar nada: GIF andando, conferencia
     contra o render do PowerPoint, tudo igual.
  Slide sem clique e sem saida/caminho fica INTOCADO (entrada sozinha termina com
  tudo visivel, que e o que o render parado ja mostra).
  O que este motor NAO faz: a animacao da entrada em si (o esmaecer de 0,5 s). A
  tela mostra o fim de cada clique.
"""
import copy
import re
import zipfile

from lxml import etree

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
      "ct": "http://schemas.openxmlformats.org/package/2006/content-types"}
P = "{%s}" % NS["p"]
A = "{%s}" % NS["a"]
NOTAS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"


def _fim_do_caminho(path):
    """'M 0 0 L 0.25 -0.1 E' -> (0.25, -0.1): o ultimo par de numeros antes do E."""
    nums = re.findall(r"-?\d+(?:\.\d+)?(?:[eE]-?\d+)?", (path or "").replace("E", " "))
    if len(nums) < 2:
        return 0.0, 0.0
    return float(nums[-2]), float(nums[-1])


def efeitos(raiz):
    """[[efeito, ...] do que roda sozinho ao entrar, [clique 1], [clique 2], ...]
    efeito = (classe, spid, (dx, dy))"""
    grupos = [[]]
    for seq in raiz.iter(P + "cTn"):
        if seq.get("nodeType") != "mainSeq":
            continue
        for c in seq.iter(P + "cTn"):
            classe = c.get("presetClass")
            tipo = c.get("nodeType")
            if not classe or tipo not in ("clickEffect", "withEffect", "afterEffect"):
                continue
            if tipo == "clickEffect":
                grupos.append([])
            alvo = next((t.get("spid") for t in c.iter(P + "spTgt")), None)
            mov = (0.0, 0.0)
            if classe == "path":
                m = next(c.iter(P + "animMotion"), None)
                mov = _fim_do_caminho(m.get("path") if m is not None else "")
            grupos[-1].append((classe, alvo, mov))
    return grupos


def estados(raiz):
    """Lista de estados (escondidos:set, deslocados:{spid:(dx,dy)}), um por tela."""
    gs = efeitos(raiz)
    primeiro = {}
    for g in gs:
        for classe, alvo, _ in g:
            primeiro.setdefault(alvo, classe)
    esc = {s for s, c in primeiro.items() if c == "entr"}
    mov = {}
    saida = []

    def aplica(g):
        for classe, alvo, d in g:
            if classe == "entr":
                esc.discard(alvo)
            elif classe == "exit":
                esc.add(alvo)
            elif classe == "path":
                x, y = mov.get(alvo, (0.0, 0.0))
                mov[alvo] = (x + d[0], y + d[1])

    aplica(gs[0])
    saida.append((set(esc), dict(mov)))
    for g in gs[1:]:
        aplica(g)
        saida.append((set(esc), dict(mov)))
    return saida


def _xfrm(el):
    for cam in ("p:spPr/a:xfrm", "p:grpSpPr/a:xfrm"):
        x = el.find(cam, NS)
        if x is not None:
            return x
    return None


def slide_no_estado(raiz, escondidos, deslocados, LX, LY, avisos):
    r = copy.deepcopy(raiz)
    arvore = r.find("p:cSld/p:spTree", NS)
    por_id = {}
    for c in arvore.iter(P + "cNvPr"):
        forma = c.getparent().getparent()          # nvSpPr/nvPicPr/nvGrpSpPr -> a forma
        por_id[c.get("id")] = forma
    for spid in escondidos:
        f = por_id.get(spid)
        if f is None:
            avisos.append("forma %s do efeito nao existe" % spid)
            continue
        if f.getparent() is not None:
            f.getparent().remove(f)
    for spid, (dx, dy) in deslocados.items():
        f = por_id.get(spid)
        if f is None or spid in escondidos or (dx == 0 and dy == 0):
            continue
        if f.getparent() is not arvore:
            avisos.append("caminho em forma dentro de grupo (%s): posicao aproximada" % spid)
        off = _xfrm(f).find("a:off", NS)
        off.set("x", str(int(round(int(off.get("x")) + dx * LX))))
        off.set("y", str(int(round(int(off.get("y")) + dy * LY))))
    tm = r.find("p:timing", NS)
    if tm is not None:
        r.remove(tm)
    return r


def expande(entrada, saida):
    """Grava em `saida` o pptx com um slide por tela. Devolve o relatorio:
    {"telas": [[slide_original, n_telas], ...], "avisos": [...]}"""
    zi = zipfile.ZipFile(entrada)
    pres = etree.fromstring(zi.read("ppt/presentation.xml"))
    sz = pres.find("p:sldSz", NS)
    LX, LY = int(sz.get("cx")), int(sz.get("cy"))
    prels = etree.fromstring(zi.read("ppt/_rels/presentation.xml.rels"))
    alvo_de = {r.get("Id"): r.get("Target") for r in prels}
    tipos = etree.fromstring(zi.read("[Content_Types].xml"))
    novos, trocados, rel = {}, {}, {"telas": [], "avisos": []}
    prox_num = 1000
    prox_id = max(int(s.get("id")) for s in pres.iter(P + "sldId")) + 1
    prox_rid = 1 + max(int(re.sub(r"\D", "", k) or 0) for k in alvo_de)
    lista = pres.find("p:sldIdLst", NS)
    for pos, s in enumerate(list(lista)):
        alvo = alvo_de[s.get("{%s}id" % NS["r"])]
        nome = "ppt/" + alvo.lstrip("/").replace("../", "")
        raiz = etree.fromstring(zi.read(nome))
        es = estados(raiz)
        mexe = len(es) > 1 or es[-1][1] or any(
            c == "exit" for g in efeitos(raiz) for c, _, _ in g)
        if not mexe:
            rel["telas"].append([pos + 1, 1])
            continue
        av = []
        partes = [slide_no_estado(raiz, e, d, LX, LY, av) for e, d in es]
        rel["avisos"] += ["slide %d: %s" % (pos + 1, a) for a in av]
        rel["telas"].append([pos + 1, len(partes)])
        trocados[nome] = partes[0]
        rels_nome = nome.replace("slides/", "slides/_rels/") + ".rels"
        rels_xml = etree.fromstring(zi.read(rels_nome))
        for r in list(rels_xml):
            if r.get("Type") == NOTAS:
                rels_xml.remove(r)                 # a nota pertence ao slide original
        depois = s
        for extra in partes[1:]:
            n = "ppt/slides/slide%d.xml" % prox_num
            novos[n] = etree.tostring(extra, xml_declaration=True, encoding="UTF-8", standalone=True)
            novos["ppt/slides/_rels/slide%d.xml.rels" % prox_num] = etree.tostring(
                rels_xml, xml_declaration=True, encoding="UTF-8", standalone=True)
            ov = etree.SubElement(tipos, "{%s}Override" % NS["ct"])
            ov.set("PartName", "/" + n)
            ov.set("ContentType", "application/vnd.openxmlformats-officedocument.presentationml.slide+xml")
            rid = "rId%d" % prox_rid
            r = etree.SubElement(prels, "{%s}Relationship" % NS["rel"])
            r.set("Id", rid)
            r.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide")
            r.set("Target", "slides/slide%d.xml" % prox_num)
            novo = etree.Element(P + "sldId")
            novo.set("id", str(prox_id))
            novo.set("{%s}id" % NS["r"], rid)
            depois.addnext(novo)
            depois = novo
            prox_num += 1; prox_id += 1; prox_rid += 1
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            if it.filename in trocados:
                b = etree.tostring(trocados[it.filename], xml_declaration=True, encoding="UTF-8", standalone=True)
            elif it.filename == "ppt/presentation.xml":
                b = etree.tostring(pres, xml_declaration=True, encoding="UTF-8", standalone=True)
            elif it.filename == "ppt/_rels/presentation.xml.rels":
                b = etree.tostring(prels, xml_declaration=True, encoding="UTF-8", standalone=True)
            elif it.filename == "[Content_Types].xml":
                b = etree.tostring(tipos, xml_declaration=True, encoding="UTF-8", standalone=True)
            else:
                b = zi.read(it.filename)
            zo.writestr(it, b)
        for n, b in novos.items():
            zo.writestr(n, b)
    return rel


if __name__ == "__main__":
    import sys, json
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(expande(sys.argv[1], sys.argv[2]), ensure_ascii=False))
