// O botão redondo do cartão das duas telas (.dt-redondo do app.css da 3.0.12): 42 px, o desenho em TRAÇO (os mesmos
// caminhos do ICO_TROCAR e do ICO_PRONTO do app.js). 13/11 (ele: "melhorar o design daquela seta ... igual a gente já
// tinha estabelecido"): no nativo eram letras ("⇄" e "✓") num botão branco do Qt.
import QtQuick
import QtQuick.Controls
import QtQuick.Shapes

Rectangle {
    id: b
    property string desenho: ""          // o "d" do caminho, na grade de 24 x 24
    property real traco: 2.2
    property real lado: 22               // o tamanho do desenho na tela
    property bool verde: false
    property string dica: ""
    signal clicked()
    implicitWidth: 42; implicitHeight: 42; width: 42; height: 42; radius: 21
    color: verde ? (area.pressed ? "#27784b" : area.containsMouse ? "#37a066" : "#2e8b57")
                 : (area.pressed ? "#16233c" : area.containsMouse ? "#26375a" : "#1e2d49")
    border.color: verde ? "transparent" : "#2c3d5c"; border.width: verde ? 0 : 1
    Shape {
        anchors.centerIn: parent; width: 24; height: 24; scale: b.lado / 24
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: b.verde ? "white" : "#eaf0fb"; strokeWidth: b.traco; fillColor: "transparent"
            capStyle: ShapePath.RoundCap; joinStyle: ShapePath.RoundJoin
            PathSvg { path: b.desenho }
        }
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: b.clicked() }
    ToolTip.visible: area.containsMouse && b.dica !== ""; ToolTip.text: b.dica; ToolTip.delay: 500
}
