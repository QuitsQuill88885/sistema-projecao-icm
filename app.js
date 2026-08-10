/* ICM Iperó — Projeção | painel de controle */
(function () {
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const BIBLIA = window.BIBLIA, LOUVORES = window.LOUVORES;
const BASE_LOUVORES = LOUVORES.slice();   // coletânea original (os "Meus louvores" entram depois dela)
const ESTILOS = window.ESTILOS, GALERIA = window.GALERIA || [];
const TAM_DEF = { louvor: 6.4, biblia: 5.55 };

const est = {
  aba: 'louvor', projetando: false, freeze: false, estilo: 'limpo',
  louvorIdx: -1, louvorSlide: 0,
  livro: null, cap: null, bibPos: null, fila: [], setPos: -1, vistaFim: null, aguardando: false, contAfter: 0, juntos: false,
  descansoFundo: null,   // tela de espera escolhida (null = padrão do estilo)
  live: null, ultimo: { modo: 'preto' },
  timerFim: 0, timerParadoMs: 0, timerRotulo: 'Oração',
  tamTexto: 6, textoFundo: null, fundoCat: 'Todos', slidePos: -1,
  escalaLouvor: 1, escalaVers: 1, escalaTexto: 1,   // A-/A+ = fator multiplicado SOBRE o auto-ajuste (1 = padrão)
};
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
let projWin = null, dragFrom = null;
const previews = [];
// ---- guarda os dados do usuário FORA do programa (sobrevive a atualizações) ----
let VERSAO = '1.0.0';
const Guardar = {
  cache: {}, servidor: false,
  ler(chave, padrao) {
    if (chave in this.cache) return this.cache[chave];
    try { const v = localStorage.getItem(chave); return v == null ? padrao : JSON.parse(v); } catch (e) { return padrao; }
  },
  gravar(chave, valor) {
    this.cache[chave] = valor;
    try { localStorage.setItem(chave, JSON.stringify(valor)); } catch (e) {}
    if (this.servidor) { clearTimeout(this._t); this._t = setTimeout(() => this.enviar(), 400); }
  },
  enviar() {
    try {
      if (nativo()) window.pywebview.api.gravar_config(this.cache);
      else fetch('/api/config', { method: 'POST', body: JSON.stringify(this.cache) });
    } catch (e) {}
  },
  async carregar() {   // ao abrir: o que estiver salvo ao lado do programa manda
    if (!window.pywebview) {   // dá um instante pra ponte nativa ficar pronta
      await new Promise(r => { const t = setTimeout(r, 1500); window.addEventListener('pywebviewready', () => { clearTimeout(t); r(); }, { once: true }); });
    }
    try {
      const r = nativo() ? await window.pywebview.api.ler_config()
                         : await fetch('/api/config').then(r => r.json());
      if (r && r.ok) {
        VERSAO = r.versao || VERSAO; this.servidor = true;
        if (r.dados && Object.keys(r.dados).length) { this.cache = r.dados; return true; }
      }
    } catch (e) {}
    return false;
  },
};
// fundos que o próprio usuário adiciona (foto + nome)
let CUSTOM = Guardar.ler('icm_fundos', []) || [], OCULTOS = Guardar.ler('icm_ocultos', []) || [];
function salvarCustom() { Guardar.gravar('icm_fundos', CUSTOM); }
function salvarOcultos() { Guardar.gravar('icm_ocultos', OCULTOS); }
function apagarFundo(f) {
  if (f.custom) { CUSTOM = CUSTOM.filter(x => x !== f); salvarCustom(); }
  else { if (!OCULTOS.includes(f.arquivo)) OCULTOS.push(f.arquivo); salvarOcultos(); }
  if (est.descansoFundo === f.arquivo) est.descansoFundo = null;
  renderFundos(); toast('Fundo removido.');
}

// fundos do estilo ativo
let FB = {};
function aplicarEstilo() {
  const e = ESTILOS[est.estilo] || ESTILOS.limpo;
  FB = {
    biblia: e.biblia, louvor1: e.louvor1, louvor2: e.louvor2 || e.louvor1,
    descanso: e.descanso, oracao: e.oracao || e.descanso,
    plano: e.louvor2 || e.descanso,   // fundo liso p/ timer/relógio (sem texto)
  };
}
const ESTILO_NOME = { limpo: 'Estilo Padrão', mapa: 'Estilo Mapa-múndi' };

// ---------- envio ----------
// canal que alcança a janela de projeção mesmo quando ela é uma janela PRÓPRIA do Sistema
const CANAL = (function () { try { return new BroadcastChannel('sistema-projecao'); } catch (e) { return null; } })();
if (CANAL) CANAL.onmessage = e => {   // mensagens vindas da janela de projeção
  const d = e.data; if (!d || !d.tipo) return;
  if (d.tipo === 'proj-pronta') setTimeout(() => { try { CANAL.postMessage(est.ultimo); } catch (_) {} }, 120);
  else if (d.tipo === 'cmd' && window.__cmdProj) window.__cmdProj(d.cmd);   // setas apertadas no telão
};
const nativo = () => !!(window.pywebview && window.pywebview.api);
function post(win, st) { if (win) try { win.postMessage(JSON.stringify(st), '*'); } catch (e) {} }
// o que a prévia do celular deve mostrar
function publicarTela(st) {
  if (!st) return;
  try { fetch('/api/tela', { method: 'POST', body: JSON.stringify(st) }); } catch (e) {}
}
function projetar(st) {
  est.aguardando = false;   // qualquer projeção nova cancela o "aguardando próximo" (reativado só no fim do louvor)
  if (st.modo !== 'bibmulti') est.juntos = false;   // sair de qualquer projeção que não seja "Juntos" desliga o modo
  st.estilo = est.estilo;
  est.ultimo = st;
  previews.forEach(w => post(w, st));
  // congelado: o celular tem que continuar mostrando o quadro PRESO no telão.
  // Publicar o novo aqui fazia a prévia mentir bem na hora em que ela é a única
  // forma de o operador saber o que a congregação está vendo.
  // congelado: não reenvia nada. O quadro preso já foi publicado uma vez pelo
  // toggleFreeze — reenviar a cada clique fazia o celular rebaixar o mesmo fundo
  // inteiro várias vezes por minuto, justo quando o operador mais mexe.
  if (!est.freeze) publicarTela(st);
  if (!est.freeze) {
    if (projWin && !projWin.closed) post(projWin, st);       // janela aberta pelo navegador
    if (CANAL && est.projetando) { try { CANAL.postMessage(st); } catch (e) {} }   // janela própria do Sistema
  }
  atualizarAgora();
}

// ---------- estados ----------
function stLouvor(idx, slide, fade) {
  const s = LOUVORES[idx], sl = s.slides[slide], prim = slide === 0;
  return {
    modo: 'louvor', fundo: prim ? FB.louvor1 : FB.louvor2,
    titulo: prim ? ((s.num ? s.num + ' - ' : '') + s.titulo) : '',
    label: sl.label, linhas: sl.linhas, tam: TAM_DEF.louvor, escala: est.escalaLouvor,
    // todos os slides do louvor usam o tamanho que serve pro maior deles (não "pula" de tamanho)
    linhasRef: s._maxL || (s._maxL = Math.max(...s.slides.map(x => x.linhas.length + (x.label ? 1 : 0)))),
    fim: slide === s.slides.length - 1,   // "fim" no cantinho do último slide (igual Glorifica)
    transicao: true, fade: fade ? 600 : 240,   // fade suave entre slides; um pouco maior no encerramento
  };
}
function stBiblia(ref, texto) {
  return { modo: 'biblia', fundo: FB.biblia, ref, linhas: [texto], tam: TAM_DEF.biblia, escala: est.escalaVers, transicao: true, fade: 400 };
}

// ---------- LOUVOR ----------
function projetarLouvor(idx, slide, fade) {
  est.louvorIdx = idx; est.louvorSlide = slide;
  est.live = { tipo: 'louvor', idx, slide };
  projetar(stLouvor(idx, slide, fade));
  marcarSlide();
}
function louvorProximo() {
  const s = LOUVORES[est.louvorIdx]; if (!s) return;
  if (est.louvorSlide < s.slides.length - 1) projetarLouvor(est.louvorIdx, est.louvorSlide + 1, false);
  else finalizarLouvor();   // acabou o louvor -> vai pra tela de espera; o PRÓXIMO "Avançar" engata o seguinte
}
// terminou o louvor: cai na tela de espera (descanso). Fica "aguardando" o próximo Avançar.
function finalizarLouvor() {
  descanso(true); est.aguardando = true; atualizarAgora();   // congelado continua congelado
}
function louvorAnterior() { if (est.louvorSlide > 0) projetarLouvor(est.louvorIdx, est.louvorSlide - 1, false); }

// tira acentos: procurar "coracao" acha "CORAÇÃO", e vice-versa
function semAcento(t) { return (t || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }
function renderListaLouvores(filtro) {
  const cont = $('#lista-louvores'); cont.innerHTML = '';
  const f = semAcento(filtro).trim();
  LOUVORES.forEach((s, i) => {
    if (f) {
      const noTit = (s._tit || (s._tit = semAcento(s.titulo))).includes(f) || (s.num && semAcento(s.num).includes(f));
      const naLetra = !noTit && (s._letra || (s._letra = semAcento(s.slides.map(x => x.linhas.join(' ')).join(' ')))).includes(f);
      if (!noTit && !naLetra) return;
      s._naLetra = !noTit && naLetra;
    }
    const naLista = est.fila.some(x => x.tipo === 'louvor' && x.chave === chaveLouvor(s));
    const d = document.createElement('div'); d.className = 'item' + (naLista ? ' na-lista' : ''); d.dataset.i = i;
    d.innerHTML = (naLista ? '<span class="marca-lista" title="Já está na lista de projeção">♪</span>' : '') +
      (s.num ? '<small>' + s.num + '</small>' : '') + s.titulo +
      (f && s._naLetra ? ' <small style="color:#6fa8dc">· letra</small>' : '');
    // o clique simples espera um tico: se vier o segundo clique, ele é cancelado
    // e o louvor só vai pra lista — sem piscar no telão
    d.onclick = () => { clearTimeout(d._t); d._t = setTimeout(() => selecionarLouvor(i), 230); };
    d.ondblclick = () => {
      clearTimeout(d._t);
      selecionarLouvor(i, true);      // só mostra os slides no painel; não projeta
      adicionarLista({ tipo: 'louvor', idx: i, chave: chaveLouvor(s), rotulo: (s.num ? s.num + ' · ' : '') + s.titulo });
    };
    cont.appendChild(d);
  });
}
// semProjetar: usado pelo duplo-clique, que só GUARDA na lista. Sem isso, montar
// a lista com a projeção aberta fazia a congregação ver os 4 louvores do culto
// desfilarem no telão antes de começar.
function selecionarLouvor(i, semProjetar) {
  est.setPos = -1;
  $$('#lista-louvores .item').forEach(e => e.classList.toggle('sel', +e.dataset.i === i));
  const s = LOUVORES[i];
  $('#tit-slides').textContent = (s.num ? s.num + ' · ' : '') + s.titulo;
  const cont = $('#lista-slides'); cont.innerHTML = '';
  s.slides.forEach((sl, k) => {
    const d = document.createElement('div'); d.className = 'item'; d.dataset.k = k;
    d.innerHTML = (sl.label ? '<small style="color:#f5d76e">' + sl.label + '</small><br>' : '') +
      sl.linhas.slice(0, 2).map(x => x.replace(/\u0001/g, '')).join('<br>') + (sl.linhas.length > 2 ? '…' : '');
    d.onclick = () => projetarLouvor(i, k, false);
    d.ondblclick = () => {   // 2 cliques no slide também manda o louvor pra lista
      const s2 = LOUVORES[i];
      adicionarLista({ tipo: 'louvor', idx: i, chave: chaveLouvor(s2), rotulo: (s2.num ? s2.num + ' · ' : '') + s2.titulo });
    };
    cont.appendChild(d);
  });
  if (!semProjetar) projetarLouvor(i, 0, false);
  else marcarSlide();
}
function marcarSlide() {
  $$('#lista-slides .item').forEach(e => e.classList.toggle('sel', +e.dataset.k === est.louvorSlide));
  const at = $('#lista-slides .item.sel'); if (at) at.scrollIntoView({ block: 'nearest' });
}

// ---------- BÍBLIA ----------
function renderLivros(filtro) {
  const cont = $('#lista-livros'); cont.innerHTML = '';
  const f = (filtro || '').toLowerCase().trim();
  BIBLIA.ordem.forEach(nome => {
    if (f && !nome.toLowerCase().includes(f)) return;
    const d = document.createElement('div'); d.className = 'item'; d.textContent = nome;
    d.onclick = () => selecionarLivro(nome, d);
    cont.appendChild(d);
  });
}
function selecionarLivro(nome, elDom) {
  est.livro = nome; est.cap = null;
  $$('#lista-livros .item').forEach(e => e.classList.remove('sel')); if (elDom) elDom.classList.add('sel');
  const caps = BIBLIA.livros[nome];
  const g = $('#grid-caps'); g.innerHTML = ''; $('#grid-vers').innerHTML = '<div class="vazio">Escolha um capítulo</div>';
  caps.forEach((_, i) => {
    const c = i + 1; const b = document.createElement('div'); b.className = 'gnum'; b.textContent = c;
    b.onclick = () => selecionarCap(c, b); g.appendChild(b);
  });
  $('#tit-caps').textContent = nome + ' — Capítulos';
}
function selecionarCap(c, elDom) {
  est.cap = c;
  $$('#grid-caps .gnum').forEach(e => e.classList.remove('sel')); if (elDom) elDom.classList.add('sel');
  const versObj = BIBLIA.livros[est.livro][c - 1];
  const nums = Object.keys(versObj).map(Number).sort((a, b) => a - b);
  const g = $('#grid-vers'); g.innerHTML = '';
  nums.forEach(v => {
    const b = document.createElement('div'); b.className = 'gnum'; b.dataset.v = v; b.textContent = v;
    b.title = versObj[v];
    b.onclick = () => { est.setPos = -1; projetarVerso(est.livro, c, v); };          // 1 clique = PROJETA
    b.ondblclick = () => { adicionarLista({ tipo: 'verso', ref: est.livro + ' ' + c + ':' + v, livro: est.livro, cap: c, v, on: true }); }; // 2 cliques = GUARDA
    g.appendChild(b);
  });
  $('#tit-vers').textContent = est.livro + ' ' + c + ' — 1 clique projeta · 2 cliques guarda na lista';
  marcarVersosNaFila();
}
// destaca no grid o versículo no ar (azul) e os que já estão na lista (contorno dourado)
function marcarVerso() {
  if (!est.bibPos || est.bibPos.livro !== est.livro || est.bibPos.cap !== est.cap) {
    $$('#grid-vers .gnum').forEach(e => e.classList.remove('sel')); return;
  }
  $$('#grid-vers .gnum').forEach(e => e.classList.toggle('sel', +e.dataset.v === est.bibPos.v));
}
function marcarVersosNaFila() {
  const na = new Set(est.fila.filter(x => x.tipo === 'verso' && x.livro === est.livro && x.cap === est.cap).map(x => x.v));
  $$('#grid-vers .gnum').forEach(e => e.classList.toggle('na-fila', na.has(+e.dataset.v)));
}
function projetarVerso(livro, cap, v) {
  const texto = BIBLIA.livros[livro] && BIBLIA.livros[livro][cap - 1] && BIBLIA.livros[livro][cap - 1][v];
  if (texto == null) return false;
  est.bibPos = { livro, cap, v }; est.live = { tipo: 'biblia' };
  projetar(stBiblia(livro + ' ' + cap + ':' + v, texto));
  renderFila(); marcarVerso();
  return true;
}
function versNums(livro, cap) { return Object.keys(BIBLIA.livros[livro][cap - 1]).map(Number).sort((a, b) => a - b); }
function bibliaProximo() {
  if (!est.bibPos) return; let { livro, cap, v } = est.bibPos;
  const caps = BIBLIA.livros[livro]; const nums = versNums(livro, cap); const i = nums.indexOf(v);
  if (i >= 0 && i < nums.length - 1) return projetarVerso(livro, cap, nums[i + 1]);       // próximo versículo
  if (cap < caps.length) return projetarVerso(livro, cap + 1, versNums(livro, cap + 1)[0]); // próximo capítulo
  const li = BIBLIA.ordem.indexOf(livro);                                                  // próximo livro
  if (li < BIBLIA.ordem.length - 1) { const p = BIBLIA.ordem[li + 1]; projetarVerso(p, 1, versNums(p, 1)[0]); }
}
function bibliaAnterior() {
  if (!est.bibPos) return; let { livro, cap, v } = est.bibPos;
  const nums = versNums(livro, cap); const i = nums.indexOf(v);
  if (i > 0) return projetarVerso(livro, cap, nums[i - 1]);
  if (cap > 1) { const n = versNums(livro, cap - 1); return projetarVerso(livro, cap - 1, n[n.length - 1]); }
  const li = BIBLIA.ordem.indexOf(livro);
  if (li > 0) { const p = BIBLIA.ordem[li - 1]; const c = BIBLIA.livros[p].length; const n = versNums(p, c); projetarVerso(p, c, n[n.length - 1]); }
}
// LISTA DE PROJEÇÃO (setlist): louvores (+) e versículos (Guardar), na ordem, um após o outro
function adicionarLista(item) {
  if (item.tipo === 'louvor' && est.fila.some(x => x.tipo === 'louvor' && x.chave === item.chave)) {
    toast('Esse louvor já está na lista.'); return;                    // não duplica
  }
  // o mesmo para versículo: com a lista rolada ele não via o item entrar, clicava
  // de novo, e no "Juntos" a congregação lia o mesmo texto duas vezes na tela
  if (item.tipo === 'verso' && est.fila.some(x => x.tipo === 'verso' &&
      x.livro === item.livro && x.cap === item.cap && x.v === item.v)) {
    toast('Esse versículo já está na lista.'); return;
  }
  est.fila.push(item); est.contAfter = 0;
  renderFila(); reprojetarVista();
  if (item.tipo === 'louvor') renderListaLouvores($('#busca-louvor').value);   // marca na lista da esquerda
  toast('Adicionado à lista de projeção.');
}
function guardarVerso() {
  if (!est.bibPos) { toast('Projete um versículo antes de guardá-lo.'); return; }
  const { livro, cap, v } = est.bibPos;
  adicionarLista({ tipo: 'verso', ref: livro + ' ' + cap + ':' + v, livro, cap, v, on: true });
}
function limparLista() { est.fila = []; est.setPos = -1; est.vistaFim = null; est.juntos = false; renderFila(); }
function versoTexto(x) { return (BIBLIA.livros[x.livro] && BIBLIA.livros[x.livro][x.cap - 1] && BIBLIA.livros[x.livro][x.cap - 1][x.v]) || ''; }
// NAVEGAÇÃO NORMAL: projeta UM item da lista por vez, na ordem que você montou
// A primeira linha entra na chave porque existem louvores DIFERENTES com o mesmo
// número e o mesmo título (7 pares no catálogo, ex. dois "MARANATA"). Sem ela a
// lista projetava o louvor errado e o outro nem podia ser adicionado.
function chaveLouvor(s) {
  return (s.num || '') + '|' + s.titulo + '|' + ((s.slides[0] && s.slides[0].linhas[0]) || '');
}
function idxDoItem(it) {   // resolve o índice pela CHAVE (o índice cru muda se você apagar um "Meu louvor")
  // Se a chave não acha mais, o louvor foi APAGADO. Devolver it.idx aqui fazia o
  // telão abrir um louvor completamente diferente, calado, no meio do culto.
  if (it.chave) return LOUVORES.findIndex(s => chaveLouvor(s) === it.chave);
  return it.idx;
}
function projetarItemLista(i, aoFim) {
  const it = est.fila[i]; if (!it) return;
  est.setPos = i; est.vistaFim = i; est.contAfter = 0; est.juntos = false;
  if (it.tipo === 'louvor') {
    const k = idxDoItem(it);
    if (k < 0 || !LOUVORES[k]) { toast('Este louvor não está mais disponível.'); renderFila(); return; }
    selecionarLouvor(k);
    // aoFim: chegando por Voltar, abre no último slide em vez de recomeçar
    if (aoFim) projetarLouvor(k, LOUVORES[k].slides.length - 1, false);
  }
  else projetarVerso(it.livro, it.cap, it.v);
  est.setPos = i; est.vistaFim = i; renderFila();
}
// JUNTOS: projeta os versículos MARCADOS (✓) juntos numa tela só; atualiza ao vivo ao marcar/reordenar
function projetarVersiculosJuntos() {
  const versos = est.fila.filter(x => x.tipo === 'verso' && x.on === true);
  if (!versos.length) { toast(est.fila.some(x => x.tipo === 'verso') ? 'Marque (✓) os versículos que devem aparecer juntos' : 'Adicione versículos (2 cliques) à lista'); return; }
  if (versos.length === 1) {                  // um só marcado -> versículo normal (não estica pra tela toda)
    const s = versos[0]; est.juntos = false; projetarVerso(s.livro, s.cap, s.v); return;
  }
  const itens = versos.map(x => ({ ref: x.livro + ' - ' + x.cap + ':' + x.v, texto: versoTexto(x) }));
  const u = versos[versos.length - 1]; est.bibPos = { livro: u.livro, cap: u.cap, v: u.v };   // continuar leitura após o último
  est.juntos = true; est.setPos = -1; est.vistaFim = null; est.contAfter = 0;
  est.live = { tipo: 'bibmulti', n: itens.length, ref: itens.length === 1 ? itens[0].ref.replace(' - ', ' ') : '' };
  projetar({ modo: 'bibmulti', fundo: FB.biblia, itens, tam: TAM_DEF.biblia, escala: est.escalaVers, transicao: true, fade: 400 });
  renderFila();
}
// Mexeu na lista com VERSÍCULO no ar -> o telão acompanha ao vivo.
// Com louvor, PowerPoint, cronômetro ou aviso no ar, NÃO: só organizar a lista
// (adicionar, reordenar, remover) arrancava o louvor do telão e jogava por cima
// os versículos guardados da leitura anterior, na frente da congregação.
function reprojetarVista() {
  const tipo = est.live && est.live.tipo;
  if (tipo !== 'biblia' && tipo !== 'bibmulti') return;
  const marcados = est.fila.filter(x => x.tipo === 'verso' && x.on === true).length;
  if (marcados) { projetarVersiculosJuntos(); return; }           // qualquer ✓ marcado já vai pro telão
  if (tipo === 'bibmulti' && est.bibPos) projetarVerso(est.bibPos.livro, est.bibPos.cap, est.bibPos.v);
}
function moverFila(i, d) {
  const j = i + d; if (j < 0 || j >= est.fila.length) return;
  const t = est.fila[i]; est.fila[i] = est.fila[j]; est.fila[j] = t;
  if (est.setPos === i) est.setPos = j; else if (est.setPos === j) est.setPos = i;
  est.vistaFim = est.setPos;                 // mantém o realce no item certo
  renderFila(); reprojetarVista();
}
function removerFila(i) {
  const eraOAtual = est.setPos === i;
  est.fila.splice(i, 1);
  if (est.setPos === i) est.setPos = est.fila.length ? Math.min(i, est.fila.length - 1) : -1;  // segue no item que assumiu a posição
  else if (est.setPos > i) est.setPos--;
  est.vistaFim = est.setPos;
  renderFila(); reprojetarVista();
  // Apagou justamente o item que estava no ar: o telão precisa concordar com o
  // realce. Sem isto ele continuava tocando o item apagado e o Avançar seguinte
  // PULAVA o próximo, que nunca era projetado.
  if (eraOAtual) {
    if (est.fila.length) projetarItemLista(est.setPos);
    else { est.setPos = -1; est.vistaFim = null; descanso(); }
  }
}
function soltarFila(to) {   // arrastar-e-soltar: move o item arrastado p/ a posição de destino
  if (dragFrom == null || dragFrom === to) { dragFrom = null; return; }
  const atual = est.setPos >= 0 ? est.fila[est.setPos] : null;
  const it = est.fila.splice(dragFrom, 1)[0];
  // o splice acima já encurtou a lista, então `to` sozinho é a posição certa.
  // Com o "to - 1" a última posição era inalcançável: o item parava sempre na
  // penúltima e ficava dançando no meio da lista.
  est.fila.splice(to, 0, it);
  if (atual) est.setPos = est.fila.indexOf(atual);
  est.vistaFim = est.setPos;
  dragFrom = null; renderFila(); reprojetarVista();
}
function renderFila() {
  const cont = $('#fila-itens'); if (!cont) { marcarVersosNaFila(); return; } cont.innerHTML = '';
  const vFim = est.vistaFim != null ? est.vistaFim : est.setPos;
  if (!est.fila.length) {
    cont.innerHTML = '<div class="vazio">Dê dois cliques em um louvor ou versículo para montar a lista.</div>';
  } else est.fila.forEach((it, i, arr) => {
    const antes = arr[i - 1];
    if (!antes || antes.tipo !== it.tipo) {          // separa visualmente louvores de versículos
      const t = document.createElement('div'); t.className = 'fila-grupo';
      t.textContent = it.tipo === 'louvor' ? 'Louvores' : 'Versículos';
      cont.appendChild(t);
    }
    const chkOn = it.on === true;                                   // marcado = entra na projeção "Juntos"
    const naVista = est.setPos >= 0 && i >= est.setPos && i <= vFim; // realça o item atual da navegação
    const d = document.createElement('div');
    d.className = 'fila-item' + (naVista ? ' atual' : '') + (chkOn ? ' agrupado' : '');   // ✓ = está no telão
    const rot = it.tipo === 'louvor' ? it.rotulo : it.ref;
    const chk = it.tipo === 'verso' ? '<span class="chk' + (chkOn ? ' on' : '') + '" title="Marcado = entra na projeção Juntos">' + (chkOn ? '✓' : '') + '</span>' : '';
    d.innerHTML = chk + '<span class="rot" style="color:' + (it.tipo === 'louvor' ? '#bfe6ff' : '#f5d76e') + '">' +
      (it.tipo === 'louvor' ? '♪ ' : '') + rot + '</span>' +
      '<span class="fila-btns"><button class="fb up" title="Subir">▲</button>' +
      '<button class="fb dn" title="Descer">▼</button><button class="fb x" title="Remover">✕</button></span>';
    // marcar o ✓ é um pedido EXPLÍCITO de projetar: vai pro telão mesmo com
    // louvor no ar (ao contrário de reordenar/remover, que só organizam)
    const cb = d.querySelector('.chk'); if (cb) cb.onclick = ev => {
      ev.stopPropagation(); it.on = it.on !== true; renderFila();
      if (est.fila.some(x => x.tipo === 'verso' && x.on === true)) projetarVersiculosJuntos();
      else reprojetarVista();
    };
    d.querySelector('.up').onclick = ev => { ev.stopPropagation(); moverFila(i, -1); };
    d.querySelector('.dn').onclick = ev => { ev.stopPropagation(); moverFila(i, +1); };
    d.querySelector('.x').onclick = ev => { ev.stopPropagation(); removerFila(i); };
    d.onclick = () => projetarItemLista(i);
    d.draggable = true;
    d.ondragstart = ev => { dragFrom = i; ev.dataTransfer.effectAllowed = 'move'; d.classList.add('arrastando'); };
    d.ondragend = () => { dragFrom = null; $$('.fila-item').forEach(e => e.classList.remove('arrastando', 'drop-alvo')); };
    d.ondragover = ev => { ev.preventDefault(); d.classList.add('drop-alvo'); };
    d.ondragleave = () => d.classList.remove('drop-alvo');
    d.ondrop = ev => { ev.preventDefault(); soltarFila(i); };
    cont.appendChild(d);
  });
  const fd = $('#fila-dica'); if (fd) fd.style.display = est.fila.some(x => x.tipo === 'verso') ? '' : 'none';
  // rola a caixa até o item que está no ar. Na janela da igreja só cabem 3 ou 4
  // linhas: a partir do 4º item o realce saía da vista e o operador perdia a
  // referência de onde estava na lista. 'nearest' mexe só na caixa, não na página.
  const atual = cont.querySelector('.fila-item.atual');
  if (atual) atual.scrollIntoView({ block: 'nearest' });
  marcarVersosNaFila();
}

// ---------- TIMER / RELÓGIO / TEXTO / FUNDOS ----------
let timerUI = null;
const fmt = ms => { const s = Math.max(0, Math.round(ms / 1000)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };
function iniciarTimer(min, rotulo) {
  est.timerFim = Date.now() + min * 60000; est.timerParadoMs = 0; est.timerRotulo = rotulo || 'Oração';
  est.live = { tipo: 'timer' };
  projetar({ modo: 'timer', fundo: FB.plano, rotulo: est.timerRotulo, fimTs: est.timerFim, transicao: true, fade: 500 });
  clearInterval(timerUI); timerUI = setInterval(() => { $('#timer-view').textContent = fmt(est.timerFim - Date.now()); }, 250);
}
function pausarTimer() {
  if (!est.timerFim) return; est.timerParadoMs = Math.max(0, est.timerFim - Date.now()); clearInterval(timerUI);
  projetar({ modo: 'timer', fundo: FB.plano, rotulo: est.timerRotulo, parado: true, texto: fmt(est.timerParadoMs) });
}
// Parar tem que APAGAR o tempo guardado: sem isso, encostar depois no botão
// "Pausar" ressuscitava o cronômetro antigo no telão, contando de onde parou.
function pararTimer() { clearInterval(timerUI); est.timerFim = 0; est.timerParadoMs = 0; descanso(); }
// Texto/Avisos: campo Título vira linha AMARELA; o texto vem branco embaixo. Projeta ao vivo.
function projetarTexto(instant) {
  const tit = ($('#texto-titulo') ? $('#texto-titulo').value : '').trim();
  const linhas = $('#texto-livre').value.split(String.fromCharCode(10)).map(s => s.trim()).filter(Boolean);
  if (tit) linhas.unshift('\u0001' + tit + '\u0001');
  est.live = { tipo: 'texto' };
  const fundo = est.textoFundo || (fundosLisos()[0] && fundosLisos()[0].arquivo) || FB.plano;
  projetar({ modo: 'texto', fundo, linhas, zona: zonaDoFundo(fundo), tam: est.tamTexto, escala: est.escalaTexto, transicao: !instant, fade: 400 });
}

// ---------- controles globais ----------
function temProximoNaLista() { return est.setPos >= 0 && est.setPos < est.fila.length - 1; }
function proximo() {
  if (est.aguardando) {                       // tela de espera logo após terminar um louvor
    if (temProximoNaLista()) { est.aguardando = false; projetarItemLista(est.setPos + 1); }
    else toast('Louvor concluído. Escolha o próximo — ou use Voltar para retomar o último slide.');
    return;                                   // NÃO consome o "aguardando" à toa: o Voltar continua valendo
  }
  // O que está NO AR manda. Sem isto, quem já tinha usado a Lista via o Avançar
  // sequestrar o telão: no meio do PowerPoint da Escola Bíblica pulava pro
  // próximo louvor, e com o cronômetro de oração na tela virava um versículo.
  const noAr = est.live && est.live.tipo;
  if (noAr === 'slide') { slideProximo(); return; }
  if (noAr === 'timer' || noAr === 'relogio' || noAr === 'texto' || noAr === 'fundo' || noAr === 'preto') return;
  if (est.setPos >= 0) {                      // navegando UM A UM pela LISTA (ordem que você montou)
    if (est.live && est.live.tipo === 'louvor') { louvorProximo(); return; }
    if (temProximoNaLista()) { projetarItemLista(est.setPos + 1); return; }   // PRÓXIMO item da lista
    if (est.bibPos) { est.contAfter++; bibliaProximo(); }                     // passou do último -> leitura contínua
    return;
  }
  if (!est.live) return;
  if (est.live.tipo === 'louvor') louvorProximo();
  else if (est.live.tipo === 'slide') slideProximo();
  else if (est.live.tipo === 'biblia' || est.live.tipo === 'bibmulti') bibliaProximo();
  else if (est.live.tipo === 'descanso' && est.louvorIdx >= 0) toast('Selecione o próximo louvor para continuar.');
}
function anterior() {
  if (est.aguardando || (est.live && est.live.tipo === 'descanso' && est.louvorIdx >= 0)) {
    est.aguardando = false; const s = LOUVORES[est.louvorIdx];               // volta pro último slide do louvor
    if (s) projetarLouvor(est.louvorIdx, s.slides.length - 1, false);
    return;
  }
  const noAr = est.live && est.live.tipo;      // o que está no ar manda (ver proximo())
  if (noAr === 'slide') { slideAnterior(); return; }
  if (noAr === 'timer' || noAr === 'relogio' || noAr === 'texto' || noAr === 'fundo' || noAr === 'preto') return;
  if (est.setPos >= 0) {
    // voltando pro louvor anterior, cai no ÚLTIMO slide dele — recomeçar do
    // slide 1 obrigava a apertar Avançar 5, 6 vezes na frente da congregação
    if (est.live && est.live.tipo === 'louvor') { if (est.louvorSlide > 0) louvorAnterior(); else if (est.setPos > 0) projetarItemLista(est.setPos - 1, true); return; }
    if (est.contAfter > 0) { est.contAfter--; if (est.contAfter === 0) projetarItemLista(est.setPos); else bibliaAnterior(); return; }
    if (est.setPos > 0) { projetarItemLista(est.setPos - 1, true); return; }  // item anterior (respeita a ordem que você montou)
    if (est.bibPos) { est.setPos = -1; renderFila(); bibliaAnterior(); }      // antes do primeiro escolhido -> segue voltando pelo capítulo
    return;
  }
  if (!est.live) return;
  if (est.live.tipo === 'louvor') louvorAnterior();
  else if (est.live.tipo === 'slide') slideAnterior();
  else if (est.live.tipo === 'biblia' || est.live.tipo === 'bibmulti') bibliaAnterior();
}
function esperaAtual() { return est.descansoFundo || FB.descanso; }
function definirEspera(arq) { est.descansoFundo = arq; Guardar.gravar('icm_espera', arq); }   // lembra ao fechar e abrir
// manterCongelado: usado quando a espera vem SOZINHA (fim do louvor). Descongelar
// ali quebrava o congelamento que o operador pediu justamente para preparar o
// próximo escondido — e a congregação via a tela trocar.
function descanso(manterCongelado) {
  // pedir a espera na mão é uma ordem para o telão OBEDECER: aí sim descongela
  if (est.freeze && !manterCongelado) { est.freeze = false; $('#btn-congelar').classList.remove('freeze-on'); }
  est.live = { tipo: 'descanso' };
  projetar({ modo: 'fundo', fundo: esperaAtual(), transicao: true, fade: 500 });
}
function preto() { est.live = { tipo: 'preto' }; projetar({ modo: 'preto', transicao: false }); }
function toggleFreeze() {
  if (!est.freeze) est.telaCongelada = est.ultimo;   // guarda o quadro que fica preso no telão
  est.freeze = !est.freeze;
  $('#btn-congelar').classList.toggle('freeze-on', est.freeze);
  if (!est.freeze) {
    if (projWin && !projWin.closed) post(projWin, est.ultimo);
    // faltava o CANAL: na janela própria do Sistema (o .exe) descongelar não
    // devolvia nada ao telão — ele ficava preso até a projeção seguinte
    if (CANAL && est.projetando) { try { CANAL.postMessage(est.ultimo); } catch (e) {} }
  }
  publicarTela(est.freeze ? est.telaCongelada : est.ultimo);
  atualizarProjBtn();
  toast(est.freeze ? 'Projeção congelada. Prepare o próximo com tranquilidade.' : 'Projeção ao vivo novamente.');
}
// re-projeta o que está no ar (usado ao mudar tamanho/estilo)
function reprojetarAtual() {
  const l = est.live; if (!l) return;
  if (l.tipo === 'louvor') projetarLouvor(est.louvorIdx, est.louvorSlide, false);
  else if (l.tipo === 'biblia') { if (est.bibPos) projetarVerso(est.bibPos.livro, est.bibPos.cap, est.bibPos.v); }
  else if (l.tipo === 'bibmulti') projetarVersiculosJuntos();
  else if (l.tipo === 'texto') projetarTexto(false);
}
// A-/A+ : fator de ESCALA sobre o auto-ajuste. Aumentar SEMPRE aumenta; diminuir SEMPRE diminui.
function ajustarTam(d) {
  const l = est.live; if (!l) return;
  const f = d > 0 ? 1.08 : 1 / 1.08;
  if (l.tipo === 'louvor') est.escalaLouvor = clamp(est.escalaLouvor * f, 0.5, 2.5);
  else if (l.tipo === 'biblia' || l.tipo === 'bibmulti') est.escalaVers = clamp(est.escalaVers * f, 0.5, 2.5);
  else if (l.tipo === 'texto') est.escalaTexto = clamp(est.escalaTexto * f, 0.5, 2.5);
  else return;
  reprojetarAtual();
}
function tamPadrao() {
  const l = est.live; if (!l) return;
  if (l.tipo === 'louvor') est.escalaLouvor = 1;
  else if (l.tipo === 'biblia' || l.tipo === 'bibmulti') est.escalaVers = 1;
  else if (l.tipo === 'texto') est.escalaTexto = 1; else return;
  reprojetarAtual();
}
function atualizarTamLabel() {
  const el = $('#tam-label'); if (!el) return; const l = est.live; let s;
  if (l && l.tipo === 'louvor') s = est.escalaLouvor;
  else if (l && (l.tipo === 'biblia' || l.tipo === 'bibmulti')) s = est.escalaVers;
  else if (l && l.tipo === 'texto') s = est.escalaTexto;
  else s = 1;                                    // nada aplicável: mostra "Padrão", não um traço solto
  el.textContent = Math.abs(s - 1) < 0.02 ? 'Padrão' : (s > 1 ? '+' : '') + Math.round((s - 1) * 100) + '%';
}

// ---------- estilo ----------
function trocarEstilo() {
  est.estilo = est.estilo === 'limpo' ? 'mapa' : 'limpo';
  aplicarEstilo(); renderFundos();
  $('#estilo-nome').textContent = ESTILO_NOME[est.estilo];
  const l = est.live;
  if (l && l.tipo === 'louvor') projetarLouvor(est.louvorIdx, est.louvorSlide, false);
  else if (l && l.tipo === 'biblia' && est.bibPos) projetarVerso(est.bibPos.livro, est.bibPos.cap, est.bibPos.v);
  else if (l && l.tipo === 'bibmulti') projetarVersiculosJuntos();
  else if (l && l.tipo === 'texto') projetarTexto(false);
  else if (l && l.tipo === 'descanso') descanso();
  else if (l && l.tipo === 'fundo') { /* fundo escolhido na galeria: não mexe */ }
  else if (est.ultimo && est.ultimo.fundo) projetar(Object.assign({}, est.ultimo, { fundo: FB[est.ultimo.modo === 'biblia' ? 'biblia' : 'plano'] }));
  toast(ESTILO_NOME[est.estilo]);
}

// ---------- projeção ----------
async function detectarTelas() {   // esforça-se ao máximo p/ achar a 2ª tela
  if (!('getScreenDetails' in window)) return { externa: null, permissao: 'indisponivel' };
  try {
    const sd = await window.getScreenDetails();
    const ext = sd.screens.find(s => s !== sd.currentScreen && !s.isInternal) || sd.screens.find(s => s !== sd.currentScreen) || null;
    return { externa: ext, permissao: 'ok' };
  } catch (e) { return { externa: null, permissao: 'negada' }; }
}
async function abrirProjecao() {
  if (nativo()) {                        // janela PRÓPRIA do Sistema (sem navegador)
    est.projetando = true; atualizarProjBtn();     // marca ANTES: a janela já vai nascer ao vivo
    let r = null;
    try { r = await window.pywebview.api.abrir_projecao(); } catch (e) {}
    setTimeout(() => { if (CANAL) try { CANAL.postMessage(est.ultimo); } catch (e) {} }, 900);
    if (r && r.externa) toast('Projetor detectado — projetando em tela cheia.');
    else avisoSemProjetor();                       // uma só tela: explica o que fazer
    return;
  }
  if (projWin && !projWin.closed) { projWin.focus(); return; }
  const info = await detectarTelas();
  let feats = 'width=1280,height=720,menubar=no,toolbar=no', naExterna = false;
  if (info.externa) {
    const a = info.externa;
    feats = `left=${a.availLeft},top=${a.availTop},width=${a.availWidth},height=${a.availHeight}`;
    naExterna = true;
  }
  projWin = window.open('projecao.html', 'projecaoICM', feats);
  if (!projWin) { toast('O navegador bloqueou a janela. Permita pop-ups e tente novamente.'); return; }
  est.projetando = true; atualizarProjBtn();
  telaAlvo = info.externa || null;   // a projeção pede tela cheia NESTA tela (API oficial, sem truque)
  setTimeout(() => {
    if (!projWin || projWin.closed) return;
    post(projWin, est.ultimo);
    post(projWin, { tipo: 'fullscreen', tela: naExterna ? 1 : 0 });
    if (naExterna) forcarTelaCheia();
  }, 700);
  if (naExterna) toast('Projetor detectado — projetando em tela cheia.');
  else mostrarAjudaProjecao(info);
}
// coloca a janela da projeção em tela cheia NA TELA DO PROJETOR (Window Management API)
let telaAlvo = null;
async function forcarTelaCheia() {
  if (!projWin || projWin.closed || !telaAlvo) return;
  try {
    const doc = projWin.document;
    if (doc && doc.documentElement.requestFullscreen) await doc.documentElement.requestFullscreen({ screen: telaAlvo });
  } catch (e) { /* alguns navegadores exigem o gesto dentro da própria janela — o duplo-clique resolve */ }
}
// as quatro janelinhas da tecla Windows (o quadrado sozinho não era reconhecível)
const LOGO_WIN = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true">' +
  '<path d="M2.4 5.1 10.3 4v7.5H2.4zM11.4 3.85 21.6 2.4v9.1h-10.2zM2.4 12.5h7.9V20L2.4 18.9zM11.4 12.5h10.2v9.1l-10.2-1.45z"/></svg>';
// janela própria, uma tela só: avisa e ensina, sem deixar a projeção "cair na cara" calada
function avisoSemProjetor() {
  const ov = document.createElement('div'); ov.className = 'ajuda-overlay';
  ov.innerHTML =
    '<div class="ajuda-box" style="max-width:440px">' +
      '<h3>Projetor não encontrado</h3>' +
      '<p>A projeção abriu <b>nesta tela</b> por enquanto.</p>' +
      '<p>Conecte o cabo do projetor (HDMI) e pressione ' +
        '<span class="teclas"><kbd class="win">' + LOGO_WIN + '<span>Windows</span></kbd>' +
        '<span class="mais">+</span><kbd>P</kbd></span>, escolhendo <b>Estender</b>.</p>' +
      '<p>Depois clique em <b>Procurar novamente</b> — a projeção vai sozinha para o projetor.</p>' +
      '<div class="ajuda-btns">' +
        '<button class="big-btn verde" id="aj-retry">Procurar novamente</button>' +
        '<button class="big-btn" id="aj-ok">Continuar assim</button>' +
      '</div></div>';
  document.body.appendChild(ov);
  ov.querySelector('#aj-ok').onclick = () => ov.remove();
  ov.onclick = e => { if (e.target === ov) ov.remove(); };
  ov.querySelector('#aj-retry').onclick = async () => {
    ov.remove();
    try { await window.pywebview.api.fechar_projecao(); } catch (e) {}
    est.projetando = false; atualizarProjBtn();
    setTimeout(abrirProjecao, 300);
  };
}
function mostrarAjudaProjecao(info) {
  const negada = info.permissao === 'negada';
  const ov = document.createElement('div'); ov.className = 'ajuda-overlay';
  ov.innerHTML =
    '<div class="ajuda-box" style="max-width:430px">' +
      '<h3>Projetor não encontrado</h3>' +
      (negada
        ? '<p>Para projetar automaticamente, o Sistema precisa da permissão de <b>gerenciamento de janelas</b>.</p>' +
          '<p>Clique no cadeado ao lado do endereço, conceda a permissão e procure novamente.</p>'
        : '<p>Conecte o cabo do projetor (HDMI) ao computador.</p>' +
          '<p>No teclado, pressione <span class="teclas"><kbd class="win">' + LOGO_WIN + '<span>Windows</span></kbd>' +
            '<span class="mais">+</span><kbd>P</kbd></span> e escolha <b>Estender</b>.</p>' +
          '<p>Depois, clique em <b>Procurar novamente</b> — a projeção será enviada automaticamente.</p>') +
      '<div class="ajuda-btns">' +
        '<button class="big-btn verde" id="aj-retry">Procurar novamente</button>' +
        '<button class="big-btn" id="aj-ok">Continuar assim</button>' +
      '</div>' +
    '</div>';
  document.body.appendChild(ov);
  ov.querySelector('#aj-ok').onclick = () => ov.remove();
  ov.querySelector('#aj-retry').onclick = async () => {
    ov.remove(); if (projWin && !projWin.closed) projWin.close();
    projWin = null; est.projetando = false; atualizarProjBtn(); await abrirProjecao();
  };
  ov.onclick = e => { if (e.target === ov) ov.remove(); };
}
function fecharProjecao() {
  descanso();   // volta pra tela de espera antes de fechar (nunca deixa a congregação vendo algo solto)
  if (nativo()) { try { window.pywebview.api.fechar_projecao(); } catch (e) {} }
  if (projWin && !projWin.closed) projWin.close();
  projWin = null; est.projetando = false; atualizarProjBtn();
}
function atualizarProjBtn() {
  const b = $('#btn-projecao'); b.classList.toggle('on', est.projetando);
  const noAr = est.projetando && !(est.live && est.live.tipo === 'descanso');
  b.innerHTML = (noAr ? '<span class="ico" data-i="descanso"></span> Parar de projetar'
                      : '<span class="ico" data-i="play"></span> ' + (est.projetando ? 'Em espera' : 'Abrir Projeção'));
  // "Em espera" NÃO é a mesma coisa que "Abrir Projeção": o telão já está ligado.
  // A dica dizia "Abrir a projeção no projetor" e o operador clicava esperando
  // religar alguma coisa — e nada acontecia.
  b.title = noAr ? 'Volta para a tela de espera (o telão continua ligado)'
                 : (est.projetando ? 'O telão já está ligado, na tela de espera'
                                   : 'Abrir a projeção no projetor');
  b.classList.toggle('on', est.projetando);   // ligado é ligado, mesmo em espera
  b.classList.toggle('em-espera', est.projetando && !noAr);
  window.Icones && window.Icones.aplicar(b);
  // estado INEQUÍVOCO: o operador precisa saber na hora se o que ele mexe vai pro telão
  const barra = $('#estado-barra'), selo = $('#prev-selo'), txt = $('#est-proj');
  const congelado = est.projetando && est.freeze;
  const emEspera = est.projetando && !congelado && est.live && est.live.tipo === 'descanso';
  const classe = congelado ? ' congelado' : (emEspera ? ' espera' : (est.projetando ? ' aovivo' : ''));
  barra.className = 'estado-barra' + classe;
  txt.textContent = congelado ? 'Congelado — o telão não muda'
    : (emEspera ? 'Em espera — nada sendo projetado' : (est.projetando ? 'Projetando ao vivo' : 'Projeção fechada'));
  if (selo) { selo.textContent = congelado ? 'Congelado' : (emEspera ? 'Em espera' : (est.projetando ? 'Ao vivo' : 'Prévia')); selo.className = 'prev-selo' + classe; }
  $('#dot').classList.toggle('on', est.projetando && !congelado);
  const bc = $('#btn-congelar');
  if (bc) bc.innerHTML = est.freeze ? '<span class="ico" data-i="congelar"></span> Descongelar' : '<span class="ico" data-i="congelar"></span> Congelar';
  window.Icones && bc && window.Icones.aplicar(bc);
}

// ---------- UI ----------
function atualizarAgora() {
  let t = 'Pronto.'; const l = est.live;
  // contador NA FRENTE: a tarja tem 327px e título com mais de ~44 letras comia
  // justamente o "slide 3/7" na reticência — a única coisa que diz quanto falta
  if (l && l.tipo === 'louvor') { const s = LOUVORES[l.idx]; t = 'Slide ' + (l.slide + 1) + '/' + s.slides.length + (l.fim ? ' (fim)' : '') + ' — ' + s.titulo; }
  else if (l && l.tipo === 'biblia' && est.bibPos) t = est.bibPos.livro + ' ' + est.bibPos.cap + ':' + est.bibPos.v;
  else if (l && l.tipo === 'bibmulti') t = l.n === 1 ? (l.ref || '1 versículo') : l.n + ' versículos juntos';
  else if (l && l.tipo === 'timer') t = 'Timer — ' + est.timerRotulo;
  else if (l && l.tipo === 'relogio') t = 'Relógio';
  else if (l && l.tipo === 'texto') t = 'Texto livre';
  else if (l && l.tipo === 'slide') t = 'Slide ' + (l.i + 1) + '/' + l.n + (SLIDES.nome ? ' — ' + SLIDES.nome : '');
  else if (l && l.tipo === 'fundo') t = 'Fundo';
  else if (l && l.tipo === 'descanso') t = est.aguardando ? 'Fim do louvor — "Avançar" chama o próximo' : 'Descanso (Maranata)';
  else if (l && l.tipo === 'preto') t = 'Tela preta';
  $('#agora').textContent = t;
  atualizarTamLabel();
  atualizarProjBtn();   // a barra de estado acompanha o CONTEÚDO, não só abrir/fechar
}
function toast(m) { const t = $('#toast'); t.textContent = m; t.classList.add('show'); clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove('show'), 1800); }
function trocarAba(aba) { est.aba = aba; $$('.tab').forEach(t => t.classList.toggle('ativo', t.dataset.aba === aba)); $$('.view').forEach(v => v.classList.toggle('ativo', v.dataset.aba === aba)); }

function listaFundos() {
  return [{ arquivo: FB.descanso, nome: 'Descanso (Maranata)', cat: 'Cultos' },
          { arquivo: FB.oracao, nome: 'Silêncio e Oração', cat: 'Oração' },
          { arquivo: FB.plano, nome: 'Fundo liso', cat: 'Base', liso: true }]
    .concat(GALERIA).concat(CUSTOM.map(f => Object.assign({ cat: 'Meus fundos', liso: true }, f)))
    .filter(f => !OCULTOS.includes(f.arquivo));
}
function categoriasFundo() {
  const ordem = ['Cultos', 'Lema do ano', 'Senhoras', 'Oração', 'Boas-vindas', 'Avisos', 'Base', 'Meus fundos'];
  const tem = {}; listaFundos().forEach(f => tem[f.cat || 'Base'] = true);
  return ['Todos'].concat(ordem.filter(c => tem[c]));
}
function renderFundos() {
  const g = $('#grid-fundos'); g.innerHTML = '';
  // abas de categoria (Cultos, Senhoras, Lema do ano…)
  const cg = $('#fundo-cats');
  if (cg) {
    cg.innerHTML = '';
    categoriasFundo().forEach(c => {
      const b = document.createElement('button'); b.className = 'fcat' + (c === est.fundoCat ? ' on' : '');
      b.textContent = c; b.onclick = () => { est.fundoCat = c; renderFundos(); };
      cg.appendChild(b);
    });
  }
  listaFundos().filter(f => est.fundoCat === 'Todos' || (f.cat || 'Base') === est.fundoCat).forEach(f => {
    const eEspera = f.arquivo === esperaAtual();
    const c = document.createElement('div'); c.className = 'fundo-card' + (eEspera ? ' espera' : '');
    c.innerHTML = '<img src="' + f.arquivo + '" alt="">' +
      (eEspera ? '<span class="badge-espera">★ Espera</span>' : '') +
      '<div class="fundo-acoes">' +
        (eEspera ? '' : '<button class="fa fa-espera" title="Definir como tela de espera padrão">Espera</button>') +
        '<button class="fa fa-del" title="Apagar este fundo">✕</button>' +
      '</div><span class="nome">' + f.nome + '</span>';
    const projetarFundo = () => { est.live = { tipo: 'fundo' }; projetar({ modo: 'fundo', fundo: f.arquivo, transicao: true, fade: 500 }); toast('Fundo: ' + f.nome); };
    c.querySelector('img').onclick = projetarFundo; c.querySelector('.nome').onclick = projetarFundo;
    const sb = c.querySelector('.fa-espera'); if (sb) sb.onclick = ev => { ev.stopPropagation(); definirEspera(f.arquivo); renderFundos(); toast('Tela de espera: ' + f.nome); };
    c.querySelector('.fa-del').onclick = ev => { ev.stopPropagation(); apagarFundo(f); };
    g.appendChild(c);
  });
  const add = document.createElement('div'); add.className = 'fundo-card add-card';
  add.innerHTML = '<div class="add-inner"><span class="plus">+</span><span>Adicionar fundo</span></div>';
  add.onclick = mostrarAddFundo; g.appendChild(add);
  renderFundosLiso();
}
// só telas LISAS (boas pra escrever em cima) — não mostra a Maranata/descanso que é cheia de informação
// só telas onde dá pra escrever por cima (marcadas como "liso" na inspeção visual dos fundos)
// zona: 'barra' = o fundo já tem faixa no topo -> o texto entra ABAIXO dela; 'livre' = tela toda
function fundosLisos() {
  return [{ arquivo: FB.plano, nome: 'Fundo liso', zona: 'livre' },
          { arquivo: FB.biblia, nome: 'Fundo Bíblia', zona: 'barra' }]
    .concat(GALERIA.filter(f => f.liso)).concat(CUSTOM)
    .filter(f => !OCULTOS.includes(f.arquivo));
}
function zonaDoFundo(arq) {
  const f = fundosLisos().find(x => x.arquivo === arq);
  if (f && f.zona) return f.zona;
  return /biblia|avisos|barra|louvor|primeiro/i.test(arq || '') ? 'barra' : 'livre';
}
function renderFundosLiso() {
  const g = $('#fundos-liso'); if (!g) return; g.innerHTML = '';
  const lista = fundosLisos();
  if (est.textoFundo == null && lista[0]) est.textoFundo = lista[0].arquivo;
  lista.forEach(f => {
    const c = document.createElement('div'); c.className = 'liso-card' + (f.arquivo === est.textoFundo ? ' sel' : '');
    c.innerHTML = '<img src="' + f.arquivo + '" alt=""><span>' + f.nome + '</span>';
    c.onclick = () => { est.textoFundo = f.arquivo; renderFundosLiso(); if (est.live && est.live.tipo === 'texto') projetarTexto(false); };
    g.appendChild(c);
  });
}
// ================= SLIDES (PowerPoint / PDF) =================
let SLIDES = [];   // {nome, lista:[url]}
function statusSlides(txt, erro) { const e = $('#sl-status'); if (e) { e.textContent = txt || ''; e.className = 'sl-status' + (erro ? ' erro' : ''); } }
async function abrirApresentacao() {
  statusSlides('Escolhendo o arquivo…');
  try {
    const r1 = nativo() ? await window.pywebview.api.escolher()
                        : await fetch('/api/escolher', { method: 'POST' }).then(r => r.json());
    if (!r1.ok || !r1.caminho) { statusSlides(''); return; }
    statusSlides('Convertendo a apresentação… isso leva alguns segundos.');
    const r2 = nativo() ? await window.pywebview.api.importar(r1.caminho)
                        : await fetch('/api/importar', { method: 'POST', body: JSON.stringify({ caminho: r1.caminho }) }).then(r => r.json());
    if (!r2.ok) { statusSlides(r2.erro || 'Não foi possível abrir este arquivo.', true); return; }
    SLIDES = { nome: r2.nome, lista: r2.slides };
    est.slidePos = -1;
    renderSlides(); statusSlides(r2.slides.length + ' slides prontos — clique em um para projetar.');
  } catch (e) {
    statusSlides('Esta função precisa do Sistema aberto pelo atalho (não pelo navegador).', true);
  }
}
function renderSlides() {
  const g = $('#sl-grade'); if (!g) return; g.innerHTML = '';
  if (!SLIDES.lista || !SLIDES.lista.length) return;
  SLIDES.lista.forEach((src, i) => {
    const c = document.createElement('div'); c.className = 'sl-card' + (est.slidePos === i ? ' sel' : '');
    c.innerHTML = '<img src="' + src + '" alt=""><span>' + (i + 1) + '</span>';
    c.onclick = () => projetarSlide(i);
    g.appendChild(c);
  });
}
function projetarSlide(i) {
  if (!SLIDES.lista || !SLIDES.lista[i]) return;
  est.slidePos = i; est.live = { tipo: 'slide', i, n: SLIDES.lista.length };
  projetar({ modo: 'fundo', fundo: SLIDES.lista[i], transicao: true, fade: 260 });
  renderSlides();
  const at = $('#sl-grade .sl-card.sel'); if (at) at.scrollIntoView({ block: 'nearest' });
}
function slideProximo() { if (SLIDES.lista && est.slidePos < SLIDES.lista.length - 1) projetarSlide(est.slidePos + 1); }
function slideAnterior() { if (SLIDES.lista && est.slidePos > 0) projetarSlide(est.slidePos - 1); }

// ================= MENU ☰ CONFIGURAÇÕES =================
const DIAS_NOME = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];
// cultos padrão da ICM (o usuário liga/desliga e ajusta horário conforme a igreja dele)
const CULTOS_PADRAO = [
  { dia: 0, nome: 'Escola Bíblica Dominical', hora: '10:00', on: true },
  { dia: 0, nome: 'Culto Evangelístico', hora: '19:00', on: true },
  { dia: 1, nome: 'Culto de Glorificação', hora: '19:30', on: false },
  { dia: 2, nome: 'Culto de Doutrina', hora: '19:30', on: false },
  { dia: 3, nome: 'Culto de Senhoras', hora: '19:30', on: true },
  { dia: 4, nome: 'Culto de Oração', hora: '19:30', on: true },
  { dia: 4, nome: 'Madrugada', hora: '06:00', on: true },
  { dia: 5, nome: 'Culto no Lar', hora: '19:30', on: true },
  { dia: 6, nome: 'Culto de Doutrina', hora: '19:30', on: true },
  { dia: 6, nome: 'Madrugada', hora: '06:00', on: true },
];
let IGREJA = { nome: '', endereco: '', cultos: null };
let MEUS = [];   // louvores que o usuário adicionou
function carregarDadosUsuario() {
  est.descansoFundo = Guardar.ler('icm_espera', null);   // a tela de espera que você escolheu continua valendo
  IGREJA = Object.assign({ nome: '', endereco: '', cultos: null }, Guardar.ler('icm_igreja', {}) || {});
  MEUS = Guardar.ler('icm_meus_louvores', []) || [];
  CUSTOM = Guardar.ler('icm_fundos', []) || [];
  OCULTOS = Guardar.ler('icm_ocultos', []) || [];
  if (!IGREJA.cultos) IGREJA.cultos = CULTOS_PADRAO.map(c => Object.assign({}, c));
}
carregarDadosUsuario();
function salvarIgreja() { Guardar.gravar('icm_igreja', IGREJA); }
function salvarMeus() { Guardar.gravar('icm_meus_louvores', MEUS); }

function abrirMenu() {
  $('#menu-overlay').classList.remove('oculto');
  menuSecao('inicio');   // abre calmo, na tela de início (não no editor)
  const m = $('#ini-marca'); if (m && window.Icones) m.innerHTML = window.Icones.MARCA(52);
  const ig = $('#ini-igreja'); if (ig) ig.textContent = IGREJA.nome || 'Projeção para a sua igreja';
  renderMeus(); renderCultos(); renderAvisos(); mostrarRede();
}
// endereço + QR para o celular entrar
async function mostrarRede() {
  const u = $('#cel-url'), q = $('#cel-qr'); if (!u) return;
  try {
    const r = await fetch('/api/rede').then(r => r.json());
    u.textContent = r.url || '—';
    q.innerHTML = r.qr ? '<img src="' + r.qr + '" alt="Código para o celular">' : '<span class="cel-semqr">—</span>';
    const c = $('#cel-copiar');
    if (c) c.onclick = () => { try { navigator.clipboard.writeText(r.url); toast('Endereço copiado.'); } catch (e) {} };
  } catch (e) { u.textContent = 'Indisponível'; }
}
function fecharMenu() { $('#menu-overlay').classList.add('oculto'); }
function menuSecao(sec) {
  $$('.menu-aba').forEach(b => b.classList.toggle('ativo', b.dataset.sec === sec));
  $$('.menu-sec').forEach(s => s.classList.toggle('ativo', s.dataset.sec === sec));
}
// ---- editor de louvores ----
function parseLetra(txt) {
  return txt.split(/\n\s*\n/).map(bloco => {
    const linhas = []; let label = '';
    bloco.split('\n').map(s => s.trim()).filter(Boolean).forEach(l => {
      const m = l.match(/^(CORO|FINAL|BIS)\s*:?\s*$/i);
      if (m && !label) label = m[1].toUpperCase(); else linhas.push(l.toUpperCase());
    });
    return linhas.length ? { label, linhas } : null;
  }).filter(Boolean);
}
function salvarLouvorEditor() {
  const tit = $('#ed-titulo').value.trim(), letra = $('#ed-letra').value.trim();
  if (!tit) { toast('Informe o título do louvor.'); return; }
  if (!letra) { toast('Informe a letra do louvor.'); return; }
  const slides = parseLetra(letra);
  if (!slides.length) { toast('Não foi possível interpretar a letra.'); return; }
  const num = ($('#ed-num').value.trim() || 'MEU').toUpperCase();
  const idx = $('#ed-salvar').dataset.editando;
  const novo = { titulo: tit.toUpperCase(), num, col: 'Meus louvores', slides, meu: true };
  if (idx != null && idx !== '') { MEUS[+idx] = novo; delete $('#ed-salvar').dataset.editando; }
  else MEUS.push(novo);
  salvarMeus(); recarregarLouvores(); renderMeus(); limparEditor();
  toast('Louvor salvo.');
}
function limparEditor() { $('#ed-num').value = ''; $('#ed-titulo').value = ''; $('#ed-letra').value = ''; delete $('#ed-salvar').dataset.editando; }
function renderMeus() {
  const c = $('#ed-lista'); if (!c) return; c.innerHTML = '';
  if (!MEUS.length) { c.innerHTML = '<div class="vazio">Nenhum ainda.</div>'; return; }
  MEUS.forEach((s, i) => {
    const d = document.createElement('div'); d.className = 'ed-item';
    d.innerHTML = '<span>' + (s.num ? '<small>' + s.num + '</small> ' : '') + s.titulo + '</span>' +
      '<span class="ed-btns"><button class="fb edit" title="Editar">✎</button><button class="fb x" title="Apagar">✕</button></span>';
    d.querySelector('.edit').onclick = () => {
      $('#ed-num').value = s.num === 'MEU' ? '' : s.num; $('#ed-titulo').value = s.titulo;
      $('#ed-letra').value = s.slides.map(sl => (sl.label ? sl.label + '\n' : '') + sl.linhas.join('\n')).join('\n\n');
      $('#ed-salvar').dataset.editando = i; menuSecao('louvores');
    };
    d.querySelector('.x').onclick = () => { MEUS.splice(i, 1); salvarMeus(); recarregarLouvores(); renderMeus(); toast('Louvor removido.'); };
    c.appendChild(d);
  });
}
function recarregarLouvores() {
  LOUVORES.length = BASE_LOUVORES.length;
  for (let i = 0; i < BASE_LOUVORES.length; i++) LOUVORES[i] = BASE_LOUVORES[i];
  MEUS.forEach(m => LOUVORES.push(m));
  renderListaLouvores($('#busca-louvor').value);
}
// ---- minha igreja ----
function renderCultos() {
  const c = $('#ig-cultos'); if (!c) return; c.innerHTML = '';
  $('#ig-nome').value = IGREJA.nome || ''; $('#ig-endereco').value = IGREJA.endereco || '';
  for (let dia = 0; dia < 7; dia++) {
    const doDia = IGREJA.cultos.filter(x => x.dia === dia);
    if (!doDia.length) continue;
    const bloco = document.createElement('div'); bloco.className = 'ig-dia';
    bloco.innerHTML = '<h4>' + DIAS_NOME[dia] + '</h4>';
    doDia.forEach(cul => {
      const linha = document.createElement('label'); linha.className = 'ig-linha';
      linha.innerHTML = '<input type="checkbox"' + (cul.on ? ' checked' : '') + '><span>' + cul.nome + '</span>' +
        '<input type="time" value="' + cul.hora + '">';
      linha.querySelector('input[type=checkbox]').onchange = e => { cul.on = e.target.checked; salvarIgreja(); renderAvisos(); marcarSalvo(); };
      linha.querySelector('input[type=time]').onchange = e => { cul.hora = e.target.value; salvarIgreja(); renderAvisos(); marcarSalvo(); };
      bloco.appendChild(linha);
    });
    c.appendChild(bloco);
  }
}
// selo estável "Salvo" — o operador precisa ter certeza, não só um popup que some
function marcarSalvo() {
  const el = $('#ig-salvo'); if (!el) return;
  el.textContent = '✓ Salvo automaticamente';
  el.classList.add('on'); clearTimeout(marcarSalvo._t);
  marcarSalvo._t = setTimeout(() => el.classList.remove('piscar'), 60);
  el.classList.add('piscar');
}
// ---- avisos (modelos + automático pelo dia) ----
function cultosDoDia(dia) { return IGREJA.cultos.filter(c => c.dia === dia && c.on); }
// PRÓXIMO culto a partir de AGORA: se ainda há culto hoje (ex.: de manhã na EBD, o da noite), avisa esse
function avisoProximo() {
  const agora = new Date(), hoje = agora.getDay(), minAgora = agora.getHours() * 60 + agora.getMinutes();
  const emMin = h => { const [a, b] = (h || '00:00').split(':').map(Number); return a * 60 + (b || 0); };
  const restamHoje = cultosDoDia(hoje).filter(c => emMin(c.hora) > minAgora + 20).sort((a, b) => emMin(a.hora) - emMin(b.hora));
  if (restamHoje.length) return { titulo: 'HOJE', corpo: restamHoje.map(c => c.nome + ' — ' + c.hora).join('\n') };
  for (let d = 1; d <= 7; d++) {                     // senão, o próximo dia que tiver culto
    const dia = (hoje + d) % 7, lista = cultosDoDia(dia);
    if (lista.length) {
      const quando = d === 1 ? 'AMANHÃ — ' + DIAS_NOME[dia].toUpperCase() : DIAS_NOME[dia].toUpperCase();
      return { titulo: quando, corpo: lista.map(c => c.nome + ' — ' + c.hora).join('\n') };
    }
  }
  return { titulo: 'AVISO', corpo: 'Que Deus abençoe a todos!' };
}
function avisoSemana() {
  const l = [];
  for (let d = 0; d < 7; d++) cultosDoDia(d).forEach(c => l.push(DIAS_NOME[d] + ' — ' + c.hora + ' — ' + c.nome));
  return { titulo: 'CULTOS DA SEMANA', corpo: l.join('\n') };
}
function modelosAviso() {
  return [
    { nome: 'Próximo culto', auto: true, faz: avisoProximo },
    { nome: 'Cultos da semana', auto: true, faz: avisoSemana },
    { nome: 'Aniversariantes', faz: () => ({ titulo: 'ANIVERSARIANTES', corpo: 'Vamos orar pelos irmãos que fazem aniversário nesta semana.' }) },
    { nome: 'Santa Ceia', faz: () => ({ titulo: 'SANTA CEIA', corpo: (cultosDoDia(1)[0] ? 'Segunda-feira — ' + cultosDoDia(1)[0].hora : 'Segunda-feira') + '\nParticipemos todos!' }) },
    { nome: 'Bem-vindos', faz: () => ({ titulo: 'SEJAM BEM-VINDOS', corpo: (IGREJA.nome || 'Igreja Cristã Maranata') + '\nA paz do Senhor!' }) },
    { nome: 'Silêncio e oração', faz: () => ({ titulo: 'MOMENTO DE ORAÇÃO', corpo: 'Pedimos silêncio e reverência.' }) },
    { nome: 'Desligue o celular', faz: () => ({ titulo: 'ATENÇÃO', corpo: 'Por favor, desligue ou silencie o celular.' }) },
  ];
}
function renderAvisos() {
  const c = $('#av-lista'); if (!c) return; c.innerHTML = '';
  modelosAviso().forEach(m => {
    const d = document.createElement('button'); d.className = 'av-chip' + (m.auto ? ' auto' : '');
    d.textContent = m.nome; d.title = 'Preenche: ' + m.faz().titulo;
    d.onclick = () => {
      const a = m.faz();
      $('#texto-titulo').value = a.titulo; $('#texto-livre').value = a.corpo;
      trocarAba('texto'); projetarTexto(false); toast('Aviso preenchido. Ajuste se desejar e projete.');
    };
    c.appendChild(d);
  });
}
// ---- resets ----
const RESET_TXT = {
  fundos: 'Restaurar os fundos originais e apagar os que você adicionou?',
  tamanhos: 'Voltar todos os tamanhos de letra ao padrão?',
  louvores: 'Apagar TODOS os louvores que você adicionou? (a coletânea original continua)',
  slides: 'Apagar todas as apresentações já importadas?',
  tudo: 'Devolver o Sistema ao estado de fábrica? Você verá a apresentação inicial de novo.',
};
function resetar(o) { confirmar(RESET_TXT[o] || 'Restaurar?', () => aplicarReset(o)); }
function aplicarReset(o) {
  if (o === 'fundos' || o === 'tudo') { CUSTOM = []; OCULTOS = []; salvarCustom(); salvarOcultos(); est.descansoFundo = null; est.textoFundo = null; renderFundos(); }
  if (o === 'tamanhos' || o === 'tudo') { est.escalaLouvor = est.escalaVers = est.escalaTexto = 1; atualizarTamLabel(); }
  if (o === 'louvores' || o === 'tudo') { MEUS = []; salvarMeus(); recarregarLouvores(); renderMeus(); }
  if (o === 'slides' || o === 'tudo') {   // apaga as apresentações importadas
    SLIDES = []; est.slidePos = -1; renderSlides(); statusSlides('');
    try { fetch('/api/limpar', { method: 'POST' }); } catch (e) {}
  }
  if (o === 'tudo') {
    IGREJA = { nome: '', endereco: '', cultos: CULTOS_PADRAO.map(c => Object.assign({}, c)) };
    salvarIgreja(); aplicarNomeIgreja(); renderCultos(); renderAvisos();
    est.estilo = 'limpo'; aplicarEstilo(); $('#estilo-nome').textContent = ESTILO_NOME[est.estilo];
    Guardar.gravar('icm_bemvindo_ok', false);
    fecharMenu(); abrirBemVindo(true); return;   // volta pro começo, como um sistema novo
  }
  toast('Configurações restauradas ao padrão.');
}
// caixa de confirmação (nada destrutivo acontece sem o operador confirmar)
function confirmar(msg, aoConfirmar) {
  const ov = document.createElement('div'); ov.className = 'ajuda-overlay';
  ov.innerHTML = '<div class="ajuda-box" style="max-width:430px"><h3>Confirmar</h3><p>' + msg + '</p>' +
    '<div class="ajuda-btns"><button class="big-btn vermelho" id="cf-sim">Sim, restaurar</button>' +
    '<button class="big-btn" id="cf-nao">Cancelar</button></div></div>';
  document.body.appendChild(ov);
  ov.querySelector('#cf-nao').onclick = () => ov.remove();
  ov.onclick = e => { if (e.target === ov) ov.remove(); };
  ov.querySelector('#cf-sim').onclick = () => { ov.remove(); aoConfirmar(); };
}
// ================= BOAS-VINDAS (primeira vez / ☰ > Sistema) =================
const BV_PASSOS = [
  { tit: 'Bem-vindo ao Sistema', sub: 'A projeção da sua igreja, simples de operar.',
    html: '<div class="bv-marca" id="bv-marca"></div>' +
      '<p class="bv-verso">“Escreve a visão e torna-a bem legível sobre tábuas, para que a possa ler quem passa correndo.”<span>Habacuque 2:2</span></p>' +
      '<p>Em poucos passos você vê como tudo funciona. Se preferir, pode pular e começar direto.</p>' },
  { tit: 'Louvores', sub: 'Toda a coletânea, na hora.',
    html: '<ul class="bv-lista">' +
      '<li><b>Um clique</b> no louvor já mostra os slides.</li>' +
      '<li><b>Dois cliques</b> mandam ele para a Lista de projeção.</li>' +
      '<li>Procure por <b>número, nome ou um trecho da letra</b>.</li>' +
      '<li>A letra <b>se ajusta sozinha</b> para caber na tela.</li></ul>' },
  { tit: 'Bíblia', sub: 'Do versículo ao capítulo inteiro.',
    html: '<ul class="bv-lista">' +
      '<li><b>Um clique</b> no versículo projeta na hora.</li>' +
      '<li><b>Dois cliques</b> guardam ele na Lista de projeção.</li>' +
      '<li><b>Avançar</b> segue a ordem que você montou e depois continua sozinho pelo capítulo.</li>' +
      '<li>Marque o <b>✓</b> dos versículos na Lista e eles aparecem <b>juntos</b> numa tela só.</li></ul>' },
  { tit: 'Durante o culto', sub: 'Você sempre sabe o que está no telão.',
    html: '<ul class="bv-lista">' +
      '<li>A <b>faixa vermelha</b> avisa quando está <b>AO VIVO</b>.</li>' +
      '<li><b>Congelar</b> segura a imagem para você preparar o próximo sem ninguém ver.</li>' +
      '<li><b>Parar de projetar</b> (ou a tecla <b>P</b>) volta para a tela de espera.</li>' +
      '<li>As <b>setas do teclado</b> avançam e voltam.</li></ul>' },
  { tit: 'Sua igreja', sub: 'Para os avisos saírem prontos.', igreja: true,
    html: '<p>Diga o nome da sua igreja e marque os cultos. O Sistema monta os avisos do dia sozinho.</p>' },
];
let bvPasso = 0;
function abrirBemVindo(forcado) {
  if (!forcado && Guardar.ler('icm_bemvindo_ok', false)) return false;
  bvPasso = 0; $('#bemvindo').classList.remove('oculto'); renderBV(); return true;
}
function fecharBemVindo() {
  Guardar.gravar('icm_bemvindo_ok', true);
  $('#bemvindo').classList.add('oculto');
}
function renderBV() {
  const p = BV_PASSOS[bvPasso], ultimo = bvPasso === BV_PASSOS.length - 1;
  $('#bv-passos').innerHTML = BV_PASSOS.map((_, i) => '<span class="bv-ponto' + (i === bvPasso ? ' on' : '') + '"></span>').join('');
  $('#bv-corpo').innerHTML = '<h2>' + p.tit + '</h2><p class="bv-sub">' + p.sub + '</p>' + p.html +
    (p.igreja ? '<div class="bv-igreja"><input type="text" id="bv-nome" placeholder="Nome da igreja (ex.: ICM Iperó)">' +
      '<div class="bv-cultos" id="bv-cultos"></div></div>' : '');
  const m = $('#bv-marca'); if (m && window.Icones) m.innerHTML = window.Icones.MARCA(74);
  if (p.igreja) {
    $('#bv-nome').value = IGREJA.nome || '';
    $('#bv-nome').oninput = e => { IGREJA.nome = e.target.value; };
    const c = $('#bv-cultos');
    for (let dia = 0; dia < 7; dia++) {
      const doDia = IGREJA.cultos.filter(x => x.dia === dia); if (!doDia.length) continue;
      const b = document.createElement('div'); b.className = 'bv-dia'; b.innerHTML = '<h4>' + DIAS_NOME[dia] + '</h4>';
      doDia.forEach(cul => {
        const l = document.createElement('label'); l.className = 'ig-linha';
        l.innerHTML = '<input type="checkbox"' + (cul.on ? ' checked' : '') + '><span>' + cul.nome + '</span><input type="time" value="' + cul.hora + '">';
        l.querySelector('input[type=checkbox]').onchange = e => { cul.on = e.target.checked; };
        l.querySelector('input[type=time]').onchange = e => { cul.hora = e.target.value; };
        b.appendChild(l);
      });
      c.appendChild(b);
    }
  }
  $('#bv-voltar').style.visibility = bvPasso === 0 ? 'hidden' : 'visible';
  $('#bv-avancar').textContent = ultimo ? 'Iniciar o Sistema' : 'Continuar';
  $('#bv-pular').textContent = ultimo ? 'Deixar para depois' : 'Pular apresentação';
}
function bvAvancar() {
  if (bvPasso < BV_PASSOS.length - 1) { bvPasso++; renderBV(); return; }
  salvarIgreja(); aplicarNomeIgreja(); renderCultos(); renderAvisos(); fecharBemVindo();
  toast('Tudo pronto. Que Deus abençoe o culto.');
}
function aplicarNomeIgreja() {
  const el = $('#marca-igreja'); if (el) el.textContent = IGREJA.nome || 'Projeção';
  document.title = 'Sistema v' + VERSAO;   // barra da janela: "Sistema v1.0.0"
}
function mostrarAddFundo() {
  const ov = document.createElement('div'); ov.className = 'ajuda-overlay';
  ov.innerHTML =
    '<div class="ajuda-box"><h3>Adicionar fundo</h3>' +
    '<p>Escolha uma imagem (de preferência larga, 16:9) e dê um nome.</p>' +
    '<div class="add-form"><input type="file" id="af-file" accept="image/*">' +
    '<input type="text" id="af-nome" placeholder="Nome do fundo (ex.: Aviso, Ceia, Batismo…)" maxlength="40">' +
    '<img id="af-prev" class="af-prev" alt="" style="display:none"></div>' +
    '<div class="ajuda-btns"><button class="big-btn verde" id="af-save">Adicionar</button>' +
    '<button class="big-btn" id="af-cancel">Cancelar</button></div></div>';
  document.body.appendChild(ov);
  let dataURL = null;
  const fileInp = ov.querySelector('#af-file'), nomeInp = ov.querySelector('#af-nome'), prev = ov.querySelector('#af-prev');
  fileInp.onchange = () => {
    const f = fileInp.files[0]; if (!f) return;
    const r = new FileReader();
    r.onload = () => { dataURL = r.result; prev.src = dataURL; prev.style.display = 'block'; if (!nomeInp.value) nomeInp.value = f.name.replace(/\.[^.]+$/, ''); };
    r.readAsDataURL(f);
  };
  ov.querySelector('#af-cancel').onclick = () => ov.remove();
  ov.onclick = e => { if (e.target === ov) ov.remove(); };
  ov.querySelector('#af-save').onclick = () => {
    if (!dataURL) { toast('Selecione uma imagem.'); return; }
    CUSTOM.push({ arquivo: dataURL, nome: (nomeInp.value || 'Meu fundo').trim(), custom: true });
    salvarCustom(); renderFundos(); ov.remove(); toast('Fundo adicionado.');
  };
}

function ligarEventos() {
  $$('.tab').forEach(t => t.onclick = () => trocarAba(t.dataset.aba));
  $('#btn-estilo').onclick = trocarEstilo;
  $('#busca-louvor').oninput = e => renderListaLouvores(e.target.value);
  $('#busca-livro').oninput = e => renderLivros(e.target.value);
  $$('[data-min]').forEach(b => b.onclick = () => { const m = +b.dataset.min; $('#timer-min').value = m; $('#timer-view').textContent = fmt(m * 60000); });
  $('#timer-min').oninput = e => $('#timer-view').textContent = fmt((+e.target.value || 0) * 60000);
  $('#timer-iniciar').onclick = () => iniciarTimer(+$('#timer-min').value || 5, $('#timer-rotulo').value);
  $('#timer-pausar').onclick = () => est.timerParadoMs ? iniciarTimer(est.timerParadoMs / 60000, est.timerRotulo) : pausarTimer();
  $('#timer-parar').onclick = pararTimer;
  $('#relogio-projetar').onclick = () => { est.live = { tipo: 'relogio' }; projetar({ modo: 'relogio', fundo: FB.plano, transicao: true, fade: 400 }); };
  setInterval(() => { const d = new Date(); $('#relogio-view').textContent = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); }, 1000);
  $('#texto-projetar').onclick = () => projetarTexto(false);
  $('#texto-livre').oninput = () => { if (est.live && est.live.tipo === 'texto') projetarTexto(true); };   // atualiza AO VIVO enquanto digita
  $('#texto-titulo').oninput = () => { if (est.live && est.live.tipo === 'texto') projetarTexto(true); };
  // projetando -> "Parar" só volta pra tela de espera; o telão continua ligado
  $('#btn-projecao').onclick = () => { if (est.projetando) { descanso(); toast('Tela de espera no telão.'); } else abrirProjecao(); };
  $('#btn-proximo').onclick = proximo; $('#btn-anterior').onclick = anterior;
  $('#btn-menor').onclick = () => ajustarTam(-0.3); $('#btn-maior').onclick = () => ajustarTam(+0.3);
  $('#tam-label').onclick = tamPadrao;                      // clicar no rótulo volta ao padrão
  $('#btn-congelar').onclick = toggleFreeze;   // "Parar de projetar" já faz o papel da espera
  const bg = $('#btn-guardar'); if (bg) bg.onclick = guardarVerso;
  const bl = $('#btn-limpar'); if (bl) bl.onclick = limparLista;
  const sa = $('#sl-abrir'); if (sa) sa.onclick = abrirApresentacao;
  // ---- menu ☰ ----
  $('#btn-menu').onclick = abrirMenu;
  $('#menu-fechar').onclick = fecharMenu;
  $('#menu-overlay').onclick = e => { if (e.target.id === 'menu-overlay') fecharMenu(); };
  $$('.menu-aba').forEach(b => b.onclick = () => menuSecao(b.dataset.sec));
  $('#ed-salvar').onclick = salvarLouvorEditor;
  $('#ed-limpar').onclick = limparEditor;
  $('#ig-salvar').onclick = () => { IGREJA.nome = $('#ig-nome').value.trim(); IGREJA.endereco = $('#ig-endereco').value.trim(); salvarIgreja(); aplicarNomeIgreja(); renderAvisos(); marcarSalvo(); toast('Dados da igreja salvos.'); };
  $('#bv-avancar').onclick = bvAvancar;
  $('#bv-voltar').onclick = () => { if (bvPasso > 0) { bvPasso--; renderBV(); } };
  $('#bv-pular').onclick = () => { salvarIgreja(); aplicarNomeIgreja(); fecharBemVindo(); };
  $('#btn-rever').onclick = () => { fecharMenu(); abrirBemVindo(true); };
  const ir = $('#ini-rever'); if (ir) ir.onclick = () => { fecharMenu(); abrirBemVindo(true); };
  $$('[data-ir]').forEach(b => b.onclick = () => menuSecao(b.dataset.ir));
  $$('[data-reset]').forEach(b => b.onclick = () => resetar(b.dataset.reset));
  document.addEventListener('keydown', e => {
    // com uma janela aberta (menu, boas-vindas, confirmação) as teclas NÃO mexem no telão
    const modal = document.querySelector('.ajuda-overlay, .menu-overlay:not(.oculto), .bv-overlay:not(.oculto)');
    if (modal) {
      if (e.key === 'Escape') { if (modal.classList.contains('ajuda-overlay')) modal.remove(); else if (modal.id === 'menu-overlay') fecharMenu(); }
      return;
    }
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;
    if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); proximo(); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); anterior(); }
    else if (e.key === '+' || e.key === '=') ajustarTam(+0.3);
    else if (e.key === '-') ajustarTam(-0.3);
    else if (e.key.toLowerCase() === 'p') descanso();
    else if (e.key.toLowerCase() === 'b') preto();
    else if (e.key.toLowerCase() === 'f') toggleFreeze();
  });
  window.addEventListener('message', ev => {
    const d = ev.data; if (!d) return;
    if (d.tipo === 'proj-pronta' && projWin) post(projWin, est.ultimo);
    else if (d.tipo === 'cmd') window.__cmdProj(d.cmd);
  });
  // comandos vindos do telão (setas apertadas lá) — usados pelas duas formas de projetar
  window.__cmdProj = cmd => ({ prox: proximo, ant: anterior, descanso: descanso, preto: preto,
    freeze: toggleFreeze, mais: () => ajustarTam(+0.3), menos: () => ajustarTam(-0.3) }[cmd] || (() => {}))();
  ligarControleCelular();
  // vigia da janela do telão: se ela foi fechada, o painel PRECISA parar de dizer
  // "ao vivo" — senão o operador (e o celular) acham que está projetando sem telão
  setInterval(() => {
    if (!est.projetando) return;
    if (nativo()) {
      // janela própria do Sistema (.exe): quem sabe se ela existe é o Python
      try {
        window.pywebview.api.projecao_aberta().then(r => {
          if (r && !r.aberta && est.projetando) { est.projetando = false; atualizarProjBtn(); }
        }).catch(() => {});
      } catch (e) {}
    } else if (!projWin || projWin.closed) {          // janela aberta pelo navegador
      est.projetando = false; projWin = null; atualizarProjBtn();
    }
  }, 1500);
}

