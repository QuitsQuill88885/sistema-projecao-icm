"""GESTOS NA TV DE RETORNO (16/10/2026, para a Evangelização de Crianças de 25/10).

Casa cada slide do Período de Louvor com as FIGURAS dos "Gestos em gravuras" da Cris (já recortadas
pela Coletânea em Coletanea-Ipero\\gerador\\gestos.json + figs\\<louvor>\\) e monta UMA imagem por slide:
as figuras das frases daquele slide, na ordem, com a frase embaixo. Grava em gestos\\<pasta>\\sNN.webp e
escreve dados\\gestos.js, que o retorno.html lê (chave "apres:<nome da apresentação>", slide 0-based,
o mesmo est.slidePos do app.js).

Uso:  python ferramentas\\gestos_da_apresentacao.py            (mostra o mapa, não grava)
      python ferramentas\\gestos_da_apresentacao.py --gravar
"""
import json, re, sys, unicodedata
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

APP = Path(__file__).resolve().parent.parent
# as figuras recortadas pelo extrator da Coletânea (extrai_gestos.py), rodado numa cópia: o
# gestos.json saiu IGUAL ao da Coletânea (md5 f235e657), mas a pasta figs de lá foi refeita depois
# com outros nomes e não casa mais com ele.
COLET = Path(r"C:\Projetos\Sistema\Evangelizacao Outubro 2026\gerador\gestos_cris")
APRES = "Louvores da Evangelização de Outubro 2026"
PASTA = "evang_out2026"
LOUVORES = {"fui_lavado": "FUI LAVADO NO SANGUE", "81": "SENHOR TÃO PEQUENO SOU",
            "97": "JESUS É O CAMINHO", "198": "O DIA ESTÁ CHEGANDO"}
# frases que VOLTAM nos slides sem estar repetidas no papel (o coro do 97 vem uma vez, "CORO 2x",
# e volta depois de cada estrofe). Índice = posição no gestos.json da Coletânea.
REPETEM = {"97": {4, 5}}
# figuras que o recorte da Coletânea NÃO pegou (16/10, conferido no PDF da Cris 1790803279, pág. 1):
# a mão do "Jesus" (imagem 48 do PDF, extraída para figs\extra\jesus_mao.png) ao lado de
# "A Jesus honra e louvor" (y 77) e de "Jesus, é o caminho" (y 242) / "Jesus, é a verdade" (y 509).
FALTAM = {("fui_lavado", 11): ["../extra/jesus_mao.png"],
          ("97", 0): ["../extra/jesus_mao.png"], ("97", 6): ["../extra/jesus_mao.png"]}
# figura que o recorte grudou na frase errada (conferente cego, 16/10): o papel junta "Que me faz
# vencedor. Estamos preparando, estamos preparando" numa frase só, e a figura 198_106 (= 198_108, md5
# 18508e00) fica ao lado de "Estamos preparando" (pág. 3, y 470-522). Ela NÃO é do slide 25, e o
# slide 26 já mostra esse mesmo gesto pela 198_108.
TIRAR = {("198", 17)}
COBRE = 0.8           # reserva: fração das palavras DIFERENTES da frase presentes, juntas, no slide


def norm(t):
    t = unicodedata.normalize("NFD", t.upper())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.findall(r"[A-Z]{3,}", t)


def frases_do(louvor, gestos):
    out = []
    for i, it in enumerate(gestos[louvor]):
        if it["tipo"] != "frase":
            continue
        txt = " ".join("".join(p[0] for p in it["ped"]).split())
        figs = [] if (louvor, i) in TIRAR else it["figs"]
        out.append({"i": i, "txt": txt, "pal": norm(txt), "figs": figs + FALTAM.get((louvor, i), [])})
    return out


def _ocorre(seq, sub):
    n = len(sub)
    return [k for k in range(len(seq) - n + 1) if seq[k:k + n] == sub]


