# -*- coding: utf-8 -*-
"""As SUGESTÕES DE LOUVOR para o versículo no ar (a faixa "Louvores para este versículo" da aba Bíblia), 07/11/2026.
Cópia linha por linha do app.js da 3.0.13: sugerirPara, montarRoda, pintarSug, maisSugestoes, carregarHistoricoSug,
familiaridade, ident/identTitulo, e a parte calculada (consultaDoVerso, cosTemas, calcularRoda) com o índice temático
(temas.js) e as figuras (tipologia.js). Os dados são os MESMOS arquivos da 3.0.13 (dados/sugestoes.js, temas.js,
tipologia.js), lidos na primeira vez que fazem falta."""
import json, math, os, re
import cerebro

SUG_POR_VEZ = 3        # três é o que cabe sem empurrar a grade de versículos para fora da tela
SUG_TETO = 30          # dez trios: daí para baixo já é louvor que só encosta no assunto
SUG_JANELA = 4         # versículos de cada lado que entram na busca
SUG_HIST_PISO = 8
IDENT_LETRA = 60
# o CHAVES_ANTIGAS do app.js da 3.0.13: a chave velha (1ª linha corrigida) conta no louvor de hoje
CHAVES_ANTIGAS = {
    "AV|QUANDO AO FIM DA JORNADA EU CHEGAR|HAVERÁ LUZ NOS CÉUS DAS MORADAS DE DEUS?":
        "AV|QUANDO AO FIM DA JORNADA EU CHEGAR|HAVERÁ LUZ NOS CÉUS NAS MORADAS DE DEUS?",
}


def _js(nome, var):
    """Um window.X = {...} dos dados da 3.0.13, como valor Python."""
    with open(cerebro.dado(nome), encoding="utf-8") as f:
        t = f.read()
    i = t.index("=", t.index(var)) + 1
    return json.JSONDecoder().raw_decode(t[i:].lstrip())[0]


def ident_titulo(titulo, linha1):
    return cerebro.so_letras(titulo) + "|" + cerebro.so_letras(linha1)[:12]


