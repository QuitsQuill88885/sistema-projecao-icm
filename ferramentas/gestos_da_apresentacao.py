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
# Uma entrada por apresentação. "slides" = só estes slides podem ter gesto (None = todos). Na aula, a capa
# e o fim também dizem "Você sabe o que é salvação?" e empurrariam o ponteiro antes do louvor começar.
APRESENTACOES = {
    "Louvores da Evangelização de Outubro 2026": {
        "pasta": "evang_out2026", "slides": None,
        "louvores": {"fui_lavado": "FUI LAVADO NO SANGUE", "81": "SENHOR TÃO PEQUENO SOU",
                     "97": "JESUS É O CAMINHO", "198": "O DIA ESTÁ CHEGANDO"}},
    "Evangelização de Outubro 2026": {
        "pasta": "evang_out2026_aula", "slides": {7, 8, 9, 10, 11, 17, 18, 19, 20},
        "louvores": {"69": "VOCÊ SABE O QUE É SALVAÇÃO", "249": "ESTA É A MENSAGEM ETERNA DE DEUS"}},
}
APRES = "Louvores da Evangelização de Outubro 2026"
for _i, _a in enumerate(__import__("sys").argv):
    if _a == "--apres" and _i + 1 < len(__import__("sys").argv):
        APRES = __import__("sys").argv[_i + 1]
PASTA = APRESENTACOES[APRES]["pasta"]
LOUVORES = APRESENTACOES[APRES]["louvores"]
SLIDES = APRESENTACOES[APRES]["slides"]
# frases que VOLTAM nos slides sem estar repetidas no papel (o coro do 97 vem uma vez, "CORO 2x",
# e volta depois de cada estrofe). Índice = posição no gestos.json da Coletânea.
REPETEM = {"97": {4, 5},
           # a aula (3.0.9): o "bis" do 69 e o coro do 249, que volta no slide 20
           "69": {11, 12, 15}, "249": {8, 9, 10, 11}}
# figuras que o recorte da Coletânea NÃO pegou. 18/10: VAZIO. A mão levantada (imagem 48 do PDF) que
# entrava aqui à mão em 3 frases era jogada fora pelo filtro de largura do extrai_gestos.py; com o filtro
# consertado ela vem do próprio livro em 9 frases de 5 louvores, cada uma no lugar dela.
FALTAM = {}
# figura que o recorte grudou na frase errada (conferente cego, 16/10): o papel junta "Que me faz
# vencedor. Estamos preparando, estamos preparando" numa frase só, e a figura 198_106 (= 198_108, md5
# 18508e00) fica ao lado de "Estamos preparando" (pág. 3, y 470-522). Ela NÃO é do slide 25, e o
# slide 26 já mostra esse mesmo gesto pela 198_108.
TIRAR = {("198", 17)}
# aula (3.0.9): o papel dos gestos diz "e entregue"; a apostila da Cris e o slide dizem "e entrega" (a versao
# do caderno, a certa). Casa e escreve como a apostila. O slide 11 tem o texto colado ("ENTREGAA"): a 2a forma.
CASA_COMO = {("69", 12): ["e entrega", "e entregaa"]}
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
        formas = CASA_COMO.get((louvor, i), [txt])
        legs = pedacos(txt, it.get("legs"), len(it["figs"])) if figs else []
        for forma in formas:
            out.append({"i": i, "txt": formas[0] if (louvor, i) in CASA_COMO else txt, "pal": norm(forma),
                        "figs": figs + FALTAM.get((louvor, i), []), "legs": legs})
    return out


def pedacos(txt, legs, n):
    """O pedaço da letra de CADA figura, lido pelo extrator na posição do texto em volta dela no livro.
    Só vale onde muda alguma coisa: frase com 2+ figuras ("O Pai Celeste" | "que deseja a ti todo Bem.")
    ou frase que o extrator montou cruzando as duas colunas (249: "oportunidade," era a figura de
    "De nova vida e felicidade."). Pedaço vazio = não deu para repartir: fica a frase inteira, como antes."""
    if not legs or len(legs) != n or not all(legs):
        return []
    if n == 1 and sorted(norm(legs[0])) == sorted(norm(txt)):
        return []                       # a mesma frase: segue a legenda do slide (e o CASA_COMO)
    return list(legs)


def leg_da_figura(f, j, texto):
    return f["legs"][j] if f.get("legs") else legenda(f, texto)


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
    itens = [(Path(COLET, "figs", louvor, fig), leg_da_figura(f, j, texto)) for f in frases for j, fig in enumerate(f["figs"])]
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


