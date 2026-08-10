# -*- coding: utf-8 -*-
"""Instalador leve do Sistema — o pequeno, que busca o resto na internet.

POR QUE ELE EXISTE
------------------
O instalador completo tem 58 MB porque leva tudo dentro: os 2.459 louvores, a
Bíblia inteira, os fundos, as fontes. É o certo para quem vai instalar na
igreja, onde muitas vezes não há internet boa.

Este aqui tem menos de 15 MB e serve para outra coisa: passar de mão em mão.
Cabe no WhatsApp, sobe em qualquer lugar, e o Google Drive consegue varrer o
arquivo e atestar que não tem vírus — o que ele não faz com um arquivo grande.

O QUE ELE PERGUNTA
------------------
Duas perguntas, nessa ordem, e nada além disso:

  1. Instalar NESTE computador, ou levar para OUTRO?
  2. Se for levar: para a pasta Downloads, para um pendrive, ou para uma
     pasta escolhida a dedo?

"Instalar neste computador" baixa e instala na hora, sem mais nenhum clique.
"Levar para outro" baixa o instalador completo e deixa ele no destino, pronto
para o outro computador rodar sem internet nenhuma.

DE ONDE VEM O ARQUIVO
---------------------
Do GitHub, do endereço "releases/latest" — que aponta sempre para a versão mais
nova, sem precisar mexer neste programa quando sair uma atualização.
"""
import ctypes
import ctypes.wintypes          # SystemParametersInfoW precisa do RECT daqui
import os
import shutil
import subprocess
import sys
import threading
import urllib.request

# O endereco "latest" do GitHub redireciona sozinho para a versao mais nova.
# Quando sair a v2.4.0, este arquivo continua funcionando sem ser recompilado.
DONO = "QuitsQuill88885"
REPO = "sistema-projecao-icm"
ARQUIVO = "Instalar-o-Sistema.exe"
URL = "https://github.com/%s/%s/releases/latest/download/%s" % (DONO, REPO, ARQUIVO)

SEM_JANELA = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}


# ----------------------------------------------------------------- utilidades

def origem():
    """A pasta de onde este programa está rodando (funciona compilado ou não)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def fechar_splash():
    """Tira a telinha de carregamento do PyInstaller. Sem isto ela fica na tela
    para sempre, por cima da janela de verdade."""
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass


def centro_da_tela(larg, alt):
    """Centraliza na área ÚTIL do monitor — descontando a barra de tarefas —
    e nunca deixa a janela nascer com coordenada negativa."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    try:
        r = ctypes.wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0)
        lx, ly, lw, lh = r.left, r.top, r.right - r.left, r.bottom - r.top
    except Exception:
        lx, ly = 0, 0
        lw = ctypes.windll.user32.GetSystemMetrics(0)
        lh = ctypes.windll.user32.GetSystemMetrics(1)
    return max(0, lx + (lw - larg) // 2), max(0, ly + (lh - alt) // 2)


def pasta_downloads():
    """A pasta Downloads DE VERDADE. O usuário pode tê-la movido para outro
    disco, e aí o palpite "~/Downloads" aponta para uma pasta que não existe.
    Quem sabe o caminho certo é o Windows."""
    try:
        from ctypes import windll, wintypes
        _ID = "{374DE290-123F-4565-9164-39C4925E467B}"          # FOLDERID_Downloads
        class GUID(ctypes.Structure):
            _fields_ = [("d1", wintypes.DWORD), ("d2", wintypes.WORD),
                        ("d3", wintypes.WORD), ("d4", ctypes.c_byte * 8)]
        g = GUID()
        if windll.ole32.CLSIDFromString(_ID, ctypes.byref(g)) == 0:
            p = ctypes.c_wchar_p()
            if windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None,
                                                   ctypes.byref(p)) == 0:
                caminho = p.value
                windll.ole32.CoTaskMemFree(p)
                if caminho and os.path.isdir(caminho):
                    return caminho
    except Exception:
        pass
    palpite = os.path.join(os.path.expanduser("~"), "Downloads")
    return palpite if os.path.isdir(palpite) else os.path.expanduser("~")


# As pastas de conteúdo pesado que o instalador NÃO carrega dentro do .exe
# (juntas passam de 580 MB). Se ESTE computador as tem, a exportação leva
# junto, numa pasta "Conteudo" ao lado do instalador. Foi a falta disto que
# fez as animações dos CIAS nunca chegarem à igreja: o pendrive levava só o
# programa, e o programa sem a pasta instala calado, sem os botões.
PASTAS_CONTEUDO = ("animacoes", "cifras", "melodias")


