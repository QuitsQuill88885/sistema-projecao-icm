// Os sinais ▲ ▼ ✕ dos botões da lista, DESENHADOS (a 3.0.13 escreve o caractere; cada sistema desenharia com outra
// fonte). Tamanho pelo font-size do botão (12 px): o triângulo cheio do ▲/▼ e o X fino do ✕, como o Edge mostra.
import QtQuick
import QtQuick.Shapes

Shape {
    id: s
    property string tipo: "up"
    property color cor: "#cdd9ee"
    property real px: 12
    // medido no Edge: o ▲/▼ do botão (12 px) tem ~11 x 7,5 px; o ✕ ~7,5 x 7,5
    width: tipo === "x" ? px * 0.62 : px * 0.92; height: tipo === "x" ? px * 0.62 : px * 0.64
    preferredRendererType: Shape.CurveRenderer
    ShapePath {
        strokeColor: s.tipo === "x" ? s.cor : "transparent"
        strokeWidth: s.tipo === "x" ? s.px * 0.09 : 0
        fillColor: s.tipo === "x" ? "transparent" : s.cor
        capStyle: ShapePath.FlatCap
        PathSvg {
            path: s.tipo === "up" ? "M" + s.width / 2 + " 0L" + s.width + " " + s.height + "L0 " + s.height + "Z"
                : s.tipo === "dn" ? "M0 0L" + s.width + " 0L" + s.width / 2 + " " + s.height + "Z"
                : "M0 0L" + s.width + " " + s.height + "M" + s.width + " 0L0 " + s.height
        }
    }
}