// ================= CONTROLE PELO CELULAR =================
// O celular manda comandos pro servidor; aqui a gente busca e executa. Tudo na rede local.
function executarDoCelular(c) {
  if (!c || !c.cmd) return;
  switch (c.cmd) {
    case 'louvor':  if (LOUVORES[c.idx]) selecionarLouvor(c.idx); break;
    case 'slide':   if (LOUVORES[c.idx]) { if (est.louvorIdx !== c.idx) selecionarLouvor(c.idx); projetarLouvor(c.idx, c.slide, false); } break;
    case 'verso':   est.setPos = -1; projetarVerso(c.livro, c.cap, c.v); break;
    case 'slidepp': projetarSlide(c.i); break;
    // toque longo no versículo pelo celular: guarda na lista já marcado. Com dois
    // ou mais marcados, reprojetarVista (dentro de adicionarLista) manda juntos.
    // Entra MARCADO, que é o sentido de "segure para juntar". O risco de o ✓
    // ressuscitar os versículos mais tarde morreu na raiz: reprojetarVista agora
    // só age com versículo no ar (adicionarLista já cuida de não duplicar).
    case 'guardar':
      adicionarLista({ tipo: 'verso', ref: c.livro + ' ' + c.cap + ':' + c.v,
                       livro: c.livro, cap: c.cap, v: c.v, on: true });
      break;
    // o celular manda o ALVO (on: true/false), não "inverta": assim dois toques
    // seguidos param no mesmo lugar em vez de congelar e descongelar
    case 'freeze':  if (c.on === undefined || !!c.on !== !!est.freeze) toggleFreeze(); break;
    default:        window.__cmdProj(c.cmd);
  }
}
function ligarControleCelular() {
  let erros = 0;
  setInterval(async () => {
    try {
      const r = await fetch('/api/comandos').then(r => r.json());
      erros = 0;
      (r.comandos || []).forEach(c => {
        try { executarDoCelular(c); }
        catch (e) { console.error('comando do celular falhou:', c, e); }   // um comando ruim não derruba os outros
      });
    } catch (e) { erros++; }
  }, 600);
  // publica o que está no telão, pro celular mostrar
  setInterval(() => {
    const el = $('#agora');
    try {
      fetch('/api/estado', { method: 'POST', body: JSON.stringify({
        agora: el ? el.textContent : '',
        projetando: est.projetando, congelado: est.freeze,
        slides: (SLIDES.lista || []).length,
        // posição do que está no ar — o celular usa para acender o item certo
        // mesmo quando quem avançou foi o computador ou a Lista de Projeção
        louvor: est.louvorIdx, slide: est.louvorSlide, slidepp: est.slidePos,
      }) });
    } catch (e) {}
  }, 1000);
}
async function iniciar() {
  await Guardar.carregar();     // dados salvos ao lado do programa vêm primeiro (sobrevivem a atualizações)
  carregarDadosUsuario();
  const v = $('#ini-versao'); if (v) v.textContent = 'Versão ' + VERSAO;
  aplicarEstilo();
  $('#estilo-nome').textContent = ESTILO_NOME[est.estilo];
  const pf = $('#preview'); pf.addEventListener('load', () => { previews.length = 0; previews.push(pf.contentWindow); post(pf.contentWindow, est.ultimo); });
  if (pf.contentWindow) { previews.push(pf.contentWindow); }
  const ms = $('#marca-svg'); if (ms && window.Icones) ms.innerHTML = window.Icones.MARCA(30);
  aplicarNomeIgreja();
  recarregarLouvores(); renderLivros(''); renderFundos(); renderFila(); renderAvisos();   // avisos já prontos na aba Texto
  $('#timer-view').textContent = '05:00';
  ligarEventos(); atualizarProjBtn(); atualizarAgora();
  abrirBemVindo(false);   // primeira vez: apresentação + configuração da igreja
}
document.addEventListener('DOMContentLoaded', iniciar);
})();
