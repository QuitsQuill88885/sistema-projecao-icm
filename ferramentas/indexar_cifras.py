# -*- coding: utf-8 -*-
"""Descobre em que página de cada PDF de cifra está cada louvor.

O músico do banquinho precisa abrir a cifra do louvor que está sendo cantado —
sem depender de quem passa os slides. Para isso o Sistema precisa saber, para
cada louvor do catálogo, em que PDF e em que página está a cifra dele.

Cada coletânea publica de um jeito diferente:
    "Coletânea 2018 - Cifrada Nivel II"   -> a 1ª linha da página é o TÍTULO
    "Coletânea Cifras 2025"               -> a 1ª linha é "NN - TÍTULO"
    "Coletânea de Louvores Avulsos 2024"  -> a 1ª linha é "NN - TÍTULO (TOM)"

Então lemos a primeira linha de cada página e casamos com o catálogo pelo
TÍTULO (sem acento, sem pontuação) — que é o que os três têm em comum. O número
serve de confirmação quando existe, e o tom é guardado quando aparece.

Gera %APPDATA%\\Sistema Projecao\\cifras\\indice.json:
    { "Coletânea 2018|60": {"pdf": "...", "pag": 61, "tom": "G"}, ... }

Uso:  python indexar_cifras.py <pasta_com_os_pdfs> [--destino <pasta>]
"""
import io, json, os, re, sys, unicodedata

# "23 - AS ESTRELAS DO CÉU (G)"  ->  numero, titulo, tom
LINHA = re.compile(r"^\s*(?:(\d{1,4})\s*[-–]\s*)?(.+?)(?:\s*\(([A-G][#b]?m?)\))?\s*$")


def normal(t):
    """Título comparável: sem acento, sem pontuação, sem espaço dobrado."""
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^A-Za-z0-9 ]+", " ", t.upper())
    return re.sub(r"\s+", " ", t).strip()


def pasta_padrao():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Sistema Projecao", "cifras")


def carregar_catalogo(caminho_js):
    s = io.open(caminho_js, encoding="utf-8").read()
    return json.loads(s[s.index("["):s.rindex("]") + 1])


# Uma página normal traz de 1 a 4 louvores. As páginas com dezenas de títulos são
# o ÍNDICE REMISSIVO do começo do PDF — se entrassem, todo louvor apontaria para
# a página do sumário em vez da cifra.
MAX_POR_PAGINA = 6


def paginas_do_pdf(caminho, titulos):
    """Devolve [(pagina_1based, numero_ou_None, titulo_normalizado, tom_ou_None)].

    Varre a página INTEIRA: as coletâneas imprimem de 1 a 4 louvores por página,
    então olhar só a primeira linha achava quase nada.
    """
    from pypdf import PdfReader
    r = PdfReader(caminho)
    saida = []
    for i, pag in enumerate(r.pages):
        try:
            linhas = (pag.extract_text() or "").splitlines()
        except Exception:
            continue
        achados, vistos = [], set()
        for ln in linhas:
            m = LINHA.match(ln.strip())
            if not m:
                continue
            num, titulo, tom = m.group(1), normal(m.group(2)), m.group(3)
            if len(titulo) < 5 or titulo not in titulos or titulo in vistos:
                continue
            vistos.add(titulo)
            achados.append((i + 1, int(num) if num else None, titulo, tom))
        if len(achados) <= MAX_POR_PAGINA:      # senão é sumário: descarta a página inteira
            saida.extend(achados)
    return saida


def indexar(pasta_pdfs, catalogo, destino=None, aviso=None):
    destino = destino or pasta_padrao()
    os.makedirs(destino, exist_ok=True)

    # o catálogo indexado por título normalizado (um título pode estar em várias coletâneas)
    porTitulo = {}
    for x in catalogo:
        porTitulo.setdefault(normal(x["titulo"]), []).append(x)

    indice, sem_dono = {}, []
    pdfs = sorted(p for p in os.listdir(pasta_pdfs) if p.lower().endswith(".pdf"))
    for nome in pdfs:
        cam = os.path.join(pasta_pdfs, nome)
        if aviso:
            aviso(nome)
        for pagina, num, titulo, tom in paginas_do_pdf(cam, porTitulo):
            cands = porTitulo.get(titulo)
            if not cands:
                sem_dono.append((nome, pagina, titulo))
                continue
            # O NÚMERO diz QUAL louvor é (quando há títulos repetidos com letras
            # diferentes). Mas o mesmo louvor existe em várias coletâneas com
            # números diferentes — mesma letra, outra numeração. A cifra vale
            # para todos eles. Antes eu dava a cifra só para o que casava o
            # número, e os 665 gêmeos da Coletânea Antiga ficavam sem nenhuma.
            certo = [c for c in cands if num is not None and _num(c) == num]
            if certo:
                letra = primeira_linha(certo[0])
                escolhidos = [c for c in cands if primeira_linha(c) == letra]
            else:
                escolhidos = cands
            for c in escolhidos:
                # MESMA chave do app (chaveLouvor em app.js): número|título|1ª linha.
                # Só "coletânea|número" colidia: os 531 Avulsos têm num "AV", então
                # todos caíam na mesma chave e 530 ficavam sem cifra.
                chave = chave_louvor(c)
                if chave in indice:       # já achado num PDF anterior: não sobrescreve
                    continue
                indice[chave] = {"pdf": nome, "pag": pagina}
                if tom:
                    indice[chave]["tom"] = tom

    tmp = os.path.join(destino, "indice.json.tmp")
    with io.open(tmp, "w", encoding="utf-8") as g:
        json.dump(indice, g, ensure_ascii=False)
    os.replace(tmp, os.path.join(destino, "indice.json"))
    return indice, sem_dono, pdfs


def primeira_linha(x):
    """1ª linha da letra: é o que distingue louvores DIFERENTES de mesmo título."""
    sl = x.get("slides") or []
    return normal(sl[0]["linhas"][0]) if sl and sl[0].get("linhas") else ""


def chave_louvor(x):
    p = ""
    sl = x.get("slides") or []
    if sl and sl[0].get("linhas"):
        p = sl[0]["linhas"][0]
    return (x.get("num") or "") + "|" + x["titulo"] + "|" + p


def _num(x):
    n = x.get("num") or ""
    return int(n) if n.isdigit() else None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    pasta = sys.argv[1]
    destino = sys.argv[sys.argv.index("--destino") + 1] if "--destino" in sys.argv else None
    aqui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    catalogo = carregar_catalogo(os.path.join(aqui, "dados", "louvores.js"))
    indice, sem_dono, pdfs = indexar(
        pasta, catalogo, destino, aviso=lambda n: sys.stderr.write("  lendo %s\n" % n))

    from collections import Counter
    dono = {chave_louvor(x): x["col"] for x in catalogo}
    por_col = Counter(dono.get(k, "?") for k in indice)
    total = Counter(x["col"] for x in catalogo)
    print("\n%d PDFs lidos, %d louvores com cifra localizada\n" % (len(pdfs), len(indice)))
    for col in sorted(total):
        print("  %-20s %4d de %4d  (%.0f%%)"
              % (col, por_col.get(col, 0), total[col], 100.0 * por_col.get(col, 0) / total[col]))
    com_tom = sum(1 for v in indice.values() if v.get("tom"))
    print("\n  com tom informado: %d" % com_tom)
    print("  páginas sem louvor correspondente: %d" % len(sem_dono))


if __name__ == "__main__":
    main()
