/* AFINADOR — roda no PRÓPRIO aparelho, nada de áudio viajando pela rede.
 *
 * O desenho é o que o Samuel descreveu, e ele está certo: não precisa de
 * biblioteca nenhuma. É matemática em cima do áudio cru.
 *
 *   1. o microfone entrega blocos de amostras (2048 a 48 kHz = 43 ms)
 *   2. PORTÃO DE SILÊNCIO: se o volume (RMS) está abaixo do limiar, nem analisa.
 *      Sem isso o mostrador fica pulando com o barulho da igreja.
 *   3. AUTOCORRELAÇÃO: o sinal comparado consigo mesmo, deslocado. O
 *      deslocamento que mais casa é o período da onda; 1/período é a
 *      frequência. É melhor que procurar o pico da FFT no meio da barulheira,
 *      porque casa com a FORMA da onda e não com a energia — e a corda do
 *      violão tem o harmônico mais forte que a fundamental muitas vezes, o que
 *      engana quem só procura o pico mais alto.
 *   4. nota = 12 x log2(f / 440) + 69, e o desvio em CENTS é o resto.
 *
 * Toda afinação alternativa (meio tom abaixo, Drop D, viola, violino) é só
 * outra lista de alvos — a mesma comparação transformada.
 *
 * MICROFONE E HTTPS: getUserMedia só funciona em contexto seguro. No computador
 * (localhost) funciona sempre; no celular, só com HTTPS. Quando não dá, este
 * arquivo diz o motivo em português em vez de morrer calado.
 */