def casa_slide(texto, frases, ponteiro, louvor=""):
    """As frases deste louvor que estão no slide, NA ORDEM DO SLIDE.

    1) a frase tem de aparecer EM SEQUÊNCIA (palavra após palavra) no texto do slide;
       a mais comprida ganha, e a que cabe dentro de outra já casada sai
       ("Jesus vai voltar!" dentro de "Mas Jesus vai voltar!");
    2) reserva para as frases que o recorte da Coletânea leu embaralhadas (duas colunas
       misturadas, ex. "para Jesus Jesus, meu encontrar, Bom Pastor"): 4+ palavras e
       COBRE das palavras presentes no slide;
    3) frase repetida no louvor (o coro, a 2ª volta) pega a ocorrência a partir do ponteiro,
       porque a figura pode ser outra."""
    seq = norm(texto)
    # 4) o Período anda para a frente: frase que já passou só volta se for REPETIÇÃO
    #    (tem outra ocorrência igual dali em diante: o coro, a 2ª volta)
    adiante = {" ".join(f["pal"]) for f in frases if f["i"] >= ponteiro or f["i"] in REPETEM.get(louvor, ())}
    frases = [f for f in frases if f["i"] >= ponteiro or " ".join(f["pal"]) in adiante]
    usados = set()                      # posições do slide já tomadas
    achadas = {}                        # chave da frase -> (posição no slide, frase)
    def escolhe(chave, pos, f):
        atual = achadas.get(chave)
        ai = atual[1]["i"] if atual else None    # fica a 1ª ocorrência dali em diante
        if atual is None or (ai < ponteiro <= f["i"]) or (ponteiro <= f["i"] < ai):
            achadas[chave] = (pos if atual is None else atual[0], f)
    for f in sorted(frases, key=lambda f: -len(f["pal"])):
        if not f["pal"] or (len(f["pal"]) < 2 and not f["figs"]):
            continue                    # "Bem." solto, sem figura: só atrapalha
        chave = " ".join(f["pal"])
        if chave in achadas:
            escolhe(chave, None, f); continue
        primeira = None
        for k in _ocorre(seq, f["pal"]):  # toma TODAS as vezes que ela aparece (o slide traz a
            faixa = set(range(k, k + len(f["pal"])))   # frase e a cópia lida da gravura)
            if not faixa & usados:
                usados |= faixa
                if primeira is None:
                    primeira = k
        if primeira is not None:
            escolhe(chave, primeira, f)
    for f in frases:                    # 2) reserva: frases embaralhadas e compridas
        chave = " ".join(f["pal"])
        dif = set(f["pal"])
        curta = len(dif) < 4
        if chave in achadas or (curta and (not f["figs"] or len(dif) < 2)):
            continue                    # curta só com figura, e aí com TODAS as palavras juntas
        if any(len(set(g["pal"])) >= 3 and len(dif & set(g["pal"])) >= 0.8 * min(len(dif), len(set(g["pal"])))
               for _, g in achadas.values()):
            continue                    # quase igual a uma já casada ("...a ti todo" e "...a ti todo Bem.")
        janela = 2 * len(f["pal"])      # as palavras têm de estar PERTO, não espalhadas no slide
        for k in range(len(seq)):
            # conta também as repetidas ("vai voltar, vai voltar" são 4 palavras, não 2)
            jan = seq[k:k + janela]
            tem = sum(min(jan.count(p), f["pal"].count(p)) for p in dif)
            exige = 1.0 if curta else COBRE
            if curta:                   # curta: as palavras NA ORDEM, com no máximo 3 no meio
                if seq[k] != f["pal"][0]:
                    continue
                j, ok = k, True
                for p in f["pal"][1:]:
                    nxt = next((x for x in range(j + 1, min(len(seq), j + 5)) if seq[x] == p), None)
                    if nxt is None:
                        ok = False; break
                    j = nxt
                if ok and not (set(range(k, j + 1)) & usados):
                    escolhe(chave, k, f)
                    break
                continue
            if seq[k] in dif and len(dif & set(jan)) / len(dif) >= exige and tem / len(f["pal"]) >= 0.6:
                livres = [j for j in range(len(seq)) if seq[j] in dif and j not in usados]
                escolhe(chave, livres[0] if livres else k, f)
                break
    return [f for _, f in sorted(achadas.values(), key=lambda x: (x[0], x[1]["i"]))]


