# -*- coding: utf-8 -*-
"""O CÉREBRO do Sistema Nativo (03/11/2026): o acervo e as regras das telas, sem tela nenhuma.

Lê os MESMOS arquivos de dados da 3.0.12 (dados/louvores.js, repeticoes.js, repetidos.js, fundos.js e o índice das
animações das CIAS) e monta cada tela do telão igual ao app.js monta (stLouvor, numerosLouvor, daVez, daAnimacao).
O painel, o telão e o celular só leem daqui e mandam ordens para cá.
"""
import functools, json, os, re, time, unicodedata

# os dados: DENTRO do pacote quando é o .exe (tudo dentro, nada instalado); na máquina de trabalho, a pasta do App
import sys as _sys
if getattr(_sys, "frozen", False):
    APP = _sys._MEIPASS
else:
    APP = os.environ.get("SISTEMA_APP", r"C:\Projetos\Sistema\App\ICM Ipero Projecao")
# 08/11 (teste dele no Vaio: "os louvores das crianças só têm a letra"): no Linux não há APPDATA e isto virava o caminho
# RELATIVO "Sistema Projecao/animacoes" (0 telas das CIAS achadas). A 3.0.12 do Linux guarda em ~/Sistema Projecao,
# a mesma regra do DADOS_USUARIO lá embaixo.
ANIM = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "Sistema Projecao", "animacoes")
# os vídeos das CIAS ficam com as animações, na pasta do usuário (conteúdo, não programa); na máquina de trabalho, aqui
CACHE_CIAS = os.environ.get("NATIVO_CIAS") or os.path.join(ANIM, "video") if getattr(_sys, "frozen", False) else os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_cias")
# 08/11/2026 (auditoria): no programa instalado a pasta acima NÃO existia (0 vídeos no PC de casa: as CIAS caíam na imagem
# parada). Os vídeos vão DENTRO do pacote (_internal/video); a pasta do usuário fica só de reserva.
if getattr(_sys, "frozen", False) and not os.environ.get("NATIVO_CIAS") and os.path.isdir(os.path.join(_sys._MEIPASS, "video")):
    CACHE_CIAS = os.path.join(_sys._MEIPASS, "video")
# AS CIAS EM 16:9, DA FONTE (08/11/2026, ordem dele: "volta na FONTE"): cada louvor das CIAS que tem a versão 16:9 no
# PowerPoint oficial ("CIAS COM ANIMAÇÃO 16.9 - 2025.pptx") vira <pasta>/<número>/ (ferramentas/pptx/cias169.py): o slide
# inteiro + o movimento (fundo, camadas e a linha do tempo do PowerPoint). Quando existe, vale no lugar do WebP 4:3; os
# que não têm 16:9 seguem no 4:3, sem esticar. Conteúdo, não programa: na pasta do usuário, ao lado das animações.
CIAS169 = os.environ.get("NATIVO_CIAS169") or (os.path.join(os.path.dirname(ANIM), "cias169") if getattr(_sys, "frozen", False)
                                                 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_cias169"))
# 12/11/2026 (regra dele: "baixa um arquivo e naquele arquivo vai ter tudo"; máquina que nunca viu a 3.0.x): o INSTALADOR
# COMPLETO leva dentro do programa os índices das CIAS 16:9 (_internal/cias169/<n>/pronto.json + movimento.json, sem WebP)
# e o índice das 4:3 (_internal/animacoes/indice.json); as imagens e os vídeos vão em _internal/leve. Sem a pasta do
# usuário (a 3.0.x nunca instalada), vale a de dentro.
_DENTRO = getattr(_sys, "_MEIPASS", None)
if _DENTRO and not os.environ.get("NATIVO_CIAS169") and not os.path.isdir(CIAS169) and os.path.isdir(os.path.join(_DENTRO, "cias169")):
    CIAS169 = os.path.join(_DENTRO, "cias169")
INDICE_ANIM = [os.path.join(ANIM, "indice.json")] + ([os.path.join(_DENTRO, "animacoes", "indice.json")] if _DENTRO else [])

# 10/11 (o pacote sem WebP): o slide 16:9 "existe" se o arquivo existe OU se a versão leve dele existe (.jpg/.mp4 na
# pasta leve). O sistema_nativo põe aqui quem sabe achar o leve; sem ele, só o arquivo.
TEM_SLIDE = os.path.exists

TAM_LOUVOR = 5.75          # % da altura do telão (calibrado na transmissão oficial, projecao.html #lou-txt)
TAM_BIBLIA = 5.55
ESMAECER = 700             # ms, o fade do PowerPoint oficial (app.js ESMAECER)
ORDEM_NUM = {"Coletânea Antiga": 1, "Avulsos 2018": 2}
# os nomes das coletâneas como o painel da 3.0.12 escreve (app.js NOME_COL / ORDEM_COL / rotuloLouvor)
NOME_COL = {"Coletânea 2018": "COLETÂNEA 2018", "CIA 2018": "CIAS", "Coletânea Antiga": "COLETÂNEA ANTIGA",
            "Avulsos 2018": "AV", "Avulsos 2024": "AV 2024", "Avulsos 2026": "AV 2026", "Meus louvores": "MEUS LOUVORES"}
ORDEM_COL = ["Coletânea 2018", "CIA 2018", "Coletânea Antiga", "Avulsos 2018", "Avulsos 2024", "Avulsos 2026", "Meus louvores"]
CURTO_COL = {"COLETÂNEA 2018": "COLETÂNEA", "COLETÂNEA ANTIGA": "ANTIGA", "AV": "AV", "AV 2024": "AV 24", "AV 2026": "AV 26",
             "MEUS LOUVORES": "MEU", "CIAS": "CIAS"}
SIGLA_COL = {"Coletânea 2018": "COLETÂNEA", "CIA 2018": "CIAS", "Coletânea Antiga": "ANTIGA", "Avulsos 2018": "AV",
             "Avulsos 2024": "AV 24", "Avulsos 2026": "AV 26", "Meus louvores": "MEU"}


def dado(nome):
    """O arquivo de dados (louvores, selos do livro, cifras escondidas...). 08/11 (teste dele no Vaio: "cadê a conferência
    absoluta"): no Linux o Nativo lia a pasta da 3.0.12 (letras de 24/10, antes da conferência de 03/11). O pacote do
    Linux agora traz os da 3.0.13 em <programa>/dados: esses vencem; o que não vier no pacote, da pasta de sempre."""
    meu = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados", nome)
    return meu if not getattr(_sys, "frozen", False) and os.path.exists(meu) else os.path.join(APP, "dados", nome)


def _js(nome, var=None):
    t = open(dado(nome), encoding="utf-8").read()
    if var:
        i = t.index("window.%s" % var)
        t = t[i:]
    t = t[t.index("=") + 1:].strip()
    dec = json.JSONDecoder()
    obj, _ = dec.raw_decode(t)
    return obj


_MARCAS = re.compile(r"[̀-ͯ]")     # o bloco dos acentos combinantes (todos são categoria Mn)
_NAO_ASCII = re.compile(r"[^\x00-\x7f]")


def sem_acento(t):
    # 08/11/2026: o mesmo resultado, ~10x mais rápido (no Vaio, os textos da busca levavam 5,5 s e atrasavam a subida).
    # Texto só ASCII não tem acento; tirados os acentos do bloco comum, só o que ainda não é ASCII passa letra a letra.
    t = t or ""
    if t.isascii():
        return t.lower()
    n = _MARCAS.sub("", unicodedata.normalize("NFD", t))
    if n.isascii():
        return n.lower()
    # sobrou letra fora do ASCII ("º", "–", "’"...): só ELAS passam pela categoria (as ASCII nunca são marca)
    return _NAO_ASCII.sub(lambda m: "" if unicodedata.category(m.group()) == "Mn" else m.group(), n).lower()


def so_letras(t):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", sem_acento(t))).strip()


def chave(s):
    sl = s["slides"][0]["linhas"][0] if s.get("slides") and s["slides"][0].get("linhas") else ""
    return "%s|%s|%s" % (s.get("num") or "", s["titulo"], sl)


def num_louvor(s):
    n = s.get("num") or ""
    return "" if n in ("", "AV", "MEU") else n


def parse_letra(txt):
    """O parseLetra da 3.0.13: slides separados por linha em branco; CORO / FINAL / BIS sozinho na linha vira o rótulo
    (o primeiro do bloco); o resto em MAIÚSCULAS. Devolve [{label, linhas}] (blocos vazios saem)."""
    out = []
    for bloco in re.split(r"\n\s*\n", txt):
        label, linhas = "", []
        for l in (x.strip() for x in bloco.split("\n")):
            if not l:
                continue
            m = re.match(r"^(CORO|FINAL|BIS)\s*:?\s*$", l, re.I)
            if m and not label:
                label = m.group(1).upper()
            else:
                linhas.append(l.upper())
        if linhas:
            out.append({"label": label, "linhas": linhas})
    return out


# ---- a BUSCA da 3.0.13 (pontuarLouvor + som/perto/somDaFrase do app.js), linha por linha, 07/11/2026 ---------------
@functools.lru_cache(maxsize=65536)           # a mesma palavra aparece em centenas de louvores: calcula uma vez só
def som(p):
    """Reduz a palavra ao SOM ("resplandesse" e "resplandece", "querro" e "quero" viram o mesmo)."""
    p = unicodedata.normalize("NFD", p or "").lower()
    p = p.replace("c\u0327", "s")                       # cedilha ANTES do c -> k
    p = re.sub(r"[\u0300-\u036f]", "", p)
    p = re.sub(r"[^a-z]", "", p)
    if not p:
        return ""
    p = p.replace("lh", "L").replace("nh", "N").replace("ch", "X")
    p = p.replace("xc", "s").replace("sc", "s")
    p = re.sub(r"c([ei])", r"s\1", p).replace("c", "k").replace("q", "k").replace("ku", "k")
    p = p.replace("ph", "f")
    p = re.sub(r"([aeiou])s([aeiou])", r"\1z\2", p).replace("z", "s")
    p = re.sub(r"r{2,}", "r", p)
    p = re.sub(r"l{2,}", "l", p).replace("h", "")
    p = re.sub(r"[mn]$", "n", p).replace("y", "i")
    return re.sub(r"(.)\1+", r"\1", p)


def perto(a, b, teto=2):
    """Distância de edição com corte: a e b estão a no máximo `teto` trocas?"""
    teto = teto or 2
    if abs(len(a) - len(b)) > teto:
        return False
    ant = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i]; melhor = i
        for j in range(1, len(b) + 1):
            v = min(ant[j] + 1, cur[j - 1] + 1, ant[j - 1] + (1 if a[i - 1] != b[j - 1] else 0))
            cur.append(v)
            if v < melhor: melhor = v
        if melhor > teto:
            return False
        ant = cur
    return ant[len(b)] <= teto