def conteudo_local():
    """[(nome, caminho, bytes)] do conteúdo que este computador tem para dar."""
    base = os.path.join(os.environ.get("APPDATA") or "", "Sistema Projecao")
    achadas = []
    for nome in PASTAS_CONTEUDO:
        p = os.path.join(base, nome)
        if not os.path.isdir(p):
            continue
        total = 0
        for raiz, _sub, arqs in os.walk(p):
            for a in arqs:
                try:
                    total += os.path.getsize(os.path.join(raiz, a))
                except OSError:
                    pass
        if total > 4096:        # pasta só com o LEIA-ME.txt não é conteúdo
            achadas.append((nome, p, total))
    return achadas


def copiar_conteudo(pasta, achadas, progresso):
    """Copia as pastas de conteúdo para "Conteudo" ao lado do instalador.

    progresso recebe a fração 0..1 do total de bytes já copiado."""
    destino = os.path.join(pasta, "Conteudo")
    total = sum(t for _n, _p, t in achadas) or 1
    feito = 0
    for nome, origem_pasta, _t in achadas:
        for raiz, _sub, arqs in os.walk(origem_pasta):
            rel = os.path.relpath(raiz, origem_pasta)
            alvo = os.path.join(destino, nome) if rel == "." \
                else os.path.join(destino, nome, rel)
            os.makedirs(alvo, exist_ok=True)
            for a in arqs:
                de = os.path.join(raiz, a)
                shutil.copy2(de, os.path.join(alvo, a))
                try:
                    feito += os.path.getsize(de)
                except OSError:
                    pass
                progresso(feito / float(total))


def pendrives():
    """Lista os pendrives plugados agora: [{'letra','nome','livre'}].

    Só entram unidades REMOVÍVEIS e que estejam realmente acessíveis. Um leitor
    de cartão vazio aparece na lista de unidades do Windows mas explode quando
    alguém tenta escrever nele — por isso o teste de espaço livre, que só passa
    se houver mídia dentro."""
    achados = []
    try:
        k = ctypes.windll.kernel32
        bits = k.GetLogicalDrives()
        for i in range(26):
            if not (bits & (1 << i)):
                continue
            letra = "%s:\\" % chr(65 + i)
            if k.GetDriveTypeW(letra) != 2:                     # 2 = DRIVE_REMOVABLE
                continue
            try:
                livre = ctypes.c_ulonglong(0)
                if not k.GetDiskFreeSpaceExW(letra, ctypes.byref(livre), None, None):
                    continue
            except Exception:
                continue
            nome = ""
            try:
                buf = ctypes.create_unicode_buffer(261)
                if k.GetVolumeInformationW(letra, buf, 260, None, None, None, None, 0):
                    nome = (buf.value or "").strip()
            except Exception:
                pass
            achados.append({"letra": letra, "nome": nome or "Pendrive",
                            "livre": int(livre.value)})
    except Exception:
        pass
    return achados


def tamanho_curto(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return ("%.0f %s" % (n, u)) if u != "GB" else ("%.1f GB" % n)
        n /= 1024.0


# ----------------------------------------------------------------- o download

def baixar(destino, progresso, url=URL):
    """Baixa o instalador completo para `destino`, avisando o andamento.

    Grava num arquivo .parte e só renomeia no fim. Assim uma queda de internet
    no meio do caminho não deixa para trás um .exe pela metade, que o usuário
    tentaria executar e daria erro sem explicação."""
    parcial = destino + ".parte"
    pasta = os.path.dirname(destino)
    if pasta and not os.path.isdir(pasta):
        os.makedirs(pasta, exist_ok=True)

    req = urllib.request.Request(url, headers={"User-Agent": "Sistema-Instalador"})
    progresso(2, "Procurando a versão mais nova…")
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("Content-Length") or 0)
        feito = 0
        with open(parcial, "wb") as f:
            while True:
                pedaco = r.read(262144)
                if not pedaco:
                    break
                f.write(pedaco)
                feito += len(pedaco)
                if total:
                    pct = 3 + int(feito * 82.0 / total)
                    progresso(min(85, pct), "Baixando… %s de %s"
                              % (tamanho_curto(feito), tamanho_curto(total)))
                else:
                    progresso(40, "Baixando… %s" % tamanho_curto(feito))

    if total and os.path.getsize(parcial) < total * 0.98:
        os.remove(parcial)
        raise RuntimeError("O download veio incompleto. Tente de novo.")

    if os.path.exists(destino):
        os.remove(destino)
    os.replace(parcial, destino)
    return destino