class Sugestoes:
    def __init__(self, acervo, biblia, ler_historico):
        self.A, self.B, self.ler_hist = acervo, biblia, ler_historico
        self.tab = None            # SUGESTOES
        self.temas = None          # TEMAS
        self.tip = None            # TIPOLOGIA
        self._norma = None
        self.vezes = self.vezes_letra = None; self.vezes_max = 0
        self._ident = {}
        self.cand, self.roda, self.pag, self.vers, self.cheia = [], [], 0, None, False

    # ---- as duas chaves do louvor (cópias de coletânea e rebatizados contam como um só)
    def ident(self, i):
        s = self.A.louvores[i]
        d = self._ident.get(id(s))
        if d is None:
            sl = (s.get("slides") or [{}])[0]
            d = (ident_titulo(s.get("titulo") or "", (sl.get("linhas") or [""])[0] if sl.get("linhas") else ""),
                 cerebro.so_letras(" ".join(" ".join(x.get("linhas") or []) for x in s.get("slides") or []))[:IDENT_LETRA])
            self._ident[id(s)] = d
        return d

    def cod(self, livro, cap, v):
        try:
            return "%d.%d.%d" % (self.B.ordem.index(livro), cap, v)
        except ValueError:
            return None

    # ---- o peso do que a igreja já cantou (uma vez por sessão)
    def _historico(self):
        if self.vezes is not None:
            return
        por_tit, por_let, por_chave, mx = {}, {}, {}, 0
        for i, s in enumerate(self.A.louvores):
            por_chave[cerebro.chave(s)] = i                     # o Map.set: o último vence
        def conta(m, k):
            nonlocal mx
            if not k: return
            m[k] = m.get(k, 0) + 1
            if m[k] > mx: mx = m[k]
        try:
            regs = self.ler_hist() or []
        except Exception:
            regs = []
        for x in regs:
            if x.get("q") != "louvor" or not x.get("chave"):
                continue
            ch = CHAVES_ANTIGAS.get(str(x["chave"]), str(x["chave"]))
            p = ch.split("|")
            conta(por_tit, ident_titulo(p[1] if len(p) > 1 else "", "|".join(p[2:])))
            i = por_chave.get(ch)
            if i is not None:
                conta(por_let, self.ident(i)[1])
        self.vezes, self.vezes_letra, self.vezes_max = por_tit, por_let, mx

    def familiaridade(self, i):
        if self.vezes is None:
            return 0
        d = self.ident(i)
        n = max(self.vezes.get(d[0], 0), self.vezes_letra.get(d[1], 0))
        return math.log(1 + n) / math.log(1 + max(self.vezes_max, SUG_HIST_PISO)) if n else 0

    # ---- a roda
    def montar_roda(self, refazer=False):
        presos = [] if refazer else self.roda[:(self.pag + 1) * SUG_POR_VEZ]
        fixo, roda = set(presos), list(presos)
        v_tit, v_let = set(), set()
        def anotar(i):
            d = self.ident(i); v_tit.add(d[0]); v_let.add(d[1])
        def ja_veio(i):
            d = self.ident(i); return d[0] in v_tit or d[1] in v_let
        for i in presos: anotar(i)
        n = len(self.A.louvores)
        cs = [{"i": c["i"], "p": c["prox"] * (1 + 0.4 * self.familiaridade(c["i"]))}
              for c in self.cand if c["i"] not in fixo and 0 <= c["i"] < n]
        cs.sort(key=lambda c: -c["p"])                         # o sort do JS é estável: empate fica na ordem
        for c in cs:
            if ja_veio(c["i"]) or len(roda) >= SUG_TETO:
                continue
            anotar(c["i"]); roda.append(c["i"])
        if len(roda) > SUG_POR_VEZ:
            del roda[len(roda) - len(roda) % SUG_POR_VEZ:]
        self.roda = roda

    def sugerir(self, livro, cap, v):
        """O sugerirPara: monta a roda do versículo. Devolve False quando a tabela não tem nada para ele (a faixa some)."""
        if self.tab is None:
            self.tab = _js("sugestoes.js", "SUGESTOES")
        base = self.tab.get(self.cod(livro, cap, v) or "", [])
        if not base:
            self.vers, self.roda, self.cand = None, [], []
            return False
        self.vers, self.pag, self.cheia, self.roda = (livro, cap, v), 0, False, []
        self._historico()
        alto = max(a[1] for a in base) or 1
        self.cand = [{"i": a[0], "prox": 0.7 + 0.3 * (a[1] / alto)} for a in base]
        for k in range(v - SUG_JANELA, v + SUG_JANELA + 1):
            if k == v or k < 1:
                continue
            for a in self.tab.get(self.cod(livro, cap, k) or "", []):
                self.cand.append({"i": a[0], "prox": 0.5 + 0.15 * min(1, a[1] / alto)})
        self.montar_roda()
        return True

    def trio(self):
        """O pintarSug: o trio à mostra (a roda dá a volta) e se o "ver mais" aparece."""
        n = len(self.roda)
        paginas = max(1, -(-n // SUG_POR_VEZ))
        self.pag = ((self.pag % paginas) + paginas) % paginas
        return self.roda[self.pag * SUG_POR_VEZ:self.pag * SUG_POR_VEZ + SUG_POR_VEZ], (n > SUG_POR_VEZ or not self.cheia)

    def mais(self):
        """O maisSugestoes: gira; na 1ª vez que falta, a parte calculada (o índice temático) engorda a roda."""
        if not self.vers:
            return
        self.pag += 1
        if self.cheia or len(self.roda) > SUG_POR_VEZ:
            self.trio()                                        # o pintarSug de antes do cálculo (ele acerta a página)
        if self.cheia:
            return
        self.calcular_roda()

    # ---- a parte calculada
    def _temas(self):
        if self.temas is None:
            self.temas = _js("temas.js", "TEMAS")
            try:
                self.tip = _js("tipologia.js", "TIPOLOGIA")
            except Exception:
                self.tip = None
        return self.temas

    def normas(self):
        if self._norma is None:
            self._norma = [math.sqrt(sum(w * w for w in p.values())) or 1 for p in self._temas()["louvores"]]
        return self._norma

    @staticmethod
    def norma_cons(q):
        return math.sqrt(sum(w * w for w in q.values())) or 1

    def cos_temas(self, i, q, nq):
        p = self.temas["louvores"][i]; s = 0
        for k, w in p.items():
            if q.get(k): s += w * q[k]
        return s / (self.normas()[i] * nq)

    def consulta(self, livro, cap, v):
        T = self._temas()
        caps = self.B.livros.get(livro) or []
        cs = caps[cap - 1] if 0 < cap <= len(caps) else {}
        q, trecho = {}, set()
        def por(txt, w):
            for p in cerebro.so_letras(txt).split(" "):
                if len(p) < 3: continue
                trecho.add(p)
                g = T["idf"].get(p)
                if g: q[p] = max(q.get(p, 0), w * g)
        por(cs.get(str(v)) or "", 1)
        for k in range(v - SUG_JANELA, v + SUG_JANELA + 1):
            if k != v and cs.get(str(k)): por(cs[str(k)], 0.45)
        for fam in T["familias"].values():                     # a ponte dos temas: duas palavras da família
            if sum(1 for p in fam if p in trecho) < 2: continue
            for p in fam:
                g = T["idf"].get(p)
                if g: q[p] = max(q.get(p, 0), 0.55 * g)
        for f in self.tip or []:                               # a ponte das figuras: um gatilho basta
            if not any(p in trecho for p in f["g"]): continue
            for p in f["t"]:
                g = T["idf"].get(p)
                if g: q[p] = max(q.get(p, 0), f["p"] * g)
        return q

    def calcular_roda(self):
        self.cheia = True
        T = self._temas()
        q = self.consulta(*self.vers); nq = self.norma_cons(q)
        qb, ja = {}, set()
        for c in self.cand:
            ja.add(c["i"])
            if c["i"] >= len(T["louvores"]): continue
            p = T["louvores"][c["i"]]
            if not p: continue
            n = self.normas()[c["i"]]
            for k, w in p.items(): qb[k] = qb.get(k, 0) + w / n
        nqb = self.norma_cons(qb); pts = []
        nl = len(self.A.louvores)
        for i in range(len(T["louvores"])):
            if i in ja or i >= nl: continue
            s = 0.6 * self.cos_temas(i, q, nq) + 0.4 * self.cos_temas(i, qb, nqb)
            if s > 0: pts.append((i, s))
        pts.sort(key=lambda a: -a[1])
        if not pts:
            self.montar_roda(); return
        alto = pts[0][1]
        self.cand = self.cand + [{"i": i, "prox": 0.45 * (s / alto)} for i, s in [a for a in pts if a[1] >= alto * 0.2][:SUG_TETO * 8]]
        self.montar_roda()
