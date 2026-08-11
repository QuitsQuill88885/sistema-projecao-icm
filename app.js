/* ICM Iperó — Projeção | painel de controle */
(function () {
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const BIBLIA = window.BIBLIA, LOUVORES = window.LOUVORES;
const BASE_LOUVORES = LOUVORES.slice();   // coletânea original (os "Meus louvores" entram depois dela)
const ESTILOS = window.ESTILOS, GALERIA = window.GALERIA || [];
// louvor 5.75: calibrado na transmissão oficial (129, 10/08/2026) — letra a
// 4,36% da altura da tela com avanço de 11,05%; o desenho fino está no
// comentário do #lou-txt em projecao.html
const TAM_DEF = { louvor: 5.75, biblia: 5.55 };

const est = {
  aba: 'louvor', projetando: false, freeze: false, estilo: 'limpo',
  louvorIdx: -1, louvorSlide: 0,
  // contAfter/contAntes = quantos versículos você já andou DEPOIS do último e
  // ANTES do primeiro item escolhido na lista. São o caminho de volta: sem eles
  // a lista era abandonada e o Avançar seguia o capítulo para sempre.
  livro: null, cap: null, bibPos: null, fila: [], setPos: -1, vistaFim: null, aguardando: false,
  contAfter: 0, contAntes: 0, juntos: false,
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

// ---------- SUGESTÕES: louvores que combinam com o versículo ----------
// A tabela vem PRONTA (dados/sugestoes.js): o computador da igreja não calcula
// nada para abrir a lista. O resto da roda é calculado na hora, uma vez por
// versículo, e fica guardado até o operador trocar de verso.
//
// A LISTA É UMA RODA, NÃO UMA FILA QUE ACABA. Mostra três; o botão troca pelos
// três seguintes; passado o último trio, volta ao primeiro. Quem fica clicando
// atravessa todos os louvores que têm nexo com o versículo e recomeça — nunca
// acaba, e dentro de uma volta nenhum louvor aparece duas vezes.
const SUG_POR_VEZ = 3;    // três é o que cabe sem empurrar a grade de versículos para fora da tela
const SUG_TETO = 30;      // dez trios: daí para baixo já é louvor que só encosta no assunto
const SUG_JANELA = 4;     // versículos de cada lado que entram na busca (o assunto não cabe numa linha só)
let sugCand = [];         // candidatos { i, prox } — prox = proximidade com a mensagem, de 0 a 1
let sugRoda = [];         // a roda pronta: índices de louvor, em ordem de peso e sem repetidos
let sugPag = 0;           // qual trio está na tela
let sugVers = null;       // { livro, cap, v } a que esta roda pertence
let sugCheia = false;     // a parte calculada já entrou nesta roda?

function codVers(livro, cap, v) {
  const li = BIBLIA.ordem.indexOf(livro);
  return li < 0 ? null : li + '.' + cap + '.' + v;
}
// O mesmo louvor está em várias coletâneas: são 2.459 entradas no catálogo para
// pouco mais de 1.500 louvores distintos, e a tabela de sugestões repete o mesmo
// em 15.122 dos 25.806 versículos (Gênesis 1:1 sugeria "DEUS CRIOU OS CÉUS E A
// TERRA" duas vezes, uma das CIAS e outra da Antiga). Numa lista de três, isso é
// um terço da tela desperdiçado, e numa roda é "repetir fora de hora".
//
// SÃO DUAS CHAVES, porque nenhuma delas sozinha reconhece a cópia.
//   pelo TÍTULO + o começo da primeira linha — junta o que a coletânea copiou
//   com outra pontuação ou outra quebra de linha ("(BIS)", "3X", "fez"/"faz").
//   Doze letras da primeira linha porque as coletâneas quebram a linha em pontos
//   diferentes, e comparar a linha inteira separava justamente o que é igual.
//   pela LETRA — junta o que a coletânea REBATIZOU, e aí o título não serve de
//   nada: 71 das CIAS é "JESUS VIU A MULTIDÃO" e 9997 da Antiga é "JESUS VIU A
//   MULTIDÃO (A MULTIPLICAÇÃO)", mesma letra palavra por palavra; 353 é
//   "DEIXA-ME CHORAR" e 3371 é "DEIXA-ME CHORAR AOS TEUS PÉS". Só pelo título,
//   esses pares entravam os dois na mesma volta da roda e o operador via o mesmo
//   louvor duas vezes — foi o que aconteceu em 4 dos 6 versículos medidos.
// Sessenta letras da letra, e não menos: os cinco arranjos do Salmo 23 começam
// todos com "o senhor é o meu pastor, nada me faltará" e seguem cada um para um
// lado. Com 40 letras eles viravam um só e a igreja perdia quatro louvores.
const IDENT_LETRA = 60;
function identTitulo(titulo, linha1) {
  return soLetras(titulo) + '|' + soLetras(linha1).slice(0, 12);
}
// As duas chaves de um louvor, calculadas uma vez só: a da letra percorre todos
// os slides, e a roda pergunta por elas centenas de vezes a cada montagem.
// A lembrança é pelo LOUVOR, não pelo índice: apagar um "Meu louvor" empurra os
// de baixo uma casa para trás, e uma lista guardada por índice passaria a
// responder pelo louvor errado.
const identCache = new Map();
function ident(i) {
  const s = LOUVORES[i] || {};
  let d = identCache.get(s);
  if (!d) {
    const sl = (s.slides || [])[0] || {};
    d = [identTitulo(s.titulo || '', (sl.linhas || [])[0] || ''),
         soLetras((s.slides || []).map(x => (x.linhas || []).join(' ')).join(' ')).slice(0, IDENT_LETRA)];
    identCache.set(s, d);
  }
  return d;
}

// ---- o peso do que a igreja já cantou ----
// historico.json guarda cada projeção com a chave do louvor. Aqui só interessa
// QUANTAS VEZES cada um subiu ao telão, somando as coletâneas: para a igreja o
// 470 da Coletânea e o 7752 da Antiga são o mesmo louvor.
let sugVezes = null, sugVezesLetra = null, sugVezesMax = 0, sugHistPedido = false;
function carregarHistoricoSug() {
  if (sugHistPedido) return;
  sugHistPedido = true;
  fetch('/api/historico').then(r => r.json()).then(r => {
    // duas contagens, uma por chave, para a projeção do 9997 contar também para
    // o 71 das CIAS — que é o mesmo louvor com outro nome. A chave de título sai
    // direto do que está gravado; a da letra só o catálogo tem, então o registro
    // é reencontrado pelo louvor que o gerou.
    const porTit = new Map(), porLet = new Map(), porChave = new Map();
    LOUVORES.forEach((s, i) => porChave.set(chaveLouvor(s), i));
    const conta = (m, k) => {
      if (!k) return;
      const n = (m.get(k) || 0) + 1;
      m.set(k, n);
      if (n > sugVezesMax) sugVezesMax = n;
    };
    (r.registros || []).forEach(x => {
      if (x.q !== 'louvor' || !x.chave) return;
      const p = String(x.chave).split('|');       // num|titulo|primeira linha
      conta(porTit, identTitulo(p[1] || '', p.slice(2).join('|')));
      // não achou: é louvor que saiu do catálogo, e o que saiu não vai ser
      // sugerido de qualquer jeito
      const i = porChave.get(String(x.chave));
      if (i !== undefined) conta(porLet, ident(i)[1]);
    });
    sugVezes = porTit; sugVezesLetra = porLet;
    // O histórico chegou depois da lista pintada. Aqui a roda é refeita do zero,
    // sem preservar o que já estava na tela: acontece uma única vez por sessão,
    // nos primeiros instantes, e sem isso o primeiro trio ficaria para sempre na
    // ordem que tinha ANTES de o histórico ser lido — justo o trio que mais
    // importa acertar.
    if (sugVers) { montarRoda(true); pintarSug(); }
  }).catch(() => { sugVezes = new Map(); sugVezesLetra = new Map(); });
}
// COMO OS DOIS PESOS SE COMBINAM
//   proximidade   — o quanto o louvor fala do que o versículo fala, de 0 a 1.
//   familiaridade — quantas vezes a igreja cantou o louvor, na escala do mais
//                   cantado de todos: ln(1+vezes) / ln(1+maisCantado). O
//                   logaritmo é o que impede o campeão de esmagar o resto:
//                   cantar 40 vezes não vale 40, vale pouco mais que cantar 10.
//   peso final    = proximidade × (1 + 0,4 × familiaridade)
// O histórico é BÔNUS, nunca nota. O louvor que a igreja canta toda semana ganha
// no máximo 40% e passa na frente de quem tinha empatado com ele; o que ela nunca
// cantou não perde nada — fica com a nota inteira que a mensagem lhe deu, só não
// ganha o empurrão. E como a proximidade já nasce em faixas separadas (o
// versículo manda mais que os vizinhos, que mandam mais que o calculado), o bônus
// remexe a vizinhança de cada louvor sem virar a lista do avesso.
// A escala tem piso: numa igreja que acabou de instalar o Sistema, o louvor mais
// cantado tem UMA projeção, e sem o piso essa única vez valeria o bônus inteiro —
// o acaso do primeiro culto mandando na lista. Com o piso, o histórico só pesa de
// verdade quando já existe histórico; até lá empurra de leve.
const SUG_HIST_PISO = 8;
function familiaridade(i) {
  if (!sugVezes) return 0;
  const d = ident(i);
  // as duas contagens são do mesmo louvor por dois caminhos: vale a maior, somar
  // contaria a mesma projeção duas vezes
  const n = Math.max(sugVezes.get(d[0]) || 0, (sugVezesLetra && sugVezesLetra.get(d[1])) || 0);
  return n ? Math.log(1 + n) / Math.log(1 + Math.max(sugVezesMax, SUG_HIST_PISO)) : 0;
}
function montarRoda(refazer) {
  // o que já passou pela tela nesta volta fica onde está: crescer a roda no meio
  // do giro não pode reembaralhar o que o operador acabou de ver
  const presos = refazer ? [] : sugRoda.slice(0, (sugPag + 1) * SUG_POR_VEZ);
  const fixo = new Set(presos), roda = presos.slice();
  // basta bater UMA das duas chaves para ser o mesmo louvor de novo
  const vTit = new Set(), vLet = new Set();
  const anotar = i => { const d = ident(i); vTit.add(d[0]); vLet.add(d[1]); };
  const jaVeio = i => { const d = ident(i); return vTit.has(d[0]) || vLet.has(d[1]); };
  presos.forEach(anotar);
  sugCand.filter(c => !fixo.has(c.i) && LOUVORES[c.i])
         .map(c => ({ i: c.i, p: c.prox * (1 + 0.4 * familiaridade(c.i)) }))
         .sort((a, b) => b.p - a.p)
         .forEach(c => {
           if (jaVeio(c.i) || roda.length >= SUG_TETO) return;
           anotar(c.i); roda.push(c.i);
         });
  // trio incompleto no fim faria a última tela parecer defeito; sobram no máximo
  // dois louvores de fora, e são os dois mais fracos da roda
  if (roda.length > SUG_POR_VEZ) roda.length -= roda.length % SUG_POR_VEZ;
  sugRoda = roda;
}
function sugerirPara(livro, cap, v) {
  const cx = $('#sug'); if (!cx) return;
  const base = (window.SUGESTOES && window.SUGESTOES[codVers(livro, cap, v)]) || [];
  if (!base.length) {
    // some da tela e esvazia: faixa escondida com o trio do versículo anterior
    // dentro é sugestão errada esperando um descuido do CSS para reaparecer
    cx.classList.add('oculto'); sugVers = null; sugRoda = []; sugCand = [];
    const c = $('#sug-lista'); if (c) c.innerHTML = '';
    return;
  }
  cx.classList.remove('oculto');
  sugVers = { livro, cap, v }; sugPag = 0; sugCheia = false; sugRoda = [];
  carregarHistoricoSug();
  // Faixa 0,70–1,00 para o que a tabela deu a ESTE versículo, 0,50–0,65 para o
  // que ela deu aos vizinhos. Os vizinhos entram porque a tabela repete tanto
  // louvor que sobrava trio de dois — e porque o versículo seguinte fala do
  // mesmo assunto. Sai de graça: já está tudo carregado, não calcula nada.
  const alto = Math.max.apply(null, base.map(a => a[1])) || 1;
  sugCand = base.map(a => ({ i: a[0], prox: 0.7 + 0.3 * (a[1] / alto) }));
  for (let k = v - SUG_JANELA; k <= v + SUG_JANELA; k++) {
    if (k === v || k < 1) continue;
    ((window.SUGESTOES && window.SUGESTOES[codVers(livro, cap, k)]) || [])
      .forEach(a => sugCand.push({ i: a[0], prox: 0.5 + 0.15 * Math.min(1, a[1] / alto) }));
  }
  montarRoda(); pintarSug();
}
function pintarSug() {
  const c = $('#sug-lista'); if (!c) return;
  c.innerHTML = '';
  const n = sugRoda.length;
  const paginas = Math.max(1, Math.ceil(n / SUG_POR_VEZ));
  sugPag = ((sugPag % paginas) + paginas) % paginas;    // é aqui que a roda dá a volta
  sugRoda.slice(sugPag * SUG_POR_VEZ, sugPag * SUG_POR_VEZ + SUG_POR_VEZ).forEach(i => {
    const s = LOUVORES[i]; if (!s) return;
    const d = document.createElement('div'); d.className = 'sug-l';
    d.innerHTML = '<small>' + (numLouvor(s) || '—') + ' ' + siglaCol(s) + '</small>' +
                  '<span class="nm">' + s.titulo + '</span>' +
                  '<button class="add" title="Guardar na Lista de Projeção">+</button>';
    d.onclick = ev => {
      if (ev.target.classList.contains('add')) {
        ev.stopPropagation();
        adicionarLista({ tipo: 'louvor', idx: i, chave: chaveLouvor(s), rotulo: rotuloLouvor(s) });
        return;
      }
      selecionarLouvor(i, true); trocarAba('louvor');
    };
    c.appendChild(d);
  });
  const b = $('#sug-mais');
  // o rótulo não muda nunca: quem clica está pedindo MAIS SUGESTÕES, não
  // esperando um carregamento. O que demora (o índice temático) vem por trás,
  // com o trio seguinte já na tela.
  if (b) { b.textContent = 'mais sugestões'; b.style.display = (n > SUG_POR_VEZ || !sugCheia) ? '' : 'none'; }
}
// O índice temático tem 883 KB. Carregar sempre pesaria no arranque do micro
// da igreja para um recurso que talvez ninguém use no culto — então ele só é
// buscado no primeiro "mais sugestões", e daí em diante fica na memória.
let temasPedidos = false, temasEsperando = [];
function carregarTemas(feito) {
  if (window.TEMAS) return feito();
  // FILA, não "já pedi, deixa pra lá": o operador clica em "mais sugestões",
  // troca de versículo e clica de novo enquanto o índice ainda vem. O segundo
  // pedido é de OUTRO versículo, e largá-lo fazia esse clique morrer — a roda
  // do versículo novo só crescia no clique seguinte.
  temasEsperando.push(feito);
  if (temasPedidos) return;
  temasPedidos = true;
  const sc = document.createElement('script');
  sc.src = 'dados/temas.js';
  sc.onload = () => { const fila = temasEsperando; temasEsperando = []; fila.forEach(f => f()); };
  sc.onerror = () => { temasPedidos = false; temasEsperando = []; toast('Não consegui abrir a lista de temas.'); };
  document.head.appendChild(sc);
}
function maisSugestoes() {
  if (!sugVers) return;
  sugPag++;
  // Gira JÁ, com o que a tabela deu aos versículos vizinhos — o índice temático
  // vem por trás e engorda a roda sem tirar nada da tela. Só quando os vizinhos
  // não deram nem um segundo trio é que vale a pena esperar: repintar o MESMO
  // trio seria o operador clicar e achar que o botão está quebrado.
  if (sugCheia || sugRoda.length > SUG_POR_VEZ) pintarSug();
  if (sugCheia) return;
  const alvo = sugVers;
  carregarTemas(() => {
    // trocou de versículo enquanto o índice carregava: o cálculo já não é deste
    if (!sugVers || sugVers !== alvo) return;
    calcularRoda(); pintarSug();
  });
}

// ---- a parte calculada da roda ----
// Feita uma vez por versículo, e só quando o operador pede. O louvor e o texto
// bíblico falam do mesmo assunto com palavras diferentes, então a busca junta
// três coisas: o TRECHO (o versículo e os vizinhos), as FAMÍLIAS de palavras que
// o trecho encosta, e a PARECENÇA com os louvores que a tabela já garantiu.
let sugNorma = null;
function normasTemas() {
  if (!sugNorma) sugNorma = TEMAS.louvores.map(p => {
    let s = 0; for (const k in p) s += p[k] * p[k];
    return Math.sqrt(s) || 1;
  });
  return sugNorma;
}
function normaCons(q) { let s = 0; for (const k in q) s += q[k] * q[k]; return Math.sqrt(s) || 1; }
// cosseno: divide pelo tamanho do vetor para que louvor comprido não ganhe só
// por ter mais palavras que os outros
function cosTemas(i, q, nq) {
  const p = TEMAS.louvores[i]; let s = 0;
  for (const k in p) if (q[k]) s += p[k] * q[k];
  return s / (normasTemas()[i] * nq);
}
function consultaDoVerso(livro, cap, v) {
  const cs = (BIBLIA.livros[livro] || [])[cap - 1] || {};
  const q = {}, doTrecho = new Set();
  const por = (txt, w) => soLetras(txt).split(' ').forEach(p => {
    if (p.length < 3) return;
    doTrecho.add(p);
    // palavra que está em quase todo louvor não tem peso no índice, e é isso
    // mesmo: "senhor" e "deus" não dizem de que assunto o versículo trata
    const g = TEMAS.idf[p];
    if (g) q[p] = Math.max(q[p] || 0, w * g);
  });
  por(cs[v] || '', 1);
  for (let k = v - SUG_JANELA; k <= v + SUG_JANELA; k++) if (k !== v && cs[k]) por(cs[k], 0.45);
  // A PONTE DOS TEMAS. Êxodo 12 fala de fermento, ázimo e umbral; o louvor de
  // Páscoa fala de cálice, mosto, lagar e cordeiro — nenhuma palavra igual. Se o
  // trecho encosta em duas palavras de uma família, a família inteira entra na
  // busca, e aí os dois se encontram. Duas e não uma: uma só é coincidência.
  for (const nome in TEMAS.familias) {
    const fam = TEMAS.familias[nome];
    let bate = 0;
    for (const p of fam) if (doTrecho.has(p)) bate++;
    if (bate < 2) continue;
    for (const p of fam) { const g = TEMAS.idf[p]; if (g) q[p] = Math.max(q[p] || 0, 0.55 * g); }
  }
  return q;
}
function calcularRoda() {
  sugCheia = true;
  const q = consultaDoVerso(sugVers.livro, sugVers.cap, sugVers.v), nq = normaCons(q);
  // os louvores que a tabela deu já são a resposta certa: quem se parece com eles
  // também tem a ver com o versículo, mesmo sem repetir palavra do texto
  const qb = {}, jaTem = new Set();
  sugCand.forEach(c => {
    jaTem.add(c.i);
    const p = TEMAS.louvores[c.i]; if (!p) return;
    const n = normasTemas()[c.i];
    for (const k in p) qb[k] = (qb[k] || 0) + p[k] / n;
  });
  const nqb = normaCons(qb), pts = [];
  for (let i = 0; i < TEMAS.louvores.length; i++) {
    if (jaTem.has(i) || !LOUVORES[i]) continue;
    const s = 0.6 * cosTemas(i, q, nq) + 0.4 * cosTemas(i, qb, nqb);
    if (s > 0) pts.push([i, s]);
  }
  pts.sort((a, b) => b[1] - a[1]);
  if (!pts.length) { montarRoda(); return; }
  const alto = pts[0][1];
  // Abaixo de um quinto do melhor não é mais "ter nexo", é ter uma palavra em
  // comum. O corte de quantidade é generoso de propósito: o mesmo louvor vem
  // três e quatro vezes (uma por coletânea), e quem junta as cópias é a montagem
  // da roda — cortar antes disso deixava a roda com meia dúzia de louvores.
  sugCand = sugCand.concat(pts.filter(a => a[1] >= alto * 0.2).slice(0, SUG_TETO * 8)
                              .map(a => ({ i: a[0], prox: 0.45 * (a[1] / alto) })));
  montarRoda();
}

// ---------- HISTÓRICO ----------
// Guarda o que foi ao telão e por QUANTO TEMPO. O tempo é o que separa o louvor
// que a igreja cantou inteiro daquele que passou de raspão — é o dado que faz o
// painel valer alguma coisa. Só conta com a projeção ABERTA: ensaiar no painel
// com o telão desligado não é culto e não entra na conta.
let noAr = null;      // { q, rot, chave, ini }
const MIN_SEG = 5;    // menos que isso foi engano de clique, não louvor cantado
let pendentes = [];

function fecharNoAr() {
  if (!noAr) return;
  const seg = Math.round((Date.now() - noAr.ini) / 1000);
  if (seg >= MIN_SEG) pendentes.push({ q: noAr.q, rot: noAr.rot, chave: noAr.chave,
                                       ini: Math.round(noAr.ini / 1000), seg });
  noAr = null;
  if (pendentes.length) enviarHistorico();
}
function abrirNoAr(q, rot, chave) {
  if (noAr && noAr.chave === chave) return;    // mesmo item, outro slide: o relógio continua
  fecharNoAr();
  if (!est.projetando) return;                 // telão desligado não é culto
  noAr = { q, rot, chave, ini: Date.now() };
}
let mandando = false;
function enviarHistorico() {
  if (mandando || !pendentes.length) return;
  mandando = true;
  const lote = pendentes; pendentes = [];
  fetch('/api/historico', { method: 'POST', body: JSON.stringify(lote) })
    .catch(() => { pendentes = lote.concat(pendentes); })   // falhou: tenta de novo depois
    .finally(() => { mandando = false; });
}
// fechar o Sistema no meio de um louvor não pode perder o registro dele
window.addEventListener('beforeunload', () => {
  fecharNoAr();
  if (pendentes.length && navigator.sendBeacon)
    navigator.sendBeacon('/api/historico', JSON.stringify(pendentes));
});

// ---------- PAINEL: o que a igreja cantou ----------
let HIST = null, histDias = 30;
function tempoCurto(seg) {
  if (seg < 60) return seg + 's';
  const m = Math.round(seg / 60);
  return m < 60 ? m + ' min' : Math.floor(m / 60) + 'h' + String(m % 60).padStart(2, '0');
}
function abrirPainel() {
  fetch('/api/historico').then(r => r.json()).then(r => { HIST = r.registros || []; pintarPainel(); })
    .catch(() => { HIST = []; pintarPainel(); });
}
function pintarPainel() {
  if (!HIST) return;
  const corte = histDias ? (Date.now() / 1000 - histDias * 86400) : 0;
  const regs = HIST.filter(x => x.ini >= corte && x.q === 'louvor');
  const resumo = $('#pn-resumo');

  if (!regs.length) {
    resumo.innerHTML = '';
    ['#pn-mais', '#pn-tempo', '#pn-cultos'].forEach(k =>
      $(k).innerHTML = '<div class="pn-vazio">Nada registrado neste período.</div>');
    return;
  }
  // "culto" = um dia de projeção. É o recorte que a igreja entende.
  const dias = new Set(regs.map(x => new Date(x.ini * 1000).toDateString()));
  const segTotal = regs.reduce((a, x) => a + x.seg, 0);
  resumo.innerHTML =
    cx(regs.length, 'louvores projetados') +
    cx(dias.size, dias.size === 1 ? 'culto' : 'cultos') +
    cx(tempoCurto(segTotal), 'no telão');

  const por = {};
  regs.forEach(x => {
    const k = x.rot || x.chave;
    (por[k] = por[k] || { n: 0, seg: 0 }).n++;
    por[k].seg += x.seg;
  });
  const lista = Object.entries(por);
  linhas('#pn-mais', lista.sort((a, b) => b[1].n - a[1].n).slice(0, 10),
         v => v.n + (v.n === 1 ? ' vez' : ' vezes'), v => v.n);
  linhas('#pn-tempo', lista.slice().sort((a, b) => b[1].seg - a[1].seg).slice(0, 10),
         v => tempoCurto(v.seg), v => v.seg);

  // últimos cultos, do mais recente para o mais antigo
  const porDia = {};
  regs.forEach(x => {
    const d = new Date(x.ini * 1000); const k = d.toDateString();
    (porDia[k] = porDia[k] || { n: 0, seg: 0, ts: x.ini }).n++;
    porDia[k].seg += x.seg;
    porDia[k].ts = Math.min(porDia[k].ts, x.ini);
  });
  const cultos = Object.entries(porDia).sort((a, b) => b[1].ts - a[1].ts).slice(0, 10);
  const maxC = Math.max(...cultos.map(c => c[1].n), 1);
  $('#pn-cultos').innerHTML = cultos.map(([k, v]) => {
    const d = new Date(v.ts * 1000);
    const dia = d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: '2-digit' });
    const sem = d.toLocaleDateString('pt-BR', { weekday: 'long' }).replace('-feira', '');
    return '<div class="pn-l"><i class="bar" style="width:' + (100 * v.n / maxC) + '%"></i>' +
           '<span class="nm">' + dia + ' · ' + sem + '</span>' +
           '<span class="vl">' + v.n + ' louvores · ' + tempoCurto(v.seg) + '</span></div>';
  }).join('');
}
function cx(n, rot) { return '<div class="pn-cx"><b>' + n + '</b><span>' + rot + '</span></div>'; }
function linhas(alvo, arr, texto, peso) {
  const max = Math.max(...arr.map(a => peso(a[1])), 1);
  $(alvo).innerHTML = arr.map(([nome, v], i) =>
    '<div class="pn-l"><i class="bar" style="width:' + (100 * peso(v) / max) + '%"></i>' +
    '<span class="pos">' + (i + 1) + '</span>' +
    '<span class="nm">' + nome + '</span>' +
    '<span class="vl">' + texto(v) + '</span></div>').join('');
}

// ---------- LOUVOR ----------
function projetarLouvor(idx, slide, fade) {
  const s = LOUVORES[idx];
  if (s) abrirNoAr('louvor', rotuloLouvor(s), chaveLouvor(s));
  est.louvorIdx = idx; est.louvorSlide = slide;
  est.live = { tipo: 'louvor', idx, slide };
  // Louvor de CIAS com animação: o GIF já é a TELA PRONTA (título, letra e fundo
  // animado), então ele SUBSTITUI o texto — não se soma a ele. As telas do GIF
  // não são as mesmas do texto, por isso a contagem vem do próprio GIF.
  const anim = est.modoAnim !== false ? daAnimacao(s) : null;
  if (anim && anim.length) {
    const i = Math.min(slide, anim.length - 1);
    est.louvorSlide = i;
    est.live = { tipo: 'louvor', idx, slide: i, anim: true, n: anim.length };
    projetar({ modo: 'slide', src: '/animacoes/' + encodeURIComponent(anim[i]),
               transicao: true, fade: fade ? 500 : 200 });
  } else {
    projetar(stLouvor(idx, slide, fade));
  }
  marcarSlide(); atualizarExtras();
}
// quantas telas tem o louvor no ar (o GIF pode ter menos que o texto)
function telasDoLouvor(idx) {
  const s = LOUVORES[idx]; if (!s) return 0;
  const a = est.modoAnim !== false ? daAnimacao(s) : null;
  return a && a.length ? a.length : s.slides.length;
}
function louvorProximo() {
  const s = LOUVORES[est.louvorIdx]; if (!s) return;
  // conta as telas do que está NO AR: o GIF das CIAS costuma ter menos telas que
  // o texto, e usar a contagem do texto deixaria telas fantasma no fim
  if (est.louvorSlide < telasDoLouvor(est.louvorIdx) - 1) projetarLouvor(est.louvorIdx, est.louvorSlide + 1, false);
  else finalizarLouvor();   // acabou o louvor -> vai pra tela de espera; o PRÓXIMO "Avançar" engata o seguinte
}
// terminou o louvor: cai na tela de espera (descanso). Fica "aguardando" o próximo Avançar.
function finalizarLouvor() {
  descanso(true); est.aguardando = true; atualizarAgora();   // congelado continua congelado
}
function louvorAnterior() { if (est.louvorSlide > 0) projetarLouvor(est.louvorIdx, est.louvorSlide - 1, false); }

// tira acentos: procurar "coracao" acha "CORAÇÃO", e vice-versa
function semAcento(t) { return (t || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }
// tira também a pontuação: ninguém digita a vírgula do título, então quem
// procura "resplandece jerusalem" tem que achar "RESPLANDECE, Ó JERUSALÉM"
function soLetras(t) { return semAcento(t).replace(/[^a-z0-9]+/g, ' ').replace(/\s+/g, ' ').trim(); }

// ---- busca que perdoa erro de escrita ----------------------------------
// Quem digita errado digita PELO SOM. Então reduzimos a palavra ao som antes de
// comparar: "resplandesse" e "resplandece" viram a mesma coisa, "querro" e
// "quero" também. A chave é calculada uma vez por louvor e fica guardada, então
// no momento da busca é só comparar texto curto — leve no computador da igreja.
function som(p) {
  p = (p || '').normalize('NFD').toLowerCase();
  p = p.replace(/c\u0327/g, 's');                    // cedilha ANTES do c -> k
  p = p.replace(/[\u0300-\u036f]/g, '').replace(/[^a-z]/g, '');
  if (!p) return '';
  p = p.replace(/lh/g, 'L').replace(/nh/g, 'N').replace(/ch/g, 'X');
  p = p.replace(/xc/g, 's').replace(/sc/g, 's');     // exceto = eseto
  p = p.replace(/c([ei])/g, 's$1').replace(/c/g, 'k').replace(/q/g, 'k').replace(/ku/g, 'k');
  p = p.replace(/ph/g, 'f');
  p = p.replace(/([aeiou])s([aeiou])/g, '$1z$2').replace(/z/g, 's');
  p = p.replace(/r{2,}/g, 'r').replace(/l{2,}/g, 'l').replace(/h/g, '');
  p = p.replace(/[mn]$/, 'n').replace(/y/g, 'i');
  return p.replace(/(.)\1+/g, '$1');
}
// distância de edição com corte: só interessa saber se está a <= teto trocas,
// e desistir cedo é o que mantém isso barato em 2.459 louvores
function perto(a, b, teto) {
  teto = teto || 2;
  if (Math.abs(a.length - b.length) > teto) return false;
  let ant = []; for (let j = 0; j <= b.length; j++) ant.push(j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i]; let melhor = i;
    for (let j = 1; j <= b.length; j++) {
      const v = Math.min(ant[j] + 1, cur[j - 1] + 1, ant[j - 1] + (a[i - 1] !== b[j - 1] ? 1 : 0));
      cur.push(v); if (v < melhor) melhor = v;
    }
    if (melhor > teto) return false;
    ant = cur;
  }
  return ant[b.length] <= teto;
}
// o som tem que sair do texto ORIGINAL: soLetras já tirou o cedilha, e sem ele
// "coração" virava "korakao" em vez de "korasao" — "korason" não achava nada
function somDaFrase(t) {
  return (t || '').split(/[^A-Za-zÀ-ÿ]+/).filter(Boolean).map(som);
}

// QUÃO PERTO o louvor está do que foi digitado — quanto maior, mais acima.
// A ordem que o operador espera: título igual, título que COMEÇA com aquilo,
// título que contém, título com todas as palavras soltas, e só no fim a LETRA.
// Sem isso, procurar "Jesus" enterrava o louvor CHAMADO "Jesus" debaixo de
// centenas de louvores que só citam Jesus no meio da letra.
function pontuarLouvor(s, alvo, palavras) {
  const tit = s._tl || (s._tl = soLetras(s.titulo));
  if (tit === alvo) return 1000;
  if (tit.startsWith(alvo)) return 900 - Math.min(tit.length, 99);      // título curto primeiro
  if (tit.includes(alvo)) return 800 - Math.min(tit.indexOf(alvo), 99);
  if (palavras.length > 1 && palavras.every(p => tit.includes(p)))
    return 600 - Math.min(tit.indexOf(palavras[0]), 99);
  const letra = s._ll || (s._ll = soLetras(s.slides.map(x => x.linhas.join(' ')).join(' ')));
  if (letra.includes(alvo)) return 300;
  if (palavras.length > 1 && palavras.every(p => letra.includes(p))) return 200;
  // NADA bateu escrito certo: tenta pelo SOM. Vale menos que o acerto exato,
  // mas salva quem digitou "resplandesse" ou "querro".
  const sons = s._sm || (s._sm = somDaFrase(s.titulo));
  const alvoSom = window._somBusca || [];
  if (alvoSom.length && sons.length) {
    const casadas = alvoSom.filter(a => sons.some(b => b === a || perto(a, b, a.length > 5 ? 2 : 1)));
    if (casadas.length === alvoSom.length) return 150 - Math.min(sons.length, 40);
    if (casadas.length && alvoSom.length > 1) return 80;
  }
  return 0;
}
// ---- coletâneas ----------------------------------------------------------
// O mesmo número existe em coletâneas diferentes com letras diferentes: o 60 da
// Coletânea 2018 e o 60 das CIAS são louvores distintos. Alguém anuncia só
// "sessenta" ou "setenta CIAS" e o operador tem segundos para achar o certo.
// A lista mostra os resultados AGRUPADOS por coletânea, com o nome escrito:
// ele digita o número e vê os dois, cada um debaixo do seu cabeçalho.
const NOME_COL = {
  'Coletânea 2018': 'COLETÂNEA 2018',
  'CIA 2018': 'CIAS',
  'Coletânea Antiga': 'COLETÂNEA ANTIGA',
  'Avulsos 2018': 'AVULSOS',
  'Meus louvores': 'MEUS LOUVORES',
};
const ORDEM_COL = ['Coletânea 2018', 'CIA 2018', 'Coletânea Antiga', 'Avulsos 2018', 'Meus louvores'];
function nomeCol(s) { return NOME_COL[s.col] || String(s.col || '').toUpperCase(); }
function ehCias(s) { return s.col === 'CIA 2018'; }
// etiqueta curta da coletânea, usada quando a lista vem ranqueada (sem grupo)
function siglaCol(s) {
  return { 'Coletânea 2018': 'COLETÂNEA', 'CIA 2018': 'CIAS', 'Coletânea Antiga': 'ANTIGA',
           'Avulsos 2018': 'AVULSO', 'Meus louvores': 'MEU' }[s.col] || '';
}
// "AV" não é número: nos Avulsos a coluna fica com um traço em vez de repetir a sigla
function numLouvor(s) { return (!s.num || s.num === 'AV') ? '' : s.num; }
function numInt(s) { const n = numLouvor(s); return /^\d+$/.test(n) ? parseInt(n, 10) : null; }
// como o louvor se apresenta fora da lista (fila, barra de estado, celular),
// onde não existe o cabeçalho de grupo para dizer de que coletânea ele é
function rotuloLouvor(s) {
  const n = numLouvor(s), c = nomeCol(s);
  // palavra, nunca outro número: "709 2018" parecia um código duplo
  const curto = { 'COLETÂNEA 2018': 'COLETÂNEA', 'COLETÂNEA ANTIGA': 'ANTIGA', 'AVULSOS': 'AVULSO',
                  'MEUS LOUVORES': 'MEU', 'CIAS': 'CIAS' }[c] || c;
  return (n ? n + ' ' : '') + curto + ' · ' + s.titulo;
}

function renderListaLouvores(filtro) {
  const cont = $('#lista-louvores'); cont.innerHTML = '';
  const f = semAcento(filtro).trim();
  // digitar "60" tem que trazer o 60, não o 160, o 600 e o 1160: quando a busca
  // é só dígitos, o número casa por IGUALDADE, não por "contém"
  const soNumero = /^\d+$/.test(f) ? parseInt(f, 10) : null;
  const alvo = soLetras(filtro);
  const palavras = alvo ? alvo.split(' ').filter(Boolean) : [];
  window._somBusca = alvo ? somDaFrase(filtro) : [];   // usado pelo desempate fonético
  const achados = [];
  LOUVORES.forEach((s, i) => {
    let pontos = 1;
    if (f) {
      if (soNumero !== null) {                     // busca por número: igualdade
        if (numInt(s) !== soNumero) return;
        pontos = 1000;
      } else {
        pontos = pontuarLouvor(s, alvo, palavras);
        if (!pontos) return;
        s._naLetra = pontos <= 300;                // achou só na letra
      }
    }
    achados.push([s, i, pontos]);
  });
  // agrupa mantendo a ordem das coletâneas; a 2018 é a mais cantada, vem primeiro
  achados.sort((a, b) => {
    // PROCURANDO: manda a proximidade com o que foi digitado. LISTA INTEIRA:
    // manda a ordem natural (coletânea e número), que é como o operador folheia.
    if (f && b[2] !== a[2]) return b[2] - a[2];
    const d = ORDEM_COL.indexOf(a[0].col) - ORDEM_COL.indexOf(b[0].col);
    if (d) return d;
    const na = numInt(a[0]), nb = numInt(b[0]);
    if (na !== null && nb !== null) return na - nb;
    return a[1] - b[1];
  });

  // Agrupar por coletânea resolve a ambiguidade do NÚMERO (o 60 da 2018 e o 60
  // das CIAS). Mas em busca por TEXTO o grupo brigaria com a ordem de
  // proximidade — o cabeçalho se repetiria a cada linha. Então: número agrupa,
  // texto vem ranqueado, com a coletânea escrita em cada linha.
  const agrupar = !f || soNumero !== null;
  let colAtual = null;
  achados.forEach(([s, i]) => {
    if (agrupar && s.col !== colAtual) {      // cabeçalho da coletânea
      colAtual = s.col;
      const g = document.createElement('div');
      g.className = 'grupo-col' + (ehCias(s) ? ' cias' : '');
      g.textContent = nomeCol(s);
      cont.appendChild(g);
    }
    const naLista = est.fila.some(x => x.tipo === 'louvor' && x.chave === chaveLouvor(s));
    const d = document.createElement('div');
    d.className = 'item' + (naLista ? ' na-lista' : '') + (ehCias(s) ? ' cias' : '');
    d.dataset.i = i;
    const n = numLouvor(s);
    d.innerHTML = (naLista ? '<span class="marca-lista" title="Já está na lista de projeção">♪</span>' : '') +
      '<small>' + (n || '—') + '</small>' +
      (agrupar ? '' : '<small class="etq-col">' + siglaCol(s) + '</small>') + s.titulo +
      (f && s._naLetra ? ' <small style="color:#6fa8dc">· letra</small>' : '');
    // o clique simples espera um tico: se vier o segundo clique, ele é cancelado
    // e o louvor só vai pra lista — sem piscar no telão
    d.onclick = () => { clearTimeout(d._t); d._t = setTimeout(() => selecionarLouvor(i), 230); };
    d.ondblclick = () => {
      clearTimeout(d._t);
      selecionarLouvor(i, true);      // só mostra os slides no painel; não projeta
      adicionarLista({ tipo: 'louvor', idx: i, chave: chaveLouvor(s), rotulo: rotuloLouvor(s) });
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
  $('#tit-slides').textContent = rotuloLouvor(s);   // diz a coletânea também
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
  atualizarExtras();                 // este louvor tem cifra? tem animação?
  if (!semProjetar) projetarLouvor(i, 0, false);
  else marcarSlide();
}
// ---- recursos extras do louvor (cifra e animação das CIAS) ----------------
// A animação é importada pelo menu e fica na pasta do usuário; se o operador
// nunca importou nada, ANIMACOES fica vazio e o botão nem aparece — nada de
// botão morto no painel.
// A cifra vem de /api/musico, o MESMO catálogo que o celular usa. Assim a folha
// que o operador abre no computador e a que o músico lê no celular são a mesma,
// com os mesmos acordes nas mesmas colunas.
let ANIMACOES = {}, CIFRAS = {};
function carregarExtras() {
  fetch('/api/animacoes').then(r => r.json()).then(r => { ANIMACOES = r.indice || {}; atualizarExtras(); }).catch(() => {});
  fetch('/api/musico').then(r => r.json()).then(r => { CIFRAS = r.violao || {}; atualizarExtras(); }).catch(() => {});
}
function temAnimacao(s) { return !!(s && s.col === 'CIA 2018' && ANIMACOES[String(parseInt(s.num, 10))]); }
function daAnimacao(s) { return temAnimacao(s) ? ANIMACOES[String(parseInt(s.num, 10))] : null; }
// o catálogo guarda o TOM, e há cifra cujo tom o PDF não declarou (string vazia).
// Testar o valor esconderia o botão dessas: quem manda é a chave EXISTIR.
function temCifra(s) { return !!s && CIFRAS[chaveLouvor(s)] !== undefined; }

/* ---------- A CIFRA, DESENHADA AQUI DENTRO ----------
   Isto abria o PDF da coletânea num iframe. O PDF da Cifrada Nível II tem 93
   megabytes de página escaneada: mesmo num computador bom demorava, e o da
   igreja é o mais fraco que existe. Agora o servidor manda só os acordes já
   extraídos deste louvor — uns dois kilobytes — e quem desenha a folha é o
   Sistema, na hora.

   As funções abaixo são as MESMAS do controle.html, de propósito. Se o desenho
   divergisse, o operador e o músico estariam lendo cifras diferentes do mesmo
   louvor, e ninguém descobriria isso a não ser no meio do ensaio. */
let cifraDados = null,      // a resposta de /api/cifra do louvor aberto
    cifraLouvor = null,     // qual louvor está na tela (para descartar resposta atrasada)
    cifraTom = null,        // o tom IMPRESSO, o ponto de partida do transporte
    cifraDesloc = 0;        // quantos semitons acima/abaixo do impresso

function escaparCifra(t) {
  return (t || '').split('&').join('&amp;').split('<').join('&lt;');
}

/* Desenha a linha de acordes ACIMA da letra, cada um na coluna que veio do PDF.
   Em fonte monoespaçada a coluna É o caractere: acorde na coluna 8 fica em cima
   da 8ª letra. É por isso que a folha não pode usar fonte proporcional — com ela
   o alinhamento vai embora e a cifra perde a serventia. */
function linhaDeAcordes(acordes) {
  if (!acordes || !acordes.length) return '';
  let fila = '';
  for (const par of acordes) {
    const col = par[0], nome = par[1];
    // encostou no anterior: dois espaços, senão "DbmEb0" sai grudado e o músico
    // lê um acorde que não existe
    if (fila.length && fila.length >= col) fila += '  ';
    while (fila.length < col) fila += ' ';
    fila += nome;
  }
  return '<span class="ac">' + escaparCifra(fila) + '</span>\n';
}

/* ---------- TRANSPOR: o tom que o músico quiser ----------
   Como no Cifra Club: os doze tons numa grade, meio tom para cada lado e o
   restaurar. O deslocamento é só desta tela e do louvor aberto — nada disso
   mexe no telão nem no que o celular do músico está mostrando. */
const SEMI = {C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,'E#':5,Fb:4,F:5,'F#':6,Gb:6,
              G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11,'B#':0,Cb:11};
const SUS = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
const BEM = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B'];

/* Sustenido ou bemol: pela armadura do tom de destino, não por gosto. Tons de
   bemol (F, Bb, Eb, Ab, Db, Gb e suas relativas menores) se escrevem com bemol;
   o resto com sustenido. Escrever "A#" onde o músico espera "Bb" faz ele parar
   para pensar no meio do louvor. */
function usaBemol(tom) {
  if (!tom) return false;
  const raiz = tom.replace(/m$/, '');
  if (raiz.includes('b')) return true;
  if (raiz.includes('#')) return false;
  return (tom.endsWith('m') ? ['D','G','C','F','Bb','Eb'] : ['F','Bb','Eb','Ab','Db','Gb'])
         .includes(raiz);
}
function transpor(nota, passos, bemol) {
  if (!passos) return nota;                 // 0 devolve INTACTO: senão "Eb" viraria "D#"
  const m = /^([A-G])(#|b)?/.exec(nota || '');
  if (!m) return nota;
  const base = m[1] + (m[2] || '');
  if (!(base in SEMI)) return nota;
  const tab = bemol ? BEM : SUS;
  return tab[(SEMI[base] + passos % 12 + 12) % 12] + nota.slice(m[0].length);
}
function transporAcorde(a, passos, bemol) {
  return String(a).split('/').map(p => transpor(p, passos, bemol)).join('/');
}
function transporTom(tom, passos, bemol) {
  if (!tom) return tom;
  const menor = /m$/.test(tom);
  return transpor(menor ? tom.slice(0, -1) : tom, passos, bemol) + (menor ? 'm' : '');
}
// a grafia certa do tom que está valendo agora (o bemol depende do destino)
function tomAgora() {
  return transporTom(cifraTom, cifraDesloc,
                     usaBemol(transporTom(cifraTom, cifraDesloc, usaBemol(cifraTom))));
}

function pintarTomCifra() {
  const cx = $('#cifra-tom-cx'); if (!cx) return;
  if (!cifraDados || !cifraTom) { cx.innerHTML = ''; return; }
  cx.innerHTML = '<button class="tom-btn" id="cifra-tom-btn" title="Tocar em outro tom">' +
                 tomAgora() + '</button>';
  $('#cifra-tom-btn').onclick = abrirTons;
}

/* A grade dos doze tons. Escolher "Bb" direto é uma tacada; chegar nele
   apertando "+" seis vezes são seis. */
function abrirTons() {
  if ($('#tom-painel')) { fecharTons(); return; }
  const menor = /m$/.test(cifraTom || '');
  const escala = ['A','Bb','B','C','Db','D','Eb','E','F','F#','G','Ab'];
  const raizAtual = (tomAgora() || '').replace(/m$/, '');
  let h = '<div class="tom-painel" id="tom-painel"><div class="tom-linha">' +
          '<button data-d="-1">−½ tom</button><button data-d="1">+½ tom</button></div>' +
          '<div class="tom-grade">';
  for (const t of escala) {
    // mesma nota escrita de outro jeito ainda é a mesma tecla
    const igual = SEMI[t] === SEMI[raizAtual];
    h += '<button class="tom-op' + (igual ? ' on' : '') + '" data-t="' + t + '">' +
         t + (menor ? 'm' : '') + '</button>';
  }
  h += '</div>' + (cifraDesloc ? '<button class="tom-restaura" data-z="1">↺ Restaurar o tom impresso</button>' : '') + '</div>';
  $('#cifra-cab').insertAdjacentHTML('afterend', h);
  $('#tom-painel').onclick = e => {
    const b = e.target.closest('button'); if (!b) return;
    if (b.dataset.d) cifraDesloc += parseInt(b.dataset.d, 10);
    else if (b.dataset.z) cifraDesloc = 0;
    else if (b.dataset.t) {
      const raiz = (cifraTom || '').replace(/m$/, '');
      cifraDesloc = ((SEMI[b.dataset.t] - SEMI[raiz]) % 12 + 12) % 12;
      if (cifraDesloc > 6) cifraDesloc -= 12;      // −2 em vez de +10: o músico lê melhor
    }
    fecharTons(); redesenhar();
  };
}
function fecharTons() { const p = $('#tom-painel'); if (p) p.remove(); }

function redesenhar() {
  if (!cifraDados) return;
  // guarda onde a folha estava: trocar de tom no meio do terceiro verso não pode
  // jogar quem está lendo de volta para o começo da página
  const f = $('#cifra-folha'), y = f ? f.scrollTop : 0;
  desenharFolha(cifraDados);
  if (f) f.scrollTop = y;
}

function desenharFolha(d) {
  cifraDados = d;
  const f = $('#cifra-folha');
  cifraTom = d.violao ? (d.violao.tom || '') : null;
  const bemol = usaBemol(tomAgora());
  let cab = '';
  if (cifraDesloc) cab = '<p class="cab"><b>' + (cifraDesloc > 0 ? '+' : '') + cifraDesloc +
    (Math.abs(cifraDesloc) > 1 ? ' semitons' : ' semitom') + '</b> do impresso (' +
    (cifraTom || 'tom não declarado') + ')</p>';
  let corpo = '';
  if (d.violao && d.violao.linhas && d.violao.linhas.length) {
    for (const l of d.violao.linhas) {
      const a = (l.a || []).map(par => [par[0], transporAcorde(par[1], cifraDesloc, bemol)]);
      corpo += linhaDeAcordes(a) + escaparCifra(l.t) + '\n';
    }
  } else {
    corpo = 'Este louvor não tem cifra.';
  }
  f.innerHTML = cab + '<pre>' + corpo + '</pre>';
  pintarTomCifra();
}

/* Tamanho da letra da folha: quem lê esta tela muitas vezes está com o violão na
   mão, um metro atrás do monitor. */
let cifraFonte = 14;
function aplicarFonteCifra() {
  const f = $('#cifra-folha'); if (f) f.style.setProperty('--cf', cifraFonte + 'px');
}
function ajustarFonteCifra(d) {
  cifraFonte = clamp(cifraFonte + d, 10, 30);
  aplicarFonteCifra();
  Guardar.gravar('icm_cifra_fonte', cifraFonte);
}
// Ao contrário dos outros A−/A+, este tamanho fica GRAVADO ao lado do programa —
// e por isso é o único que o "Restaurar" precisa apagar de verdade. Sem esta
// função, quem tivesse posto a folha em 30px continuava em 30px depois de mandar
// restaurar os tamanhos, e até depois do "Restaurar tudo".
function fonteCifraPadrao() {
  cifraFonte = 14;
  aplicarFonteCifra();
  Guardar.gravar('icm_cifra_fonte', 14);
}

async function abrirCifra() {
  const s = est.louvorIdx >= 0 ? LOUVORES[est.louvorIdx] : null;
  if (!temCifra(s)) { toast('Este louvor não tem cifra.'); return; }
  cifraLouvor = s; cifraDados = null; cifraTom = null;
  cifraDesloc = 0;                       // louvor novo começa no tom impresso
  fecharTons();
  $('#cifra-tit').textContent = rotuloLouvor(s);
  $('#cifra-tom-cx').innerHTML = '';
  $('#cifra-folha').innerHTML = '<p class="cab">Carregando…</p>';
  $('#cifra-ov').classList.remove('oculto');
  window.Icones && window.Icones.aplicar($('#cifra-ov'));
  aplicarFonteCifra();
  est.modoCifra = true; atualizarExtras();
  try {
    // em=C pede a folha de VIOLÃO, a de acordes. Os cadernos melódicos (Bb, Eb,
    // F) são para o músico ler no próprio celular, cada um no dele.
    const d = await fetch('/api/cifra/' + encodeURIComponent(chaveLouvor(s)) + '?em=C')
                    .then(r => r.json());
    if (cifraLouvor !== s) return;   // ele já abriu outro louvor: esta resposta não vale mais
    desenharFolha(d);
  } catch (e) {
    $('#cifra-folha').innerHTML = '<p class="cab">Não consegui carregar a cifra deste louvor.</p>';
  }
}
function fecharCifra() {
  $('#cifra-ov').classList.add('oculto');
  fecharTons();
  cifraDados = null; cifraLouvor = null;   // solta a folha da memória
  est.modoCifra = false; atualizarExtras();
}

// Liga/desliga a exibição animada das CIAS. Ela vem LIGADA: é assim que o louvor
// de criança se apresenta. Desligando, cai no texto normal.
function alternarAnimacao() {
  est.modoAnim = est.modoAnim === false;      // undefined/true -> false; false -> true
  atualizarExtras();
  if (est.louvorIdx >= 0) projetarLouvor(est.louvorIdx, est.louvorSlide || 0, true);
  toast(est.modoAnim === false ? 'Exibindo o texto deste louvor.' : 'Exibindo a animação das CIAS.');
}

// Mostra/esconde os botões conforme o louvor que está selecionado agora.
function atualizarExtras() {
  const barra = $('#barra-extras'), bc = $('#btn-cifra'), ba = $('#btn-anim');
  if (!barra) return;
  const s = est.louvorIdx >= 0 ? LOUVORES[est.louvorIdx] : null;
  const cifra = temCifra(s), anim = temAnimacao(s);
  bc.classList.toggle('oculto', !cifra);
  ba.classList.toggle('oculto', !anim);
  barra.classList.toggle('oculto', !cifra && !anim);
  // o "!!" não é enfeite: est.modoCifra nasce indefinido, e toggle(classe,
  // undefined) INVERTE em vez de desligar — o botão acendia sozinho a cada
  // louvor escolhido, dizendo que a cifra estava aberta quando não estava
  bc.classList.toggle('on', !!(cifra && est.modoCifra));
  // a animação vem LIGADA por natureza: é assim que o louvor de CIAS se apresenta
  ba.classList.toggle('on', anim && est.modoAnim !== false);
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
    // 1 clique PROJETA. Se esse versículo já está na Lista, a navegação continua
    // obedecendo a Lista — antes o clique fazia setPos = -1 e o Sistema "esquecia"
    // os outros escolhidos, virando leitura solta do capítulo.
    b.onclick = () => {
      est.setPos = -1;
      projetarVerso(est.livro, c, v);
      devolverPosicaoNaFila({ livro: est.livro, cap: c, v });
    };
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
  sugerirPara(livro, cap, v);   // louvores que combinam com este versículo
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
  est.setPos = i; est.vistaFim = i; est.contAfter = 0; est.contAntes = 0; est.juntos = false;
  if (it.tipo === 'louvor') {
    const k = idxDoItem(it);
    if (k < 0 || !LOUVORES[k]) { toast('Este louvor não está mais disponível.'); renderFila(); return; }
    selecionarLouvor(k);
    // aoFim: chegando por Voltar, abre no último slide em vez de recomeçar
    if (aoFim) projetarLouvor(k, telasDoLouvor(k) - 1, false);
  }
  else projetarVerso(it.livro, it.cap, it.v);
  est.setPos = i; est.vistaFim = i; renderFila();
}
// JUNTOS: projeta os versículos MARCADOS (✓) juntos numa tela só; atualiza ao vivo ao marcar/reordenar
// Se o versículo que está no ar está na Lista, a navegação tem que voltar a
// obedecer a Lista. Sem isso o operador ficava preso na leitura contínua sem
// entender por quê — a lista estava ali, montada, e o Voltar a ignorava.
function devolverPosicaoNaFila(v) {
  const i = est.fila.findIndex(x => x.tipo === 'verso' && x.livro === v.livro && x.cap === v.cap && x.v === v.v);
  if (i >= 0) { est.setPos = i; est.vistaFim = i; est.contAfter = 0; est.contAntes = 0; renderFila(); }
}
function projetarVersiculosJuntos() {
  const versos = est.fila.filter(x => x.tipo === 'verso' && x.on === true);
  if (!versos.length) { toast(est.fila.some(x => x.tipo === 'verso') ? 'Marque (✓) os versículos que devem aparecer juntos' : 'Adicione versículos (2 cliques) à lista'); return; }
  if (versos.length === 1) {                  // um só marcado -> versículo normal (não estica pra tela toda)
    const s = versos[0]; est.juntos = false;
    projetarVerso(s.livro, s.cap, s.v);
    // DEVOLVE a posição na lista. O modo "juntos" zera setPos de propósito, mas
    // ao desmarcar e sobrar um só versículo ninguém devolvia — e o Voltar passava
    // a ler o capítulo de trás em vez de ir ao versículo anterior da lista.
    devolverPosicaoNaFila(s);
    return;
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
    // Já cantado: item do MESMO grupo que ficou para trás. No meio do culto o
    // operador precisa bater o olho e saber o que já passou e o que falta —
    // senão ele não sabe onde parou nem qual é o próximo. Voltar desfaz a marca.
    const atualNaFila = est.setPos >= 0 ? est.fila[est.setPos] : null;
    const jaFoi = !!atualNaFila && it.tipo === atualNaFila.tipo && i < est.setPos;
    const d = document.createElement('div');
    d.className = 'fila-item' + (naVista ? ' atual' : '') + (jaFoi ? ' ja-foi' : '') + (chkOn ? ' agrupado' : '');
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
// A Lista tem dois grupos — LOUVORES e VERSÍCULOS — e eles NÃO conversam.
// Uma hora é a hora do louvor, outra é a hora da palavra: avançar dentro dos
// versículos nunca pode cair num louvor, nem o contrário. Antes a fila era
// percorrida em linha reta e voltar do primeiro versículo caía no louvor de trás.
function vizinhoNaFila(dir) {
  const atual = est.fila[est.setPos]; if (!atual) return -1;
  for (let i = est.setPos + dir; i >= 0 && i < est.fila.length; i += dir) {
    if (est.fila[i].tipo === atual.tipo) return i;
  }
  return -1;
}
function temProximoNaLista() { return est.setPos >= 0 && vizinhoNaFila(1) >= 0; }
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
    // voltando dos versículos que ficaram ANTES do primeiro escolhido: desanda o
    // caminho até reencontrar a lista, em vez de seguir o capítulo para sempre
    if (est.contAntes > 0) {
      est.contAntes--;
      if (est.contAntes === 0) projetarItemLista(est.setPos); else bibliaProximo();
      return;
    }
    const prox = vizinhoNaFila(1);
    if (prox >= 0) { projetarItemLista(prox); return; }   // próximo DO MESMO GRUPO
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
    if (s) projetarLouvor(est.louvorIdx, telasDoLouvor(est.louvorIdx) - 1, false);
    return;
  }
  const noAr = est.live && est.live.tipo;      // o que está no ar manda (ver proximo())
  if (noAr === 'slide') { slideAnterior(); return; }
  if (noAr === 'timer' || noAr === 'relogio' || noAr === 'texto' || noAr === 'fundo' || noAr === 'preto') return;
  if (est.setPos >= 0) {
    // voltando pro louvor anterior, cai no ÚLTIMO slide dele — recomeçar do
    // slide 1 obrigava a apertar Avançar 5, 6 vezes na frente da congregação
    const ant = vizinhoNaFila(-1);                       // anterior DO MESMO GRUPO
    if (est.live && est.live.tipo === 'louvor') { if (est.louvorSlide > 0) louvorAnterior(); else if (ant >= 0) projetarItemLista(ant, true); return; }
    if (est.contAfter > 0) { est.contAfter--; if (est.contAfter === 0) projetarItemLista(est.setPos); else bibliaAnterior(); return; }
    if (est.contAntes > 0 && est.bibPos) { est.contAntes++; bibliaAnterior(); return; }
    if (ant >= 0) { projetarItemLista(ant, true); return; }  // item anterior (respeita a ordem que você montou)
    // Antes do PRIMEIRO escolhido: segue lendo o capítulo para trás, mas CONTANDO
    // os passos. Antes daqui saía `est.setPos = -1`, que largava a lista de vez —
    // depois disso o Avançar não voltava mais para os versículos escolhidos,
    // seguia o capítulo direto. Agora o caminho de volta existe.
    if (est.bibPos) { est.contAntes++; bibliaAnterior(); }
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
  fecharNoAr();                       // saiu do ar: fecha o cronômetro
  // pedir a espera na mão é uma ordem para o telão OBEDECER: aí sim descongela
  if (est.freeze && !manterCongelado) { est.freeze = false; $('#btn-congelar').classList.remove('freeze-on'); }
  est.live = { tipo: 'descanso' };
  projetar({ modo: 'fundo', fundo: esperaAtual(), transicao: true, fade: 500 });
}
// Põe no telão o que está selecionado AGORA, na ordem do que faz mais sentido:
// versículos marcados > item da lista > versículo aberto > louvor aberto.
function projetarSelecaoAtual() {
  if (est.fila.some(x => x.tipo === 'verso' && x.on === true)) { projetarVersiculosJuntos(); return; }
  if (est.setPos >= 0 && est.fila[est.setPos]) { projetarItemLista(est.setPos); return; }
  if (est.bibPos) { projetarVerso(est.bibPos.livro, est.bibPos.cap, est.bibPos.v); return; }
  if (est.louvorIdx >= 0 && LOUVORES[est.louvorIdx]) { projetarLouvor(est.louvorIdx, est.louvorSlide || 0, false); return; }
  if (est.fila.length) { projetarItemLista(0); return; }
  toast('Escolha um louvor ou versículo para projetar.');
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
  // Com o telão ligado na tela de espera o botão dizia "Em espera" e clicar nele
  // não fazia nada — rótulo de estado onde tinha que haver ação. Agora ele
  // convida: "Projetar" põe no ar o que está selecionado.
  b.innerHTML = (noAr ? '<span class="ico" data-i="descanso"></span> Parar de projetar'
                      : '<span class="ico" data-i="play"></span> ' + (est.projetando ? 'Projetar' : 'Abrir Projeção'));
  // "Em espera" NÃO é a mesma coisa que "Abrir Projeção": o telão já está ligado.
  // A dica dizia "Abrir a projeção no projetor" e o operador clicava esperando
  // religar alguma coisa — e nada acontecia.
  b.title = noAr ? 'Volta para a tela de espera (o telão continua ligado)'
                 : (est.projetando ? 'Põe no telão o que está selecionado'
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
    : (emEspera ? 'Tela de espera no telão' : (est.projetando ? 'Projetando ao vivo' : 'Telão desligado'));
  if (selo) { selo.textContent = congelado ? 'Congelado' : (emEspera ? 'Em espera' : (est.projetando ? 'Ao vivo' : 'Prévia')); selo.className = 'prev-selo' + classe; }
  // A bolinha VERMELHA quer dizer uma coisa só: está indo pro telão agora.
  // Ela acendia também na tela de espera, e o vermelho contradizia o "em espera".
  const dot = $('#dot');
  dot.classList.toggle('on', est.projetando && !congelado && !emEspera);
  dot.classList.toggle('espera', emEspera);
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
  cifraFonte = clamp(parseInt(Guardar.ler('icm_cifra_fonte', 14), 10) || 14, 10, 30);
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
  // o histórico só é lido ao abrir o Painel: não pesa nada no arranque
  if (sec === 'painel') abrirPainel();
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
  // Zerar só a memória não restaura nada: a escolha da tela de espera fica
  // gravada em 'icm_espera' e voltava sozinha no arranque seguinte.
  if (o === 'fundos' || o === 'tudo') {
    CUSTOM = []; OCULTOS = []; salvarCustom(); salvarOcultos();
    est.descansoFundo = null; est.textoFundo = null;
    Guardar.gravar('icm_espera', null);
    renderFundos();
  }
  if (o === 'tamanhos' || o === 'tudo') { est.escalaLouvor = est.escalaVers = est.escalaTexto = 1; atualizarTamLabel(); fonteCifraPadrao(); }
  if (o === 'louvores' || o === 'tudo') { MEUS = []; salvarMeus(); recarregarLouvores(); renderMeus(); }
  if (o === 'slides' || o === 'tudo') {   // apaga as apresentações importadas
    SLIDES = []; est.slidePos = -1; renderSlides(); statusSlides('');
    try { fetch('/api/limpar', { method: 'POST' }); } catch (e) {}
  }
  if (o === 'tudo') {
    // "de fábrica" tem que incluir a Lista de Projeção e onde a navegação parou.
    // Sem isto o Sistema voltava com a lista do culto anterior montada e o
    // realce em cima de um item que o operador achava que tinha apagado.
    est.fila = []; est.setPos = -1; est.vistaFim = null; est.juntos = false;
    est.contAfter = 0; est.contAntes = 0; est.bibPos = null;
    est.louvorIdx = -1; est.louvorSlide = 0; est.aguardando = false;
    est.freeze = false; est.telaCongelada = null; est.live = null;
    est.timerFim = 0; est.timerParadoMs = 0;
    renderFila();
    IGREJA = { nome: '', endereco: '', cultos: CULTOS_PADRAO.map(c => Object.assign({}, c)) };
    salvarIgreja(); aplicarNomeIgreja(); renderCultos(); renderAvisos();
    est.estilo = 'limpo'; aplicarEstilo(); $('#estilo-nome').textContent = ESTILO_NOME[est.estilo];
    Guardar.gravar('icm_bemvindo_ok', false);
    fecharMenu(); abrirBemVindo(true); return;   // volta pro começo, como um sistema novo
  }
  toast('Configurações restauradas ao padrão.');
}
// caixa de confirmação (nada destrutivo acontece sem o operador confirmar)
function confirmar(msg, aoConfirmar, rotulo) {
  const ov = document.createElement('div'); ov.className = 'ajuda-overlay';
  ov.innerHTML = '<div class="ajuda-box" style="max-width:430px"><h3>Confirmar</h3><p>' + msg + '</p>' +
    '<div class="ajuda-btns"><button class="big-btn vermelho" id="cf-sim">' + (rotulo || 'Sim, restaurar') + '</button>' +
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

/* ---------- ATUALIZAÇÃO: buscar, avisar e instalar ----------
   A busca é um pedido leve ao GitHub (só o número da versão). A instalação
   baixa SÓ o programa (~58 MB): o conteúdo pesado mora nos dados do usuário
   e nenhuma atualização baixa ele de novo. */
function ligarAtualizacao() {
  const bb = $('#btn-atualizar'), ba = $('#btn-atu-auto');
  if (!bb || !ba) return;
  const pintarAuto = () => { ba.textContent = Guardar.ler('atu_auto', true) ? 'Ligado' : 'Desligado'; };
  pintarAuto();
  ba.onclick = () => { Guardar.gravar('atu_auto', !Guardar.ler('atu_auto', true)); pintarAuto(); };
  bb.onclick = () => verificarAtualizacao(false);
  // ao abrir: pesquisa em silêncio, se o dono deixou ligado. Sem internet,
  // nada aparece — a igreja não pode ver erro só por não ter internet.
  if (Guardar.ler('atu_auto', true)) setTimeout(() => verificarAtualizacao(true), 5000);
}
async function verificarAtualizacao(silenciosa) {
  const st = $('#atu-status');
  if (!silenciosa && st) st.textContent = 'Procurando…';
  let r = null;
  try { r = await fetch('/api/atualizacao').then(x => x.json()); } catch (e) {}
  if (!r || !r.ok) {
    if (!silenciosa && st) st.textContent = 'Sem internet agora. O Sistema segue funcionando normal.';
    return;
  }
  if (!r.tem) {
    // a melhor versão de todas — atualizada E completa — merece o dourado:
    // é a sensação de plano PRO, só que de graça
    let tudo = null;
    try { tudo = await fetch('/api/conteudo').then(x => x.json()); } catch (e) {}
    if (st) {
      if (tudo && !tudo.falta) {
        st.innerHTML = '<b class="st-ouro">Você está com a melhor versão do Sistema: ' +
                       'completa e atualizada (' + r.atual + ').</b>';
      } else if (!silenciosa) {
        st.textContent = 'Você já está na versão mais nova (' + r.atual + ').';
      }
    }
    return;
  }
  if (st) st.textContent = 'Existe a versão ' + r.nova + ' (você está na ' + r.atual + ').';
  if (silenciosa) { toast('Há uma versão nova do Sistema (' + r.nova + ') — veja em Configurações › Sistema.'); return; }
  confirmar('Existe uma versão nova (<b>' + r.nova + '</b>). Atualizar agora?<br><br>' +
            'O Sistema vai fechar e reabrir sozinho. Suas coisas não são apagadas, ' +
            'e as animações e cifras não baixam de novo.', async () => {
    await fetch('/api/atualizar', { method: 'POST', body: '{}' });
    const t = setInterval(async () => {
      let a = null;
      try { a = await fetch('/api/atualizar').then(x => x.json()); } catch (e) { return; }
      if (!a) return;
      if (a.erro) { clearInterval(t); if (st) st.textContent = a.erro; return; }
      if (st) st.textContent = (a.txt || 'Baixando…') + (a.pct ? ' — ' + a.pct + '%' : '');
      if (a.fim) clearInterval(t);
    }, 800);
  }, 'Atualizar agora');
}

/* ---------- COMPLETAR O SISTEMA ----------
   Quem instalou o essencial (58 MB) completa por aqui: baixa as animações,
   cifras e melodias da nuvem, direto para os dados — sem reinstalar nada.
   A linha só aparece quando o conteúdo realmente falta. */
function ligarCompletar() {
  const linha = $('#linha-completar'), st = $('#comp-status'), b = $('#btn-completar');
  if (!b) return;
  fetch('/api/conteudo').then(r => r.json()).then(r => {
    if (r && r.falta) linha.hidden = false;
  }).catch(() => {});
  b.onclick = () => {
    confirmar('Baixar as animações das CIAS, as cifras e os cadernos de melodia '
              + '(cerca de <b>590 MB</b>)?<br><br>Precisa de internet. O Sistema '
              + 'continua funcionando normalmente enquanto baixa.', async () => {
      await fetch('/api/conteudo', { method: 'POST', body: '{}' });
      b.disabled = true;
      const t = setInterval(async () => {
        let a = null;
        try { a = await fetch('/api/conteudo').then(x => x.json()); } catch (e) { return; }
        if (!a) return;
        if (a.erro) { clearInterval(t); b.disabled = false; st.textContent = a.erro; return; }
        st.textContent = (a.txt || 'Baixando…') + (a.pct ? ' — ' + a.pct + '%' : '');
        if (a.fim) {
          clearInterval(t);
          toast('Pronto! As animações e cifras já estão no Sistema.');
          linha.hidden = true;
          carregarExtras();          // os botões de animação e cifra acordam na hora
        }
      }, 900);
    }, 'Baixar agora');
  };
}

/* ---------- EXPORTAR PARA PENDRIVE ----------
   Grava no pendrive o instalador guardado + a pasta Conteudo (animações,
   cifras, melodias, configurações, louvores e fundos próprios). No outro
   computador são dois cliques: o instalador copia a pasta sozinho. */
function ligarExportarUsb() {
  const st = $('#usb-status'), b = $('#btn-usb');
  if (!b) return;
  b.onclick = async () => {
    let r = null;
    try { r = await fetch('/api/pendrives').then(x => x.json()); } catch (e) {}
    const us = (r && r.pendrives) || [];
    if (!us.length) { st.textContent = 'Nenhum pendrive plugado. Coloque um e clique de novo.'; return; }
    // mais de um plugado: vai no de mais espaço livre, dizendo qual foi
    const alvo = us.reduce((a, b2) => (b2.livre > a.livre ? b2 : a), us[0]);
    const gb = (alvo.livre / 1073741824).toFixed(1);
    confirmar('Exportar o Sistema para <b>' + alvo.nome + '</b> (' + alvo.letra.slice(0, 2) +
              ', ' + gb + ' GB livres)?<br><br>Vai junto: o instalador, as animações, as ' +
              'cifras, as melodias e as suas configurações.', async () => {
      await fetch('/api/exportar-usb', { method: 'POST', body: JSON.stringify({ letra: alvo.letra }) });
      const t = setInterval(async () => {
        let a = null;
        try { a = await fetch('/api/exportar-usb').then(x => x.json()); } catch (e) { return; }
        if (!a) return;
        if (a.erro) { clearInterval(t); st.textContent = a.erro; return; }
        st.textContent = (a.txt || 'Copiando…') + (a.pct ? ' — ' + a.pct + '%' : '');
        if (a.fim) clearInterval(t);
      }, 800);
    }, 'Exportar');
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
  // Projetar <-> Parar de projetar. O estado do meio ("Em espera") deixou de ser
  // um rótulo morto: dali o clique põe no ar o que está selecionado.
  $('#btn-projecao').onclick = () => {
    if (!est.projetando) { abrirProjecao(); return; }
    const emEspera = est.live && est.live.tipo === 'descanso';
    if (emEspera) projetarSelecaoAtual();
    else { descanso(); toast('Tela de espera no telão.'); }
  };
  $('#btn-proximo').onclick = proximo; $('#btn-anterior').onclick = anterior;
  $('#btn-menor').onclick = () => ajustarTam(-0.3); $('#btn-maior').onclick = () => ajustarTam(+0.3);
  $('#tam-label').onclick = tamPadrao;                      // clicar no rótulo volta ao padrão
  $('#btn-congelar').onclick = toggleFreeze;   // "Parar de projetar" já faz o papel da espera
  const bcf = $('#btn-cifra'); if (bcf) bcf.onclick = abrirCifra;
  const sm = $('#sug-mais'); if (sm) sm.onclick = maisSugestoes;
  $$('.pn-f').forEach(b => b.onclick = () => {
    $$('.pn-f').forEach(x => x.classList.toggle('ativo', x === b));
    histDias = +b.dataset.dias; pintarPainel();
  });
  const cx = $('#cifra-x'); if (cx) cx.onclick = fecharCifra;
  const cme = $('#cifra-menor'); if (cme) cme.onclick = () => ajustarFonteCifra(-1);
  const cma = $('#cifra-maior'); if (cma) cma.onclick = () => ajustarFonteCifra(+1);
  const cov = $('#cifra-ov'); if (cov) cov.onclick = e => { if (e.target === cov) fecharCifra(); };
  const ban = $('#btn-anim'); if (ban) ban.onclick = alternarAnimacao;
  carregarExtras();                            // cifras e animações que já foram importadas
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
  ligarAtualizacao();
  ligarExportarUsb();
  ligarCompletar();
  const bc = $('#btn-contato');
  if (bc) bc.onclick = () => {
    const mail = 'samuelsaxdiesel@gmail.com';
    try { navigator.clipboard.writeText(mail); } catch (e) {}
    toast('E-mail copiado: ' + mail);
  };
  $$('[data-ir]').forEach(b => b.onclick = () => menuSecao(b.dataset.ir));
  $$('[data-reset]').forEach(b => b.onclick = () => resetar(b.dataset.reset));
  document.addEventListener('keydown', e => {
    // com uma janela aberta (menu, boas-vindas, confirmação) as teclas NÃO mexem no telão
    // a cifra aberta também segura as teclas: ali a seta rola a folha. Se ela
    // passasse adiante, o telão trocaria de slide com o operador olhando a cifra.
    const cif = $('#cifra-ov');
    if (cif && !cif.classList.contains('oculto')) {
      if (e.key === 'Escape') { fecharCifra(); return; }
      const f = $('#cifra-folha'); if (!f) return;
      const salto = { ArrowDown: 60, ArrowUp: -60, ' ': f.clientHeight * 0.9,
                      PageDown: f.clientHeight * 0.9, PageUp: -f.clientHeight * 0.9,
                      Home: -1e7, End: 1e7 }[e.key];
      if (salto !== undefined) { e.preventDefault(); f.scrollTop += salto; }
      return;
    }
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
    case 'verso':   est.setPos = -1; projetarVerso(c.livro, c.cap, c.v);
                    devolverPosicaoNaFila(c); break;   // mesmo cuidado do computador
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
    // o celular manda um louvor pra Lista sem projetar nada — é como o grupo de
    // louvor monta a ordem do culto de onde estiver
    case 'addlouvor': {
      const s2 = LOUVORES[c.idx]; if (!s2) break;
      adicionarLista({ tipo: 'louvor', idx: c.idx, chave: chaveLouvor(s2), rotulo: rotuloLouvor(s2) });
      break;
    }
    case 'tirardalista': {
      if (c.i >= 0 && c.i < est.fila.length) removerFila(c.i);
      break;
    }
    case 'irpara': {
      if (c.i >= 0 && c.i < est.fila.length) projetarItemLista(c.i);
      break;
    }
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
        // a Lista de Projeção vai inteira pro celular: o grupo de louvor precisa
        // VER o que está montado e poder acrescentar, sem pedir pro operador
        fila: est.fila.map(x => ({ tipo: x.tipo, rotulo: x.tipo === 'louvor' ? x.rotulo : x.ref, on: x.on === true })),
        pos: est.setPos,
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
  // A prévia não nasce PRETA. Ela já mostra a tela de espera — a do Sistema, ou
  // a que o operador escolheu antes. É o que ele espera ver quando abre, e não
  // precisa que ninguém explique que aquilo é a "tela de espera".
  est.live = { tipo: 'descanso' };
  est.ultimo = { modo: 'fundo', fundo: esperaAtual(), estilo: est.estilo, transicao: false };
  previews.forEach(w => post(w, est.ultimo));
  ligarEventos(); atualizarProjBtn(); atualizarAgora();
  abrirBemVindo(false);   // primeira vez: apresentação + configuração da igreja
}
document.addEventListener('DOMContentLoaded', iniciar);
})();