(function () {
  'use strict';

  var NOMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

  // ---- a matemática ------------------------------------------------------
  // MIDI 69 = A4 = 440 Hz. Daqui sai tudo: nome da nota, oitava e desvio.
  function deHz(f, la) {
    return 12 * Math.log(f / (la || 440)) / Math.LN2 + 69;
  }
  function paraHz(n, la) {
    return (la || 440) * Math.pow(2, (n - 69) / 12);
  }
  function nomeDe(midi) {
    var i = ((Math.round(midi) % 12) + 12) % 12;
    return NOMES[i] + (Math.floor(Math.round(midi) / 12) - 1);
  }

  // O que um instrumento de igreja produz. O piso vai a 30 Hz por causa do Mi
  // grave do BAIXO (41,2 Hz): com o piso antigo de 55 Hz o baixista não
  // conseguia afinar justamente a corda mais grave — o banco de prova pegou.
  var HZ_MIN = 30, HZ_MAX = 1600;

  /* AUTOCORRELAÇÃO NORMALIZADA, de janela FIXA, com interpolação parabólica.
     Três decisões, todas medidas no banco de prova (ferramentas/teste_afinador.html):

     - JANELA FIXA. A receita clássica compara b[0..n-i] consigo mesma, e a soma
       encurta conforme o deslocamento cresce. Isso pende a favor dos
       deslocamentos curtos e o afinador lê SEMPRE um pouco agudo (no banco, todo
       erro dava para o mesmo lado, até +4,6 cents no Mi grave). Comparando
       sempre o MESMO número de amostras o viés some.
     - NORMALIZADA. Dividir pela energia das duas janelas devolve um número
       entre -1 e 1 — um "quanto casou" comparável entre deslocamentos, que
       serve de medida de confiança honesta.
     - PRIMEIRO pico forte, não o maior. O maior pico pode ser o do dobro do
       período (a oitava abaixo); o primeiro que chega perto dele é o certo.

     Só percorre a faixa útil de deslocamento, então custa MENOS que a versão
     anterior mesmo fazendo mais conta. */
  function frequencia(buf, taxa) {
    var n = buf.length, i, j;

    // 1) portão de silêncio: quanta energia tem aqui?
    var soma = 0;
    for (i = 0; i < n; i++) soma += buf[i] * buf[i];
    var rms = Math.sqrt(soma / n);
    if (rms < 0.01) return { hz: 0, rms: rms };      // silêncio: não chuta nada

    var b = buf;

    /* BUSCA GROSSA, no sinal reduzido a 1/4.
       Varrer todos os deslocamentos no sinal cheio custava 15 ms por leitura —
       quase um quadro inteiro de tela, e isso 60 vezes por segundo no celular
       do músico. Procurar primeiro num sinal 4 vezes menor acha a vizinhança
       do período por 1/16 do preço; depois só a vizinhança é refinada no sinal
       cheio, e a precisão fica a mesma (o banco de prova confere). Somar 4
       amostras de cada vez também já serve de filtro contra o agudo. */
    var D = 4, m = (n / D) | 0;
    var bd = new Float32Array(m);
    for (i = 0; i < m; i++) {
      var acc = 0;
      for (j = 0; j < D; j++) acc += b[i * D + j];
      bd[i] = acc / D;
    }
    var taxaD = taxa / D;
    var lagMinD = Math.max(2, Math.floor(taxaD / HZ_MAX));
    var lagMaxD = Math.min(m - 128, Math.ceil(taxaD / HZ_MIN));
    if (lagMaxD <= lagMinD) return { hz: 0, rms: rms };

    var casou = correlaciona(bd, lagMinD, lagMaxD, m - lagMaxD);
    if (!casou || casou.maior < 0.45) return { hz: 0, rms: rms };

    // BUSCA FINA no sinal cheio, só ao redor do que a grossa apontou
    var centro = casou.pos * D;
    var lagMin = Math.max(2, centro - 2 * D);
    var lagMax = Math.min(n - 256, centro + 2 * D);
    var fina = correlaciona(b, lagMin, lagMax, n - (lagMax + 1));
    if (!fina) return { hz: 0, rms: rms };

    var hz = taxa / fina.fino;
    if (hz < HZ_MIN || hz > HZ_MAX) return { hz: 0, rms: rms };
    return { hz: hz, rms: rms, casou: casou.maior };
  }

  /* Correlação normalizada de JANELA FIXA numa faixa de deslocamento, com a
     parábola por cima do melhor ponto. Janela fixa (o mesmo número de amostras
     em todo deslocamento) é o que tira o viés que fazia o afinador ler agudo. */
  function correlaciona(b, lagMin, lagMax, W) {
    var i, j;
    if (W < 128 || lagMax <= lagMin) return null;
    var e0 = 0;
    for (j = 0; j < W; j++) e0 += b[j] * b[j];
    if (!e0) return null;

    var r = new Float32Array(lagMax - lagMin + 1), maior = -2, pos = -1;
    for (i = lagMin; i <= lagMax; i++) {
      var s = 0, e = 0, y;
      for (j = 0; j < W; j++) {
        y = b[j + i];
        s += b[j] * y;
        e += y * y;
      }
      var v = e > 0 ? s / Math.sqrt(e0 * e) : 0;
      r[i - lagMin] = v;
      if (v > maior) { maior = v; pos = i; }
    }
    // o PRIMEIRO pico que chega a 90% do melhor — o maior pode ser o do dobro
    // do período, e aí o afinador mostraria a oitava abaixo
    var alvo = maior * 0.9;
    for (i = lagMin + 1; i < lagMax; i++) {
      var k = i - lagMin;
      if (r[k] >= alvo && r[k] >= r[k - 1] && r[k] >= r[k + 1]) { pos = i; break; }
    }
    var k0 = pos - lagMin;
    var x0 = k0 > 0 ? r[k0 - 1] : r[k0],
        x1 = r[k0],
        x2 = k0 + 1 < r.length ? r[k0 + 1] : r[k0];
    var a = (x0 + x2 - 2 * x1) / 2, bb = (x2 - x0) / 2;
    return { pos: pos, maior: maior, fino: a ? pos - bb / (2 * a) : pos };
  }

  // ---- os instrumentos ---------------------------------------------------
  // Cada corda é guardada em MIDI, não em Hz: assim o "meio tom abaixo" é uma
  // subtração, e mudar o Lá de referência (440/442) recalcula tudo sozinho.
  function m(nome) {                     // "E2" -> midi
    var s = nome.match(/^([A-G]#?)(-?\d)$/);
    return NOMES.indexOf(s[1]) + (parseInt(s[2], 10) + 1) * 12;
  }
  var INSTRUMENTOS = [
    { id: 'violao', nome: 'Violão', cordas: ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
      afinacoes: [
        { id: 'padrao', nome: 'Padrão', desloca: 0 },
        { id: 'meio', nome: 'Meio tom abaixo', desloca: -1 },
        { id: 'um', nome: 'Um tom abaixo', desloca: -2 },
        { id: 'dropd', nome: 'Drop D', troca: { 0: 'D2' } },
      ] },
    { id: 'violao7', nome: 'Violão 7 cordas', cordas: ['B1', 'E2', 'A2', 'D3', 'G3', 'B3', 'E4'] },
    { id: 'baixo', nome: 'Baixo', cordas: ['E1', 'A1', 'D2', 'G2'],
      afinacoes: [
        { id: 'padrao', nome: 'Padrão', desloca: 0 },
        { id: 'meio', nome: 'Meio tom abaixo', desloca: -1 },
        { id: 'dropd', nome: 'Drop D', troca: { 0: 'D1' } },
      ] },
    { id: 'cavaco', nome: 'Cavaquinho', cordas: ['D4', 'G4', 'B4', 'D5'] },
    { id: 'viola', nome: 'Viola', cordas: ['C3', 'G3', 'D4', 'A4'] },
    { id: 'violino', nome: 'Violino', cordas: ['G3', 'D4', 'A4', 'E5'] },
    { id: 'violoncelo', nome: 'Violoncelo', cordas: ['C2', 'G2', 'D3', 'A3'] },
    // Sopro não tem corda: ele sustenta uma nota e vê se está no lugar. É o
    // modo que serve para sax, flauta, trompete — e para a voz.
    { id: 'cromatico', nome: 'Sopro e voz (qualquer nota)', cordas: null },
  ];
  // Sax e trompete leem numa altura e soam noutra. Quem toca sax tenor lê um Ré
  // e sai um Dó: sem isto o afinador diz a nota certa e o músico acha que errou.
  var TRANSPOSICAO = [
    { id: 'C', nome: 'Instrumento em Dó (soa como escrito)', semi: 0 },
    { id: 'Bb', nome: 'Em Si bemol (tenor, soprano, trompete)', semi: 2 },
    { id: 'Eb', nome: 'Em Mi bemol (alto, barítono)', semi: 9 },
    { id: 'F', nome: 'Em Fá (trompa)', semi: 7 },
  ];

  function cordasDe(inst, afin) {
    if (!inst.cordas) return null;
    var lista = inst.cordas.slice();
    if (afin && afin.troca) {
      for (var k in afin.troca) lista[k] = afin.troca[k];
    }
    var d = (afin && afin.desloca) || 0;
    return lista.map(function (c) { return m(c) + d; });
  }

  // ---- a tela ------------------------------------------------------------
  var CSS = [
    '.afn{--ok:#3fbf72;--erro:#e05a5a;--ouro:#e8b93c}',
    '.afn-topo{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px}',
    '.afn-sel{flex:1;min-width:130px;background:#0c1830;color:#fff;border:1px solid #24365a;',
    '  border-radius:9px;padding:10px;font-size:14px;font-family:inherit}',
    '.afn-mostra{background:#0c1830;border:1px solid #24365a;border-radius:12px;padding:16px 12px;text-align:center}',
    '.afn-nota{font-size:52px;font-weight:800;line-height:1;letter-spacing:1px;color:#fff}',
    '.afn-nota.certo{color:var(--ok)}',
    '.afn-hz{font-size:12px;color:#7f9ac0;margin-top:6px;font-variant-numeric:tabular-nums}',
    '.afn-alvo{font-size:12.5px;color:var(--ouro);margin-top:4px;min-height:1.2em}',
    // a régua: o ponteiro anda do -50 ao +50 cents, e a faixa do meio é o certo
    '.afn-regua{position:relative;height:34px;margin:14px 0 4px;background:#0b1526;',
    '  border-radius:8px;overflow:hidden}',
    '.afn-centro{position:absolute;left:50%;top:0;bottom:0;width:2px;margin-left:-1px;background:#3b5480}',
    '.afn-zona{position:absolute;left:47%;right:47%;top:0;bottom:0;background:#1d7a4533}',
    '.afn-ponteiro{position:absolute;top:4px;bottom:4px;width:5px;margin-left:-2.5px;border-radius:3px;',
    '  background:var(--erro);left:50%;transition:left .09s linear,background .15s}',
    '.afn-ponteiro.certo{background:var(--ok)}',
    '.afn-cents{font-size:12px;color:#9db3d6;font-variant-numeric:tabular-nums}',
    '.afn-cordas{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin-top:12px}',
    '.afn-corda{background:#16233c;border:1px solid #24365a;color:#cfe0f5;border-radius:8px;',
    '  padding:8px 11px;font-size:13px;font-weight:700;min-width:46px}',
    '.afn-corda.perto{border-color:var(--ouro);color:var(--ouro)}',
    '.afn-corda.certo{border-color:var(--ok);color:var(--ok);background:#12301f}',
    '.afn-aviso{font-size:12.5px;color:#f0d493;background:#2a2313;border:1px solid #6b5a24;',
    '  border-radius:9px;padding:11px 13px;line-height:1.5;margin-top:10px}',
    '.afn-bt{width:100%;margin-top:11px;background:#1d7a45;color:#fff;border:none;border-radius:9px;',
    '  padding:13px;font-size:14px;font-weight:700;font-family:inherit;cursor:pointer}',
    '.afn-bt.parar{background:#7a2233;color:#ffd9d9}',
    '.afn-la{display:flex;align-items:center;gap:8px;justify-content:center;margin-top:10px;',
    '  font-size:12px;color:#7f9ac0}',
    '.afn-la input{width:64px;background:#0c1830;color:#fff;border:1px solid #24365a;border-radius:7px;',
    '  padding:5px;text-align:center;font-family:inherit;font-size:13px}',
  ].join('\n');

  function podeMicrofone() {
    if (window.isSecureContext === false) return 'inseguro';
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return 'sem';
    return 'ok';
  }

  function montar(alvo) {
    if (!document.getElementById('afn-css')) {
      var st = document.createElement('style'); st.id = 'afn-css'; st.textContent = CSS;
      document.head.appendChild(st);
    }
    alvo.className = 'afn';
    alvo.innerHTML =
      '<div class="afn-topo">' +
        '<select class="afn-sel" id="afn-inst"></select>' +
        '<select class="afn-sel" id="afn-afin"></select>' +
        '<select class="afn-sel afn-transp" id="afn-transp" style="display:none"></select>' +
      '</div>' +
      '<div class="afn-mostra">' +
        '<div class="afn-nota" id="afn-nota">—</div>' +
        '<div class="afn-hz" id="afn-hz">toque uma corda</div>' +
        '<div class="afn-alvo" id="afn-alvo"></div>' +
        '<div class="afn-regua"><div class="afn-zona"></div><div class="afn-centro"></div>' +
          '<div class="afn-ponteiro" id="afn-pont"></div></div>' +
        '<div class="afn-cents" id="afn-cents">−50 ¦ 0 ¦ +50</div>' +
        '<div class="afn-cordas" id="afn-cordas"></div>' +
      '</div>' +
      '<button class="afn-bt" id="afn-bt">Ligar o microfone</button>' +
      '<div class="afn-la">Lá de referência <input type="number" id="afn-la" min="415" max="466" value="440"> Hz</div>' +
      '<div id="afn-aviso"></div>';

    var elInst = alvo.querySelector('#afn-inst'), elAfin = alvo.querySelector('#afn-afin'),
        elTr = alvo.querySelector('#afn-transp'), elNota = alvo.querySelector('#afn-nota'),
        elHz = alvo.querySelector('#afn-hz'), elAlvo = alvo.querySelector('#afn-alvo'),
        elPont = alvo.querySelector('#afn-pont'), elCents = alvo.querySelector('#afn-cents'),
        elCordas = alvo.querySelector('#afn-cordas'), elBt = alvo.querySelector('#afn-bt'),
        elLa = alvo.querySelector('#afn-la'), elAviso = alvo.querySelector('#afn-aviso');

    INSTRUMENTOS.forEach(function (i, k) {
      var o = document.createElement('option'); o.value = k; o.textContent = i.nome; elInst.appendChild(o);
    });
    TRANSPOSICAO.forEach(function (t, k) {
      var o = document.createElement('option'); o.value = k; o.textContent = t.nome; elTr.appendChild(o);
    });
    try { elInst.value = localStorage.getItem('afn_inst') || 0; } catch (e) {}

    var ctx = null, fluxo = null, analisador = null, buf = null, rodando = false, anim = null;
    var cordas = null, la = 440;

    function instAtual() { return INSTRUMENTOS[+elInst.value] || INSTRUMENTOS[0]; }
    function afinAtual() {
      var i = instAtual();
      return (i.afinacoes && i.afinacoes[+elAfin.value]) || null;
    }
    function pintarOpcoes() {
      var i = instAtual();
      elAfin.innerHTML = '';
      if (i.afinacoes) {
        i.afinacoes.forEach(function (a, k) {
          var o = document.createElement('option'); o.value = k; o.textContent = a.nome; elAfin.appendChild(o);
        });
        elAfin.style.display = '';
      } else { elAfin.style.display = 'none'; }
      elTr.style.display = i.cordas ? 'none' : '';     // transposição só no modo de sopro
      cordas = cordasDe(i, afinAtual());
      elCordas.innerHTML = '';
      if (cordas) {
        cordas.forEach(function (midi) {
          var d = document.createElement('div'); d.className = 'afn-corda';
          d.dataset.midi = midi; d.textContent = nomeDe(midi);
          elCordas.appendChild(d);
        });
      }
      try { localStorage.setItem('afn_inst', elInst.value); } catch (e) {}
    }
    elInst.onchange = pintarOpcoes;
    elAfin.onchange = pintarOpcoes;
    elLa.onchange = function () { la = Math.min(466, Math.max(415, +elLa.value || 440)); elLa.value = la; };
    pintarOpcoes();

    function pintar(hz) {
      if (!hz) {
        elNota.textContent = '—'; elNota.classList.remove('certo');
        elHz.textContent = rodando ? 'ouvindo…' : 'toque uma corda';
        elAlvo.textContent = ''; elPont.style.left = '50%';
        elPont.classList.remove('certo');
        [].forEach.call(elCordas.children, function (c) { c.classList.remove('perto', 'certo'); });
        return;
      }
      var midi = deHz(hz, la), alvoMidi;
      if (cordas) {
        // a corda mais perto do que ele tocou — é o alvo, mesmo desafinado
        alvoMidi = cordas.reduce(function (a, b) {
          return Math.abs(b - midi) < Math.abs(a - midi) ? b : a;
        });
      } else {
        alvoMidi = Math.round(midi);
      }
      var cents = Math.round((midi - alvoMidi) * 100);
      var certo = Math.abs(cents) <= 5;

      // no modo de sopro, mostra também como o instrumento LÊ a nota
      var rot = nomeDe(alvoMidi);
      if (!cordas) {
        var t = TRANSPOSICAO[+elTr.value];
        if (t && t.semi) rot += '  (lê ' + nomeDe(alvoMidi + t.semi) + ')';
      }
      elNota.textContent = rot;
      elNota.classList.toggle('certo', certo);
      elHz.textContent = hz.toFixed(1) + ' Hz  ·  alvo ' + paraHz(alvoMidi, la).toFixed(1) + ' Hz';
      elAlvo.textContent = certo ? 'afinado' : (cents < 0 ? 'apertar (está grave)' : 'soltar (está agudo)');
      var p = Math.max(-50, Math.min(50, cents));
      elPont.style.left = (50 + p) + '%';
      elPont.classList.toggle('certo', certo);
      elCents.textContent = (cents > 0 ? '+' : '') + cents + ' cents';
      [].forEach.call(elCordas.children, function (c) {
        var meu = +c.dataset.midi === alvoMidi;
        c.classList.toggle('perto', meu && !certo);
        c.classList.toggle('certo', meu && certo);
      });
    }

    function laco() {
      if (!rodando) return;
      analisador.getFloatTimeDomainData(buf);
      var r = frequencia(buf, ctx.sampleRate);
      pintar(r.hz);
      anim = requestAnimationFrame(laco);
    }

    function parar() {
      rodando = false;
      if (anim) cancelAnimationFrame(anim);
      if (fluxo) fluxo.getTracks().forEach(function (t) { t.stop(); });
      if (ctx && ctx.state !== 'closed') ctx.close();
      ctx = fluxo = analisador = null;
      elBt.textContent = 'Ligar o microfone'; elBt.classList.remove('parar');
      pintar(0);
    }

    async function ligar() {
      var pode = podeMicrofone();
      if (pode !== 'ok') {
        elAviso.innerHTML = '<div class="afn-aviso">' + (pode === 'inseguro'
          ? 'O celular está entrando pelo endereço comum (http). O navegador só libera o ' +
            'microfone em endereço seguro (https) — é regra dele, não do Sistema. ' +
            'No computador o afinador funciona normalmente.'
          : 'Este navegador não abre o microfone.') + '</div>';
        return;
      }
      try {
        // desliga os "melhoradores" do navegador: eles mexem no som e estragam
        // a leitura da frequência, que é justamente o que interessa aqui
        fluxo = await navigator.mediaDevices.getUserMedia({ audio: {
          echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
      } catch (e) {
        elAviso.innerHTML = '<div class="afn-aviso">Não consegui usar o microfone. ' +
          'Se o navegador perguntou, é preciso permitir. (' + (e && e.name) + ')</div>';
        return;
      }
      elAviso.innerHTML = '';
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      var fonte = ctx.createMediaStreamSource(fluxo);
      analisador = ctx.createAnalyser();
      // 4096 e não 2048: o Mi grave do violão (82 Hz) tem um ciclo de 585
      // amostras, e em 2048 cabiam só três ciclos e meio — pouco para a
      // correlação se firmar no meio do barulho da igreja, e era justo a corda
      // mais difícil de afinar que caía primeiro. Com 4096 cabem sete, e o
      // atraso continua imperceptível (85 ms).
      analisador.fftSize = 4096;
      buf = new Float32Array(analisador.fftSize);
      fonte.connect(analisador);            // NÃO liga na saída: nada de microfonia
      rodando = true;
      elBt.textContent = 'Desligar o microfone'; elBt.classList.add('parar');
      laco();
    }

    elBt.onclick = function () { rodando ? parar() : ligar(); };
    return { parar: parar, frequencia: frequencia, deHz: deHz, paraHz: paraHz, nomeDe: nomeDe };
  }

  window.Afinador = { montar: montar, frequencia: frequencia, deHz: deHz,
                      paraHz: paraHz, nomeDe: nomeDe, INSTRUMENTOS: INSTRUMENTOS };
})();