def legenda(frase, texto):
    """A frase como está ESCRITA NO SLIDE (o recorte da Coletânea às vezes embaralha duas colunas):
    as linhas seguidas do slide cujas palavras são todas da frase, a que cobre mais."""
    if _ocorre(norm(texto), frase["pal"]):
        return frase["txt"]             # a frase do papel está inteira no slide: o texto dela é limpo
    dif, linhas = set(frase["pal"]), [l.strip() for l in texto.splitlines() if l.strip()]
    melhor, nota = frase["txt"], 0
    for i in range(len(linhas)):
        junta, cobre = [], set()
        for l in linhas[i:]:
            w = set(norm(l))
            if not w or len(w & dif) * 2 <= len(w):  # mais da metade da linha tem de ser desta frase
                break
            junta.append(l); cobre |= w
        if len(cobre) > nota:
            melhor, nota = " ".join(junta), len(cobre)
    return melhor if nota >= max(1, len(dif) // 2) else frase["txt"]


def monta_imagem(frases, louvor, destino, texto=""):
    itens = [(Path(COLET, "figs", louvor, fig), legenda(f, texto)) for f in frases for fig in f["figs"]]
    itens = [(p, t) for p, t in itens if p.exists()]
    if not itens:
        return False
    L, A = 1600, 900
    tela = Image.new("RGB", (L, A), "white")
    d = ImageDraw.Draw(tela)
    fonte = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 34)
    n = len(itens)
    colunas = min(n, 4)
    linhas = (n + colunas - 1) // colunas
    cw, ch = L // colunas, A // linhas
    ESP, ALT_LIN = 18, 42                # vão figura-legenda e altura de cada linha da legenda
    for k, (p, t) in enumerate(itens):
        c, r = k % colunas, k // colunas
        # a frase, quebrada para caber na coluna (até 3 linhas: "...a ti todo bem." não pode perder o fim)
        palavras, linha, lin = t.upper().split(), "", []
        for w in palavras:
            prova = (linha + " " + w).strip()
            if d.textlength(prova, font=fonte) > cw - 30 and linha:
                lin.append(linha); linha = w
            else:
                linha = prova
        lin.append(linha)
        lin = lin[:3]
        leg_h = ALT_LIN * len(lin)
        # figura + legenda colada embaixo, o bloco inteiro centrado na célula
        fig = Image.open(p).convert("RGBA")
        caixa_h = ch - 20 - ESP - ALT_LIN * 3
        esc = min((cw - 40) / fig.width, caixa_h / fig.height)
        fig = fig.resize((max(1, int(fig.width * esc)), max(1, int(fig.height * esc))))
        y = r * ch + (ch - (fig.height + ESP + leg_h)) // 2
        tela.paste(fig, (c * cw + (cw - fig.width) // 2, y), fig)
        ty = y + fig.height + ESP
        for s in lin:
            d.text((c * cw + (cw - d.textlength(s, font=fonte)) // 2, ty), s, font=fonte, fill="#1a1a1a")
            ty += ALT_LIN
    destino.parent.mkdir(parents=True, exist_ok=True)
    tela.save(destino, "WEBP", quality=82)
    return True


def main():
    gravar = "--gravar" in sys.argv
    gestos = json.load(open(COLET / "gestos.json", encoding="utf-8"))
    textos = json.load(open(APP / "apresentacoes" / APRES / "textos.json", encoding="utf-8"))
    frases = {k: frases_do(k, gestos) for k in LOUVORES}
    ponteiro = {k: 0 for k in LOUVORES}
    tabela = {}
    for s, texto in enumerate(textos):
        melhor, achadas = None, []
        for k in LOUVORES:
            a = casa_slide(texto, frases[k], ponteiro[k], k)
            if len(a) > len(achadas):
                melhor, achadas = k, a
        if sum(len(f["pal"]) for f in achadas) < 4:   # versículo ou título que cruzou 1-3 palavras
            print("slide %2d  (espera)  %s" % (s, " ".join(texto.split())[:60]))
            continue
        # só frase ÚNICA no louvor empurra o ponteiro: a repetida (o coro) pode estar na
        # última volta e empurraria para além da estrofe que ainda vem
        conta = {}
        for f in frases[melhor]:
            conta[" ".join(f["pal"])] = conta.get(" ".join(f["pal"]), 0) + 1
        unicas = [f["i"] for f in achadas if conta[" ".join(f["pal"])] == 1]
        ponteiro[melhor] = max(ponteiro[melhor], (max(unicas) if unicas else max([f["i"] for f in achadas if f["figs"]] or [ponteiro[melhor] - 1])) + 1)
        nome = "s%02d.webp" % s
        figs = sum(len(f["figs"]) for f in achadas)
        print("slide %2d  %-10s %s %d frases, %d figuras: %s" % (s, melhor, [f["i"] for f in achadas], len(achadas), figs,
              " / ".join(f["txt"] for f in achadas)[:110]))
        if gravar and monta_imagem(achadas, melhor, APP / "gestos" / PASTA / nome, texto):
            tabela[str(s)] = {"img": "gestos/%s/%s" % (PASTA, nome), "louvor": LOUVORES[melhor]}
    if gravar:
        js = ("// Gerado por ferramentas/gestos_da_apresentacao.py (" + APRES + "). Não editar à mão.\n"
              "window.GESTOS = window.GESTOS || {};\n"
              "window.GESTOS[" + json.dumps("apres:" + APRES, ensure_ascii=False) + "] = "
              + json.dumps(tabela, ensure_ascii=False, indent=1) + ";\n")
        (APP / "dados" / "gestos.js").write_text(js, encoding="utf-8")
        print("gravado: %d slides com gesto em dados/gestos.js" % len(tabela))


if __name__ == "__main__":
    main()
