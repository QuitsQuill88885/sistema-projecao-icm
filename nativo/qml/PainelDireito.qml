// O <aside id="painel"> da 3.0.13 (index.html), a coluna da direita, sempre visível: a barra de estado, a prévia com o
// selo, a tarja "agora", ‹ Projetar ›, a barra Congelar · A− Padrão A+ · telas, os extras (Cifra, Animação) e a Lista de
// projeção. Medidas e cores: as regras do app.css (Tema.js); o comportamento: o atualizarProjBtn / renderFila do app.js.
import QtQuick
import QtQuick.Window
import QtQuick.Shapes
import QtQuick.Controls as QC
import "Tema.js" as T

Rectangle {
    id: pd
    // ---- o estado (quem preenche é o Painel.qml, a partir do controle)
    property bool projetando: false          // o telão está ligado (est.projetando)
    property bool congelado: false
    property string vivo: ""                 // o tipo no ar (descanso/espera = tela de espera)
    property string agora: "Pronto."
    property string tamRotulo: "Padrão"
    property bool temCifra: false
    property bool cifraOn: false
    property bool temAnim: false
    property bool animOn: false
    property var fila: []
    property int posLista: -1
    property alias previa: caixaPrevia.data  // o Palco da prévia entra aqui
    property real alturaJanela: Window.height > 0 ? Window.height : 690   // o "vh" do CSS (a prévia mede 26vh)
    // o MODO APRESENTAÇÃO da 3.0.13 (body.pb-on): somem a barra de estado, a tarja "agora" e os extras; ‹ Projetar › e a
    // barra vão para a faixa de baixo do palco; a prévia ganha o selo "1"; a lista muda de cor
    property bool modoApr: false
    signal projetarClique()
    signal anterior()
    signal proximo()
    signal congelar()
    signal menor()
    signal maior()
    signal padrao()
    signal procurarTelas()
    signal cifra()
    signal animacao()
    signal limpar()
    signal irPara(int i)
    signal mover(int i, int d)
    signal tirar(int i)
    signal marcar(int i)
    signal arrastar(int de, int para)

    readonly property bool emEspera: projetando && !congelado && (vivo === "espera" || vivo === "descanso")
    readonly property bool noAr: projetando && !(vivo === "espera" || vivo === "descanso")
    readonly property string classe: congelado && projetando ? "congelado" : (emEspera ? "espera" : (projetando ? "aovivo" : ""))

    readonly property var st: T.estilo(["#painel"], false)
    readonly property var pad: st.padding
    readonly property real gap: st.gap
    color: "transparent"
    gradient: Gradient {
        GradientStop { position: 0; color: pd.st.background.paradas[0].c }
        GradientStop { position: 1; color: pd.st.background.paradas[1].c }
    }
    Rectangle { width: pd.st["border-left"].w; height: parent.height; color: pd.st["border-left"].cor }

    Column {
        id: col
        x: pd.pad[3] + pd.st["border-left"].w; y: pd.pad[0]
        width: pd.width - pd.pad[1] - pd.pad[3] - pd.st["border-left"].w
        spacing: pd.gap

        // 1. a barra de estado (.estado-barra): bolinha + "Telão desligado" / "Projetando ao vivo" / ...
        Caixa {
            id: estado; objectName: "estadoBarra"
            visible: !pd.modoApr
            width: col.width; clicavel: false
            sels: [".estado-barra"]; estados: pd.classe ? [".estado-barra." + pd.classe] : []
            texto: pd.congelado && pd.projetando ? "Congelado — o telão não muda"
                 : (pd.emEspera ? "Tela de espera no telão" : (pd.projetando ? "Projetando ao vivo" : "Telão desligado"))
            bolinha: pd.classe === "aovivo" ? [".estado-barra .dot", ".dot", ".estado-barra.aovivo .dot", ".dot.on"]
                   : pd.classe === "espera" ? [".estado-barra .dot", ".dot", ".estado-barra.espera .dot", ".dot.espera"]
                   : pd.classe === "congelado" ? [".estado-barra .dot", ".dot", ".estado-barra.congelado .dot"]
                   : [".estado-barra .dot", ".dot"]
        }
        // 2. a prévia (.preview-box .mini): 16:9, cantos de 8, sombra; o selo embaixo (Prévia / Ao vivo / Em espera / Congelado)
        Item {
            width: col.width
            readonly property var sm: T.estilo([".preview-box .mini"], false)
            // width: min(100%, calc(26vh * 16 / 9)) — vh = a altura da janela
            readonly property real lw: Math.min(col.width, 0.26 * pd.alturaJanela * 16 / 9)
            height: lw * 9 / 16
            Item {
                id: mini
                width: parent.lw; height: parent.height; x: Math.round((parent.width - width) / 2)
                Rectangle {   // a sombra (box-shadow 0 4px 18px #0007), desenhada pela placa
                    anchors.fill: parent; radius: parent.parent.sm["border-radius"]; color: "#000"
                    layer.enabled: false
                }
                RectShadowCSS { anchors.fill: parent; radius: parent.parent.sm["border-radius"]; sombra: parent.parent.sm["box-shadow"][0] }
                Item { id: caixaPrevia; anchors.fill: parent; clip: true }
                // os cantos arredondados POR CIMA da prévia (overflow:hidden + border-radius): 4 cantos na cor do fundo
                CantosRedondos { anchors.fill: parent; raio: parent.parent.sm["border-radius"]; cor: pd.st.background.paradas[0].c }
                // o selo "1" do Identificar (body.pb-on .preview-box .pb-n)
                Rectangle {
                    visible: pd.modoApr; z: 4
                    readonly property var s: T.estilo(["body.pb-on .preview-box .pb-n"], false)
                    x: 7; y: 7; width: s.width; height: s.height; radius: s["border-radius"]
                    border.width: 1.5; border.color: T.V.ouro
                    gradient: Gradient { orientation: Gradient.Vertical
                        GradientStop { position: 0; color: "#14487a" } GradientStop { position: 1; color: "#0f2f5e" } }
                    RectShadowCSS { z: -1; anchors.fill: parent; radius: parent.radius; sombra: parent.s["box-shadow"][0] }
                    Letra { anchors.centerIn: parent; text: "1"; px: 14; weight: 800; color: T.V.ouro }
                }
                Caixa {
                    objectName: "seloPrevia"
                    anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                    clicavel: false
                    sels: [".prev-selo"]; estados: pd.classe ? [".prev-selo." + pd.classe] : []
                    texto: pd.congelado && pd.projetando ? "Congelado" : (pd.emEspera ? "Em espera" : (pd.projetando ? "Ao vivo" : "Prévia"))
                }
            }
        }
        // 3. a tarja do que está no ar (.agora)
        Caixa {
            objectName: "agora"
            visible: !pd.modoApr
            width: col.width; clicavel: false; alinhar: Qt.AlignLeft
            sels: [".agora"]; texto: pd.agora
            larguraTexto: col.width - pad[1] - pad[3]
        }
        // 4. ‹ Projetar › (.nav2) e 5. a barra de ferramentas (.barra-ferr): no modo apresentação vão para a faixa de baixo
        Nav2 {
            visible: !pd.modoApr
            width: col.width
            projetando: pd.projetando; noAr: pd.noAr
            onProjetar: pd.projetarClique(); onAnterior: pd.anterior(); onProximo: pd.proximo()
        }
        BarraFerr {
            visible: !pd.modoApr
            width: col.width
            congelado: pd.congelado; tamRotulo: pd.tamRotulo
            onCongelar: pd.congelar(); onMenor: pd.menor(); onMaior: pd.maior(); onPadrao: pd.padrao(); onProcurarTelas: pd.procurarTelas()
        }
        // 6. os extras do louvor no ar (.barra-extras): só existem quando há cifra ou animação
        Caixa {
            visible: (pd.temCifra || pd.temAnim) && !pd.modoApr
            width: col.width; clicavel: false; sels: [".barra-extras"]; alinhar: Qt.AlignLeft
            implicitHeight: linhaEx.height + pad[0] + pad[2] + (st["border-top"] ? st["border-top"].w : 0)
            Row {
                id: linhaEx; x: parent.pad[3]; y: parent.pad[0]; spacing: parent.st.gap
                // .ff{flex:1}: os botões visíveis dividem a fileira em partes iguais
                readonly property int n: (pd.temCifra ? 1 : 0) + (pd.temAnim ? 1 : 0)
                readonly property real cada: (parent.width - parent.pad[1] - parent.pad[3] - (n - 1) * spacing) / Math.max(1, n)
                Caixa { visible: pd.temCifra; objectName: "botaoCifra"; sels: [".ff", ".ff.extra", ".ff.extra.cifra"]; estados: pd.cifraOn ? [".ff.extra.cifra.on"] : []
                        icone: "violao"; texto: "Cifra"; width: linhaEx.cada; onClicado: pd.cifra() }
                Caixa { visible: pd.temAnim; objectName: "botaoAnim"; sels: [".ff", ".ff.extra", ".ff.extra.cias"]; estados: pd.animOn ? [".ff.extra.cias.on"] : []
                        icone: "cias"; texto: "Animação"; width: linhaEx.cada; onClicado: pd.animacao() }
            }
        }
        // 7. "Lista de projeção" + Limpar (.fila-tit-row)
        Item {
            id: titRow
            // .fila-tit-row{margin-top:2px}: os 2 px entram em cima (medido no Edge: a linha começa 2 px depois do vão)
            readonly property real margem: T.estilo([".fila-tit-row"], false)["margin-top"] || 0
            width: col.width; height: Math.max(titulo.height, bLimpar.height) + margem
            Caixa { id: titulo; clicavel: false; sels: [".fila-tit"]; texto: "Lista de projeção"; alinhar: Qt.AlignLeft
                    anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: titRow.margem / 2 }
            Caixa { id: bLimpar; objectName: "botaoLimpar"; sels: [".mini-btn"]; texto: "Limpar"
                    anchors { right: parent.right; verticalCenter: parent.verticalCenter; verticalCenterOffset: titRow.margem / 2 }
                    onClicado: pd.limpar() }
        }
    }
    // 8. a LISTA (.fila-itens): ocupa o que sobra embaixo e rola; o item no ar com a barrinha dourada
    Caixa {
        id: caixaFila
        clicavel: false; sels: [".fila-itens"]
        x: col.x; width: col.width
        y: col.y + col.height + pd.gap
        height: Math.max(T.n(".fila-itens", "min-height", 90), pd.height - y - pd.pad[2])
        Letra {
            visible: pd.fila.length === 0
            readonly property var sv: T.estilo([".vazio"], false)
            x: caixaFila.pad[3] + sv.padding[3]; y: caixaFila.pad[0] + sv.padding[0]
            width: caixaFila.width - x * 2
            text: "Dê dois cliques em um louvor ou versículo para montar a lista."
            px: sv["font-size"]; color: sv.color; italico: true; quebra: Text.WordWrap; alinhamento: Text.AlignHCenter
        }
        ListView {
            QC.ScrollBar.vertical: BarraRolagem {}
            id: filaView; objectName: "filaView"
            x: caixaFila.pad[3] + caixaFila.bw; y: caixaFila.pad[0] + caixaFila.bw
            width: caixaFila.width - x * 2; height: caixaFila.height - y * 2
            clip: true; model: pd.fila; reuseItems: true
            property int de: -1
            property int alvo: -1
            // provas: a altura de uma linha (para achar a linha k sem adivinhar)
            readonly property real alturaItem: count > 0 && itemAtIndex(0) ? itemAtIndex(0).height : 0
            interactive: de < 0
            delegate: ItemFila {
                width: filaView.width
                linha: index; item: modelData
                noAr: index === pd.posLista
                jaFoi: pd.posLista >= 0 && index < pd.posLista
                alvoArrasto: filaView.alvo === index && filaView.de !== index
                arrastando: filaView.de === index
                lista: filaView
                pb: pd.modoApr
                onIr: pd.irPara(index)
                onSubir: pd.mover(index, -1)
                onDescer: pd.mover(index, 1)
                onTirar: pd.tirar(index)
                onMarcar: pd.marcar(index)
                onSoltar: (de, para) => pd.arrastar(de, para)
            }
        }
    }
}
