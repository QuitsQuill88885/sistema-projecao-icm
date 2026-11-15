# -*- coding: utf-8 -*-
"""O CONTEÚDO DO INSTALADOR COMPLETO (12/11/2026; regra dele: "baixa um arquivo e naquele arquivo vai ter tudo" e "o
sistema não tem 'se precisar', ele tem o que é preciso"). Lista (origem, destino dentro do pacote) do que vai a mais no
COMPLETO, além do programa normal: SÓ o que o 4.0 usa numa máquina que nunca viu a 3.0.x.
  - cias169/<n>/pronto.json + movimento.json   (os índices das CIAS 16:9; os WebP NÃO: tudo tem .jpg e filme MP4,
                                                 conferido por ferramentas/confere_pacote_completo.py)
  - animacoes/indice.json                        (o índice das CIAS 4:3, da pasta da 3.0.x desta máquina)
  - leve/cias169/*                               (o .jpg de cada slide, os MP4 dos cliques e os <n>__filme.json)
  - leve/cias43/<n>-*  só dos louvores SEM 16:9  (os outros 4:3 ficam de fora: o 16:9 vale no lugar)
  - leve/<apresentação>__*                       (as apresentações que vêm junto: .jpg, .mp4, .filme.json)
NÃO vão: cache_cias169/*.webp (590 MB), cache_cias (os MP4 4:3 antigos, 217 MB), cache_sprites (protótipo desligado),
leve/unico (o arquivo único é a alternativa aos clipes soltos; os soltos já vão).
uso: python empacotar/conteudo_completo.py      (imprime o tamanho; o .spec importa itens())"""
import json, os, re, sys

NAT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C169 = os.path.join(NAT, "cache_cias169")
LEVE = os.path.join(NAT, "leve")
ANIM_IND = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "Sistema Projecao", "animacoes", "indice.json")
APRES = os.path.join(r"C:\Projetos\Sistema\App\ICM Ipero Projecao", "apresentacoes")


def itens():
    out = []
    nums169 = set()
    for n in os.listdir(C169):
        p = os.path.join(C169, n)
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "pronto.json")):
            nums169.add(n)
            for j in ("pronto.json", "movimento.json", "textos.json"):   # textos: a letra da prévia (15/11)
                if os.path.exists(os.path.join(p, j)):
                    out.append((os.path.join(p, j), "cias169/%s/%s" % (n, j)))
    out.append((ANIM_IND, "animacoes/indice.json"))
    for f in os.listdir(os.path.join(LEVE, "cias169")):
        out.append((os.path.join(LEVE, "cias169", f), "leve/cias169/" + f))
    for f in os.listdir(os.path.join(LEVE, "cias43")):
        m = re.match(r"(\d+)-", f)
        if m and m.group(1) not in nums169:
            out.append((os.path.join(LEVE, "cias43", f), "leve/cias43/" + f))
    apres = set(os.listdir(APRES)) if os.path.isdir(APRES) else set()
    for f in os.listdir(LEVE):
        p = os.path.join(LEVE, f)
        if os.path.isfile(p) and any(f.startswith(a + "__") or f.startswith(a + ".") for a in apres):
            out.append((p, "leve/" + f))
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    it = itens()
    por = {}
    for o, d in it:
        k = "/".join(d.split("/")[:2]) if d.startswith("leve/cias") else d.split("/")[0]
        por[k] = por.get(k, 0) + os.path.getsize(o)
    for k, v in sorted(por.items(), key=lambda x: -x[1]):
        print("  %-16s %7.1f MB" % (k, v / 2**20))
    print("TOTAL a mais no completo: %d arquivos, %.1f MB" % (len(it), sum(por.values()) / 2**20))
