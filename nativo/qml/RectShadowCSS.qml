// Um box-shadow do app.css ({x, y, blur, spread, cor}) desenhado pela placa (RectangularShadow do Qt): sem camada extra.
import QtQuick
import QtQuick.Effects

RectangularShadow {
    property var sombra: null
    visible: !!sombra && !sombra.inset
    offset.x: sombra ? sombra.x : 0
    offset.y: sombra ? sombra.y : 0
    blur: sombra ? sombra.blur : 0
    spread: sombra ? sombra.spread : 0
    color: sombra ? sombra.cor : "transparent"
}
