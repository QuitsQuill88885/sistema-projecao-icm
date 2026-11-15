// O <header> da 3.0.13 (index.html): ☰ · a marca e o nome da igreja · as 7 abas com ícone · o Estilo (vermelho) · a pílula
// das duas telas. Medidas e cores: as regras header / .hamb / .marca / .tab / .estilo-btn / #dt-pilula do app.css.
import QtQuick
import QtQuick.Window
import "Tema.js" as T
import "Icones.js" as Ic

Rectangle {
    id: cab
    property int aba: 0
    property string igreja: "Projeção"
    property string nomeEstilo: "Estilo Padrão"
    property bool mostrarEstilo: true
    property string pilula: ""              // "" | "on" | "conectar" | "reconectando"
    property string pilulaTexto: ""
    signal escolheu(int i)
    signal menu()
    signal estilo()
    signal pilulaClique()
    readonly property var abasLista: [["louvor", "Louvor"], ["biblia", "Bíblia"], ["timer", "Timer"], ["relogio", "Relógio"],
                                 ["texto", "Texto"], ["slides", "Apresentações"], ["fundos", "Fundos"]]
    readonly property var st: T.estilo(["header"], false)
    readonly property var pad: st["padding"]
    readonly property var bb: st["border-bottom"]
    implicitHeight: pad[0] + Math.max(hamb.height, marca.height, abas.height, est.visible ? est.height : 0, pil.visible ? pil.height : 0) + pad[2] + bb.w   // só o que aparece (sem o Estilo a 3.0.13 fica mais baixa)
    gradient: Gradient {
        GradientStop { position: 0; color: cab.st["background"].paradas[0].c }
        GradientStop { position: 1; color: cab.st["background"].paradas[1].c }
    }
    Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: cab.bb.w; color: cab.bb.cor }

    Item {
        id: dentro
        anchors { fill: parent; leftMargin: cab.pad[3]; rightMargin: cab.pad[1]; topMargin: cab.pad[0]; bottomMargin: cab.pad[2] + cab.bb.w }
        // ☰ (.hamb): três tracinhos; com o mouse, fundo e tracinhos dourados
        Rectangle {
            id: hamb; objectName: "botaoMenu"
            readonly property var s: T.estilo([".hamb"], hambMa.containsMouse)
            readonly property var sp: T.estilo([".hamb span"], false)
            readonly property var sph: T.estilo([".hamb:hover span"], false)
            width: s.width; height: s.height; radius: s["border-radius"]
            color: T.fundo(s.background)
            anchors.verticalCenter: parent.verticalCenter
            Column {
                anchors.centerIn: parent; spacing: hamb.s.gap
                Repeater {
                    model: 3
                    Rectangle { width: hamb.width - hamb.s.padding[1] - hamb.s.padding[3]; height: hamb.sp.height; radius: hamb.sp["border-radius"]
                                color: hambMa.containsMouse ? hamb.sph.background : hamb.sp.background }
                }
            }
            MouseArea { id: hambMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: cab.menu() }
        }
        // a marca (o "S" com a trombeta, 30 px como o MARCA(30) do app.js) e o nome da igreja (<b class="marca-igreja">)
        Row {
            id: marca
            readonly property var s: T.estilo([".marca"], false)
            readonly property var si: T.estilo([".marca-igreja"], false)
            anchors { left: hamb.right; leftMargin: cab.st.gap; verticalCenter: parent.verticalCenter }
            spacing: s.gap
            Image { width: 30; height: 30; sourceSize.width: 30 * Screen.devicePixelRatio; sourceSize.height: 30 * Screen.devicePixelRatio; source: Ic.marca(); anchors.verticalCenter: parent.verticalCenter; smooth: true }
            Letra { text: cab.igreja; color: marca.si.color; px: marca.si["font-size"]; weight: 700
                    lsCss: marca.si["letter-spacing"]; anchors.verticalCenter: parent.verticalCenter
                    largura: Math.min(implicitTextWidth, 260) }
        }
        // as abas (.tabs > .tab): a escolhida fica com fundo e letra dourada (.tab.ativo)
        Row {
            id: abas
            anchors { left: marca.right; leftMargin: cab.st.gap; verticalCenter: parent.verticalCenter }
            spacing: T.estilo([".tabs"], false).gap
            Repeater {
                model: cab.abasLista
                Caixa {
                    objectName: "aba_" + modelData[0]
                    sels: [".tab"]
                    estados: index === cab.aba ? [".tab.ativo"] : []
                    icone: modelData[0]
                    texto: modelData[1]
                    onClicado: cab.escolheu(index)
                }
            }
        }
        // a pílula das duas telas (#dt-pilula) fica depois do Estilo, no canto direito
        Caixa {
            id: pil; objectName: "pilulaTelas"
            visible: cab.pilula !== ""
            sels: ["#dt-pilula"]; estados: cab.pilula ? ["#dt-pilula." + cab.pilula] : []
            texto: cab.pilulaTexto
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            onClicado: cab.pilulaClique()
            // 14/11: a bolinha era um retângulo solto por cima do texto e cobria o "2" de "2 telas · Vaio" (foto do
            // cabeçalho, pilula_larguras.png). Agora é a bolinha da própria Caixa, que empurra o texto.
            bolinha: (cab.pilula === "on" || cab.pilula === "reconectando")
                     ? ["#dt-pilula .dt-bola"].concat(cab.pilula ? ["#dt-pilula." + cab.pilula + " .dt-bola"] : []) : []
        }
        // o Estilo (.estilo-btn, vermelho); com a apresentação aberta ele some (body.modo-apr #btn-estilo)
        Caixa {
            id: est; objectName: "botaoEstilo"
            visible: cab.mostrarEstilo
            sels: [".estilo-btn"]
            icone: "estilo"
            texto: cabeTexto ? cab.nomeEstilo : ""        // sem lugar nem para 4 letras: só o ícone
            // 14/11: em janela estreita (1024) o Estilo passava por cima da aba "Fundos": o nome encolhe com reticências
            // até onde as abas deixam (mínimo: só o ícone e umas letras)
            readonly property real sobra: (pil.visible ? pil.x - cab.st.gap : parent.width) - (abas.x + abas.width + cab.st.gap)
            readonly property bool cabeTexto: sobra - pad[1] - pad[3] - 30 >= 44
            larguraTexto: cabeTexto ? Math.min(rotulo.implicitTextWidth, sobra - pad[1] - pad[3] - 30) : -1
            anchors { right: pil.visible ? pil.left : parent.right; rightMargin: pil.visible ? cab.st.gap : 0; verticalCenter: parent.verticalCenter }
            onClicado: cab.estilo()
        }
    }
}