def som_da_frase(t):
    """O som sai do texto ORIGINAL (o cedilha importa): as palavras e o som de cada uma."""
    return [som(w) for w in re.split(r"[^A-Za-zÀ-ÿ]+", t or "") if w]


def pontuar_louvor(tit, letra, sons, alvo, palavras, alvo_som):
    """QUÃO PERTO o louvor está do que foi digitado (o pontuarLouvor da 3.0.13): título igual, título que começa,
    que contém, com todas as palavras soltas; depois a LETRA; e, se nada bateu escrito certo, pelo SOM."""
    if tit == alvo: return 1000
    if tit.startswith(alvo): return 900 - min(len(tit), 99)
    if alvo in tit: return 800 - min(tit.index(alvo), 99)
    if len(palavras) > 1 and all(p in tit for p in palavras):
        return 600 - min(tit.index(palavras[0]), 99)
    if alvo in letra: return 300
    if len(palavras) > 1 and all(p in letra for p in palavras): return 200
    if alvo_som and sons:
        casadas = [a for a in alvo_som if any(b == a or perto(a, b, 2 if len(a) > 5 else 1) for b in sons)]
        if len(casadas) == len(alvo_som): return 150 - min(len(sons), 40)
        if casadas and len(alvo_som) > 1: return 80
    return 0


# INSTRUÇÃO de quem canta escrita como linha da letra ("(1ª ESTROFE 2X NO COMEÇO)" no 15 AV 24, que foi ao telão na EBD
# de 15/11): não se projeta. Só a linha INTEIRA entre parênteses que fala de estrofe/começo/repetir; as linhas cantadas
# entre parênteses ("(SIM, ELE VOLTARÁ)", 561 no acervo) ficam. O dado não muda (a 1ª linha é a chave da cifra).
RE_INSTRUCAO = re.compile(r"^\(.*\b(ESTROFE|NO COME[CÇ]O|REPETI\w*|REPITA)\b.*\)$", re.I)


def visiveis(linhas):
    """As linhas de uma tela que vão para o telão e para a prévia (sem a instrução de quem canta; nunca vazia)."""
    ls = [l for l in linhas if not RE_INSTRUCAO.match(l.replace("\x01", "").strip())]
    return ls or list(linhas)


