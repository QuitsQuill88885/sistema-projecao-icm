# -*- coding: utf-8 -*-
"""Lê um pacote .PKR (formato do Glorifica, descontinuado) e extrai o conteúdo.

O pacote "PT_ColetaneaCIAS_2018_Gifs.pkr" traz os louvores de CIAS (Crianças,
Intermediários e Adolescentes) como GIFs animados — que é o material oficial da
igreja. O Glorifica saiu de circulação, então lemos o pacote direto.

Formato (descoberto lendo os bytes):
  ARQUIVO
    0x00  "PKR!"                  magia
    0x04  uint32                  versão (1)
    0x08  uint32 + uint32         carimbo
    0x10  uint64                  quantidade de entradas
    0x18  uint64                  posição da primeira entrada
    0x20  UTF-16LE                nome do pacote ("Gifs")
  CADA ENTRADA
    +0    uint32                  tamanho deste cabeçalho (40)
    +4    uint32                  tamanho do nome, em bytes
    +8    uint32                  reservado
    +12   uint32                  tamanho dos dados
    +16   8 bytes                 carimbo
    +24   16 bytes                zeros
    +40   UTF-16LE                nome (ex: "1-1" = louvor 1, tela 1)
    ...   bytes                   o arquivo em si (GIF)
"""
import io, os, struct, sys

MAGIA = b"PKR!"
CAB_ENTRADA = 40


def abrir(caminho):
    """Devolve (nome_do_pacote, [entradas]). Cada entrada é um dicionário."""
    f = io.open(caminho, "rb")
    cab = f.read(0x40)
    if not cab.startswith(MAGIA):
        raise ValueError("não é um pacote PKR: %r" % cab[:8])

    qtd = struct.unpack_from("<Q", cab, 0x10)[0]
    pos = struct.unpack_from("<Q", cab, 0x18)[0]
    nome_pacote = cab[0x20:].split(b"\x00\x00")[0].decode("utf-16-le", "ignore").strip("\x00")

    entradas = []
    for _ in range(qtd):
        f.seek(pos)
        e = f.read(CAB_ENTRADA)
        if len(e) < CAB_ENTRADA:
            break
        tam_cab, tam_nome, _res, tam_dados = struct.unpack_from("<IIII", e, 0)
        if tam_cab != CAB_ENTRADA:          # formato diferente do esperado: para aqui
            break
        nome = f.read(tam_nome).decode("utf-16-le", "ignore").strip("\x00")
        entradas.append({"nome": nome, "pos": pos + tam_cab + tam_nome, "tam": tam_dados})
        pos = pos + tam_cab + tam_nome + tam_dados
    return nome_pacote, entradas, f


def tipo(dados):
    if dados.startswith(b"GIF8"):   return "gif"
    if dados.startswith(b"\x89PNG"): return "png"
    if dados.startswith(b"\xff\xd8"): return "jpg"
    return "bin"


def main():
    if len(sys.argv) < 2:
        print("uso: ler_pkr.py <arquivo.pkr> [pasta_de_saida]")
        return
    caminho = sys.argv[1]
    nome_pacote, entradas, f = abrir(caminho)
    print("pacote: %s   %d entradas" % (nome_pacote, len(entradas)))

    if len(sys.argv) < 3:                    # só listar
        for e in entradas[:10]:
            f.seek(e["pos"]); ini = f.read(8)
            print("  %-12s %9.2f KB  %s" % (e["nome"], e["tam"] / 1024.0, tipo(ini)))
        print("  ...")
        return

    saida = sys.argv[2]
    os.makedirs(saida, exist_ok=True)
    for e in entradas:
        f.seek(e["pos"]); dados = f.read(e["tam"])
        ext = tipo(dados)
        with io.open(os.path.join(saida, "%s.%s" % (e["nome"], ext)), "wb") as g:
            g.write(dados)
    print("gravados %d arquivos em %s" % (len(entradas), saida))


if __name__ == "__main__":
    main()
