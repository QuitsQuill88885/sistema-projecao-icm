# -*- coding: utf-8 -*-
"""Importa os louvores de CIAS com animação para dentro do Sistema.

Os GIFs vêm do pacote oficial da igreja (PT_ColetaneaCIAS_2018_Gifs.pkr, ~971 MB,
formato do Glorifica). São 971 MB: grandes demais para viajar dentro do
instalador, então entram UMA VEZ na máquina e ficam na pasta do usuário, que
sobrevive a toda atualização do Sistema:

    %APPDATA%\\Sistema Projecao\\animacoes\\
        indice.json      { "8": ["8-1.gif", "8-2.gif"], ... }
        8-1.gif
        8-2.gif
        ...

Cada GIF já é a TELA PRONTA (título amarelo, letra branca, fundo animado), não
só um fundo — por isso ele SUBSTITUI o texto, e não se combina com ele.

Uso:
    python importar_animacoes.py <arquivo.pkr>
    python importar_animacoes.py <arquivo.pkr> --destino <pasta>
"""
import io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ler_pkr import abrir, tipo

# "8-2" = louvor 8, tela 2
NOME = re.compile(r"^(\d+)-(\d+)$")

# ---------------------------------------------------------------- conversão
# Os GIFs do pacote somam 970 MB, e 153 deles nem são animados — são imagens
# paradas guardadas em GIF, que é o pior formato possível para isso. Pior: GIF
# grande é decodificado no processador, e 1440x1080 com 60 quadros ENGASGA no
# notebook da igreja bem no meio do louvor.
#
# WebP resolve as duas coisas: o navegador toca nativo (com aceleração) e o
# arquivo encolhe muito. Nas animadas ainda ficamos com metade dos quadros,
# dobrando o tempo de cada um — o laço dura o mesmo e o olho não percebe.
QUALIDADE_PARADA = 82
QUALIDADE_ANIMADA = 72
MAX_QUADROS = 30


def para_webp(dados):
    """GIF -> WebP. Devolve (bytes, extensão, quantos quadros)."""
    from PIL import Image
    im = Image.open(io.BytesIO(dados))
    n = getattr(im, "n_frames", 1)
    saida = io.BytesIO()

    if n <= 1:                                   # imagem parada
        im.convert("RGB").save(saida, "WEBP", quality=QUALIDADE_PARADA, method=6)
        return saida.getvalue(), "webp", 1

    pulo = max(1, -(-n // MAX_QUADROS))          # arredonda para cima
    quadros, tempos = [], []
    for i in range(0, n, pulo):
        im.seek(i)
        quadros.append(im.convert("RGB"))
        tempos.append((im.info.get("duration") or 60) * pulo)
    quadros[0].save(saida, "WEBP", save_all=True, append_images=quadros[1:],
                    duration=tempos, loop=0, quality=QUALIDADE_ANIMADA, method=4)
    return saida.getvalue(), "webp", len(quadros)


def pasta_padrao():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Sistema Projecao", "animacoes")


def importar(caminho_pkr, destino=None, aviso=None):
    """Extrai os GIFs e grava o índice. Devolve (quantos_louvores, quantas_telas)."""
    destino = destino or pasta_padrao()
    os.makedirs(destino, exist_ok=True)

    _pacote, entradas, f = abrir(caminho_pkr)
    indice = {}
    telas = 0
    bytes_antes = bytes_depois = 0
    for i, e in enumerate(entradas):
        m = NOME.match(e["nome"])
        if not m:                       # nome fora do padrão: ignora em vez de adivinhar
            continue
        louvor, tela = m.group(1), int(m.group(2))
        f.seek(e["pos"])
        dados = f.read(e["tam"])
        ext = tipo(dados)
        if ext == "bin":                # não é imagem: não serve pro telão
            continue
        bytes_antes += len(dados)
        try:
            dados, ext, _q = para_webp(dados)
        except Exception:
            pass                        # deu problema na conversão: grava o original
        bytes_depois += len(dados)
        arq = "%s-%d.%s" % (louvor, tela, ext)
        with io.open(os.path.join(destino, arq), "wb") as g:
            g.write(dados)
        indice.setdefault(str(int(louvor)), []).append((tela, arq))
        telas += 1
        if aviso:
            aviso(i + 1, len(entradas))
    if bytes_antes:
        print("\n  %.0f MB -> %.0f MB (%.0f%% menor)" % (
            bytes_antes / 1048576.0, bytes_depois / 1048576.0,
            100 * (1 - bytes_depois / float(bytes_antes))))

    # cada louvor com as telas em ordem
    indice = {k: [a for _t, a in sorted(v)] for k, v in indice.items()}
    tmp = os.path.join(destino, "indice.json.tmp")
    with io.open(tmp, "w", encoding="utf-8") as g:
        json.dump(indice, g, ensure_ascii=False)
    os.replace(tmp, os.path.join(destino, "indice.json"))   # nunca deixa índice pela metade
    return len(indice), telas


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    pkr = sys.argv[1]
    destino = None
    if "--destino" in sys.argv:
        destino = sys.argv[sys.argv.index("--destino") + 1]
    louvores, telas = importar(
        pkr, destino, aviso=lambda i, n: sys.stdout.write("\r  %d/%d" % (i, n)) or sys.stdout.flush())
    print("\npronto: %d louvores com animação, %d telas" % (louvores, telas))
    print("em: %s" % (destino or pasta_padrao()))


if __name__ == "__main__":
    main()
