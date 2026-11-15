// Um slide ANIMADO (WebP com vários quadros) tocando sem pesar no clique: os quadros vêm do image://anim (decodificados
// UMA vez numa linha de fundo, no tamanho em que aparecem) e aqui só se troca de quadro, no ritmo do próprio arquivo.
// Duas imagens se revezam: a próxima carrega escondida e só aparece pronta (nada pisca). Fica POR CIMA da imagem parada,
// que quem usa mantém embaixo: até os quadros ficarem prontos, aparece o 1º quadro parado, como antes.
import QtQuick

Item {
    id: a
    property string arquivo: ""          // caminho do disco ou file:///
    property int largura: 0              // 0 = tamanho original (o telão)
    property bool tocando: visible
    property int fillMode: Image.PreserveAspectFit
    property var ritmo: arquivo !== "" ? controle.ritmoAnim(arquivo) : []
    readonly property int n: ritmo.length
    property int quadro: 0
    property bool usaB: false            // qual das duas está à mostra
    property bool pronta: false          // já tem um quadro animado à mostra

    // A FILMAGEM (09/11, as camadas viram vídeo): tempo >= 0 = mostra o quadro EXATO desse instante (ms desde o começo),
    // sem relógio. emDia = o quadro pedido já está à mostra (quem filma espera isso antes da foto).
    property real tempo: -1
    readonly property int ciclo: { var s = 0; for (var i = 0; i < n; i++) s += Math.max(20, ritmo[i] || 100); return s }
    readonly property bool emDia: n < 2 || !tocando || (pronta && (usaB ? qB : qA).k === quadro && (usaB ? qB : qA).status === Image.Ready)
    function quadroEm(ms) {
        if (n < 2) return 0
        var r = ms % ciclo, k = 0
        while (k < n - 1 && r >= Math.max(20, ritmo[k] || 100)) { r -= Math.max(20, ritmo[k] || 100); k++ }
        return k
    }
    onTempoChanged: if (tempo >= 0 && n > 1 && tocando) {
        timer.stop()
        var k = quadroEm(tempo)
        if (k === quadro && emDia) return
        quadro = k
        carrega(pronta ? (usaB ? qA : qB) : qA, k)
    }
    function url(k) { return "image://anim/" + largura + "/" + k + "/" + encodeURIComponent(arquivo) }
    // o quadro pedido JÁ está nessa imagem (WebP de 2 quadros: a escondida guarda justamente o próximo): o Qt não recarrega
    // nem avisa, e a animação parava (achado na filmagem 09/11). Então se avisa à mão.
    function carrega(img, k) {
        if (img.k === k && img.source != "" && img.status === Image.Ready) { Qt.callLater(function() { a.chegou(img) }); return }
        img.k = k; img.source = url(k)
    }
    // 15/11 (ele viu as notinhas do 108 das CIAS PARADAS; a HD mediu 1 de 30 quadros com movimento): na FILMAGEM, o
    // posar() esconde e mostra as camadas a cada instante; a camada animada "recomeçava" (tocando mudou) DEPOIS de o tempo
    // já ter sido aplicado e voltava ao quadro 0: todo laço de notinha em CAMADA saía parado (o fundo animado não).
    // Filmando (tempo >= 0), o recomeço vai direto ao quadro do instante pedido.
    function comecar() {
        timer.stop(); pronta = false; usaB = false
        quadro = (tempo >= 0 && n > 1) ? quadroEm(tempo) : 0
        qB.source = ""
        if (tocando && n > 1) carrega(qA, quadro); else qA.source = ""
    }
    // depois da rodada de atualizações: quando o arquivo muda, o ritmo (n) ainda não foi recalculado (achado 07/11:
    // o grande do modo apresentação ficava parado, n = 0 na hora do começo)
    onArquivoChanged: Qt.callLater(comecar)
    onLarguraChanged: Qt.callLater(comecar)
    onTocandoChanged: Qt.callLater(comecar)
    onNChanged: Qt.callLater(comecar)
    Component.onCompleted: Qt.callLater(comecar)

    function chegou(img) {               // a escondida ficou pronta: mostra e agenda o próximo quadro
        if (img.status !== Image.Ready || img.source == "") return
        if (img.k !== quadro) return             // chegou um quadro velho (a filmagem já pediu outro)
        usaB = (img === qB); pronta = true
        if (tempo >= 0) return                   // filmando: sem relógio
        timer.interval = Math.max(20, ritmo[quadro] || 100)
        timer.restart()
    }
    Timer {
        id: timer
        onTriggered: {
            if (!a.tocando || a.n < 2) return
            a.quadro = (a.quadro + 1) % a.n
            a.carrega(a.usaB ? qA : qB, a.quadro)
        }
    }
    Image {
        id: qA
        property int k: -1
        anchors.fill: parent; visible: a.pronta && !a.usaB
        asynchronous: true; cache: false; fillMode: a.fillMode; smooth: true
        onStatusChanged: a.chegou(qA)
    }
    Image {
        id: qB
        property int k: -1
        anchors.fill: parent; visible: a.pronta && a.usaB
        asynchronous: true; cache: false; fillMode: a.fillMode; smooth: true
        onStatusChanged: a.chegou(qB)
    }
}
