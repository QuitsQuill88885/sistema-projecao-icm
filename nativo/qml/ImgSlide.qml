// A imagem de um SLIDE no painel: a imagem parada (aparece na hora) e, se o arquivo é ANIMADO (WebP com vários
// quadros), a animação por cima, como o <img> da 3.0.13. Os quadros vêm do image://anim, decodificados no fundo
// (AnimSlide): o AnimatedImage do Qt custava +300 ms por clique (prova_retorno, 07/11).
import QtQuick

Item {
    id: s
    property string fonte: ""
    property bool animada: false
    property int largura: 400
    property bool tocando: true             // a lista das miniaturas desliga a animação das que estão fora da vista
    // O ESMAECIMENTO das prévias do painel (pedido dele 11/11 00h25: "meter o blurzinho em tudo, na tela no telão agora,
    // próximo, anterior"). Com esmaece > 0 são DUAS imagens que se revezam: a que está na tela fica como está, a nova
    // carrega na outra e entra por cima em `esmaece` ms. (A 1ª versão recarregava a imagem velha para fazê-la sumir: no
    // Vaio essa leitura dava um tranco, e às vezes a imagem "se teletransportava": relato dele 11/11 11h37.)
    // `segura`: a nova espera pronta até o TELÃO começar a troca, para todo mundo esmaecer junto (ViewApr.aguardaTelao).
    property int esmaece: 0
    property bool segura: false
    property bool naB: false                // a imagem que está na tela é a B
    property bool entrando: false           // a outra já recebeu a fonte nova e espera/entra
    readonly property var daTela: naB ? imB : imA
    readonly property var daVez: naB ? imA : imB
    onFonteChanged: troca()
    onSeguraChanged: Qt.callLater(solta)
    Component.onCompleted: troca()
    function troca() {
        if (esmaece <= 0 || String(daTela.source) === "") { daTela.source = fonte; return }       // sem esmaecer / a 1ª imagem
        if (entra.running || entrando) fim()                                                       // a anterior termina já
        if (String(daTela.source) === String(fonte)) return
        if (fonte === "") { daTela.source = ""; return }
        daVez.opacity = 0; daVez.z = 1; daTela.z = 0
        daVez.source = fonte; entrando = true
        Qt.callLater(solta)
    }
    function solta() {
        if (!entrando || entra.running || segura || daVez.status === Image.Loading) return
        entra.target = daVez; entra.restart()
    }
    function fim() {
        entra.stop()
        var nova = daVez, velha = daTela
        nova.opacity = 1; entrando = false; naB = !naB
        velha.opacity = 0; velha.source = ""
    }
    NumberAnimation { id: entra; property: "opacity"; from: 0; to: 1; duration: s.esmaece; easing.type: Easing.InOutQuad
                      onFinished: s.fim() }
    Image {
        id: imA
        objectName: "imgSlide"
        anchors.fill: parent
        onStatusChanged: s.solta()
        fillMode: Image.PreserveAspectFit; asynchronous: true; cache: true
        sourceSize.width: s.largura; sourceSize.height: Math.round(s.largura * 9 / 16)
    }
    Image {
        id: imB
        anchors.fill: parent; opacity: 0; visible: s.esmaece > 0
        onStatusChanged: s.solta()
        fillMode: Image.PreserveAspectFit; asynchronous: true; cache: true
        sourceSize.width: s.largura; sourceSize.height: Math.round(s.largura * 9 / 16)
    }
    // a ANIMAÇÃO EM IMAGEM (protótipo 10/11, NATIVO_ANIM_FORMATO=B): a folha de sprites, no mesmo relógio do telão
    readonly property var sp: (typeof animFormatoB !== "undefined" && animFormatoB && s.animada && s.largura >= 640 && (typeof spriteEspelhos === "undefined" || spriteEspelhos) && typeof controle !== "undefined")
                              ? controle.spritesDe(String(s.fonte)) : ({})
    SpriteAnim { anchors.fill: parent; z: 2; semFundo: true; visible: !!s.sp.fundo && s.visible; tocando: visible && s.tocando; dados: s.sp.fundo ? s.sp : null }
    AnimSlide {
        anchors.fill: parent; z: 2
        visible: s.animada && s.visible && !s.sp.fundo
        tocando: visible && s.tocando
        arquivo: s.animada ? s.fonte : ""
        largura: s.largura
    }
}
