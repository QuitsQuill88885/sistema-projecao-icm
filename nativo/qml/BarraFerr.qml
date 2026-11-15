// A BARRA DE FERRAMENTAS (o .barra-ferr da 3.0.13): Congelar | A− Padrão A+ | procurar telas. No #painel ocupa a largura;
// na faixa do modo apresentação tem o tamanho natural (flex:none) e, apertada, o Congelar fica só com o ícone.
import QtQuick
import "Tema.js" as T

Caixa {
    id: barra
    property bool congelado: false
    property string tamRotulo: "Padrão"
    property bool natural: false            // flex:none (na faixa): a largura do conteúdo
    property bool soIcone: false            // #pb-faixa.apertada #btn-congelar{font-size:0}
    signal congelar()
    signal menor()
    signal maior()
    signal padrao()
    signal procurarTelas()
    clicavel: false; sels: [".barra-ferr"]
    implicitHeight: linhaFerr.height + pad[0] + pad[2] + 2 * bw
    implicitWidth: natural ? linhaFerr.width + pad[1] + pad[3] + 2 * bw : 0
    Row {
        id: linhaFerr
        x: barra.pad[3] + barra.bw; y: barra.pad[0] + barra.bw
        spacing: barra.st.gap
        readonly property real util: barra.width - barra.pad[1] - barra.pad[3] - 2 * barra.bw
        // as larguras fixas do app.css: .ff.mini 36 · .ff.tam-label 56 · .sep 1 + margem 2+2
        readonly property real fixos: 36 + 56 + 36 + 36 + 2 * (1 + 4) + 6 * spacing
        Caixa { id: bCong; objectName: "botaoCongelar"; sels: [".ff"]; estados: barra.congelado ? [".ff.freeze-on"] : []
                icone: "congelar"; icoTam: barra.soIcone ? 14 : 0
                texto: barra.soIcone ? "" : (barra.congelado ? "Descongelar" : "Congelar")
                width: barra.natural ? implicitWidth : linhaFerr.util - linhaFerr.fixos; onClicado: barra.congelar() }
        Item { width: 5; height: bCong.height; Rectangle { x: 2; y: 4; width: 1; height: parent.height - 8; color: T.estilo([".sep"], false).background } }
        Caixa { sels: [".ff", ".ff.mini"]; texto: "A−"; width: 36; height: bCong.height; onClicado: barra.menor() }
        Caixa { objectName: "tamLabel"; sels: [".ff", ".ff.mini", ".tam-label", ".ff.tam-label"]; texto: barra.tamRotulo; width: 56; height: bCong.height; onClicado: barra.padrao() }
        Caixa { sels: [".ff", ".ff.mini"]; texto: "A+"; width: 36; height: bCong.height; onClicado: barra.maior() }
        Item { width: 5; height: bCong.height; Rectangle { x: 2; y: 4; width: 1; height: parent.height - 8; color: T.estilo([".sep"], false).background } }
        Caixa { objectName: "procurarTelas"; sels: [".ff", ".ff.mini"]; icone: "telas"; icoTam: 13; width: 36; height: bCong.height
                clicavel: !controle.procurandoTelas; onClicado: barra.procurarTelas() }   // desligado enquanto procura (b.disabled da 3.0.13)
    }
}
