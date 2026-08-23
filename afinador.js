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
    /* PORTÃO DE SILÊNCIO BAIXO DE PROPÓSITO (era 0,01).
       O afinador pede o microfone com autoGainControl DESLIGADO — precisa, senão
       o navegador mexe no volume e estraga a leitura. Só que sem esse reforço o
       sinal que chega é fraco, e 0,01 barrava violão de verdade: o Samuel botou
       um violão bem desafinado na frente e o afinador não lia NADA.
       Quem separa som de barulho aqui não é a energia, é a PERIODICIDADE (o
       portão de correlação lá embaixo). Então este portão fica frouxo e só
       serve para não trabalhar à toa no silêncio de verdade. */
    if (rms < 0.0025) return { hz: 0, rms: rms };    // silêncio: não chuta nada

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

    /* 0,30 e não 0,45. Corda velha, encardida e MUITO desafinada casa pior
       consigo mesma (o harmônico não bate certinho com o fundamental), e em
       0,45 ela era jogada fora justo no caso em que o músico mais precisa do
       afinador. Ruído puro não chega nem perto de 0,30 — o banco de prova
       confere isso caso a caso. */
    var casou = correlaciona(bd, lagMinD, lagMaxD, m - lagMaxD);
    if (!casou || casou.maior < 0.30) return { hz: 0, rms: rms };

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
  // O desenho segue o que o Samuel pediu: a PALAVRA manda (aperte / afrouxe /
  // afinado), o número é secundário. Antes a tela mostrava "-139 cents" e ele
  // não tinha como saber o que fazer com isso.
  var CSS = [
    '.afn{--ok:#3fbf72;--erro:#e05a5a;--ouro:#e8b93c}',
    '.afn-topo{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px}',
    '.afn-sel{flex:1;min-width:130px;background:#0c1830;color:#fff;border:1px solid #24365a;',
    '  border-radius:9px;padding:10px;font-size:14px;font-family:inherit}',
    '.afn-mostra{background:#0c1830;border:1px solid #24365a;border-radius:12px;padding:14px 12px;text-align:center}',
    // o modo: automático (ele acha a corda) ou travado numa corda escolhida
    '.afn-modo{font-size:12px;color:#7f9ac0;margin-bottom:9px;min-height:1.2em}',
    '.afn-modo b{color:var(--ouro);font-weight:700}',
    '.afn-modo button{background:none;border:none;color:#7f9ac0;font:inherit;text-decoration:underline;',
    '  cursor:pointer;padding:0 0 0 6px}',
    '.afn-nota{font-size:50px;font-weight:800;line-height:1;letter-spacing:1px;color:#fff;',
    '  transition:color .18s}',
    '.afn-nota.certo{color:var(--ok)}',
    // a régua: o ponteiro anda do -50 ao +50 cents, e a faixa do meio é o certo
    '.afn-regua{position:relative;height:30px;margin:12px 0 10px;background:#0b1526;',
    '  border-radius:8px;overflow:hidden}',
    '.afn-centro{position:absolute;left:50%;top:0;bottom:0;width:2px;margin-left:-1px;background:#3b5480}',
    '.afn-zona{position:absolute;left:47%;right:47%;top:0;bottom:0;background:#1d7a4533}',
    '.afn-ponteiro{position:absolute;top:4px;bottom:4px;width:5px;margin-left:-2.5px;border-radius:3px;',
    '  background:var(--erro);left:50%;transition:left .12s ease-out,background .15s}',
    '.afn-ponteiro.certo{background:var(--ok)}',
    // A PALAVRA — é ela que o músico lê de longe, com o violão na mão
    '.afn-diz{font-size:21px;font-weight:800;letter-spacing:.5px;line-height:1.2;min-height:1.2em;',
    '  color:#cfe0f5;transition:color .18s}',
    '.afn-diz.certo{color:var(--ok)}',
    '.afn-diz.aperta{color:#7fb0e8}',
    '.afn-diz.afrouxa{color:var(--ouro)}',
    '.afn-diz.longe{color:var(--erro)}',
    '.afn-detalhe{font-size:12.5px;color:#8fa6c8;margin-top:5px;min-height:1.3em;line-height:1.35}',
    '.afn-hz{font-size:11.5px;color:#5f7a9e;margin-top:3px;font-variant-numeric:tabular-nums}',
    // as cordas: viram botão (trava nela) e desenham a espessura real da corda
    '.afn-cordas{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin-top:14px}',
    '.afn-corda{background:#16233c;border:1px solid #24365a;color:#cfe0f5;border-radius:8px;',
    '  padding:7px 10px 8px;font-size:13px;font-weight:700;min-width:46px;font-family:inherit;',
    '  cursor:pointer;line-height:1.1}',
    '.afn-corda i{display:block;background:#4a628a;border-radius:2px;margin:0 auto 6px;width:74%}',
    '.afn-corda.perto{border-color:var(--ouro);color:var(--ouro)}',
    '.afn-corda.perto i{background:var(--ouro)}',
    '.afn-corda.certo{border-color:var(--ok);color:var(--ok);background:#12301f}',
    '.afn-corda.certo i{background:var(--ok)}',
    '.afn-corda.travada{border-color:#7fb0e8;color:#fff;background:#17294a;box-shadow:0 0 0 1px #7fb0e8}',
    '.afn-aviso{font-size:12.5px;color:#f0d493;background:#2a2313;border:1px solid #6b5a24;',
    '  border-radius:9px;padding:11px 13px;line-height:1.5;margin-top:10px}',
    '.afn-toque{margin-top:11px;background:#12203a;border:1px dashed #3a5480;',
    '  color:#9db3d6;border-radius:11px;padding:15px 14px;',
    '  font-size:13.5px;line-height:1.45;text-align:center;cursor:pointer}',
    // medidor de som: prova visual de que o microfone está entregando áudio
    '.afn-nivel{height:4px;background:#0b1526;border-radius:3px;overflow:hidden;margin-top:11px}',
    '.afn-nivel i{display:block;height:100%;width:0;background:linear-gradient(90deg,#2f6d8f,#3fbf72);',
    '  border-radius:3px;transition:width .08s linear}',
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
        '<div class="afn-modo" id="afn-modo"></div>' +
        '<div class="afn-nota" id="afn-nota">—</div>' +
        '<div class="afn-regua"><div class="afn-zona"></div><div class="afn-centro"></div>' +
          '<div class="afn-ponteiro" id="afn-pont"></div></div>' +
        '<div class="afn-diz" id="afn-diz">toque uma corda</div>' +
        '<div class="afn-detalhe" id="afn-detalhe"></div>' +
        '<div class="afn-hz" id="afn-hz"></div>' +
        '<div class="afn-cordas" id="afn-cordas"></div>' +
      '</div>' +
      // MEDIDOR DE SOM: a barrinha se mexe assim que chega áudio, mesmo antes
      // de firmar uma nota. É o que responde na hora a pergunta "o microfone
      // está funcionando?" — sem ela, microfone mudo e corda errada parecem a
      // mesma coisa, e foi exatamente aí que eu fiquei cego.
      '<div class="afn-nivel"><i id="afn-nivel"></i></div>' +
      /* NÃO é um botão de liga/desliga. O navegador exige UM toque de verdade
         antes de abrir o microfone pela primeira vez (e o toque em "Afinador"
         se perde enquanto o arquivo carrega). Então a tela inteira do afinador
         vira esse toque, uma vez só. Depois que o aparelho guarda a permissão,
         isto nunca mais aparece. */
      '<div class="afn-toque" id="afn-toque" hidden>Toque na tela para o afinador ' +
        'ouvir o seu instrumento</div>' +
      '<div id="afn-aviso"></div>';

    var elInst = alvo.querySelector('#afn-inst'), elAfin = alvo.querySelector('#afn-afin'),
        elTr = alvo.querySelector('#afn-transp'), elNota = alvo.querySelector('#afn-nota'),
        elHz = alvo.querySelector('#afn-hz'), elDiz = alvo.querySelector('#afn-diz'),
        elDet = alvo.querySelector('#afn-detalhe'), elModo = alvo.querySelector('#afn-modo'),
        elPont = alvo.querySelector('#afn-pont'),
        elCordas = alvo.querySelector('#afn-cordas'), elBt = alvo.querySelector('#afn-toque'),
        elNivel = alvo.querySelector('#afn-nivel'), elAviso = alvo.querySelector('#afn-aviso');

    INSTRUMENTOS.forEach(function (i, k) {
      var o = document.createElement('option'); o.value = k; o.textContent = i.nome; elInst.appendChild(o);
    });
    TRANSPOSICAO.forEach(function (t, k) {
      var o = document.createElement('option'); o.value = k; o.textContent = t.nome; elTr.appendChild(o);
    });
    try { elInst.value = localStorage.getItem('afn_inst') || 0; } catch (e) {}

    var ctx = null, fluxo = null, analisador = null, buf = null, rodando = false, anim = null;
    /* O Lá de referência é 440 e ponto. Existia um campo para mudar (442, para
       orquestra), mas na igreja ninguém vai mexer nisso e um campo a mais é um
       campo para errar sem perceber — o Samuel mandou tirar. */
    var cordas = null, la = 440;
    // travada = a corda que ELE escolheu no dedo. null = automático (o afinador
    // acha a corda sozinho). Os dois modos convivem: era o pedido dele.
    var travada = null;
    // memória curta da leitura: mata o tremor e segura o valor na tela depois
    // que a corda para de soar — antes piscava em 0,1 s e não dava para ler.
    var hist = [], ultHz = 0, ultT = 0, ouvindo = false;

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
      travada = null;                       // trocou de instrumento, volta ao automático
      elCordas.innerHTML = '';
      if (cordas) {
        // a corda mais grave é a mais grossa: o risquinho em cima do botão
        // desenha isso, que é como o músico enxerga o braço do instrumento
        var min = Math.min.apply(null, cordas), max = Math.max.apply(null, cordas);
        cordas.forEach(function (midi) {
          var b = document.createElement('button'); b.className = 'afn-corda';
          b.dataset.midi = midi;
          var f = max === min ? 0 : (max - midi) / (max - min);      // 1 = mais grave
          b.innerHTML = '<i style="height:' + (1.5 + f * 3.5).toFixed(1) + 'px"></i>' + nomeDe(midi);
          b.onclick = function () {
            travada = (travada === midi) ? null : midi;               // toca de novo, destrava
            pintarModo(); pintar(0);
            tocarCorda(midi);          // e SOA a corda, para o ouvido conferir
          };
          elCordas.appendChild(b);
        });
      }
      pintarModo();
      try { localStorage.setItem('afn_inst', elInst.value); } catch (e) {}
    }
    /* TOCA A CORDA. Tocar em E2 faz sair o Mi grave, para o músico afinar de
       ouvido também — é o que todo afinador de celular faz e o Samuel pediu.
       De quebra serve de prova viva: se ele OUVE a nota, o áudio do aparelho
       está bom, e o que sobra para investigar é só o microfone.
       O som sai com harmônicos e morre em ~1,6 s (uma senoide pura soa como
       apito de teste, não como corda). */
    function tocarCorda(midi) {
      try {
        var c = ctx || new (window.AudioContext || window.webkitAudioContext)();
        if (c.state === 'suspended') { try { c.resume(); } catch (e) {} }
        var f = paraHz(midi, la), t0 = c.currentTime + 0.01;
        var env = c.createGain();
        env.gain.setValueAtTime(0.0001, t0);
        env.gain.exponentialRampToValueAtTime(0.30, t0 + 0.03);   // ataque de palheta
        env.gain.exponentialRampToValueAtTime(0.0001, t0 + 1.6);  // e some
        env.connect(c.destination);
        [0.6, 0.3, 0.16, 0.08].forEach(function (g, k) {
          var o = c.createOscillator(), gh = c.createGain();
          o.type = 'sine'; o.frequency.value = f * (k + 1); gh.gain.value = g;
          o.connect(gh); gh.connect(env); o.start(t0); o.stop(t0 + 1.7);
        });
      } catch (e) {}
    }

    // A linha de cima diz em que modo ele está, e dá a saída para voltar ao
    // automático sem ter que adivinhar qual botão desliga.
    function pintarModo() {
      if (!cordas) { elModo.textContent = ''; return; }
      if (travada == null) {
        elModo.innerHTML = 'Automático — toque qualquer corda, eu acho qual é. ' +
                           '<span style="opacity:.75">(ou escolha uma abaixo)</span>';
      } else {
        elModo.innerHTML = 'Travado no <b>' + nomeDe(travada) + '</b>' +
                           '<button type="button" id="afn-destrava">voltar ao automático</button>';
        var d = elModo.querySelector('#afn-destrava');
        if (d) d.onclick = function () { travada = null; pintarModo(); pintar(0); };
      }
      [].forEach.call(elCordas.children, function (c) {
        c.classList.toggle('travada', +c.dataset.midi === travada);
      });
    }
    elInst.onchange = pintarOpcoes;
    elAfin.onchange = pintarOpcoes;
    pintarOpcoes();

    function pintar(hz) {
      if (!hz) {
        elNota.textContent = '—'; elNota.classList.remove('certo');
        // "estou ouvindo" é diferente de "não chega som": sem essa distinção o
        // músico não sabe se o problema é o microfone ou a corda dele
        elDiz.textContent = !rodando ? 'ligue o microfone'
                          : ouvindo  ? 'ouvindo…' : 'toque uma corda';
        elDiz.className = 'afn-diz';
        elDet.textContent = ouvindo && rodando ? 'chegue o celular mais perto do instrumento' : '';
        elHz.textContent = '';
        elPont.style.left = '50%'; elPont.classList.remove('certo');
        [].forEach.call(elCordas.children, function (c) { c.classList.remove('perto', 'certo'); });
        return;
      }
      var midi = deHz(hz, la), alvoMidi, perto = null;
      if (cordas) {
        // a corda mais perto do que ele tocou — é ela que o automático persegue
        perto = cordas.reduce(function (a, b) {
          return Math.abs(b - midi) < Math.abs(a - midi) ? b : a;
        });
        alvoMidi = (travada != null) ? travada : perto;
      } else {
        alvoMidi = Math.round(midi);
      }
      var cents = Math.round((midi - alvoMidi) * 100);
      var d = Math.abs(cents), certo = d <= 5;

      // no modo de sopro, mostra também como o instrumento LÊ a nota
      var rot = nomeDe(alvoMidi);
      if (!cordas) {
        var t = TRANSPOSICAO[+elTr.value];
        if (t && t.semi) rot += '  (lê ' + nomeDe(alvoMidi + t.semi) + ')';
      }
      elNota.textContent = rot;
      elNota.classList.toggle('certo', certo);

      // A PALAVRA manda. O músico está com o violão na mão: ele precisa saber
      // para que lado girar a tarraxa, não quantos cents faltam.
      var diz, classe, det = '';
      if (certo) { diz = 'Afinado'; classe = 'certo'; }
      else if (cents < 0) { diz = d > 25 ? 'Aperte' : 'Aperte devagar'; classe = d > 150 ? 'longe' : 'aperta'; }
      else { diz = d > 25 ? 'Afrouxe' : 'Afrouxe devagar'; classe = d > 150 ? 'longe' : 'afrouxa'; }

      if (travada != null && perto !== null && perto !== alvoMidi && d > 150) {
        // ele travou numa corda e soou outra. Sem drama: digo o que ouvi e
        // deixo o caminho pronto, caso ele só tenha batido a corda errada.
        det = 'Soou ' + nomeDe(perto) + ', e o alvo é ' + nomeDe(alvoMidi) +
              ' — se era o ' + nomeDe(perto) + ', toque nele aqui embaixo.';
      } else if (!certo && d <= 15) {
        det = 'quase lá';
      }
      elDiz.textContent = diz;
      elDiz.className = 'afn-diz ' + classe;
      elDet.textContent = det;
      elHz.textContent = hz.toFixed(1) + ' Hz  ·  alvo ' + paraHz(alvoMidi, la).toFixed(1) + ' Hz';

      var p = Math.max(-50, Math.min(50, cents));
      elPont.style.left = (50 + p) + '%';
      elPont.classList.toggle('certo', certo);
      [].forEach.call(elCordas.children, function (c) {
        var meu = +c.dataset.midi === alvoMidi;
        c.classList.toggle('perto', meu && !certo);
        c.classList.toggle('certo', meu && certo);
      });
    }

    // A leitura crua treme e some entre uma dedilhada e outra. Duas travas:
    // (1) MEDIANA das leituras dos últimos 220 ms — segura o tremor e o pulo
    //     de oitava de uma janela solta;
    // (2) SEGURA o valor na tela por 1,2 s depois que a corda cala. Sem isso a
    //     nota pisca em 0,1 s e não dá tempo de ler — foi o que ele viu.
    function laco() {
      if (!rodando) return;
      analisador.getFloatTimeDomainData(buf);
      var r = frequencia(buf, ctx.sampleRate);
      var agora = (window.performance && performance.now) ? performance.now() : Date.now();
      if (r.hz) hist.push({ hz: r.hz, t: agora });
      while (hist.length && agora - hist[0].t > 220) hist.shift();
      /* MOSTRA JÁ NA PRIMEIRA LEITURA. Eu tinha exigido 3 leituras antes de
         escrever qualquer coisa, e isso virou um terceiro portão escondido: se
         o detector só acertava de vez em quando, a tela ficava MUDA. Com uma
         leitura só a mediana é ela mesma; com três ou mais ela já filtra o
         tremor. Nunca calar é mais importante que filtrar. */
      if (hist.length) {
        var v = hist.map(function (x) { return x.hz; }).sort(function (a, b) { return a - b; });
        ultHz = v[v.length >> 1]; ultT = agora;
      }
      ouvindo = r.rms > 0.0025;      // tem som, mesmo que ainda sem nota firme
      // a barrinha mostra que ENTRA SOM, mesmo sem nota firmada
      if (elNivel) elNivel.style.width = Math.min(100, r.rms * 900).toFixed(0) + '%';
      pintar(ultT && agora - ultT < 1200 ? ultHz : 0);
    }

    function parar() {
      rodando = false;
      hist = []; ultHz = 0; ultT = 0; ouvindo = false;
      if (anim) clearInterval(anim);
      anim = null;
      if (fluxo) fluxo.getTracks().forEach(function (t) { t.stop(); });
      if (ctx && ctx.state !== 'closed') ctx.close();
      ctx = fluxo = analisador = null;
      if (elNivel) elNivel.style.width = '0%';
      pintar(0);
    }

    async function ligar() {
      var pode = podeMicrofone();
      if (pode !== 'ok') {
        elAviso.innerHTML = '<div class="afn-aviso">' + (pode === 'inseguro'
          ? '<b>Este endereço não abre o microfone.</b><br>Você entrou por ' +
            '<b>' + location.host + '</b>, que é o endereço comum (http). O navegador só ' +
            'libera o microfone no endereço <b>seguro (https)</b> — é regra dele, não do ' +
            'Sistema. Volte e entre no afinador pelo botão, que ele leva para o endereço certo.'
          : 'Este navegador não abre o microfone.') + '</div>';
        return;
      }
      /* O CONTEXTO DE ÁUDIO NASCE AQUI, ANTES DO `await`. Ele estava sendo
         criado DEPOIS de esperar o getUserMedia, e o Safari do iPhone perde o
         "gesto do usuário" atravessando um await: o contexto nascia SUSPENSO e
         o analisador devolvia zeros para sempre. Por fora parecia afinador
         quebrado — nenhum som lido, por mais alto que se tocasse. Criando
         antes, ainda dentro do toque, ele nasce vivo; o resume() logo abaixo é
         o cinto de segurança para quando nem isso basta. */
      try {
        ctx = new (window.AudioContext || window.webkitAudioContext)();
        if (ctx.state === 'suspended') { try { await ctx.resume(); } catch (e) {} }
      } catch (e) {
        elAviso.innerHTML = '<div class="afn-aviso">Este navegador não abre o áudio.</div>';
        return;
      }
      try {
        // desliga os "melhoradores" do navegador: eles mexem no som e estragam
        // a leitura da frequência, que é justamente o que interessa aqui
        fluxo = await navigator.mediaDevices.getUserMedia({ audio: {
          echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
      } catch (e) {
        if (ctx && ctx.state !== 'closed') { try { ctx.close(); } catch (_) {} }
        ctx = null;
        var nome = (e && e.name) || '';
        elBt.hidden = false;      // a tela vira o toque que o navegador exige
        /* CADA MOTIVO TEM O SEU RECADO. Um aviso genérico não diz se o problema
           é permissão, endereço ou aparelho — e sem isso o músico (e eu) fica
           adivinhando. */
        var txt;
        if (nome === 'NotAllowedError' || nome === 'SecurityError') {
          txt = '<b>O navegador está bloqueando o microfone para esta página.</b><br>' +
                'Se ele nem perguntou, é porque a permissão já foi negada antes. No iPhone: ' +
                'toque em <b>aA</b> na barra de endereço → <b>Ajustes do Site</b> → ' +
                '<b>Microfone</b> → <b>Perguntar</b> ou <b>Permitir</b>. Depois toque na tela aqui.';
        } else if (nome === 'NotFoundError' || nome === 'OverconstrainedError') {
          txt = 'Não achei microfone neste aparelho.';
        } else {
          txt = 'Não consegui abrir o microfone (' + (nome || 'motivo desconhecido') + '). ' +
                'Toque na tela para tentar de novo.';
        }
        elAviso.innerHTML = '<div class="afn-aviso">' + txt + '</div>';
        return;
      }
      elAviso.innerHTML = ''; elBt.hidden = true;
      if (ctx.state === 'suspended') { try { await ctx.resume(); } catch (e) {} }
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
      /* setInterval e NÃO requestAnimationFrame. O rAF congela quando o
         navegador julga que a aba não está na frente — e um afinador que
         congela sozinho parece afinador quebrado. O controle.html já tinha
         aprendido isso na rolagem da cifra; aqui faltava. 30 ms = 33 leituras
         por segundo, de sobra (cada leitura custa 0,35 ms). */
      if (anim) clearInterval(anim);
      anim = setInterval(laco, 30);
      laco();
    }

    // Entrou no afinador, o microfone liga. Sem botão: o Samuel apontou que ter
    // um "Ligar o microfone" faz o músico achar que já está ouvindo quando não
    // está. O botão só aparece se o navegador exigir um toque de verdade.
    /* QUALQUER toque na tela do afinador serve de gesto para abrir o microfone.
       O navegador exige um toque de verdade na primeira vez, e o toque que
       abriu o afinador se perdeu enquanto o arquivo carregava — foi por isso
       que ele não pedia autorização nenhuma e ficava mudo. */
    alvo.addEventListener('click', function () { if (!rodando) ligar(); });
    ligar();     // se o aparelho já guardou a permissão, entra ouvindo

    /* VOLTOU PRA TELA, VOLTA A OUVIR. Quando o celular bloqueia ou o músico sai
       para outro aplicativo, o navegador suspende o áudio e estrangula o
       relógio — e ao voltar o afinador ficava mudo, com cara de quebrado.
       Aqui ele se levanta sozinho: acorda o contexto e refaz o laço. */
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState !== 'visible') return;
      if (!rodando) { ligar(); return; }
      if (ctx && ctx.state === 'suspended') { try { ctx.resume(); } catch (e) {} }
      if (anim) clearInterval(anim);
      anim = setInterval(laco, 30);
    });

    return { parar: parar, ligar: ligar, frequencia: frequencia,
             deHz: deHz, paraHz: paraHz, nomeDe: nomeDe };
  }

  window.Afinador = { montar: montar, frequencia: frequencia, deHz: deHz,
                      paraHz: paraHz, nomeDe: nomeDe, INSTRUMENTOS: INSTRUMENTOS };
})();
