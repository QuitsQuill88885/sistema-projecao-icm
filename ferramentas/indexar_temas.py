# -*- coding: utf-8 -*-
"""Constrói o índice que liga VERSÍCULO a LOUVOR pela mensagem.

O Sistema roda offline num computador fraco: não dá para pensar no momento do
culto. Então o trabalho pesado é feito aqui, uma vez, e vira um índice pequeno
que o programa consulta em milissegundos.

COMO ELE DECIDE QUE UM LOUVOR "TEM A VER" COM UM VERSÍCULO

1. Palavra rara pesa mais (TF-IDF). "Resplandece" aparece em pouquíssimos
   louvores, então quem a tem casa forte com Isaías 60:1. Já "senhor" e "deus"
   estão em quase todos e praticamente não informam nada.
2. O TÍTULO pesa o triplo do corpo da letra: é ali que mora o assunto.
3. Um dicionário de temas cobre o que a palavra igual não alcança — Neemias
   fala de muro e reconstrução; o louvor fala de obra e edificar. Sem essa
   ponte, os dois nunca se encontrariam.

O que sai daqui é METADADO: pesos de palavras por louvor. Nenhuma letra é
copiada para o índice.

Uso:  python indexar_temas.py            (grava dados/temas.js)
"""
import io, json, math, os, re, sys, unicodedata
from collections import Counter, defaultdict

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Palavras que aparecem em tudo e não dizem nada sobre o assunto.
VAZIAS = set("""
a o as os um uma uns umas de do da dos das em no na nos nas por para pra per
com sem sob sobre entre ate ate' apos e ou mas que se quando onde como qual
quais quem cujo cuja eu tu ele ela nos vos eles elas me te lhe nos vos lhes
meu minha meus minhas teu tua teus tuas seu sua seus suas nosso nossa nossos
nossas este esta estes estas esse essa esses essas aquele aquela aqueles
aquelas isto isso aquilo ja nao sim tambem so muito mais menos bem mal
ser estar ter haver ir vir fazer dar ver dizer poder querer saber
sou es e somos sao era eram foi foram sera serao seja sejam
esta estao estava estavam esteve estiveram
tem tenho temos tinha tinham teve tiveram tera terao tenha tenham
vou vai vamos vao ia iam foi foram
aqui ali la agora entao sempre nunca hoje amanha ontem
todo toda todos todas nada tudo algum alguma alguns algumas
ao aos as' à às pelo pela pelos pelas num numa nuns numas
oh ai eis pois porque porem entao assim mesmo ainda depois antes
""".split())

# Pontes de sentido: o que o texto bíblico diz -> famílias de palavras que o
# louvor usaria. É a camada que a palavra-igual não alcança.
TEMAS = {
    "reconstrucao": "muro muros reedificar reedificacao reconstruir reconstrucao ruinas escombros "
                    "obra edificar edificacao alicerce fundamento restaurar restauracao levantar",
    "clamor":       "clamor clamar clamo grito bradar suplica rogo socorro misericordia perdao "
                    "arrependimento contrito quebrantado",
    "sangue":       "sangue cruz calvario remido remissao resgate expiacao cordeiro imolado",
    "volta":        "volta voltar vem venha arrebatamento maranata nuvens trombeta encontro "
                    "breve cedo aguardar esperar noivo bodas",
    "luz":          "luz resplandecer resplandece resplandecente brilhar brilha raiar aurora "
                    "amanhecer clarear trevas escuridao",
    "colheita":     "seara ceifa colheita semear semeador semente frutos messe trabalhadores",
    "pastoreio":    "pastor ovelhas rebanho aprisco redil vale sombra guiar conduzir",
    "batalha":      "batalha guerra luta pelejar vencer vitoria armadura espada escudo inimigo",
    "louvor":       "louvor louvar adorar adoracao gloria glorificar exaltar magnificar cantar "
                    "cantico harpa citara jubilo",
    "consolo":      "consolo consolar enxugar lagrimas choro tristeza dor alivio descanso paz",
    "aliança":      "alianca promessa juramento fidelidade fiel palavra cumprir cumprida",
    "peixes":       "peixes pescar pescadores rede barco mar tempestade ondas travessia",
    "pao":          "pao multiplicar multiplicou fome saciar alimentar mesa ceia",
    "agua":         "agua fonte sede beber rio manancial poco vinho",
    "caminho":      "caminho caminhar estrada vereda peregrino jornada seguir passos",
    "espirito":     "espirito consolador poder unção derramar avivamento fogo chama pentecostes",
    "familia":      "casa lar familia filhos pais criancas geracao",
    "missao":       "ide evangelho anunciar pregar nacoes povos missionario mensagem",
    "gratidao":     "gratidao grato agradecer bondade benefico benignidade misericordias",
    "santidade":    "santo santidade puro pureza limpar purificar consagrar consagracao altar",
}


def normal(t):
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.lower()


def palavras(t):
    """Só o que informa: fora pontuação, números e palavras de ligação."""
    return [p for p in re.findall(r"[a-z]{3,}", normal(t)) if p not in VAZIAS]


def carregar(caminho, chave):
    s = io.open(caminho, encoding="utf-8").read()
    i = s.index("=") + 1
    return json.loads(s[i:].rstrip().rstrip(";"))


def construir():
    louvores = carregar(os.path.join(AQUI, "dados", "louvores.js"), "LOUVORES")

    # 1. saco de palavras de cada louvor; o TÍTULO conta 3 vezes
    sacos = []
    for x in louvores:
        letra = " ".join(l for sl in x.get("slides", []) for l in sl.get("linhas", []))
        c = Counter(palavras(letra))
        for p in palavras(x["titulo"]):
            c[p] += 3
        sacos.append(c)

    # 2. palavra rara vale mais (IDF)
    n = len(sacos)
    em_quantos = Counter()
    for c in sacos:
        em_quantos.update(c.keys())
    idf = {p: math.log(n / (1.0 + q)) for p, q in em_quantos.items()}

    # 3. guarda só as palavras que realmente distinguem o louvor
    indice = []
    for c in sacos:
        pesos = {p: round(math.sqrt(v) * idf.get(p, 0), 3) for p, v in c.items()}
        top = sorted(pesos.items(), key=lambda kv: -kv[1])[:24]
        indice.append({p: v for p, v in top if v > 0.4})

    # 4. temas: quais louvores encostam em cada família de palavras
    temas = {}
    for nome, txt in TEMAS.items():
        alvo = set(palavras(txt))
        ligados = []
        for i, c in enumerate(sacos):
            pontos = sum(math.sqrt(c[p]) * idf.get(p, 0) for p in alvo if p in c)
            if pontos > 1.5:
                ligados.append([i, round(pontos, 2)])
        ligados.sort(key=lambda a: -a[1])
        temas[nome] = ligados[:60]

    return {"idf": {p: round(v, 3) for p, v in idf.items() if v > 1.2},
            "louvores": indice,
            "temas": temas,
            "familias": {k: sorted(set(palavras(v))) for k, v in TEMAS.items()}}


def main():
    d = construir()
    saida = os.path.join(AQUI, "dados", "temas.js")
    txt = "window.TEMAS=" + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";"
    io.open(saida, "w", encoding="utf-8").write(txt)
    print("louvores indexados : %d" % len(d["louvores"]))
    print("palavras com peso  : %d" % len(d["idf"]))
    print("temas              : %d" % len(d["temas"]))
    print("arquivo            : %s  (%.0f KB)" % (saida, len(txt) / 1024.0))


if __name__ == "__main__":
    main()