def espaco_livre(pasta):
    try:
        livre = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(pasta), ctypes.byref(livre), None, None)
        return int(livre.value)
    except Exception:
        return -1


# ----------------------------------------------------------------------- tela

HTML = """<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<title>Baixar o Sistema</title><style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;font-family:'Segoe UI',system-ui,sans-serif;color:#eaf0fb;overflow:hidden;
  background:radial-gradient(ellipse at 50% 26%, #16294a 0%, #0b1526 74%)}
.tudo{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;
      gap:15px;padding:24px;text-align:center}
h1{font-size:24px;font-weight:800;letter-spacing:.3px}
.sub{font-size:13.5px;color:#8fa8cf;max-width:48ch;line-height:1.6}
.passo{font-size:12.5px;color:#9db3d6;min-height:18px}
.barra{width:340px;height:7px;border-radius:6px;background:#1e2d49;overflow:hidden;margin-top:6px}
.barra i{display:block;height:100%;width:0;border-radius:6px;transition:width .3s ease;
  background:linear-gradient(90deg,#a31a1a,#f5d76e)}
/* os dois caminhos: cartoes largos, porque a escolha e' a coisa mais
   importante da tela e precisa ser obvia a um metro de distancia */
.cartoes{display:flex;gap:12px;margin-top:6px}
.cartao{width:212px;background:#131f36;border:1px solid #24344f;border-radius:12px;
  padding:17px 15px;cursor:pointer;text-align:center;transition:.16s;color:inherit;font:inherit}
.cartao:hover{background:#1a2942;border-color:#e8b93c;transform:translateY(-2px)}
.cartao .ic{font-size:27px;line-height:1;margin-bottom:9px;display:block}
.cartao b{display:block;font-size:14.5px;margin-bottom:5px}
.cartao small{display:block;font-size:11.5px;color:#8398bb;line-height:1.45}
/* os tres destinos: quadradinhos, como combinado */
.quadros{display:flex;gap:11px;margin-top:8px}
.quadro{width:132px;height:116px;background:#131f36;border:1px solid #24344f;border-radius:12px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;
  cursor:pointer;transition:.16s;color:inherit;font:inherit;padding:9px}
.quadro:hover{background:#1a2942;border-color:#e8b93c;transform:translateY(-2px)}
.quadro:disabled{opacity:.42;cursor:default;transform:none;border-color:#24344f;background:#111a2c}
.quadro .ic{font-size:25px;line-height:1}
.quadro b{font-size:12.5px}
.quadro small{font-size:10.5px;color:#8398bb;line-height:1.35}
button{font-family:inherit;border:none;cursor:pointer;color:#fff}
.ok{background:#2e8b57;font-size:14px;font-weight:600;border-radius:9px;padding:12px 26px}
.ok:hover{background:#37a066}
.ok.grande{padding:15px 40px;font-size:15px}
.sec{background:#1e2d49;border:1px solid #2c3d5c;font-size:13px;border-radius:9px;padding:10px 20px}
.sec:hover{background:#26375a}
.linha{display:flex;gap:9px;margin-top:16px;justify-content:center;align-items:center}
.voltar{background:none;border:none;color:#6f86a9;font-size:12px;cursor:pointer;margin-top:2px;
  text-decoration:underline;padding:4px}
.voltar:hover{color:#9db3d6}
.dica{font-size:12px;color:#7f96b8;max-width:46ch;line-height:1.6;margin-top:10px;
  padding:10px 12px;background:#101d33;border-left:3px solid #e8b93c;border-radius:0 7px 7px 0;text-align:left}
.dica b{color:#cfe0f5}
.caminho{font-size:11.5px;color:#7f96b8;word-break:break-all;max-width:52ch;margin-top:3px}
.erro{color:#ffb4a8;font-size:13px;max-width:46ch;line-height:1.55}
.tela{display:flex;flex-direction:column;align-items:center;gap:10px;width:100%}
.tela.oculto{display:none}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
</style></head><body>
<div class="tudo">
  <div id="marca"></div>
  <h1 id="titulo">Baixar o Sistema</h1>

  <!-- 1: os dois caminhos -->
  <div class="tela" id="t1">
    <p class="sub">Este é o instalador leve. Ele busca o Sistema na internet e
       faz o que você mandar com ele.</p>
    <div class="cartoes">
      <button class="cartao" onclick="aqui()">
        <span class="ic">💻</span><b>Instalar neste computador</b>
        <small>Baixa e instala agora. É só esperar.</small></button>
      <button class="cartao" onclick="ir(2)">
        <span class="ic">📦</span><b>Levar para outro computador</b>
        <small>Baixa o instalador completo e guarda onde você quiser.</small></button>
    </div>
  </div>

  <!-- 2: os tres destinos -->
  <div class="tela oculto" id="t2">
    <p class="sub">Onde você quer guardar o instalador completo?</p>
    <div class="quadros" id="quadros"></div>
    <p class="dica">O arquivo completo tem <b>58 MB</b> e roda em qualquer
       computador <b>sem internet nenhuma</b>. É o que levar para a igreja.</p>
    <button class="voltar" onclick="ir(1)">voltar</button>
  </div>

  <!-- 3: baixando -->
  <div class="tela oculto" id="t3">
    <div class="barra"><i id="preenche"></i></div>
    <p class="passo" id="passo">Preparando…</p>
  </div>

  <!-- 4: terminou -->
  <div class="tela oculto" id="t4">
    <p class="sub" id="fim-txt"></p>
    <p class="caminho" id="fim-caminho"></p>
    <div class="linha" id="fim-botoes"></div>
  </div>

  <!-- 5: deu errado -->
  <div class="tela oculto" id="t5">
    <p class="erro" id="erro-txt"></p>
    <div class="linha">
      <button class="ok" onclick="ir(1)">Tentar de novo</button>
      <button class="sec" onclick="sair()">Fechar</button>
    </div>
  </div>
</div>
<script src="icones.js"></script>
<script>
const $ = s => document.querySelector(s);
$('#marca').innerHTML = (window.Icones && window.Icones.MARCA) ? window.Icones.MARCA(74) : '';

function ir(n){
  for (const k of [1,2,3,4,5]) $('#t'+k).classList.toggle('oculto', k !== n);
  $('#titulo').textContent = (n === 2) ? 'Levar para outro computador' : 'Baixar o Sistema';
  if (n === 2) destinos();
}

// Os tres quadradinhos. O do pendrive so' existe se houver um plugado agora --
// mostrar um botao morto e' pior do que nao mostrar nada.
async function destinos(){
  const cx = $('#quadros');
  cx.innerHTML = '<div class="passo">Procurando…</div>';
  let d = {downloads:'', usb:[]};
  try { d = await window.pywebview.api.destinos(); } catch(e){}
  let h = `<button class="quadro" onclick="salvar('downloads')">
             <span class="ic">⬇️</span><b>Downloads</b>
             <small>a pasta de sempre</small></button>`;
  if (d.usb && d.usb.length){
    for (const u of d.usb)
      h += `<button class="quadro" onclick="salvar('usb','${u.letra.replace(/\\\\/g,'\\\\\\\\')}')">
              <span class="ic">🔌</span><b>${u.nome}</b>
              <small>${u.letra.replace('\\\\','')} · ${u.livre} livres</small></button>`;
  } else {
    h += `<button class="quadro" disabled>
            <span class="ic">🔌</span><b>Pendrive</b>
            <small>nenhum plugado</small></button>`;
  }
  h += `<button class="quadro" onclick="salvar('escolher')">
          <span class="ic">📁</span><b>Escolher pasta</b>
          <small>eu digo onde</small></button>`;
  cx.innerHTML = h;
}

function aqui(){ ir(3); acompanhar(); window.pywebview.api.instalar_aqui(); }
function salvar(tipo, letra){ ir(3); acompanhar(); window.pywebview.api.exportar(tipo, letra || ''); }

let relogio = null;
function acompanhar(){
  if (relogio) return;
  // A TELA busca o progresso. O contrario -- Python empurrando de outra thread
  // -- trava a janela inteira; ja aconteceu e custou caro.
  relogio = setInterval(async () => {
    let d; try { d = await window.pywebview.api.progresso(); } catch(e){ return; }
    $('#preenche').style.width = (d.pct || 0) + '%';
    $('#passo').textContent = d.txt || '';
    if (!d.fim) return;
    clearInterval(relogio); relogio = null;
    if (d.erro){ $('#erro-txt').textContent = d.erro; ir(5); return; }
    $('#preenche').style.width = '100%';
    setTimeout(() => {
      $('#fim-txt').innerHTML = d.msg || '';
      $('#fim-caminho').textContent = d.caminho || '';
      $('#fim-botoes').innerHTML = (d.modo === 'instalar')
        ? `<button class="ok grande" onclick="abrirApp()">Abrir o Sistema</button>`
        : `<button class="ok" onclick="abrirPasta()">Ver a pasta</button>
           <button class="sec" onclick="sair()">Fechar</button>`;
      ir(4);
    }, 400);
  }, 200);
}
function abrirApp(){ window.pywebview.api.abrir_app(); }
function abrirPasta(){ window.pywebview.api.abrir_pasta(); }
function sair(){ window.pywebview.api.sair(); }
</script></body></html>
"""