def exporta_figuras(frases, louvor, pasta, texto=""):
    """Cada figura RECORTADA no conteúdo (sem o branco em volta), para a tela de retorno montar a grade grande
    com a legenda em HTML (3.0.9: a letra da legenda precisa de >= 45 px numa TV de 32" a 1080p)."""
    out = []
    for f in frases:
        for j, fig in enumerate(f["figs"]):
            leg = leg_da_figura(f, j, texto)
            p = Path(COLET, "figs", louvor, fig)
            if not p.exists():
                continue
            nome = "%s_%s.webp" % (louvor, Path(fig).stem)
            destino = APP / "gestos" / pasta / "f" / nome
            # 18/10: refaz sempre. O nome é a POSIÇÃO no livro (fui_lavado_02_0 era o colchete em branco e
            # agora é a mão): "se já existe, pula" deixava a figura velha com o nome novo.
            if True:
                im = Image.open(p).convert("RGBA")
                fundo = Image.new("RGBA", im.size, (255, 255, 255, 255))
                plano = Image.alpha_composite(fundo, im).convert("RGB")
                # o que não é (quase) branco: a caixa do desenho
                cinza = plano.convert("L").point(lambda v: 255 if v < 235 else 0)
                caixa = cinza.getbbox() or (0, 0, plano.width, plano.height)
                m = 6
                caixa = (max(0, caixa[0] - m), max(0, caixa[1] - m), min(plano.width, caixa[2] + m), min(plano.height, caixa[3] + m))
                destino.parent.mkdir(parents=True, exist_ok=True)
                plano.crop(caixa).save(destino, "WEBP", quality=88)
            with Image.open(destino) as im_r:   # a proporção (altura/largura): o retorno escolhe as colunas por ela
                r = round(im_r.height / im_r.width, 3)
            out.append({"img": "gestos/%s/f/%s" % (pasta, nome), "txt": leg, "r": r})
    return out


def main():
    gravar = "--gravar" in sys.argv
    gestos = json.load(open(COLET / "gestos.json", encoding="utf-8"))
    textos = json.load(open(APP / "apresentacoes" / APRES / "textos.json", encoding="utf-8"))
    frases = {k: frases_do(k, gestos) for k in LOUVORES}
    ponteiro = {k: 0 for k in LOUVORES}
    tabela = {}
    for s, texto in enumerate(textos):
        if SLIDES is not None and s not in SLIDES:
            print("slide %2d  (fora do louvor)  %s" % (s, " ".join(texto.split())[:60]))
            continue
        melhor, achadas = None, []
        for k in LOUVORES:
            a = casa_slide(texto, frases[k], ponteiro[k], k)
            if len(a) > len(achadas):
                melhor, achadas = k, a
        # versículo ou título que cruzou 1-3 palavras. Com os slides do louvor já marcados (a aula), basta 1.
        if sum(len(f["pal"]) for f in achadas) < (4 if SLIDES is None else 1):
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
            tabela[str(s)] = {"img": "gestos/%s/%s" % (PASTA, nome), "louvor": LOUVORES[melhor],
                              "figs": exporta_figuras(achadas, melhor, PASTA, texto)}
    if gravar:
        # junta: as outras apresentações que já estão no arquivo ficam como estão (mesmos bytes)
        arq = APP / "dados" / "gestos.js"
        velho = arq.read_text(encoding="utf-8") if arq.exists() else ""
        blocos = dict(re.findall(r'(window\.GESTOS\[".*?"\] = \{.*?\};\n)', velho, re.S) and
                      [(m.split("] = ", 1)[0], m) for m in re.findall(r'window\.GESTOS\[".*?"\] = \{.*?\};\n', velho, re.S)])
        chave = "window.GESTOS[" + json.dumps("apres:" + APRES, ensure_ascii=False)
        blocos[chave] = chave + "] = " + json.dumps(tabela, ensure_ascii=False, indent=1) + ";\n"
        js = ("// Gerado por ferramentas/gestos_da_apresentacao.py (" + ", ".join(APRESENTACOES) + "). Não editar à mão.\n"
              "window.GESTOS = window.GESTOS || {};\n" + "".join(blocos.values()))
        arq.write_text(js, encoding="utf-8")
        print("gravado: %d slides com gesto em dados/gestos.js" % len(tabela))


if __name__ == "__main__":
    main()