class Acervo:
    def __init__(self, adiar=False):
        # adiar=True (o programa, 08/11/2026): os textos da busca só começam em preparar_busca(), com o painel já de pé.
        # No Vaio (E-450, 2 núcleos) a linha de fundo disputava o Python com a subida da tela
        self._adiar = adiar
        L = _js("louvores.js")
        self.louvores = L.get("louvores", L) if isinstance(L, dict) else L
        self.selos = _js("repeticoes.js", "REPETICOES")
        self.repetidos = _js("repetidos.js", "REPETIDOS")
        self.estilos = _js("fundos.js", "ESTILOS")
        try:                                   # o galeria.js substitui a GALERIA do fundos.js (index.html carrega depois)
            self.galeria = _js("galeria.js", "GALERIA")
        except Exception:
            self.galeria = _js("fundos.js", "GALERIA")
        self.config = Config()
        self.anim = {}
        for ind in INDICE_ANIM:                    # a pasta do usuário; sem ela, o índice de dentro do programa (12/11)
            try:
                self.anim = json.load(open(ind, encoding="utf-8")); break
            except Exception:
                pass
        self.base_n = len(self.louvores)           # os da base; os do operador vêm depois (os índices da base não mudam)
        self.louvores = self.louvores + self.meus()
        self._indices()

    def meus(self):
        """Os louvores que o operador adicionou (icm_meus_louvores, a mesma chave da 3.0.13)."""
        m = self.config.ler("icm_meus_louvores") or []
        return [s for s in m if isinstance(s, dict) and s.get("titulo") and s.get("slides")]

    def recarregar_meus(self):
        """O recarregarLouvores da 3.0.13: a base e, no fim, os do operador; refaz os índices."""
        self.louvores = self.louvores[:self.base_n] + self.meus()
        self._indices()

    def _montar_pont(self):
        lv = self.louvores
        pont = [(so_letras(s["titulo"]), so_letras(" ".join(" ".join(x.get("linhas") or []) for x in s.get("slides") or [])),
                 som_da_frase(s["titulo"])) for s in lv]
        if lv is self.louvores:                     # o acervo não mudou no meio
            self._pont = pont

    def preparar_busca(self):
        """Monta os textos da busca numa linha de fundo (uma vez; a busca que chegar antes monta na hora)."""
        self._adiar = False
        if self._pont is None:
            import threading as _th
            _th.Thread(target=self._montar_pont, name="busca-textos", daemon=True).start()

    def _indices(self):
        self._pont = None                           # os textos da busca por palavras: montados numa linha de fundo
        if not self._adiar:                         # (~180 ms no PC de casa, ~1,3-2,5 s no Vaio: a 1ª busca não espera)
            self.preparar_busca()
        self.chaves = [chave(s) for s in self.louvores]
        por_chave = {k: i for i, k in enumerate(self.chaves)}
        self.principal_de, self.irmas = {}, {}
        for k, alvo in self.repetidos.items():
            i, p = por_chave.get(k), por_chave.get(alvo)
            if i is None or p is None or i == p:
                continue
            self.principal_de[i] = p
            self.irmas.setdefault(p, []).append(i)
        self._nums = {}
        self._busca = [(so_letras(s["titulo"] + " " + " ".join(s["slides"][0]["linhas"] if s.get("slides") else [])),
                        num_louvor(s)) for s in self.louvores]

    # ---- quem é quem
    def da_vez(self, i):
        return self.principal_de.get(i, i)

    def numeros(self, i):
        if i in self._nums:
            return self._nums[i]
        s = self.louvores[i]
        p = self.da_vez(i)
        grupo = [self.louvores[j] for j in [p] + self.irmas.get(p, [])]
        if len(grupo) < 2:
            r = num_louvor(s)
        else:
            grupo.sort(key=lambda o: ORDEM_NUM.get(o.get("col"), 0))
            nums = [("AV" if o.get("num") == "AV" else num_louvor(o)) for o in grupo]
            vist, r = [], []
            for x in nums:
                if x and x not in vist:
                    vist.append(x); r.append(x)
            r = " ".join(r)          # espaço EME, como o numerosLouvor da 3.0.13 ("69 563": o espaço largo)
        self._nums[i] = r
        return r

    def animacao(self, i):
        """As telas prontas das CIAS deste louvor (lista de arquivos WebP), ou None. Igual ao daAnimacao do app.js."""
        s = self.louvores[i]
        if s.get("col") == "CIA 2018":
            try:
                a = self.anim.get(str(int(s["num"])))
                if a:
                    return a
            except (TypeError, ValueError):
                pass
        a = self.anim.get("chave:" + self.chaves[i])
        if a:
            return a
        for j in self.irmas.get(i, []) + ([self.principal_de[i]] if i in self.principal_de else []):
            b = self.anim.get("chave:" + self.chaves[j])
            if b:
                return b
        return None

    def cias169(self, i):
        """As telas 16:9 da FONTE deste louvor (cias169.py), ou None: [{"src": SlideNNNN.webp, "mov": movimento|None}].
        Pelo número da CIA 2018 dele ou de uma irmã (o mesmo louvor noutra coletânea, como o 69)."""
        cache = self.__dict__.setdefault("_c169", {})
        for j in [i] + self.irmas.get(i, []) + ([self.principal_de[i]] if i in self.principal_de else []):
            s = self.louvores[j]
            if s.get("col") != "CIA 2018":
                continue
            try: num = int(s["num"])
            except (TypeError, ValueError): continue
            if num not in cache:
                cache[num] = self._le_c169(num)
            if cache[num]:
                return cache[num]
        return None

    @staticmethod
    def _le_c169(num):
        pasta = os.path.join(CIAS169, str(num))
        try:
            pr = json.load(open(os.path.join(pasta, "pronto.json"), encoding="utf-8"))
            mov = json.load(open(os.path.join(pasta, "movimento.json"), encoding="utf-8")).get("slides", {})
        except Exception:
            return None
        arq = lambda r: os.path.join(pasta, *r.split("/"))
        try:                                     # a letra de cada tela (textos_cias169.py, 15/11): a prévia escrita
            tx = json.load(open(os.path.join(pasta, "textos.json"), encoding="utf-8"))
        except Exception:
            tx = {}
        telas = []
        for n in pr.get("slides", []):
            src = os.path.join(pasta, "Slide%04d.webp" % n)
            if not TEM_SLIDE(src):
                return None                      # louvor pela metade: fica no 4:3 (nunca uma tela faltando)
            m = mov.get(str(n))
            if m:
                m = dict(m, base=arq(m["base"]), camadas=[dict(c, src=arq(c["src"])) for c in m.get("camadas", [])])
            telas.append({"src": src, "mov": m, "linhas": tx.get(str(n)) or []})
        return telas or None

    def tem_telas_cias(self, i):
        """O modo tela de criança existe para este louvor (16:9 da fonte ou o WebP 4:3)."""
        return bool(self.cias169(i) or self.animacao(i))

    def arquivo_cias(self, nome):
        """O que o telão toca para uma tela das CIAS: o vídeo (se a tela é animada e já foi convertida) ou a imagem."""
        mp4 = os.path.join(CACHE_CIAS, os.path.splitext(nome)[0] + ".mp4")
        if os.path.exists(mp4):
            return "video", mp4
        return "imagem", os.path.join(ANIM, nome)

    def fundo(self, estilo, qual):
        e = self.estilos.get(estilo) or self.estilos["limpo"]
        rel = e.get(qual) or (e.get("louvor1") if qual == "louvor2" else e.get("descanso"))
        return os.path.join(APP, rel.replace("/", os.sep))

    # ---- a tela do telão (o stLouvor do app.js)
    def telas_do_louvor(self, i, com_animacao=True):
        a = (self.cias169(i) or self.animacao(i)) if com_animacao else None
        return len(a) if a else len(self.louvores[i]["slides"])

    def tela_louvor(self, i, slide, estilo="limpo", escala=1.0, com_animacao=True):
        i = self.da_vez(i)
        s = self.louvores[i]
        c = self.cias169(i) if com_animacao else None
        if c:
            # a tela 16:9 da FONTE: o slide do PowerPoint com o movimento dele (o Palco toca como a apresentação)
            k = max(0, min(slide, len(c) - 1))
            return {"modo": "apres", "src": c[k]["src"], "mov": c[k]["mov"], "passo": 0, "animada": False,
                    "cias169": True, "slide": k, "de": len(c), "fade": ESMAECER}
        a = self.animacao(i) if com_animacao else None
        if a:
            k = max(0, min(slide, len(a) - 1))
            tipo, arq = self.arquivo_cias(a[k])
            return {"modo": "slide", "tipo": tipo, "arquivo": arq, "webp": os.path.join(ANIM, a[k]),
                    "slide": k, "de": len(a), "fade": ESMAECER}
        k = max(0, min(slide, len(s["slides"]) - 1))
        sl, prim = s["slides"][k], k == 0
        nums = self.numeros(i)
        av = "AV" if s.get("num") == "AV" else ""
        partes = (nums or av).split()
        return {
            "modo": "louvor", "slide": k, "de": len(s["slides"]),
            "fundo": self.fundo(estilo, "louvor1" if prim else "louvor2"), "estilo": estilo,
            "titulo": (((nums or av) and (nums or "AV") + " - ") or "") + s["titulo"] if prim else "",
            "num1": partes[0] if prim and partes else "",
            "num2": (nums.split() + ["", ""])[1] if prim and nums else "",
            "tituloSo": s["titulo"] if prim else "",
            "selo": (self.selos.get(self.chaves[i]) or {}).get(str(k), ""),
            "label": sl.get("label") or "", "linhas": visiveis(sl.get("linhas") or []),
            "tam": TAM_LOUVOR, "escala": escala,
            "linhasRef": max(len(x.get("linhas") or []) + (1 if x.get("label") else 0) for x in s["slides"]),
            "fim": k == len(s["slides"]) - 1, "fade": ESMAECER,
        }

    # ---- a TELA DE ESPERA e a GALERIA de fundos (o esperaAtual e o listaFundos do app.js, na mesma ordem:
    # o celular manda o NÚMERO da lista, então a ordem tem de ser idêntica à da 3.0.12)
    def espera_atual(self, estilo="limpo"):
        e = self.config.espera()
        if e:
            return self.caminho_fundo(e)
        return self.caminho_fundo(ESPERA_ICM) if estilo == "limpo" else self.fundo(estilo, "descanso")

    def tela_descanso(self, estilo="limpo"):
        return {"modo": "fundo", "fundo": self.espera_atual(estilo), "fade": ESMAECER}

    def caminho_fundo(self, arq):
        """'fundos/x.jpg' (de fábrica) ou o arquivo de um fundo do usuário -> caminho no disco."""
        if os.path.isabs(arq):
            return arq
        # 22/11 (a galeria nova com os fundos da igreja): no Linux o pacote traz <programa>/fundos/galeria; esse vence a pasta
        # da 3.0.12, como o dado() faz com os dados. No pacote do Windows (frozen) o APP já é o de dentro.
        meu = os.path.join(os.path.dirname(os.path.abspath(__file__)), arq.replace("/", os.sep))
        if not getattr(_sys, "frozen", False) and os.path.isfile(meu):
            return meu
        return os.path.join(APP, arq.replace("/", os.sep))

    def lista_fundos(self, estilo="limpo"):
        e = self.estilos.get(estilo) or self.estilos["limpo"]
        oracao = e.get("oracao") or e.get("descanso")
        plano = e.get("louvor2") or e.get("descanso")
        base = [{"arquivo": ESPERA_ICM, "nome": "Espera", "cat": "Cultos"},
                {"arquivo": oracao, "nome": "Silêncio e Oração", "cat": "Oração"},
                {"arquivo": plano, "nome": "Fundo liso", "cat": "Base", "liso": True}]
        meus = [dict({"cat": "Meus fundos", "liso": True}, **f) for f in self.config.meus_fundos()]
        ocultos = set(self.config.ocultos())
        return [f for f in base + self.galeria + meus if f.get("arquivo") not in ocultos]


    def fundos_lisos(self, estilo="limpo"):
        """Os fundos do card Texto (fundosLisos do app.js): o liso e o da Bíblia do estilo, os da galeria marcados como
        lisos e os do operador, menos os escondidos. Cada um com a ZONA do texto (zonaDoFundo)."""
        e = self.estilos.get(estilo) or self.estilos["limpo"]
        plano = e.get("louvor2") or e.get("descanso")
        base = [{"arquivo": plano, "nome": "Fundo liso", "zona": "livre"},
                {"arquivo": e.get("biblia"), "nome": "Fundo Bíblia", "zona": "barra"}]
        meus = [dict(f) for f in self.config.meus_fundos()]
        ocultos = set(self.config.ocultos())
        out = []
        for f in base + [g for g in self.galeria if g.get("liso")] + meus:
            if f.get("arquivo") in ocultos or not f.get("arquivo"):
                continue
            if not f.get("zona"):
                f = dict(f, zona="barra" if re.search(r"biblia|avisos|barra|louvor|primeiro", f["arquivo"], re.I) else "livre")
            out.append(f)
        return out

    # ---- busca (simples por enquanto: número exato, ou todas as palavras no título + 1a linha)
    def buscar(self, texto, limite=200):
        f = so_letras(texto)
        out = []
        if not f:
            return out
        if f.isdigit():
            n = str(int(f))
            out = [i for i, (_, num) in enumerate(self._busca)
                   if num and num.lstrip("0") == n and i not in self.principal_de]
            return out[:limite]
        pal = f.split()
        for i, (txt, _) in enumerate(self._busca):
            if i in self.principal_de:
                continue
            if all(p in txt for p in pal):
                out.append(i)
                if len(out) >= limite:
                    break
        return out

    def rotulo(self, i):
        s = self.louvores[i]
        n = self.numeros(i) or ("AV" if s.get("num") == "AV" else "")
        return ("%s - %s" % (n, s["titulo"])) if n else s["titulo"]

    def nome_col(self, i):
        c = self.louvores[i].get("col")
        return NOME_COL.get(c) or str(c or "").upper()

    def rotulo312(self, i):
        """Como a 3.0.12 escreve o louvor fora da lista de busca (rotuloLouvor): '69 563 COLETÂNEA · TÍTULO'."""
        s = self.louvores[i]
        c = self.nome_col(i)
        ns = self.numeros(i)
        return ("%s " % ns if ns else "") + CURTO_COL.get(c, c) + " · " + s["titulo"]

    def lista312(self, texto):
        """A lista da esquerda da aba Louvor (renderListaLouvores): vazio = todos; número = os daquele número (a cópia
        mostra a principal), agrupados por coletânea; palavras = por relevância, sem grupo e com a sigla."""
        f = so_letras(texto)
        import functools
        def num_int(i):
            n = num_louvor(self.louvores[i])
            return int(n) if n.isdigit() else None
        def comparar(a, b):
            # o comparador do achados.sort do app.js, igual: coletânea, depois número; sem número dos dois, a ordem de
            # chegada. (Não é transitivo quando um não tem número: por isso a MESMA ordem de entrada e o mesmo TimSort
            # do V8 dão o mesmo resultado; o "CC AV" da Coletânea 2018 aparece em 1º, como lá.)
            ca, cb = self.louvores[a].get("col"), self.louvores[b].get("col")
            d = (ORDEM_COL.index(ca) if ca in ORDEM_COL else -1) - (ORDEM_COL.index(cb) if cb in ORDEM_COL else -1)
            if d:
                return d
            na, nb = num_int(a), num_int(b)
            if na is not None and nb is not None:
                return na - nb
            return a - b
        chave = functools.cmp_to_key(comparar)
        if f in ("cias", "cia", "cias 2018", "cia 2018", "criancas"):
            # 22/11 (ele na igreja: "quando alguém procurar por 'cias' (...) deve exibir os louvores de cias do primeiro ao
            # último e os avulsos"): toda a coleção CIA, os numerados em ordem e depois os avulsos das CIAS (num "AV").
            cias = [i for i in range(len(self.louvores)) if self.louvores[i].get("col") == "CIA 2018" and i not in self.principal_de]
            achados = sorted(cias, key=lambda i: (num_int(i) is None, num_int(i) or 0, i))
            out = []
            for i in achados:
                s = self.louvores[i]
                out.append({"i": i, "nums": self.numeros(i) or "—", "tit": s["titulo"], "cias": True,
                            "grp": "CIAS" if num_int(i) is not None else "AVULSOS DAS CIAS", "sigla": ""})
            return out
        if not f:
            achados = sorted((i for i in range(len(self.louvores)) if i not in self.principal_de), key=chave)
            agrupar = True
        elif f.isdigit():
            n, vistos, achados = int(f), set(), []
            for i in range(len(self.louvores)):         # a mesma ordem de chegada do forEach do app.js
                p = self.principal_de.get(i)
                if p is not None:
                    if num_int(i) == n and p not in vistos:
                        vistos.add(p); achados.append(p)
                    continue
                if i in vistos:
                    continue
                if num_int(i) == n:
                    vistos.add(i); achados.append(i)
            achados.sort(key=chave)
            agrupar = True
        else:
            # PALAVRAS: o pontuarLouvor da 3.0.13 em todos (a repetida não aparece: quem aparece é a principal) e a ordem
            # por proximidade; empate = a mesma ordem da lista inteira (coletânea, número, chegada)
            if self._pont is None:
                self._montar_pont()
            alvo, alvo_som = f, som_da_frase(texto)
            palavras = alvo.split()
            pts = {}
            for i in range(len(self.louvores)):
                if i in self.principal_de:
                    continue
                tit, letra, sons = self._pont[i]
                v = pontuar_louvor(tit, letra, sons, alvo, palavras, alvo_som)
                if v:
                    pts[i] = v
            def comparar_p(a, b):
                if pts[a] != pts[b]:
                    return pts[b] - pts[a]
                return comparar(a, b)
            achados, agrupar = sorted(pts, key=functools.cmp_to_key(comparar_p)), False
        # o cabeçalho da coletânea vai em cada linha ("grp"): o painel desenha como seção que gruda no topo (sticky)
        out = []
        for i in achados:
            s = self.louvores[i]
            out.append({"i": i, "nums": self.numeros(i) or "—", "tit": s["titulo"], "cias": s.get("col") == "CIA 2018",
                        "grp": self.nome_col(i) if agrupar else "", "sigla": "" if agrupar else SIGLA_COL.get(s.get("col"), "")})
        return out

    def resumo_slides(self, i):
        s = self.louvores[self.da_vez(i)]
        return [((x.get("label") + ": ") if x.get("label") else "") + " / ".join(l.replace("\x01", "") for l in x.get("linhas") or [])
                for x in s["slides"]]