class Api:
    def __init__(self):
        self.janela = None
        self.estado = {"pct": 0, "txt": ""}
        self.terminou = False
        self.erro = ""
        self.modo = ""
        self.caminho = ""
        self.msg = ""
        self.exe = ""

    # ------------------------------------------------------------- consultas
    def progresso(self):
        d = dict(self.estado)
        d.update({"fim": self.terminou, "erro": self.erro, "modo": self.modo,
                  "caminho": self.caminho, "msg": self.msg})
        return d

    def destinos(self):
        return {"downloads": pasta_downloads(),
                "usb": [{"letra": u["letra"], "nome": u["nome"],
                         "livre": tamanho_curto(u["livre"])} for u in pendrives()]}

    # -------------------------------------------------------------- trabalho
    def _rodar(self, tarefa):
        def envelope():
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pythoncom = None
            try:
                tarefa()
            except Exception as e:
                self.erro = str(e) or "Não consegui concluir."
            finally:
                self.terminou = True
                if pythoncom:
                    try:
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass
        self.terminou = False
        self.erro = ""
        threading.Thread(target=envelope, daemon=True).start()
        return True

    def _p(self, pct, txt):
        self.estado = {"pct": pct, "txt": txt}

    def instalar_aqui(self):
        """Baixa o instalador completo e roda ele em silêncio. Um clique só."""
        def tarefa():
            import tempfile
            self.modo = "instalar"
            alvo = os.path.join(tempfile.mkdtemp(), ARQUIVO)
            baixar(alvo, self._p)
            self._p(88, "Instalando o Sistema…")
            r = subprocess.run([alvo, "--silencioso"], capture_output=True,
                               text=True, **SEM_JANELA)
            saida = (r.stdout or "") + (r.stderr or "")
            for linha in saida.splitlines():
                if linha.lower().startswith("instalado em:"):
                    self.exe = linha.split(":", 1)[1].strip()
            if r.returncode != 0 or not self.exe:
                raise RuntimeError("A instalação não terminou. " + saida.strip()[-180:])
            self._p(100, "Pronto!")
            self.caminho = self.exe
            self.msg = ("Tudo pronto. O <b>Sistema</b> já está na sua Área de "
                        "Trabalho e no menu Iniciar.")
        return self._rodar(tarefa)

    def exportar(self, tipo, letra=""):
        """Baixa o instalador completo e deixa ele no destino escolhido."""
        def tarefa():
            self.modo = "exportar"
            if tipo == "downloads":
                pasta = pasta_downloads()
            elif tipo == "usb":
                pasta = letra or ""
                if not pasta or not os.path.isdir(pasta):
                    raise RuntimeError("O pendrive foi retirado. Coloque de volta "
                                       "e tente de novo.")
            else:
                escolhido = self.janela.create_file_dialog(20)   # FOLDER_DIALOG
                if not escolhido:
                    raise RuntimeError("Nenhuma pasta foi escolhida.")
                pasta = escolhido[0] if isinstance(escolhido, (list, tuple)) else escolhido

            livre = espaco_livre(pasta)
            if 0 <= livre < 70 * 1024 * 1024:
                raise RuntimeError("Não cabe: faltam espaço em %s (só %s livres)."
                                   % (pasta, tamanho_curto(livre)))

            alvo = os.path.join(pasta, "Instalar o Sistema.exe")
            baixar(alvo, self._p)

            # Se ESTE computador tem as animações, cifras e melodias, elas vão
            # junto — é a única forma de chegarem ao outro computador, porque
            # são pesadas demais para viajar dentro do .exe ou pela internet
            # da igreja. Se não couberem, o instalador vai mesmo assim, e o
            # aviso diz com todas as letras o que ficou para trás.
            achadas = conteudo_local()
            levou, faltou = [], 0
            if achadas:
                precisa = sum(t for _n, _p2, t in achadas)
                livre2 = espaco_livre(pasta)
                if 0 <= livre2 < precisa + 20 * 1024 * 1024:
                    faltou = precisa + 20 * 1024 * 1024 - livre2
                else:
                    self._p(90, "Levando as animações, cifras e melodias…")
                    copiar_conteudo(pasta, achadas,
                                    lambda x: self._p(90 + int(x * 8),
                                                      "Levando as animações, cifras e melodias…"))
                    levou = [n for n, _p2, _t in achadas]

            self._p(99, "Conferindo…")
            self._explicar(pasta, levou)
            self._p(100, "Pronto!")
            self.caminho = alvo
            onde = ("no pendrive" if tipo == "usb" else
                    "na pasta Downloads" if tipo == "downloads" else "na pasta escolhida")
            self.msg = ("O instalador completo está %s. Leve para o outro "
                        "computador e execute — ele <b>não precisa de internet</b>." % onde)
            if levou:
                self.msg += (" Foi junto a pasta <b>Conteudo</b> (%s) — leve os "
                             "dois juntos, um ao lado do outro." % ", ".join(levou))
            elif faltou:
                self.msg += (" <b>Atenção:</b> as animações e cifras NÃO couberam "
                             "— faltaram %s livres. O Sistema instala sem elas."
                             % tamanho_curto(faltou))
        return self._rodar(tarefa)

    def _explicar(self, pasta, levou=()):
        """Deixa um bilhete ao lado do .exe. Quem recebe o pendrive na igreja
        muitas vezes não recebe explicação junto."""
        try:
            with open(os.path.join(pasta, "LEIA - Como instalar o Sistema.txt"),
                      "w", encoding="utf-8") as f:
                f.write(
                    "SISTEMA — projecao para a igreja\r\n"
                    "================================\r\n\r\n"
                    "COMO INSTALAR\r\n"
                    "  1. De dois cliques em \"Instalar o Sistema.exe\"\r\n"
                    "  2. Clique em Instalar\r\n"
                    "  3. Espere a barrinha encher e clique em Abrir o Sistema\r\n\r\n"
                    "Nao precisa de internet. Nao precisa instalar mais nada.\r\n"
                    "Ja vem com os louvores, a Biblia inteira e os fundos.\r\n\r\n"
                    + ("A pasta \"Conteudo\" que veio junto tem as animacoes dos\r\n"
                       "CIAS, as cifras e as melodias. DEIXE ELA AO LADO do\r\n"
                       "instalador na hora de instalar — o instalador copia\r\n"
                       "tudo sozinho. Sem ela o Sistema funciona, mas sem os\r\n"
                       "botoes de animacao e de cifra.\r\n\r\n" if levou else "")
                    + "SE O WINDOWS AVISAR\r\n"
                    "  Pode aparecer \"O Windows protegeu o computador\".\r\n"
                    "  Clique em \"Mais informacoes\" e depois em \"Executar assim mesmo\".\r\n"
                    "  Isso acontece porque o programa e' gratuito e nao tem\r\n"
                    "  assinatura digital paga — nao e' virus.\r\n\r\n"
                    "Desenvolvido por Samuel Mariano Ribeiro.\r\n")
        except Exception:
            pass

    # --------------------------------------------------------------- botoes
    def abrir_app(self):
        try:
            if self.exe and os.path.exists(self.exe):
                subprocess.Popen([self.exe], cwd=os.path.dirname(self.exe), **SEM_JANELA)
        except Exception:
            pass
        self.sair()

    def abrir_pasta(self):
        try:
            if self.caminho and os.path.exists(self.caminho):
                subprocess.Popen(["explorer", "/select,", os.path.normpath(self.caminho)])
        except Exception:
            pass

    def sair(self):
        try:
            self.janela.destroy()
        except Exception:
            pass


def main():
    import tempfile
    import webview
    api = Api()
    pasta = tempfile.mkdtemp()
    with open(os.path.join(pasta, "baixar.html"), "w", encoding="utf-8") as f:
        f.write(HTML)
    ico = os.path.join(origem(), "icones.js")
    if os.path.exists(ico):
        shutil.copy2(ico, os.path.join(pasta, "icones.js"))
    LARG, ALT = 640, 540
    x, y = centro_da_tela(LARG, ALT)
    api.janela = webview.create_window("Baixar o Sistema", os.path.join(pasta, "baixar.html"),
                                       width=LARG, height=ALT, x=x, y=y, resizable=False,
                                       background_color="#0b1526", js_api=api)
    webview.start(fechar_splash, gui="edgechromium")


if __name__ == "__main__":
    main()
