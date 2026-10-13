# -*- coding: utf-8 -*-
"""Reaplica os consertos manuais no dados/louvores.js.

POR QUE: o louvores.js e' GERADO (gen_louvores.py). Os consertos feitos a mao
(143 TENHO UMA CANDEIA com o coro completo; 218 MARANATA com a linha DESPERTA
e o 2x como selo) seriam PERDIDOS numa regeneracao. Este script poe de volta.

QUANDO RODAR: sempre, logo depois de gen_louvores.py. Nao faz mal rodar a toa:
se os slides ja estao certos, nao muda nada.
"""
import io, json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
LJS = os.path.join(RAIZ, "dados", "louvores.js")
CON = os.path.join(RAIZ, "dados", "consertos_louvores.json")


def io_json_acrescimos():
    return json.load(io.open(CON, encoding="utf-8")).get("acrescimos", [])


def _primeira_linha(slides):
    try:
        return slides[0]["linhas"][0]
    except (IndexError, KeyError, TypeError):
        return None


def casa_conserto(c, lista):
    """Devolve o indice do louvor onde o conserto c cai, ou None se o titulo nao existe.

    13/10/2026: antes casava so por col|num|titulo e parava na 1a copia. Com TITULO
    DUPLICADO (ex.: ES UM REMIDO DE DEUS nas posicoes 1564 e 1565; MARANATA dos Avulsos
    1320/1321) o conserto da 2a copia caia na 1a e a apagava. Agora:
      1) col|num|titulo; se so uma copia, e' ela (igual a antes, registros antigos valem);
      2) se empatar, a 1a linha da letra (slides[0].linhas[0], a chave, que nunca muda):
         campo opcional "primeira_linha" do registro, ou a 1a linha dos proprios slides;
      3) se ainda empatar, a posicao no acervo (campo opcional "pos");
      4) se mesmo assim nao der UMA copia, PARA com erro. Nunca escolhe a primeira calado.
    """
    cand = [i for i, l in enumerate(lista)
            if str(l.get("num")) == str(c["num"]) and l.get("col") == c["col"]
            and (l.get("titulo") or "").strip() == c["titulo"].strip()]
    if len(cand) <= 1:
        return cand[0] if cand else None
    pl = c.get("primeira_linha") or _primeira_linha(c.get("slides"))
    por_linha = [i for i in cand if _primeira_linha(lista[i].get("slides")) == pl]
    if len(por_linha) == 1:
        return por_linha[0]
    resto = por_linha or cand
    if c.get("pos") is not None and c["pos"] in resto:
        return c["pos"]
    raise SystemExit("ERRO: conserto de titulo duplicado %s|%s|%s casa com %d copias (posicoes %s) "
                     "e nem a 1a linha nem a posicao desempatam. Nada foi gravado."
                     % (c["col"], c["num"], c["titulo"], len(resto), resto))


def main():
    consertos = json.load(io.open(CON, encoding="utf-8"))["consertos"]
    s = io.open(LJS, encoding="utf-8").read()
    pref = s[:s.index("=") + 1]
    L = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    lista = L.get("louvores") if isinstance(L, dict) else L
    mudou = 0
    alvos = [casa_conserto(c, lista) for c in consertos]  # casa TUDO antes de mexer: erro nao deixa meio gravado
    for c, i in zip(consertos, alvos):
        if i is not None and lista[i].get("slides") != c["slides"]:
            lista[i]["slides"] = c["slides"]
            mudou += 1
    # ACRESCIMOS (26/09/2026): louvor que nao existe em livro nenhum desta maquina,
    # entrado de fonte de fora (acrescenta_louvor_de_fora.py). O gen_louvores.py nao
    # sabe dele, entao sem isto ele SUMIRIA na proxima regeneracao.
    acrescentados = 0
    for c in io_json_acrescimos():
        existe = any(str(l.get("num")) == str(c["num"]) and l.get("col") == c["col"]
                     and (l.get("titulo") or "").strip() == c["titulo"].strip() for l in lista)
        if not existe:
            lista.append({"num": c["num"], "titulo": c["titulo"], "col": c["col"],
                          "slides": c["slides"]})
            acrescentados += 1
            mudou += 1
    if acrescentados:
        print("louvores acrescentados:", acrescentados)
    if mudou:
        tmp = LJS + ".tmp"
        io.open(tmp, "w", encoding="utf-8").write(
            pref + " " + json.dumps(L, ensure_ascii=False, separators=(",", ":")) + ";")
        os.replace(tmp, LJS)
    print("consertos reaplicados:", mudou, "(0 = ja estava tudo certo)")


if __name__ == "__main__":
    main()