CATEGORIAS = ["Cultos", "Lema do ano", "Senhoras", "Oração", "Boas-vindas", "Avisos", "Base", "Meus fundos"]
ESPERA_ICM = "fundos/espera.jpg"
# os dados do OPERADOR (a espera escolhida, os fundos dele) ficam fora do programa, como na 3.0.12: sobrevivem a
# qualquer atualização. O Nativo grava no PRÓPRIO arquivo; o da 3.0.12 (configuracoes.json) só é LIDO, nunca
# gravado, porque o painel dela regrava aquele arquivo inteiro.
DADOS_USUARIO = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "Sistema Projecao")


class Config:
    """AS CONFIGURAÇÕES, com UMA fonte da verdade (08/11/2026, ordem da HD pela dele): as chaves que a 3.0.x também usa
    (icm_* e atu_auto) moram no configuracoes.json DELA, no MESMO formato (o gravar_config do sistema.py: o arquivo
    inteiro, json.dump com ensure_ascii=False, sem recuo, troca atômica). Abrir a 3.0.x depois do 4.0 (ou o contrário)
    mostra a mesma igreja, os mesmos fundos, os mesmos louvores. O nativo.json fica só com o que é do 4.0.
    - A 3.0.x regrava o arquivo INTEIRO: aqui também se lê o arquivo de novo antes de gravar e só a chave muda.
    - Os fundos que o operador pôs a 3.0.x guarda como imagem embutida (data:); o 4.0 usa arquivo. Na volta, a imagem
      embutida é o TEXTO ORIGINAL que veio dela (ida e volta byte a byte); fundo novo do 4.0 vira data: do arquivo.
    - Antes da 1ª gravação de cada abertura: uma cópia (configuracoes.json.antes-do-4.0-AAAAMMDD-HHMMSS.bak).
    - As icm_* que o 4.0 tinha gravado no nativo.json (versões de antes desta) passam para o arquivo da 3.0.x, mas só na
      1ª GRAVAÇÃO de verdade: ABRIR NUNCA GRAVA (achado 08/11 02h22: uma prova que só abria o acervo, sem NATIVO_SO_LOCAL,
      fez a mudança na pasta de verdade; nada se perdeu e foi desfeito por md5). Até lá, elas são lidas de onde estão.
    - PROVAS (NATIVO_SO_LOCAL=1) na pasta de VERDADE: nada se grava no arquivo da 3.0.x (fica só na memória)."""
    ARQ_312 = "configuracoes.json"

    def __init__(self, pasta=DADOS_USUARIO):
        self.pasta = pasta
        self.arq = os.path.join(pasta, "nativo.json")
        self.arq312 = os.path.join(pasta, self.ARQ_312)
        self.d = self._ler(self.arq)
        self.d312 = self._ler(self.arq312)
        self._meus = None
        self._uri_de = {}                     # arquivo do fundo -> o data: ORIGINAL que veio da 3.0.x
        self._copiou = False
        self.so_memoria = (os.environ.get("NATIVO_CONFIG_SO_LER") == "1"        # a TRAVA: lê tudo, não grava nada
                           or (os.environ.get("NATIVO_SO_LOCAL") == "1"
                               and os.path.normcase(os.path.abspath(pasta)) == os.path.normcase(os.path.abspath(DADOS_USUARIO))))
        self._velhas = {k: v for k, v in self.d.items() if self.da_312(k)}     # migram na 1ª gravação (abrir não grava)

    def _migrar(self):
        """O que o 4.0 guardava no nativo.json passa para o arquivo da 3.0.x (uma vez, na 1ª gravação)."""
        velhas, self._velhas = self._velhas, {}
        if not velhas:
            return
        for k, v in velhas.items():
            self._gravar_312(k, v)
        if not self.so_memoria:
            for k in velhas:
                self.d.pop(k, None)
            self._gravar_nativo()

    @staticmethod
    def da_312(k):
        return k.startswith("icm_") or k == "atu_auto"

    @staticmethod
    def _ler(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def ler(self, k, padrao=None):
        if self.da_312(k):
            if k in self._velhas:             # ainda não migrou: vale o que o 4.0 escolheu por último (como antes)
                return self._velhas[k]
            return self.d312.get(k, padrao)
        return self.d.get(k, padrao)

    def gravar(self, k, v):
        self._migrar()
        self._velhas.pop(k, None)
        if self.da_312(k):
            self._gravar_312(k, v)
        else:
            self.d[k] = v
            self._gravar_nativo()
        if k == "icm_fundos":
            self._meus = None

    def _gravar_nativo(self):
        if self.so_memoria:
            return
        try:
            os.makedirs(self.pasta, exist_ok=True)
            tmp = self.arq + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.d, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.arq)          # troca atômica: nunca deixa o arquivo pela metade
        except Exception as e:
            print("não gravei a config do nativo:", e)

    def _para_312(self, k, v):
        """O valor no formato da 3.0.x: fundo do operador = imagem embutida (data:)."""
        if k == "icm_fundos" and isinstance(v, list):
            return [dict(f, arquivo=self._uri(f.get("arquivo"))) if isinstance(f, dict) else f for f in v]
        if k == "icm_espera" and isinstance(v, str) and os.path.isabs(v):
            return self._uri(v)
        return v

    def _uri(self, a):
        a = str(a or "")
        if a.startswith("data:") or not os.path.isabs(a) or not os.path.exists(a):
            return a
        if a in self._uri_de:
            return self._uri_de[a]
        import base64
        tipo = {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}.get(os.path.splitext(a)[1].lower(), "image/jpeg")
        with open(a, "rb") as f:
            u = "data:%s;base64,%s" % (tipo, base64.b64encode(f.read()).decode("ascii"))
        self._uri_de[a] = u
        return u

    def _gravar_312(self, k, v):
        v312 = self._para_312(k, v)
        atual = self._ler(self.arq312)        # a 3.0.x regrava o arquivo inteiro: parte do que está no disco agora
        if not atual and self.d312:
            atual = dict(self.d312)
        atual[k] = v312
        self.d312 = atual
        if self.so_memoria:
            return
        try:
            os.makedirs(self.pasta, exist_ok=True)
            if not self._copiou and os.path.exists(self.arq312):
                import shutil
                bak = self.arq312 + time.strftime(".antes-do-4.0-%Y%m%d-%H%M%S.bak")
                if not os.path.exists(bak):        # uma cópia NUNCA cobre outra (duas aberturas no mesmo segundo)
                    shutil.copy2(self.arq312, bak)
            self._copiou = True
            tmp = self.arq312 + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(atual, f, ensure_ascii=False)        # o gravar_config da 3.0.x, igual
            os.replace(tmp, self.arq312)
        except Exception as e:
            print("não gravei o configuracoes.json:", e)

    def meus_fundos(self):
        """Os fundos que o operador acrescentou. Na 3.0.12 vêm como imagem embutida (data:); aqui viram arquivo uma
        vez só (o telão lê do disco e a imagem não fica passeando pela memória como texto)."""
        if self._meus is not None:
            return self._meus
        out = []
        for f in self.ler("icm_fundos", []) or []:
            a = str(f.get("arquivo") or "")
            if a.startswith("data:"):
                uri, a = a, self._de_data(a)
                if not a:
                    continue
                self._uri_de[a] = uri             # a volta para a 3.0.x usa este texto, byte a byte
            out.append(dict(f, arquivo=a))
        self._meus = out
        return out

    def _de_data(self, uri):
        import base64, hashlib
        try:
            cab, b64 = uri.split(",", 1)
            ext = {"image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}.get(cab[5:].split(";")[0], ".jpg")
            dados = base64.b64decode(b64)
            pasta = os.path.join(self.pasta, "nativo_fundos")
            os.makedirs(pasta, exist_ok=True)
            p = os.path.join(pasta, hashlib.md5(dados).hexdigest()[:16] + ext)
            if not os.path.exists(p):
                with open(p, "wb") as f:
                    f.write(dados)
            return p
        except Exception as e:
            print("fundo do usuário ilegível:", e)
            return ""

    def ocultos(self):
        return self.ler("icm_ocultos", []) or []

    def espera(self):
        e = self.ler("icm_espera")
        if not isinstance(e, str) or not e:
            return None
        if e.startswith("data:"):
            # 3.0.12: o cadastro "espera" da igreja (imagem embutida) = a de fábrica; outro fundo dele vira arquivo
            for f in self.ler("icm_fundos", []) or []:
                if f.get("arquivo") == e and str(f.get("nome") or "").strip().lower() == "espera":
                    return ESPERA_ICM
            arq = self._de_data(e)
            if arq:
                self._uri_de[arq] = e
            return arq or None
        return e

    def definir_espera(self, arq):
        self.gravar("icm_espera", arq)


ABREV = {"gn": "Gênesis", "ex": "Êxodo", "lv": "Levítico", "nm": "Números", "dt": "Deuteronômio", "js": "Josué",
         "jz": "Juízes", "rt": "Rute", "1sm": "1 Samuel", "2sm": "2 Samuel", "1rs": "1 Reis", "2rs": "2 Reis",
         "1cr": "1 Crônicas", "2cr": "2 Crônicas", "ed": "Esdras", "ne": "Neemias", "et": "Ester", "job": "Jó",
         "sl": "Salmos", "pv": "Provérbios", "ec": "Eclesiastes", "ct": "Cânticos", "is": "Isaías", "jr": "Jeremias",
         "lm": "Lamentações", "ez": "Ezequiel", "dn": "Daniel", "os": "Oseias", "jl": "Joel", "am": "Amós",
         "ob": "Obadias", "jn": "Jonas", "mq": "Miqueias", "na": "Naum", "hc": "Habacuque", "sf": "Sofonias",
         "ag": "Ageu", "zc": "Zacarias", "ml": "Malaquias", "mt": "Mateus", "mc": "Marcos", "lc": "Lucas",
         "jo": "João", "at": "Atos", "rm": "Romanos", "1co": "1 Coríntios", "2co": "2 Coríntios", "gl": "Gálatas",
         "ef": "Efésios", "fp": "Filipenses", "cl": "Colossenses", "1ts": "1 Tessalonicenses",
         "2ts": "2 Tessalonicenses", "1tm": "1 Timóteo", "2tm": "2 Timóteo", "tt": "Tito", "fm": "Filemom",
         "hb": "Hebreus", "tg": "Tiago", "1pe": "1 Pedro", "2pe": "2 Pedro", "1jo": "1 João", "2jo": "2 João",
         "3jo": "3 João", "jd": "Judas", "ap": "Apocalipse"}


class Biblia:
    """A ARC do Sistema (dados/biblia.js): ler a referência que o operador digita e andar de versículo em versículo."""
    def __init__(self, acervo):
        B = _js("biblia.js")
        self.ordem, self.livros = B["ordem"], B["livros"]
        self.A = acervo
        self._norm = [(so_letras(n).replace(" ", ""), n) for n in self.ordem]

    def livro(self, q):
        q = so_letras(q).replace(" ", "")
        if not q:
            return None
        for ab, nome in ABREV.items():
            if q == ab and nome in self.livros:
                return nome
        for n, nome in self._norm:          # o primeiro livro que começa assim (na ordem da Bíblia)
            if n == q:
                return nome
        for n, nome in self._norm:
            if n.startswith(q):
                return nome
        return None

    def ler(self, texto):
        """'jo 3 16', 'joão 3:16', '1co 13', 'salmos 23.1' -> (livro, cap, v). Sem versículo = 1."""
        m = re.match(r"^\s*(\d?\s*[^\d\s:.,]+)\s*(\d+)?\s*(?:[\s:.,]+\s*(\d+))?\s*$", sem_acento(texto))
        if not m:
            return None
        nome = "Jó" if re.match(r"^\s*jó(\s|\d|$)", (texto or "").lower()) else self.livro(m.group(1))   # "jo" = João
        if not nome:
            return None
        cap = int(m.group(2) or 1)
        caps = self.livros[nome]
        cap = max(1, min(cap, len(caps)))
        nums = self.versos(nome, cap)
        v = int(m.group(3) or nums[0])
        if str(v) not in caps[cap - 1]:
            v = min(nums, key=lambda x: abs(x - v))
        return nome, cap, v

    def versos(self, livro, cap):
        return sorted(int(k) for k in self.livros[livro][cap - 1].keys())

    # ---- a aba Bíblia da 3.0.13 (refDaBusca / renderLivros / buscarTrecho do app.js, as mesmas regras)
    @staticmethod
    def _bate(n, q):
        if q in n:
            return True
        if n and q and n[0] == q[0]:                 # subsequência: "1co" acha 1 Coríntios
            i = 0
            for ch in n:
                if i < len(q) and ch == q[i]:
                    i += 1
            return i == len(q)
        return False

    # A REFERÊNCIA DIGITADA (08/11/2026, relato dele no culto: "quando você pesquisa Atos 15, ele não mostra Atos 15,
    # acaba pesquisando a palavra Atos dentro do versículo... deve cobrir tudo"). CÓPIA FIEL do bloco "REFERÊNCIA
    # BÍBLICA" do app.js/controle.html: a prova_referencia_biblica confere as três na mesma tabela.
    ABREV = {
        "gn": "Gênesis", "gen": "Gênesis", "ex": "Êxodo", "exo": "Êxodo", "lv": "Levítico", "lev": "Levítico",
        "nm": "Números", "num": "Números", "dt": "Deuteronômio", "deut": "Deuteronômio", "js": "Josué", "jos": "Josué",
        "jz": "Juízes", "jui": "Juízes", "rt": "Rute", "1sm": "1 Samuel", "2sm": "2 Samuel", "1sam": "1 Samuel",
        "2sam": "2 Samuel", "1rs": "1 Reis", "2rs": "2 Reis", "1cr": "1 Crônicas", "2cr": "2 Crônicas", "ed": "Esdras",
        "esd": "Esdras", "ne": "Neemias", "et": "Ester", "est": "Ester", "sl": "Salmos", "sal": "Salmos",
        "pv": "Provérbios", "prov": "Provérbios", "ec": "Eclesiastes", "ecl": "Eclesiastes", "ct": "Cânticos",
        "cant": "Cânticos", "is": "Isaías", "isa": "Isaías", "jr": "Jeremias", "jer": "Jeremias", "lm": "Lamentações",
        "lam": "Lamentações", "ez": "Ezequiel", "dn": "Daniel", "os": "Oseias", "jl": "Joel", "am": "Amós",
        "ob": "Obadias", "jn": "Jonas", "mq": "Miqueias", "na": "Naum", "hc": "Habacuque", "sf": "Sofonias",
        "ag": "Ageu", "zc": "Zacarias", "ml": "Malaquias", "mt": "Mateus", "mc": "Marcos", "lc": "Lucas", "jo": "João",
        "at": "Atos", "rm": "Romanos", "rom": "Romanos", "1co": "1 Coríntios", "2co": "2 Coríntios",
        "1cor": "1 Coríntios", "2cor": "2 Coríntios", "gl": "Gálatas", "gal": "Gálatas", "ef": "Efésios",
        "fp": "Filipenses", "fil": "Filipenses", "cl": "Colossenses", "col": "Colossenses", "1ts": "1 Tessalonicenses",
        "2ts": "2 Tessalonicenses", "1tm": "1 Timóteo", "2tm": "2 Timóteo", "tt": "Tito", "fm": "Filemom",
        "hb": "Hebreus", "heb": "Hebreus", "tg": "Tiago", "1pe": "1 Pedro", "2pe": "2 Pedro", "1pd": "1 Pedro",
        "2pd": "2 Pedro", "1jo": "1 João", "2jo": "2 João", "3jo": "3 João", "jd": "Judas", "ap": "Apocalipse",
        "apoc": "Apocalipse"}

    def livros_ordenados(self, texto):
        """Os livros que servem para o que foi digitado, do mais provável ao menos (a abreviação de costume, "começa
        com", "contém", as letras na ordem)."""
        cru = re.sub(r"[^0-9a-zà-ÿ]+", "", (texto or "").lower())
        q = so_letras(texto or "").replace(" ", "")
        if not q:
            return []
        dedup = lambda t: re.sub(r"(.)+", r"", t)
        qd = dedup(q)
        def tier(nome):
            n = so_letras(nome).replace(" ", "")
            if cru == re.sub(r"[^0-9a-zà-ÿ]+", "", nome.lower()): return 0
            if self.ABREV.get(q) == nome: return 1
            if n == q: return 1.5
            if n.startswith(q): return 2
            if q in n or qd in dedup(n): return 3
            nd = dedup(n)
            if nd[:1] == qd[:1]:
                i = 0
                for ch in nd:
                    if i < len(qd) and ch == qd[i]: i += 1
                if i == len(qd): return 4
            return 9
        cand = [(tier(nome), k, nome) for k, nome in enumerate(self.ordem) if nome in self.livros]
        return [x[2] for x in sorted(c for c in cand if c[0] < 9)]

    def ref_da_busca(self, texto):
        t = re.sub(r"[.:;,]+$", "", (texto or "").strip())
        m = re.match(r"^(\d?\s*[^\d\s][^\d]*?)\s*(\d{1,3})(?:(?:\s*[:.;,vV]\s*|\s+)(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?)?$", t)
        if not m:
            return None
        ls = self.livros_ordenados(m.group(1))
        if not ls:
            return None
        livro = ls[0]
        caps = self.livros[livro]
        cap = int(m.group(2))
        if cap < 1 or cap > len(caps):
            return None
        v = int(m.group(3)) if m.group(3) else None
        ate = int(m.group(4)) if m.group(4) else None
        if v is not None and str(v) not in caps[cap - 1]:
            v = ate = None                      # verso que não existe: para no capítulo
        if ate is not None:
            ate = min(ate, max(int(x) for x in caps[cap - 1]))
            if ate <= v: ate = None
        return {"livro": livro, "cap": cap, "v": v, "ate": ate}

    def livros_da_busca(self, texto):
        q = so_letras(texto or "").replace(" ", "")
        return list(self.ordem) if not q else self.livros_ordenados(texto)

    def trechos(self, texto, limite=60):
        """Busca por TRECHO (o pastor cita e o operador acha): frase inteira primeiro, depois todas as palavras."""
        q = so_letras(texto)
        if len(q) < 4:
            return 0, []
        if not hasattr(self, "_indice"):
            self._indice = [(livro, ci + 1, int(v), so_letras(t)) for livro in self.ordem
                            for ci, cap in enumerate(self.livros[livro]) for v, t in cap.items()]
        termos = [p for p in q.split(" ") if len(p) > 2]
        ach = []
        for livro, cap, v, txt in self._indice:
            if q in txt:
                ach.append((livro, cap, v, 2))
            elif termos and all(t in txt for t in termos):
                ach.append((livro, cap, v, 1))
            else:
                continue
            if len(ach) > 400:
                break
        ach.sort(key=lambda a: -a[3])
        out = []
        for livro, cap, v, _ in ach[:limite]:
            t = self.texto(livro, cap, v)
            out.append({"livro": livro, "cap": cap, "v": v, "txt": t[:120] + ("…" if len(t) > 120 else "")})
        return len(ach), out

    def texto(self, livro, cap, v):
        return self.livros[livro][cap - 1].get(str(v), "")

    def proximo(self, livro, cap, v):
        nums = self.versos(livro, cap); i = nums.index(v)
        if i < len(nums) - 1: return livro, cap, nums[i + 1]
        if cap < len(self.livros[livro]): return livro, cap + 1, self.versos(livro, cap + 1)[0]
        li = self.ordem.index(livro)
        if li < len(self.ordem) - 1:
            p = self.ordem[li + 1]; return p, 1, self.versos(p, 1)[0]
        return livro, cap, v

    def anterior(self, livro, cap, v):
        nums = self.versos(livro, cap); i = nums.index(v)
        if i > 0: return livro, cap, nums[i - 1]
        if cap > 1: return livro, cap - 1, self.versos(livro, cap - 1)[-1]
        li = self.ordem.index(livro)
        if li > 0:
            p = self.ordem[li - 1]; c = len(self.livros[p]); return p, c, self.versos(p, c)[-1]
        return livro, cap, v

    def tela(self, livro, cap, v, estilo="limpo", escala=1.0):
        return {"modo": "biblia", "fundo": self.A.fundo(estilo, "biblia"), "ref": "%s %d:%d" % (livro, cap, v),
                "linhas": [self.texto(livro, cap, v)], "tam": TAM_BIBLIA, "escala": escala, "fade": 400}

    def tela_juntos(self, refs, estilo="limpo", escala=1.0):
        """Vários versículos numa tela (modo 'bibmulti' do app.js): cada um com a sua referência dourada."""
        return {"modo": "bibmulti", "fundo": self.A.fundo(estilo, "biblia"),
                "itens": [{"ref": "%s - %d:%d" % (l, c, v), "texto": self.texto(l, c, v)} for l, c, v in refs],
                "tam": TAM_BIBLIA, "escala": escala, "fade": 400}


# ---- APRESENTAÇÕES (PowerPoint convertido em telas). A lista é a MESMA do servidor da 3.0.12 (listar_apresentacoes do
# sistema.py: as que vêm junto em BASE/apresentacoes e as importadas em slides_importados, os "Louvores..." antes da
# aula, as notas, os textos da busca e a animação de dentro da tela do movimento.json). O telão nativo precisa do
# ARQUIVO; o celular, do endereço do servidor: cada tela leva os dois.
def _servidor():
    if APP not in _sys.path:
        _sys.path.insert(0, APP)
    import sistema
    return sistema


def apresentacoes():
    from urllib.parse import unquote
    S = _servidor()

    def arq(u):
        u = unquote(u)
        for pre, base in (("apresentacoes/", S.APRESENTACOES_DEMO), ("slides_importados/", S.SAIDA)):
            if u.startswith(pre):
                return os.path.normpath(os.path.join(base, u[len(pre):]))
        return u
    out = []
    for a in S.listar_apresentacoes():
        mov = {}
        for k, m in (a.get("mov") or {}).items():
            mov[k] = dict(m, base=arq(m["base"]), camadas=[dict(c, src=arq(c["src"])) for c in m.get("camadas", [])])
        out.append({"nome": a["nome"], "demo": a.get("demo", False), "urls": a["slides"],
                    "slides": [arq(u) for u in a["slides"]], "notas": a.get("notas") or [],
                    "textos": a.get("textos") or [], "mov": mov, "movUrl": a.get("mov") or {}})
    return out


def gestos():
    """A tabela dos gestinhos (dados/gestos.js, a MESMA que o retorno.html da 3.0.12 lê):
    {"apres:<nome>" ou "louvor:<chave>": {"<tela 0-based>": {"img", "louvor", "figs": [{"img", "txt", "r"}]}}}.
    Os caminhos das figuras vêm relativos à pasta do Sistema; aqui viram caminho de arquivo."""
    try:
        t = open(dado("gestos.js"), encoding="utf-8").read()
    except OSError:
        return {}
    dec, out = json.JSONDecoder(), {}
    for m in re.finditer(r'window\.GESTOS\[("(?:[^"\\]|\\.)*")\]\s*=\s*', t):
        try:
            tab, _ = dec.raw_decode(t[m.end():])
        except ValueError:
            continue
        for g in tab.values():
            if g.get("img"):
                g["img"] = os.path.join(APP, g["img"])
            for f in g.get("figs") or []:
                f["img"] = os.path.join(APP, f["img"])
        out[json.loads(m.group(1))] = tab
    return out


def importar_apresentacao(caminho):
    """Converte o PowerPoint/PDF/imagem pelo mesmo importar() da 3.0.12 (PowerPoint instalado; senão LibreOffice)."""
    S = _servidor()
    try:
        import pythoncom
        pythoncom.CoInitialize()          # roda fora da linha principal: o PowerPoint (COM) exige isto
    except Exception:
        pass
    return S.importar(caminho)


# ---------------------------------------------------------------- A CIFRA (05/11/2026)
# O banco é o MESMO da 3.0.12: <usuário>\cifras\acordes.json (4,3 MB, 2.668 louvores) + dados\cifras_ocultas.json
# (cifra não verificada não aparece, ordem dele 18/10). Guardar o banco inteiro custaria 37 MB de RAM e reler a cada
# abertura ~95 ms (medido 05/11). Então o Nativo guarda só ONDE cada louvor está no arquivo (0,3 MB) e lê o pedaço.
# As regras abaixo são as do app.js (desenharFolha, linhaDeAcordes, comTracos, marcarLinha, transpor, usaBemol,
# tomAgora, projetarCifraTelao). A prova_cifra.py roda as funções do PRÓPRIO app.js no Node e compara tudo.
ARQ_ACORDES = os.path.join(DADOS_USUARIO, "cifras", "acordes.json")
# 08/11 (HD: "o celular ficou abandonado"): a cópia do usuário só se renova quando a 3.0.x é INSTALADA; no Vaio era a de
# 10/10, no PC de casa a de 24/10, sem as correções de 03/11, e as ocultas (do pacote) já eram as novas. O pacote do Linux traz
# o banco conferido em <programa>/cifras/acordes.json: esse vence, como os dados.
_MEU_ACORDES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cifras", "acordes.json")
if not getattr(_sys, "frozen", False) and os.path.exists(_MEU_ACORDES):
    ARQ_ACORDES = _MEU_ACORDES
RE_ROTULO = re.compile(r"^\s*c[oô]ro\s*:?\s*(\(\s*bis(\s+no\s+final)?\s*\))?\s*$", re.I)
RE_INTRO = re.compile(r"^\s*(introdu[cç][aã]o|instrumentos?|final|solo)\s*:?", re.I)
RE_REPETE = re.compile(r"^\s*[\[(|]*\s*(bis(\s+no\s+final)?|\d+\s*[xX])\s*[)\]|]*\s*$")
RE_FICHA = re.compile(r"^\s*\(?\s*let\.|^\s*tonalidade\s*:|^\s*ritmo\s*:", re.I)
SEMI = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "E#": 5, "Fb": 4, "F": 5, "F#": 6, "Gb": 6,
        "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "B#": 0, "Cb": 11}
SUS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BEM = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
ESCALA_TONS = ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab"]   # a grade do abrirTons()
PARES_POR_PAG = 8                                                                 # CIFRA_PARES_POR_PAG
_RE_NOTA = re.compile(r"^([A-G])(#|b)?")


def usa_bemol(tom):
    if not tom:
        return False
    raiz = re.sub(r"m$", "", tom)
    if "b" in raiz:
        return True
    if "#" in raiz:
        return False
    return raiz in (["D", "G", "C", "F", "Bb", "Eb"] if tom.endswith("m") else ["F", "Bb", "Eb", "Ab", "Db", "Gb"])


def transpor(nota, passos, bemol):
    if not passos:
        return nota                         # 0 devolve INTACTO: senão "Eb" viraria "D#"
    m = _RE_NOTA.match(nota or "")
    if not m:
        return nota
    base = m.group(1) + (m.group(2) or "")
    if base not in SEMI:
        return nota
    return (BEM if bemol else SUS)[(SEMI[base] + passos) % 12] + nota[len(m.group(0)):]


def transpor_acorde(a, passos, bemol):
    return "/".join(transpor(p, passos, bemol) for p in str(a).split("/"))


def transpor_tom(tom, passos, bemol):
    if not tom:
        return tom
    menor = tom.endswith("m")
    return transpor(tom[:-1] if menor else tom, passos, bemol) + ("m" if menor else "")


def tom_agora(tom, desloc):
    return transpor_tom(tom, desloc, usa_bemol(transpor_tom(tom, desloc, usa_bemol(tom))))


def desloc_para(tom_impresso, alvo):
    """O botão da grade de tons: quantos semitons do impresso até o 'alvo'; −2 em vez de +10 (o músico lê melhor)."""
    raiz = re.sub(r"m$", "", tom_impresso or "")
    d = (SEMI[alvo] - SEMI[raiz]) % 12
    return d - 12 if d > 6 else d


def fila_de_acordes(acordes):
    """linhaDeAcordes: cada acorde na coluna do PDF; encostou no anterior = dois espaços ("DbmEb0" não existe)."""
    fila = ""
    for col, nome in acordes or []:
        if fila and len(fila) >= col:
            fila += "  "
        fila += " " * max(0, col - len(fila)) + nome
    return fila


def tracos(texto, acordes):
    """comTracos: o tracinho do ritmo vai antes da letra em que o acorde está (coluna 0 não ganha; espaço anda)."""
    marcas = set()
    for par in acordes or []:
        c = par[0]
        if not c:
            continue
        while c < len(texto) and texto[c] == " ":
            c += 1
        if 0 < c < len(texto):
            marcas.add(c)
    return sorted(marcas)


def tipo_da_linha(t):
    if RE_ROTULO.search(t or ""):
        return "rot"
    if RE_INTRO.search(t or ""):
        return "intro"
    if RE_REPETE.search(t or ""):
        return "rep"
    return ""


class Cifras:
    def __init__(self, arq=ARQ_ACORDES):
        self.arq = arq
        self.idx = None                     # chave -> (início, fim) em BYTES no arquivo
        self.marca = None                   # (tamanho, mtime): o arquivo mudou (cifra importada) = refaz o índice
        try:
            self.ocultas = set(json.load(open(dado("cifras_ocultas.json"), encoding="utf-8")))
        except Exception:
            self.ocultas = set()            # sem o arquivo nada some (o jeito de antes, sistema.py:309)

    def _indice(self):
        try:
            st = os.stat(self.arq)
        except OSError:
            self.idx, self.marca = {}, None
            return self.idx
        marca = (st.st_size, st.st_mtime)
        if self.idx is not None and marca == self.marca:
            return self.idx
        b = open(self.arq, "rb").read()
        s = b.decode("latin-1")             # 1 caractere = 1 byte: a posição na string É a posição no arquivo
        dec = json.JSONDecoder()
        idx, p, n = {}, s.index("{") + 1, len(s)
        ws = " \t\r\n"
        while True:
            while p < n and s[p] in ws + ",":
                p += 1
            if p >= n or s[p] == "}":
                break
            _, fk = dec.raw_decode(s, p)                     # a chave (só para achar o fim dela)
            k = json.loads(b[p:fk].decode("utf-8"))          # a chave de verdade, em UTF-8
            p = fk
            while s[p] in ws + ":":
                p += 1
            _, fv = dec.raw_decode(s, p)                     # o louvor (só para achar o fim; sai da memória já)
            if k not in self.ocultas:
                idx[k] = (p, fv)
            p = fv
        del s, b
        self.idx, self.marca = idx, marca
        return idx

    def tem(self, k):
        return k in self._indice()

    def ler(self, k):
        par = self._indice().get(k)
        if not par:
            return None
        with open(self.arq, "rb") as f:
            f.seek(par[0])
            reg = json.loads(f.read(par[1] - par[0]).decode("utf-8"))
        return reg if reg.get("linhas") else None

    def folha(self, k, desloc=0):
        """A folha do painel (desenharFolha): o tom, o cabeçalho do transporte e as linhas prontas para desenhar."""
        reg = self.ler(k)
        if not reg:
            return {"ok": False}
        tom = reg.get("tom") or ""
        agora = tom_agora(tom, desloc)
        bemol = usa_bemol(agora)
        cab = ""
        if desloc:
            cab = "%s%d %s do impresso (%s)" % ("+" if desloc > 0 else "", desloc,
                                                 "semitons" if abs(desloc) > 1 else "semitom", tom or "tom não declarado")
        linhas = []
        for l in reg["linhas"]:
            t = l.get("t") or ""
            if RE_FICHA.search(t):
                continue                                  # autor/tonalidade/ritmo: fora da folha (ele mandou)
            a = [[c, transpor_acorde(n, desloc, bemol)] for c, n in (l.get("a") or [])]
            limpo = t.replace("\x01", "")
            linhas.append({"ac": fila_de_acordes(a), "t": limpo, "tipo": tipo_da_linha(t), "tr": tracos(limpo, l.get("a"))})
        return {"ok": True, "tom": tom, "agora": agora, "desloc": desloc, "cab": cab, "linhas": linhas}

    def paginas(self, k, desloc=0):
        """projetarCifraTelao: pares [acordes, letra] de 8 em 8, a transposição da folha vai junto."""
        reg = self.ler(k)
        if not reg:
            return []
        bemol = usa_bemol(tom_agora(reg.get("tom") or "", desloc))
        pares = []
        for l in reg["linhas"]:
            if RE_FICHA.search(l.get("t") or ""):
                continue
            a = [[c, transpor_acorde(n, desloc, bemol)] for c, n in (l.get("a") or [])]
            pares.append([fila_de_acordes(a), (l.get("t") or "").replace("\x01", "")])
        return [pares[i:i + PARES_POR_PAG] for i in range(0, len(pares), PARES_POR_PAG)]


if __name__ == "__main__":
    import sys, time
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.time(); A = Acervo()
    print("acervo: %d louvores, %d selos, %d cópias, %d animações (%.2f s)" % (
        len(A.louvores), len(A.selos), len(A.principal_de), len(A.anim), time.time() - t0))
    for q in ("69", "quando ao fim", "maranata", "121"):
        r = A.buscar(q)[:3]
        print(q, "->", [A.rotulo(i) for i in r])
    i = A.buscar("69")[0]
    print(json.dumps(A.tela_louvor(i, 0, com_animacao=False), ensure_ascii=False)[:400])
    print(json.dumps(A.tela_louvor(i, 0), ensure_ascii=False)[:300])
