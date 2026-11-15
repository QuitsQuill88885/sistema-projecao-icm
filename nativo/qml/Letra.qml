// UM TEXTO do painel, com a regra única da letra (Tema.js FONTE): a fonte embutida "Painel ICM", o tamanho do app.css
// convertido (x 1,032), o espaçamento convertido (- 0,022 em) e o reforço que iguala a tinta à da 3.0.13 no Edge.
// Todo texto do painel passa por aqui: nada de tamanho ou fonte escrito cru.
//
// O TAMANHO EM FRAÇÃO DE PX (medido 07/11): o Qt arredonda o tamanho da fonte para pixel INTEIRO antes de desenhar
// (15,48 px saía em 15: "Projeção" com 61,09 px em vez de 63,06, no Windows e no Linux). Então a letra é montada
// AMPLIADA (x AMPL, onde o arredondamento vira 1/8 de px) e reduzida: o desenho do Qt (campo de distância) reduz sem borrar.
import QtQuick
import "Tema.js" as T

Item {
    id: l
    property string text: ""
    property color color: "#eaf0fb"
    property real px: 13                    // o font-size do app.css (da Segoe), em px
    property int weight: 400
    property real lsCss: 0                  // o letter-spacing do app.css, em px
    // os <input> sem type da 3.0.13 não herdam a letra da página: o navegador desenha em Arial. Aqui: a Liberation Sans
    // (OFL, as MESMAS larguras e a mesma linha da Arial), sem o encaixe de 1,032
    property bool navegador: false
    property string fonte: ""              // outra família (a mono do endereço do celular); vazio = a do painel
    readonly property string familia: fonte !== "" ? fonte : (navegador ? T.FONTE.campo.familia : T.FONTE.familia)
    readonly property real tamReal: navegador ? px : T.tam(px)
    readonly property real fAsc: navegador ? T.FONTE.campo.asc : T.FONTE.asc
    readonly property real fDesc: navegador ? T.FONTE.campo.desc : T.FONTE.desc
    property bool maiusculas: false
    property bool italico: false
    property real largura: -1               // >= 0: corta com reticências
    property int quebra: Text.NoWrap
    property int alinhamento: Text.AlignLeft
    property int textFormat: Text.PlainText
    // provas (PAR_TEXTO): "nativo" = o desenho de letra do sistema (ClearType no Windows), sem a ampliação
    readonly property string modo: typeof modoTexto === "undefined" ? "" : modoTexto
    // LINUX (08/11/2026, medido no Vaio com a bancada_letra.py): o desenho NATIVO do sistema (FreeType + fontconfig, o mesmo
    // do WebKitGTK da 3.0.12) com hinting COMPLETO, sem ampliação, sem a 2a passada e sem a franja: bate com o navegador
    // linha por linha (tinta e largura 99,9%). A ampliação x8, o reforço e a franja (calibrados contra o Edge) deixavam a
    // letra dobrada e borrada lá ("dura, amassada"). O Windows segue como estava. letraAntiga: só o par antes x depois.
    readonly property bool linuxNativo: Qt.platform.os === "linux" && (typeof letraAntiga === "undefined" || !letraAntiga)
    // 08/11 00h09, ESCOLHA DELE: "o sistema vai ficar um para um, não importa a plataforma": o desenho nativo também no
    // Windows (sem 8x, sem 2ª passada, sem franja). letraAntiga = a imitação de antes, só para o par antes x depois
    readonly property bool nativoPuro: (typeof letraAntiga === "undefined" || !letraAntiga) || modo === "nativo"
    readonly property real ampl: nativoPuro ? 1 : 8
    readonly property string _h: typeof letraHint === "undefined" ? "" : letraHint
    readonly property int hintLinux: _h === "cheio" ? Font.PreferFullHinting : (_h === "nenhum" ? Font.PreferNoHinting : Font.PreferVerticalHinting)
    // o reforço: no negrito (700) a 2a passada inteira; no 600 ela entra com opacidade parcial (medido: inteira estoura +38%)
    // o reforço e a franja imitam o ClearType da letra PEQUENA; na letra grande (o "5:00" de 54 px) eles apareciam como
    // uma franja colorida na borda: só até 20 px
    readonly property real reforcoOpac: nativoPuro || px > 20 ? 0 : (weight >= T.FONTE.reforcoPeso ? 1 : (weight >= 600 ? (modo.indexOf("o600=") === 0 ? parseFloat(modo.substr(5)) : T.FONTE.opac600)
                                                                                                                      : (modo.indexOf("o400=") === 0 ? parseFloat(modo.substr(5)) : T.FONTE.opac400)))
    readonly property real reforco: reforcoOpac > 0 && (weight >= T.FONTE.reforcoPeso || px >= T.FONTE.reforcoMinPx) ? T.FONTE.reforco : 0   // letra miúda no 600: sem reforço (medido: +25% de tinta a 11 px)
    // a FRANJA QUENTE: o ClearType do Edge pinta a borda da letra com franja vermelha/azul, e o olho vê a cor mais
    // "vibrante" (o dourado: média 218,176,96 no Edge). A 2a passada vai levemente mais quente (calibrada pela média)
    readonly property real saturacao: Math.max(color.r, color.g, color.b) - Math.min(color.r, color.g, color.b)
    readonly property real quente: saturacao < 0.3 ? 0 : (modo.indexOf("q=") === 0 ? parseFloat(modo.split(",")[0].substr(2)) : T.FONTE.quente)
    readonly property color corQuente: Qt.rgba(Math.min(1, color.r * (1 + quente)), color.g * (1 - quente), color.b * (1 - quente), color.a)   // só no negrito (medido: no 600 estoura a tinta)
    // a redução exata até o tamanho pedido (no Linux nativo o tamanho fracionado vai direto, em pontos: sem escala)
    // nativo: a sobra de largura (tamanho fracionado pedido x o inteiro desenhado) repartida entre as letras
    TextMetrics {
        id: tm
        font.family: l.familia; font.weight: l.weight >= 800 ? 900 : l.weight; font.pixelSize: Math.max(1, Math.round(l.tamReal))
        font.capitalization: l.maiusculas ? Font.AllUppercase : Font.MixedCase; font.italic: l.italico
        text: l.nativoPuro ? (l.textFormat === Text.RichText ? l.text.replace(/<[^>]*>/g, "") : l.text) : ""
    }
    readonly property real compensa: nativoPuro && tm.text.length > 0
                                     ? tm.advanceWidth * (tamReal / Math.max(1, Math.round(tamReal)) - 1) / tm.text.length : 0
    readonly property real k: nativoPuro ? 1 : tamReal / Math.round(tamReal * ampl)
    readonly property real implicitTextWidth: a.implicitWidth * k
    implicitWidth: largura >= 0 ? largura : implicitTextWidth     // o reforço é só tinta: não ocupa lugar na linha (como no Edge)
    // a LINHA do navegador: altura = (ascendente + descendente da Segoe) x o px do app.css (line-height normal), e a linha
    // de base no ascendente. A Painel ICM é desenhada 3,2% maior: a letra sobe o que falta para sentar na mesma base
    // (o Chromium arredonda o ascendente e o descendente para px INTEIRO, cada um: 13 px dá 14 + 3 = 17, medido no Edge)
    property real linha: 0                  // o line-height do app.css como número (1.3); 0 = normal
    readonly property real conteudo: Math.round(fAsc * px) + Math.round(fDesc * px)
    readonly property real alturaLinha: linha > 0 ? linha * px : conteudo
    // line-height explícito: a sobra é dividida meio a meio em cima e embaixo da letra (half-leading)
    readonly property real ascPx: Math.round(fAsc * px) + (alturaLinha - conteudo) / 2
    // linhas x a linha do navegador (o Qt somava um resto); no texto RICO o lineCount do Qt não conta a quebra (o
    // parágrafo do <code> ficava com 2 de 3 linhas): ali as linhas saem da altura do conteúdo
    implicitHeight: quebra === Text.NoWrap ? alturaLinha
                  : (textFormat === Text.RichText ? Math.max(1, Math.round(a.contentHeight * k / alturaLinha)) : Math.max(1, a.lineCount)) * alturaLinha
    Text {
        id: a
        // no texto RICO o Qt põe toda a sobra da linha EM CIMA da letra (o navegador divide meio a meio): desconta
        y: l.ascPx - l.fAsc * l.tamReal - (l.textFormat === Text.RichText ? l.alturaLinha - (l.fAsc + l.fDesc) * l.tamReal : 0)
        transformOrigin: Item.TopLeft
        scale: l.k
        width: l.largura >= 0 ? l.largura / l.k : (l.quebra !== Text.NoWrap ? l.width / l.k : implicitWidth)
        // no texto RICO o Qt não aplica a altura fixa de linha do mesmo jeito (sobrava ~1 px por linha): a altura do
        // navegador vai DENTRO do HTML (line-height em px, que o Qt aceita), já na escala ampliada
        text: l.textFormat === Text.RichText ? "<div style='line-height:" + (l.alturaLinha / l.k).toFixed(2) + "px'>" + l.text + "</div>" : l.text
        color: l.color; textFormat: l.textFormat
        // a letra inteira num objeto só. No desenho nativo o Qt ARREDONDA o tamanho para px inteiro (13,42 mede igual a 13,
        // medido 08/11 no PC de casa e no Vaio): a letra fica no inteiro e o espaço entre as letras recebe a diferença, para a
        // linha ter a MESMA largura desenhada (a do Windows), sem esticar a imagem da letra
        // (propriedade por propriedade, como sempre foi: montar a letra num Qt.font inteiro mudava a franja do texto colorido
        // no Windows, medido 08/11 no "CIAS")
        font.family: l.familia; font.weight: l.weight >= 800 ? 900 : l.weight   // 800 sem arquivo próprio = Black, como no Edge
        font.pixelSize: l.nativoPuro ? Math.max(1, Math.round(l.tamReal)) : Math.max(1, Math.round(l.tamReal * l.ampl) || 1)
        font.letterSpacing: l.nativoPuro ? T.espaco(l.lsCss, l.px) + l.compensa : T.espaco(l.lsCss, l.px) / l.k
        font.italic: l.italico
        font.capitalization: l.maiusculas ? Font.AllUppercase : Font.MixedCase
        font.hintingPreference: l.linuxNativo ? l.hintLinux : Font.PreferNoHinting
        // letra GRANDE (> 40 px) em tons de cinza, como o Edge (o motor dele não usa subpixel em letra grande): o desenho
        // por curvas do Qt. A pequena segue com o subpixel do campo de distância, que imita o ClearType
        renderType: l.nativoPuro ? Text.NativeRendering : (l.px > 40 ? Text.CurveRendering : Text.QtRendering)
        elide: l.largura >= 0 ? Text.ElideRight : Text.ElideNone
        wrapMode: l.quebra; horizontalAlignment: l.alinhamento
        lineHeightMode: l.textFormat === Text.RichText ? Text.ProportionalHeight : Text.FixedHeight
        lineHeight: l.textFormat === Text.RichText ? 1 : l.alturaLinha / l.k     // cada linha com a altura do navegador
    }
    // a 2a passada (mesma letra, uma fração de px ao lado): o Edge escurece o traço da letra clara sobre fundo escuro
    // (realce de contraste do DirectWrite); o Qt não tem esse ajuste, então a tinta é igualada assim, medida
    Text {
        visible: l.reforco > 0
        y: a.y
        z: l.quente > 0 ? -1 : 0          // a franja quente vai POR BAIXO: só a borda esquenta, o miolo fica com a cor exata
        opacity: l.quente > 0 ? T.FONTE.opacQuente : l.reforcoOpac   // a franja do texto colorido tem a dela
        // com a franja quente o deslocamento é o da franja (a borda que o ClearType pinta), senão o do reforço
        x: l.quente > 0 ? (l.modo.indexOf("dx=") >= 0 ? parseFloat(l.modo.split("dx=")[1]) : T.FONTE.franjaDx) : l.reforco
        transformOrigin: Item.TopLeft; scale: l.k
        width: a.width; text: a.text; color: l.corQuente; textFormat: a.textFormat
        font: a.font; renderType: a.renderType; elide: a.elide; wrapMode: a.wrapMode; horizontalAlignment: a.horizontalAlignment
        lineHeightMode: a.lineHeightMode; lineHeight: a.lineHeight      // a mesma altura de linha (senão a 2a linha sai fantasma)
    }
}
