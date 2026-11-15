.pragma library
// GERADO por ferramentas/conversor_312.py a partir de ICM Ipero Projecao (não editar à mão: rode o conversor de novo)
var V = {
"azul": "#0f2f5e",
"azul2": "#14487a",
"vermelho": "#a31a1a",
"ouro": "#f5d76e",
"painel": "#16233c",
"painel2": "#1e2d49",
"txt": "#eaf0fb",
"borda": "#2c3d5c",
"hover": "#26375a",
"verde": "#2e8b57",
"fundo": "#0b1526"
}
var R = {
"*": {
"box-sizing": "border-box",
"margin": [
0,
0,
0,
0
],
"padding": [
0,
0,
0,
0
]
},
"html": {
"height": {
"pct": 100.0
},
"font-family": "'Segoe UI',system-ui,sans-serif",
"background": "#0b1526",
"color": "#eaf0fb",
"overflow": "hidden"
},
"body": {
"height": {
"pct": 100.0
},
"font-family": "'Segoe UI',system-ui,sans-serif",
"background": "#0b1526",
"color": "#eaf0fb",
"overflow": "hidden",
"-webkit-user-select": "none",
"user-select": "none"
},
"button": {
"font-family": "inherit",
"cursor": "pointer",
"border": {
"w": 0,
"cor": "transparent"
},
"color": "inherit"
},
".st-ouro": {
"color": "#e8b93c",
"font-weight": 600
},
".ico": {
"display": "inline-flex",
"align-items": "center",
"justify-content": "center"
},
".ico svg": {
"display": "block"
},
"#app": {
"display": "grid",
"grid-template-rows": "auto 1fr",
"grid-template-columns": "minmax(0,1fr)",
"height": "100vh"
},
"header": {
"display": "flex",
"align-items": "center",
"gap": 10,
"background": {
"ang": 180.0,
"paradas": [
{
"p": 0.0,
"c": "#12294a"
},
{
"p": 1.0,
"c": "#0d1f3a"
}
]
},
"padding": [
6,
12,
6,
12
],
"border-bottom": {
"w": 2,
"cor": "#a31a1a",
"tracejado": false
}
},
"header .logo": {
"font-weight": 800,
"font-size": 17,
"color": "#ffffff",
"letter-spacing": 0.5,
"white-space": "nowrap"
},
".marca": {
"display": "flex",
"align-items": "center",
"gap": 9,
"white-space": "nowrap",
"min-width": 0
},
".marca svg": {
"display": "block"
},
".marca-igreja": {
"font-size": 15,
"color": "#ffffff",
"letter-spacing": 0.3,
"min-width": 0,
"overflow": "hidden",
"text-overflow": "ellipsis",
"white-space": "nowrap"
},
".bv-overlay": {
"position": "fixed",
"inset": [
0,
0,
0,
0
],
"background": "#cc060d1a",
"backdrop-filter": {
"blur": 3.0
},
"z-index": 300,
"display": "flex",
"align-items": "center",
"justify-content": "center",
"padding": [
22,
22,
22,
22
]
},
".bv-overlay.oculto": {
"display": "none"
},
".bv-box": {
"background": {
"ang": 180.0,
"paradas": [
{
"p": 0.0,
"c": "#18263f"
},
{
"p": 1.0,
"c": "#111c31"
}
]
},
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 18,
"width": "min(680px,96vw)",
"max-height": "92vh",
"display": "flex",
"flex-direction": "column",
"box-shadow": [
{
"x": 0,
"y": 24,
"blur": 70,
"spread": 0,
"cor": "#bb000000",
"inset": false
}
]
},
".bv-passos": {
"display": "flex",
"gap": 7,
"justify-content": "center",
"padding": [
18,
0,
4,
0
]
},
".bv-ponto": {
"width": 7,
"height": 7,
"border-radius": {
"pct": 50.0
},
"background": "#2c3d5c",
"transition": ".2s"
},
".bv-ponto.on": {
"background": "#f5d76e",
"width": 20,
"border-radius": 4
},
".bv-corpo": {
"flex": 1,
"overflow-y": "auto",
"padding": [
14,
34,
8,
34
],
"text-align": "center"
},
".bv-corpo h2": {
"color": "#f5d76e",
"font-size": 23,
"margin-bottom": 5,
"letter-spacing": -0.2
},
".bv-sub": {
"color": "#9db3d6",
"font-size": 13.5,
"margin-bottom": 18
},
".bv-corpo p": {
"font-size": 13.5,
"line-height": 1.65,
"color": "#cdd9ee"
},
".bv-marca": {
"display": "flex",
"justify-content": "center",
"margin": [
6,
0,
16,
0
]
},
".bv-verso": {
"font-style": "italic",
"color": "#9db3d6",
"font-size": 13,
"line-height": 1.6,
"margin": [
0,
"auto",
16,
"auto"
],
"max-width": "44ch",
"border-left": {
"w": 2,
"cor": "#f5d76e",
"tracejado": false
},
"padding-left": 14,
"text-align": "left"
},
".bv-verso span": {
"display": "block",
"font-style": "normal",
"font-size": 11,
"letter-spacing": 1.4,
"color": "#f5d76e",
"margin-top": 6,
"text-transform": "uppercase"
},
".bv-lista": {
"list-style": "none",
"text-align": "left",
"max-width": "46ch",
"margin": [
0,
"auto",
0,
"auto"
],
"display": "flex",
"flex-direction": "column",
"gap": 10
},
".bv-lista li": {
"font-size": 13.5,
"color": "#cdd9ee",
"line-height": 1.5,
"padding-left": 20,
"position": "relative"
},
".bv-lista li::before": {
"content": "''",
"position": "absolute",
"left": 0,
"top": 7,
"width": 7,
"height": 7,
"border-radius": {
"pct": 50.0
},
"background": "#f5d76e"
},
".bv-lista b": {
"color": "#ffffff"
},
".bv-igreja": {
"margin-top": 16,
"text-align": "left"
},
".bv-igreja input[type=text]": {
"width": {
"pct": 100.0
}
},
".bv-cultos": {
"margin-top": 6,
"max-height": 230,
"overflow-y": "auto",
"padding-right": 4
},
".bv-dia h4": {
"font-size": 11.5,
"color": "#f5d76e",
"text-transform": "uppercase",
"letter-spacing": 1,
"margin": [
12,
0,
6,
0
]
},
".bv-rodape": {
"display": "flex",
"align-items": "center",
"gap": 10,
"padding": [
16,
26,
20,
26
],
"border-top": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"margin-top": 8
},
".bv-pular": {
"background": "none",
"color": "#7f96b8",
"font-size": 12.5,
"text-decoration": "underline",
"padding": [
6,
2,
6,
2
]
},
".bv-pular:hover": {
"color": "#cdd9ee"
},
".bv-navs": {
"margin-left": "auto",
"display": "flex",
"gap": 8
},
".tabs": {
"display": "flex",
"gap": 2,
"min-width": 0,
"overflow-x": "auto",
"scrollbar-width": "none"
},
".tabs::-webkit-scrollbar": {
"display": "none"
},
".tab": {
"display": "flex",
"align-items": "center",
"gap": 7,
"padding": [
8,
14,
8,
14
],
"border-radius": 8,
"background": "transparent",
"color": "#9db3d6",
"font-size": 13,
"font-weight": 600
},
".tab .ico": {
"font-size": 15
},
".tab:hover": {
"background": "#26375a",
"color": "#ffffff"
},
".tab.ativo": {
"background": "#1e2d49",
"color": "#f5d76e"
},
".estilo-btn": {
"display": "flex",
"align-items": "center",
"gap": 8,
"margin-left": "auto",
"padding": [
9,
16,
9,
16
],
"border-radius": 8,
"background": "#a31a1a",
"color": "#ffffff",
"font-size": 14,
"font-weight": 700,
"flex": "none",
"white-space": "nowrap"
},
".estilo-btn:hover": {
"background": "#cc2222"
},
".estilo-btn .ico": {
"font-size": 17
},
"body.modo-apr #btn-estilo": {
"display": "none"
},
"main": {
"display": "grid",
"grid-template-columns": "1fr 348px",
"overflow": "hidden",
"min-height": 0
},
"#conteudo": {
"position": "relative",
"overflow": "hidden",
"min-height": 0
},
".view": {
"display": "none",
"position": "absolute",
"inset": [
0,
0,
0,
0
],
"overflow": "hidden"
},
".view.ativo": {
"display": "grid"
},
".view[data-aba=\"louvor\"].ativo": {
"grid-template-columns": "minmax(220px,1fr) minmax(260px,1.3fr)"
},
".view[data-aba=\"biblia\"].ativo": {
"grid-template-columns": "210px 1fr"
},
".col": {
"background": "#16233c",
"border-right": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"display": "flex",
"flex-direction": "column",
"overflow": "hidden"
},
".col:last-child": {
"border-right": {
"w": 0,
"cor": "transparent"
}
},
".col h3": {
"padding": [
8,
12,
8,
12
],
"font-size": 11,
"text-transform": "uppercase",
"letter-spacing": 1,
"color": "#8fa8cf",
"background": "#101d33"
},
".busca": {
"padding": [
8,
8,
8,
8
],
"background": "#101d33"
},
".busca input": {
"width": {
"pct": 100.0
},
"padding": [
9,
12,
9,
12
],
"border-radius": 8,
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"background": "#0c1830",
"color": "#ffffff",
"font-size": 14
},
".lista": {
"overflow-y": "auto",
"flex": 1
},
".item": {
"padding": [
7,
12,
7,
12
],
"font-size": 13,
"border-bottom": {
"w": 1,
"cor": "#0affffff",
"tracejado": false
},
"line-height": 1.3,
"white-space": "nowrap",
"overflow": "hidden",
"text-overflow": "ellipsis"
},
".item.col-lista": {
"white-space": "nowrap",
"overflow": "hidden",
"text-overflow": "ellipsis"
},
".item:hover": {
"background": "#26375a"
},
".item.sel": {
"background": "#14487a",
"color": "#ffffff",
"font-weight": 600
},
".item.na-lista": {
"box-shadow": [
{
"x": 3,
"y": 0,
"blur": 0,
"spread": 0,
"cor": "#f5d76e",
"inset": true
}
]
},
".grupo-col": {
"position": "sticky",
"top": 0,
"z-index": 2,
"padding": [
4,
12,
4,
12
],
"font-size": 10.5,
"font-weight": 700,
"letter-spacing": 0.8,
"color": "#f5d76e",
"background": "#101d33",
"border-top": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
".grupo-col:first-child": {
"border-top": {
"w": 0,
"cor": "transparent"
}
},
".grupo-col.cias": {
"color": "#c79bff"
},
".item.cias": {
"background": "#127b2d9e"
},
".item.cias:hover": {
"background": "#26375a"
},
".item.cias.sel": {
"background": "#14487a"
},
".marca-lista": {
"color": "#f5d76e",
"font-size": 11,
"margin-right": 5
},
".item small": {
"color": "#7f9ac0",
"margin-right": 5
},
"#lista-slides .item": {
"white-space": "normal"
},
".vazio": {
"padding": [
22,
14,
22,
14
],
"color": "#6f86a8",
"font-size": 14,
"text-align": "center",
"font-style": "italic"
},
".grid-num .vazio": {
"grid-column": "1/-1"
},
".grid-num": {
"display": "grid",
"grid-template-columns": "repeat(auto-fill,minmax(44px,1fr))",
"gap": 6,
"padding": [
10,
12,
10,
12
],
"overflow-y": "auto",
"align-content": "start"
},
".col-cv h3": {
"margin-top": 0,
"border-top": {
"w": 1,
"cor": "#10ffffff",
"tracejado": false
}
},
".col-cv h3:first-child": {
"border-top": {
"w": 0,
"cor": "transparent"
}
},
"#grid-caps": {
"flex": "0 0 auto",
"max-height": {
"pct": 38.0
}
},
"#grid-vers": {
"flex": "1 1 auto",
"min-height": 0
},
".gnum": {
"padding": [
9,
0,
9,
0
],
"text-align": "center",
"border-radius": 6,
"background": "#13223a",
"font-size": 14,
"position": "relative"
},
".gnum:hover": {
"background": "#26375a"
},
".gnum.sel": {
"background": "#a31a1a",
"color": "#ffffff",
"font-weight": 700
},
".centro": {
"place-items": "center",
"overflow-y": "auto",
"background": "#0b1526",
"padding": [
26,
0,
26,
0
]
},
".card": {
"background": {
"ang": 180.0,
"paradas": [
{
"p": 0.0,
"c": "#18263f"
},
{
"p": 1.0,
"c": "#141f36"
}
]
},
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 14,
"padding": [
22,
24,
22,
24
],
"margin": [
0,
20,
0,
20
],
"width": "min(620px,88%)",
"box-shadow": [
{
"x": 0,
"y": 14,
"blur": 40,
"spread": 0,
"cor": "#66000000",
"inset": false
}
]
},
".card h2": {
"color": "#f5d76e",
"margin-bottom": 4,
"font-size": 15.5,
"letter-spacing": 0.4
},
".card h2+.dica": {
"margin-bottom": 18
},
".row": {
"display": "flex",
"gap": 9,
"flex-wrap": "wrap",
"align-items": "center",
"margin-bottom": 12
},
".big-btn": {
"background": "#1e2d49",
"padding": [
9,
15,
9,
15
],
"border-radius": 8,
"font-size": 12.5,
"font-weight": 600,
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"transition": ".15s"
},
".big-btn:hover": {
"background": "#26375a",
"border-color": "#3b5680"
},
".big-btn.ouro": {
"background": "#f5d76e",
"color": "#20242c",
"border-color": "transparent",
"font-weight": 700
},
".big-btn.ouro:hover": {
"background": "#ffe390"
},
".big-btn.verde": {
"background": "#2e8b57",
"border-color": "transparent",
"color": "#ffffff"
},
".big-btn.verde:hover": {
"background": "#37a066"
},
".big-btn.vermelho": {
"background": "#a31a1a",
"border-color": "transparent",
"color": "#ffffff"
},
".big-btn.vermelho:hover": {
"background": "#c02525"
},
"input[type=number]": {
"background": "#0b1729",
"color": "#ffffff",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 9,
"padding": [
10,
12,
10,
12
],
"font-size": 13.5,
"font-family": "inherit",
"transition": ".15s"
},
"input[type=text]": {
"background": "#0b1729",
"color": "#ffffff",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 9,
"padding": [
10,
12,
10,
12
],
"font-size": 13.5,
"font-family": "inherit",
"transition": ".15s"
},
"select": {
"background": "#0b1729",
"color": "#ffffff",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 9,
"padding": [
10,
12,
10,
12
],
"font-size": 13.5,
"font-family": "inherit",
"transition": ".15s"
},
"textarea": {
"background": "#0b1729",
"color": "#ffffff",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 9,
"padding": [
10,
12,
10,
12
],
"font-size": 13.5,
"font-family": "inherit",
"transition": ".15s",
"width": {
"pct": 100.0
},
"min-height": 130,
"resize": "vertical",
"line-height": 1.6,
"-webkit-user-select": "text",
"user-select": "text"
},
"input:focus": {
"outline": {
"w": 0,
"cor": "transparent"
},
"border-color": "#f5d76e",
"background": "#0d1b31"
},
"select:focus": {
"outline": {
"w": 0,
"cor": "transparent"
},
"border-color": "#f5d76e",
"background": "#0d1b31"
},
"textarea:focus": {
"outline": {
"w": 0,
"cor": "transparent"
},
"border-color": "#f5d76e",
"background": "#0d1b31"
},
".timer-display": {
"font-size": 54,
"font-weight": 800,
"color": "#f5d76e",
"text-align": "center",
"font-variant-numeric": "tabular-nums",
"margin": [
18,
0,
18,
0
],
"letter-spacing": 1,
"text-shadow": [
{
"x": 0,
"y": 4,
"blur": 20,
"spread": 0,
"cor": "#22f5d76e",
"inset": false
}
]
},
".dica": {
"font-size": 12.5,
"color": "#8299bb",
"margin-bottom": 10,
"line-height": 1.6
},
".dica b": {
"color": "#b9cbe6"
},
".sl-status": {
"font-size": 12.5,
"color": "#8fa8cf"
},
".sl-status.erro": {
"color": "#ee8888"
},
".sl-grade": {
"display": "grid",
"grid-template-columns": "repeat(auto-fill,minmax(150px,1fr))",
"gap": 10,
"margin-top": 14,
"max-height": "52vh",
"overflow-y": "auto"
},
".sl-card": {
"position": "relative",
"border": {
"w": 2,
"cor": "transparent",
"tracejado": false
},
"border-radius": 9,
"overflow": "hidden",
"background": "#0c1830",
"cursor": "pointer"
},
".sl-card:hover": {
"border-color": "#14487a"
},
".sl-card.sel": {
"border-color": "#f5d76e"
},
".sl-card img": {
"width": {
"pct": 100.0
},
"aspect-ratio": "16/9",
"object-fit": "cover",
"display": "block"
},
".sl-card span": {
"position": "absolute",
"left": 6,
"bottom": 6,
"background": "#bb000000",
"color": "#ffffff",
"font-size": 11,
"font-weight": 700,
"border-radius": 11,
"padding": [
2,
8,
2,
8
]
},
".sl-card.sel span": {
"background": "#f5d76e",
"color": "#1a1a1a"
},
".fundo-cats": {
"display": "flex",
"flex-wrap": "wrap",
"gap": 6,
"margin-bottom": 14
},
".fcat": {
"background": "#0c1830",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 20,
"padding": [
6,
14,
6,
14
],
"font-size": 12,
"color": "#9db3d6",
"font-weight": 600,
"transition": ".15s"
},
".fcat:hover": {
"background": "#26375a",
"color": "#ffffff"
},
".fcat.on": {
"background": "#f5d76e",
"border-color": "#f5d76e",
"color": "#1a1a1a"
},
".grid-fundos": {
"display": "grid",
"grid-template-columns": "repeat(auto-fill,minmax(190px,1fr))",
"gap": 12
},
".fundo-card": {
"border-radius": 10,
"overflow": "hidden",
"border": {
"w": 2,
"cor": "transparent",
"tracejado": false
},
"background": "#0c1830",
"position": "relative"
},
".fundo-card:hover": {
"border-color": "#14487a"
},
".fundo-card.espera": {
"border-color": "#f5d76e"
},
".fundo-card.projetando": {
"border-color": "#2e8b57",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 1,
"cor": "#2e8b57",
"inset": false
}
]
},
".fundo-card img": {
"width": {
"pct": 100.0
},
"aspect-ratio": "16/9",
"object-fit": "cover",
"display": "block",
"cursor": "pointer"
},
".fundo-card .nome": {
"display": "block",
"padding": [
7,
7,
7,
7
],
"font-size": 13,
"text-align": "center",
"cursor": "pointer"
},
".fundo-acoes": {
"position": "absolute",
"top": 7,
"right": 7,
"display": "flex",
"gap": 5,
"opacity": 0,
"transition": ".15s"
},
".fundo-card:hover .fundo-acoes": {
"opacity": 1
},
".fa": {
"background": "#bb000000",
"color": "#ffffff",
"border": {
"w": 1,
"cor": "#55ffffff",
"tracejado": false
},
"border-radius": 16,
"padding": [
4,
10,
4,
10
],
"font-size": 11.5,
"font-weight": 600
},
".fa-espera:hover": {
"background": "#2e8b57",
"border-color": "#2e8b57"
},
".fa-del:hover": {
"background": "#8a2020",
"border-color": "#8a2020"
},
".badge-espera": {
"position": "absolute",
"top": 8,
"left": 8,
"background": "#f5d76e",
"color": "#1a1a1a",
"border-radius": 20,
"padding": [
4,
11,
4,
11
],
"font-size": 11.5,
"font-weight": 700
},
".add-card": {
"border": {
"w": 2,
"cor": "#2c3d5c",
"tracejado": true
},
"background": "#550c1830",
"display": "flex",
"align-items": "center",
"justify-content": "center",
"cursor": "pointer",
"min-height": 130
},
".add-card:hover": {
"border-color": "#2e8b57",
"background": "#55122440"
},
".add-inner": {
"display": "flex",
"flex-direction": "column",
"align-items": "center",
"gap": 6,
"color": "#9db3d6",
"font-size": 13
},
".add-inner .plus": {
"font-size": 36,
"line-height": 0.9,
"color": "#2e8b57",
"font-weight": 300
},
".campo-lbl": {
"display": "block",
"font-size": 11,
"text-transform": "uppercase",
"letter-spacing": 1.2,
"color": "#8fa8cf",
"font-weight": 700,
"margin-bottom": 6
},
".fundos-liso": {
"display": "grid",
"grid-template-columns": "repeat(auto-fill,minmax(140px,1fr))",
"gap": 10
},
".liso-card": {
"border": {
"w": 2,
"cor": "transparent",
"tracejado": false
},
"border-radius": 9,
"overflow": "hidden",
"background": "#0c1830",
"cursor": "pointer"
},
".liso-card:hover": {
"border-color": "#14487a"
},
".liso-card.sel": {
"border-color": "#f5d76e"
},
".liso-card img": {
"width": {
"pct": 100.0
},
"aspect-ratio": "16/9",
"object-fit": "cover",
"display": "block"
},
".liso-card span": {
"display": "block",
"padding": [
5,
5,
5,
5
],
"font-size": 11.5,
"text-align": "center",
"color": "#cdd9ee"
},
".liso-card.sel span": {
"color": "#f5d76e",
"font-weight": 600
},
".add-form": {
"display": "flex",
"flex-direction": "column",
"gap": 10,
"margin-bottom": 16
},
".add-form input[type=file]": {
"color": "#cdd9ee",
"font-size": 13
},
".af-prev": {
"width": {
"pct": 100.0
},
"aspect-ratio": "16/9",
"object-fit": "cover",
"border-radius": 8,
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
"#painel": {
"background": {
"ang": 180.0,
"paradas": [
{
"p": 0.0,
"c": "#131f33"
},
{
"p": 1.0,
"c": "#0e1830"
}
]
},
"border-left": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"display": "flex",
"flex-direction": "column",
"padding": [
10,
10,
10,
10
],
"gap": 6,
"overflow": "hidden",
"min-height": 0
},
"#painel>*:not(.fila-itens)": {
"flex-shrink": 0
},
".ctrl-linha:not(.tam)": {
"margin-top": 4
},
".fila-tit-row": {
"margin-top": 2,
"display": "flex",
"align-items": "center",
"gap": 6
},
".estado-barra": {
"display": "flex",
"align-items": "center",
"justify-content": "center",
"gap": 8,
"padding": [
9,
12,
9,
12
],
"border-radius": 9,
"font-size": 12.5,
"font-weight": 600,
"letter-spacing": 0.3,
"background": "#1a2438",
"color": "#9db3d6",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
".estado-barra.aovivo": {
"background": "#3a1418",
"border-color": "#aa3333",
"color": "#ffc9c9"
},
".estado-barra.espera": {
"background": "#1b2a44",
"border-color": "#3c5a86",
"color": "#a9c0e0"
},
".estado-barra.espera .dot": {
"background": "#5b7ba8"
},
".prev-selo.espera": {
"background": "#99000000",
"color": "#cdd9ee"
},
".estado-barra.congelado": {
"background": "#1ff5d76e",
"border-color": "#88f5d76e",
"color": "#f5d76e"
},
".estado-barra .dot": {
"width": 9,
"height": 9,
"border-radius": {
"pct": 50.0
},
"background": "#555566",
"flex": "none"
},
".estado-barra.aovivo .dot": {
"background": "#ee2233",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 9,
"spread": 0,
"cor": "#ee2233",
"inset": false
}
]
},
".estado-barra.congelado .dot": {
"background": "#f5d76e",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 8,
"spread": 0,
"cor": "#f5d76e",
"inset": false
}
]
},
".preview-box .mini": {
"position": "relative",
"width": "min(100%,calc(26vh * 16 / 9))",
"aspect-ratio": "16/9",
"border-radius": 8,
"overflow": "hidden",
"background": "#000000",
"box-shadow": [
{
"x": 0,
"y": 4,
"blur": 18,
"spread": 0,
"cor": "#77000000",
"inset": false
}
]
},
".prev-selo": {
"position": "absolute",
"left": 0,
"right": 0,
"bottom": 0,
"text-align": "center",
"font-size": 11,
"font-weight": 700,
"letter-spacing": 0.6,
"padding": [
4,
4,
4,
4
],
"background": "#cc000000",
"color": "#e8eefb"
},
".prev-selo.aovivo": {
"background": "#d98e1b1b",
"color": "#ffffff"
},
".prev-selo.congelado": {
"background": "#ddf5d76e",
"color": "#1a1a1a"
},
".dot": {
"width": 10,
"height": 10,
"border-radius": {
"pct": 50.0
},
"background": "#555566"
},
".dot.on": {
"background": "#ee2233",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 8,
"spread": 0,
"cor": "#ee2233",
"inset": false
}
]
},
".dot.espera": {
"background": "#7f9ac0",
"box-shadow": []
},
".preview-box": {
"display": "flex",
"justify-content": "center"
},
".preview-box iframe": {
"width": {
"pct": 100.0
},
"height": {
"pct": 100.0
},
"border": {
"w": 0,
"cor": "transparent"
},
"display": "block"
},
".agora": {
"font-size": 11.5,
"color": "#cdd9ee",
"background": "#0c1830",
"border-radius": 6,
"padding": [
6,
10,
6,
10
],
"white-space": "nowrap",
"overflow": "hidden",
"text-overflow": "ellipsis"
},
".ctrl": {
"background": "#1e2d49",
"border-radius": 8,
"padding": [
6,
8,
6,
8
],
"font-size": 11.5,
"font-weight": 600,
"display": "flex",
"align-items": "center",
"justify-content": "center",
"gap": 5
},
".ctrl:hover": {
"background": "#26375a"
},
".ctrl .ico": {
"font-size": 14
},
".ctrl.projetar": {
"background": "#2e8b57",
"font-size": 12.5,
"padding": [
8,
8,
8,
8
]
},
".ctrl.projetar.on": {
"background": "#a31a1a"
},
".ctrl.projetar.on.em-espera": {
"background": "#4a5c7a"
},
".barra-extras": {
"display": "flex",
"gap": 6,
"padding": [
5,
8,
5,
8
],
"border-top": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
".barra-extras.oculto": {
"display": "none"
},
".ff.extra.oculto": {
"display": "none"
},
".ff.extra": {
"display": "flex",
"align-items": "center",
"gap": 5,
"font-size": 11.5,
"padding": [
5,
10,
5,
10
],
"border-radius": 7,
"background": "#16233c",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#b9cbe6"
},
".ff.extra:hover": {
"background": "#26375a"
},
".ff.extra.cifra.on": {
"background": "#a8570f",
"border-color": "#d4761c",
"color": "#ffffff"
},
".ff.extra.cias.on": {
"background": "#8a6d10",
"border-color": "#c9a227",
"color": "#ffffff"
},
".ctrl-linha": {
"display": "flex",
"gap": 5
},
".ctrl-linha .ctrl": {
"flex": 1
},
".nav2": {
"display": "flex",
"gap": 6
},
".nav2 .projetar": {
"flex": 1
},
".nav2 .nav": {
"flex": "0 0 46px",
"background": "#14487a",
"font-size": 12.5,
"font-weight": 700,
"padding": [
8,
8,
8,
8
]
},
".nav2 .nav:hover": {
"background": "#1a5a96"
},
".nav2 .nav .ico": {
"font-size": 15
},
".ctrl-linha.tam": {
"align-items": "stretch"
},
".tam-label": {
"flex": 1.6,
"background": "#0c1830",
"color": "#f5d76e",
"font-weight": 700,
"font-size": 11.5
},
".tam-label:hover": {
"background": "#26375a"
},
".freeze-on": {
"outline": {
"w": 2,
"cor": "#f5d76e",
"tracejado": false
},
"outline-offset": -2,
"color": "#f5d76e"
},
".fila-tit": {
"font-size": 12,
"text-transform": "uppercase",
"letter-spacing": 1,
"color": "#f5d76e",
"font-weight": 700,
"padding": [
2,
2,
2,
2
]
},
".fila-itens": {
"flex": "1 1 auto",
"flex-shrink": 1,
"min-height": 90,
"overflow-y": "auto",
"scrollbar-width": "thin",
"background": "#0c1830",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 8,
"padding": [
4,
4,
4,
4
]
},
".fila-itens::-webkit-scrollbar": {
"width": 9
},
".fila-itens::-webkit-scrollbar-thumb": {
"background": "#3b5680",
"border-radius": 5
},
".fila-itens::-webkit-scrollbar-track": {
"background": "#0a1526"
},
".fila-item": {
"display": "flex",
"align-items": "center",
"gap": 6,
"padding": [
8,
9,
8,
9
],
"border-radius": 6,
"font-size": 13,
"cursor": "grab"
},
".fila-item:hover": {
"background": "#26375a"
},
".fila-item:hover .fila-btns": {
"opacity": 1
},
".fila-item.atual": {
"background": "#14487a",
"box-shadow": [
{
"x": 3,
"y": 0,
"blur": 0,
"spread": 0,
"cor": "#f5d76e",
"inset": true
}
]
},
".fila-item.ja-foi": {
"opacity": 0.42
},
".fila-item.ja-foi .rot": {
"text-decoration": "line-through",
"text-decoration-color": "#5d7ba8"
},
".fila-item.ja-foi:hover": {
"opacity": 0.85
},
".fila-item.arrastando": {
"opacity": 0.4
},
".fila-item.drop-alvo": {
"box-shadow": [
{
"x": 0,
"y": 3,
"blur": 0,
"spread": 0,
"cor": "#f5d76e",
"inset": true
}
]
},
".fila-btns": {
"margin-left": "auto",
"display": "flex",
"gap": 3,
"opacity": 0.8,
"transition": ".15s"
},
".fila-item:focus-within .fila-btns": {
"opacity": 1
},
".fila-btns .fb": {
"width": 25,
"height": 25,
"border-radius": 6,
"background": "#22314f",
"color": "#cdd9ee",
"font-size": 12,
"line-height": 1
},
".fila-btns .fb:hover": {
"background": "#26375a",
"color": "#ffffff"
},
".fila-btns .fb.x:hover": {
"background": "#7a2020",
"color": "#ffffff"
},
".gnum.na-fila": {
"box-shadow": [
{
"x": 0,
"y": -4,
"blur": 0,
"spread": 0,
"cor": "#f5d76e",
"inset": true
}
]
},
".fila-tit-row .fila-tit": {
"flex": 1,
"margin": [
0,
0,
0,
0
]
},
".mini-btn": {
"background": "#2c3d5c",
"border-radius": 6,
"padding": [
5,
9,
5,
9
],
"font-size": 11,
"color": "#cdd9ee",
"font-weight": 600
},
".mini-btn:hover": {
"background": "#26375a"
},
".mini-btn.destaque": {
"background": "#2e8b57",
"color": "#ffffff"
},
".mini-btn.destaque:hover": {
"background": "#37a066"
},
".fila-item .rot": {
"flex": 1,
"overflow": "hidden",
"text-overflow": "ellipsis",
"white-space": "nowrap"
},
".fila-item .chk": {
"width": 19,
"height": 19,
"flex": "none",
"border": {
"w": 1.5,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 5,
"display": "flex",
"align-items": "center",
"justify-content": "center",
"font-size": 12,
"background": "#0a1526"
},
".fila-item .chk.on": {
"background": "#f5d76e",
"border-color": "#f5d76e",
"color": "#1a1a1a",
"font-weight": 700
},
".fila-item .chk:hover": {
"border-color": "#f5d76e"
},
".fila-dica": {
"font-size": 10.5,
"color": "#f5d76e",
"letter-spacing": 0.3,
"opacity": 0.85
},
".fila-num": {
"flex": "0 0 auto",
"min-width": {
"em": 1.35
},
"text-align": "right",
"margin-right": 6,
"font-size": 11,
"color": "#6f86a8",
"font-variant-numeric": "tabular-nums"
},
".fila-item.atual .fila-num": {
"color": "#f5d76e"
},
".fila-grupo": {
"font-size": 9.5,
"text-transform": "uppercase",
"letter-spacing": 1.3,
"color": "#7f96b8",
"font-weight": 700,
"padding": [
8,
4,
3,
4
],
"border-bottom": {
"w": 1,
"cor": "#10ffffff",
"tracejado": false
},
"margin-bottom": 3
},
".fila-grupo:first-child": {
"padding-top": 2
},
".barra-ferr": {
"display": "flex",
"align-items": "stretch",
"gap": 3,
"background": "#0f1c30",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 9,
"padding": [
3,
3,
3,
3
]
},
".ff": {
"flex": 1,
"display": "flex",
"align-items": "center",
"justify-content": "center",
"gap": 5,
"background": "transparent",
"border-radius": 6,
"padding": [
7,
5,
7,
5
],
"font-size": 11,
"font-weight": 600,
"color": "#a9bcd8",
"white-space": "nowrap"
},
".ff:hover": {
"background": "#26375a",
"color": "#ffffff"
},
".ff .ico": {
"font-size": 13
},
".ff.mini": {
"flex": "0 0 36px"
},
".ff.tam-label": {
"flex": "0 0 56px",
"color": "#f5d76e",
"font-weight": 700
},
".ff.freeze-on": {
"background": "#f5d76e",
"color": "#1a1a1a"
},
".sep": {
"width": 1,
"background": "#2c3d5c",
"margin": [
4,
2,
4,
2
],
"flex": "none"
},
".mini-btn.destaque.ativo": {
"background": "#f5d76e",
"color": "#1a1a1a"
},
".fila-item.agrupado": {
"box-shadow": [
{
"x": 4,
"y": 0,
"blur": 0,
"spread": 0,
"cor": "#f5d76e",
"inset": true
}
],
"background": "#12f5d76e"
},
".fila-item.agrupado .chk.on": {
"background": "#f5d76e",
"border-color": "#f5d76e",
"color": "#1a1a1a"
},
".modo-juntos": {
"outline": {
"w": 1,
"cor": "#f5d76e",
"tracejado": false
},
"outline-offset": -1
},
".hamb": {
"display": "flex",
"flex-direction": "column",
"justify-content": "center",
"gap": 4,
"width": 34,
"height": 32,
"border-radius": 8,
"background": "transparent",
"padding": [
0,
7,
0,
7
]
},
".hamb span": {
"display": "block",
"height": 2,
"background": "#9db3d6",
"border-radius": 2,
"transition": ".15s"
},
".hamb:hover": {
"background": "#26375a"
},
".hamb:hover span": {
"background": "#f5d76e"
},
".menu-overlay": {
"position": "fixed",
"inset": [
0,
0,
0,
0
],
"background": "#aa000000",
"z-index": 150,
"display": "flex"
},
".menu-overlay.oculto": {
"display": "none"
},
".menu-lateral": {
"width": "min(560px,94vw)",
"height": {
"pct": 100.0
},
"background": {
"ang": 180.0,
"paradas": [
{
"p": 0.0,
"c": "#16233c"
},
{
"p": 1.0,
"c": "#101a2e"
}
]
},
"border-right": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"display": "flex",
"flex-direction": "column",
"box-shadow": [
{
"x": 8,
"y": 0,
"blur": 40,
"spread": 0,
"cor": "#aa000000",
"inset": false
}
]
},
".menu-topo": {
"display": "flex",
"align-items": "center",
"padding": [
16,
20,
16,
20
],
"border-bottom": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
".menu-topo h2": {
"color": "#f5d76e",
"font-size": 16,
"letter-spacing": 0.4,
"flex": 1
},
".menu-x": {
"background": "#22314f",
"width": 30,
"height": 30,
"border-radius": 8,
"color": "#cdd9ee",
"font-size": 13
},
".menu-x:hover": {
"background": "#7a2020",
"color": "#ffffff"
},
".menu-abas": {
"display": "flex",
"gap": 3,
"padding": [
10,
14,
0,
14
],
"border-bottom": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
".menu-aba": {
"padding": [
9,
14,
9,
14
],
"font-size": 12.5,
"font-weight": 600,
"color": "#8fa8cf",
"border-radius": "8px 8px 0 0",
"background": "transparent"
},
".menu-aba:hover": {
"background": "#26375a",
"color": "#ffffff"
},
".menu-aba.ativo": {
"background": "#1e2d49",
"color": "#f5d76e"
},
".menu-corpo": {
"flex": 1,
"overflow-y": "auto",
"padding": [
20,
20,
20,
20
]
},
".menu-sec": {
"display": "none"
},
".menu-sec.ativo": {
"display": "block"
},
".menu-sec input[type=text]": {
"width": {
"pct": 100.0
}
},
".menu-h3": {
"font-size": 11,
"text-transform": "uppercase",
"letter-spacing": 1.2,
"color": "#8fa8cf",
"margin": [
22,
0,
10,
0
],
"padding-bottom": 7,
"border-bottom": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
".ed-lista": {
"display": "flex",
"flex-direction": "column",
"gap": 6
},
".av-lista": {
"display": "flex",
"flex-direction": "column",
"gap": 7,
"flex-wrap": "wrap"
},
".ed-item": {
"display": "flex",
"align-items": "center",
"gap": 8,
"background": "#0c1830",
"border-radius": 8,
"padding": [
9,
12,
9,
12
],
"font-size": 13
},
".ed-item small": {
"color": "#f5d76e",
"font-weight": 700,
"margin-right": 5
},
".ed-btns": {
"margin-left": "auto",
"display": "flex",
"gap": 4
},
".ed-btns .fb": {
"width": 24,
"height": 24,
"border-radius": 6,
"background": "#22314f",
"color": "#b9c9e4",
"font-size": 12
},
".ed-btns .fb:hover": {
"background": "#26375a",
"color": "#ffffff"
},
".ed-btns .fb.x:hover": {
"background": "#7a2020"
},
".ini-marca": {
"display": "flex",
"justify-content": "center",
"margin": [
14,
0,
10,
0
]
},
".ini-tit": {
"text-align": "center",
"font-size": 20,
"color": "#ffffff",
"letter-spacing": 0.3
},
".ini-sub": {
"text-align": "center",
"color": "#8fa8cf",
"font-size": 12.5,
"margin-bottom": 22
},
".ini-cards": {
"display": "grid",
"grid-template-columns": "1fr 1fr",
"gap": 9
},
".ini-card": {
"display": "flex",
"flex-direction": "column",
"align-items": "flex-start",
"gap": 3,
"background": "#0c1830",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 11,
"padding": [
14,
16,
14,
16
],
"text-align": "left",
"transition": ".15s"
},
".ini-card:hover": {
"background": "#12203a",
"border-color": "#f5d76e"
},
".ini-card b": {
"font-size": 13.5,
"color": "#eaf0fb"
},
".ini-card small": {
"font-size": 11.5,
"color": "#7f96b8",
"line-height": 1.4
},
".ini-rodape": {
"text-align": "center",
"color": "#61789b",
"font-size": 11,
"margin-top": 22
},
".ini-autor": {
"text-align": "center",
"color": "#4d6183",
"font-size": 10.5,
"margin-top": 5,
"letter-spacing": 0.2
},
".ini-autor b": {
"color": "#7e93b4",
"font-weight": 600
},
".ig-rodape": {
"display": "flex",
"align-items": "center",
"gap": 12,
"margin-top": 14
},
".ig-salvo": {
"font-size": 11.5,
"color": "#61789b",
"transition": ".2s"
},
".ig-salvo.on": {
"color": "#2e8b57",
"font-weight": 600
},
".ig-salvo.piscar": {
"transform": "scale(1.04)"
},
".cel-caixa": {
"display": "flex",
"gap": 16,
"align-items": "center",
"background": "#0c1830",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 12,
"padding": [
16,
16,
16,
16
],
"margin-top": 6
},
".cel-qr img": {
"display": "block",
"width": 140,
"height": 140,
"border-radius": 8,
"background": "#ffffff",
"padding": [
6,
6,
6,
6
]
},
".cel-semqr": {
"color": "#61789b",
"font-size": 12
},
".cel-info": {
"flex": 1,
"min-width": 0
},
".cel-url": {
"font-family": "Consolas,monospace",
"font-size": 14,
"color": "#f5d76e",
"background": "#0a1526",
"border-radius": 8,
"padding": [
10,
12,
10,
12
],
"margin-bottom": 10,
"word-break": "break-all"
},
".cel-passos": {
"margin": [
0,
0,
0,
18
],
"color": "#cdd9ee",
"font-size": 13,
"line-height": 1.9
},
".cel-passos b": {
"color": "#ffffff"
},
".ig-dia": {
"margin-top": 16
},
".ig-dia h4": {
"font-size": 12,
"color": "#f5d76e",
"text-transform": "uppercase",
"letter-spacing": 1,
"margin-bottom": 7
},
".ig-linha": {
"display": "flex",
"align-items": "center",
"gap": 10,
"background": "#0c1830",
"border-radius": 8,
"padding": [
8,
12,
8,
12
],
"margin-bottom": 5,
"font-size": 13,
"cursor": "pointer"
},
".ig-linha:hover": {
"background": "#12203a"
},
".ig-linha span": {
"flex": 1
},
".ig-linha input[type=time]": {
"background": "#0b1729",
"color": "#ffffff",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 6,
"padding": [
4,
8,
4,
8
],
"font-size": 12.5,
"font-family": "inherit"
},
".ig-linha input[type=checkbox]": {
"width": 17,
"height": 17,
"accent-color": "#2e8b57",
"cursor": "pointer"
},
".mus-bloco": {
"background": "#0c1830",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 10,
"padding": [
13,
15,
13,
15
],
"margin-bottom": 10
},
".mus-bloco p": {
"font-size": 13,
"color": "#b9c9e4",
"line-height": 1.65,
"margin": [
0,
0,
9,
0
]
},
".mus-bloco p:last-child": {
"margin-bottom": 0
},
".mus-bloco b": {
"color": "#e6eefb"
},
".mus-bloco code": {
"font-family": "ui-monospace,Consolas,monospace",
"font-size": 12,
"color": "#f5d76e",
"background": "#0b1526",
"border-radius": 4,
"padding": [
1,
5,
1,
5
]
},
".mus-lista": {
"margin": [
0,
0,
9,
0
],
"padding-left": 18
},
".mus-lista li": {
"font-size": 13,
"color": "#b9c9e4",
"line-height": 1.6,
"margin-bottom": 6
},
".mus-lista li:last-child": {
"margin-bottom": 0
},
".ig-dia h4 small": {
"color": "#7d8ba6",
"font-size": 10.5,
"letter-spacing": 0.5,
"text-transform": "none",
"margin-left": 8,
"font-weight": 500
},
".ig-linha input[type=date]": {
"background": "#0b1729",
"color": "#ffffff",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 6,
"padding": [
4,
8,
4,
8
],
"font-size": 12.5,
"font-family": "inherit",
"color-scheme": "dark"
},
".ig-movel": {
"cursor": "default"
},
".ig-movel span": {
"flex": "0 0 74px"
},
".av-chip": {
"background": "#0c1830",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 20,
"padding": [
7,
14,
7,
14
],
"font-size": 12.5,
"color": "#cdd9ee",
"font-weight": 600,
"transition": ".15s"
},
".av-chip:hover": {
"background": "#12203a",
"border-color": "#f5d76e",
"color": "#ffffff"
},
".av-chip.auto": {
"border-color": "#aa2f6fc4",
"color": "#bfe6ff"
},
".reset-row": {
"display": "flex",
"align-items": "center",
"gap": 14,
"background": "#0c1830",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 10,
"padding": [
13,
16,
13,
16
],
"margin-bottom": 8
},
".reset-row div": {
"flex": 1
},
".reset-row b": {
"display": "block",
"font-size": 13.5,
"margin-bottom": 2
},
".reset-row small": {
"color": "#7f96b8",
"font-size": 11.5,
"line-height": 1.4
},
".reset-row.perigo": {
"border-color": "#7a2020"
},
".ajuda-overlay": {
"position": "fixed",
"inset": [
0,
0,
0,
0
],
"background": "#bb000000",
"display": "flex",
"align-items": "center",
"justify-content": "center",
"z-index": 200,
"padding": [
20,
20,
20,
20
]
},
".ajuda-box": {
"background": "#16233c",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 16,
"padding": [
26,
28,
26,
28
],
"max-width": 520,
"box-shadow": [
{
"x": 0,
"y": 20,
"blur": 60,
"spread": 0,
"cor": "#aa000000",
"inset": false
}
]
},
".ajuda-box h3": {
"color": "#f5d76e",
"font-size": 19,
"margin-bottom": 14
},
".ajuda-box p": {
"color": "#cdd9ee",
"margin-bottom": 11,
"line-height": 1.65,
"font-size": 13.5
},
".ajuda-box p:last-of-type": {
"margin-bottom": 20
},
".ajuda-box b": {
"color": "#ffffff"
},
".teclas": {
"display": "inline-flex",
"align-items": "center",
"gap": 5,
"white-space": "nowrap",
"vertical-align": -2
},
".teclas .mais": {
"color": "#8fa8cf",
"font-weight": 600
},
".ajuda-box kbd": {
"display": "inline-block",
"background": "#0b1729",
"border": {
"w": 1,
"cor": "#43587d",
"tracejado": false
},
"border-bottom-width": 2,
"border-radius": 5,
"padding": [
2,
8,
2,
8
],
"font-family": "inherit",
"font-size": 12.5,
"font-weight": 700,
"color": "#ffffff",
"line-height": 1.5
},
"#pj-cartao kbd": {
"display": "inline-block",
"background": "#0b1729",
"border": {
"w": 1,
"cor": "#43587d",
"tracejado": false
},
"border-bottom-width": 2,
"border-radius": 5,
"padding": [
2,
8,
2,
8
],
"font-family": "inherit",
"font-size": 12.5,
"font-weight": 700,
"color": "#ffffff",
"line-height": 1.5
},
".ajuda-box kbd.win": {
"display": "inline-flex",
"align-items": "center",
"gap": 5,
"padding": [
3,
9,
3,
9
]
},
"#pj-cartao kbd.win": {
"display": "inline-flex",
"align-items": "center",
"gap": 5,
"padding": [
3,
9,
3,
9
]
},
".ajuda-box kbd.win svg": {
"display": "block",
"color": "#cfe0ff"
},
"#pj-cartao kbd.win svg": {
"display": "block",
"color": "#cfe0ff"
},
".ajuda-box kbd.win span": {
"font-size": 11.5,
"letter-spacing": 0.2
},
"#pj-cartao kbd.win span": {
"font-size": 11.5,
"letter-spacing": 0.2
},
".ajuda-box ol": {
"margin": [
0,
0,
18,
20
],
"color": "#cdd9ee",
"line-height": 1.7
},
".ajuda-box ol b": {
"color": "#f5d76e"
},
".ajuda-btns": {
"display": "flex",
"gap": 10,
"flex-wrap": "wrap"
},
"#toast": {
"position": "fixed",
"bottom": 20,
"left": {
"pct": 50.0
},
"transform": "translateX(-50%)",
"background": "#dd000000",
"padding": [
10,
20,
10,
20
],
"border-radius": 20,
"font-size": 14,
"opacity": 0,
"transition": ".3s",
"pointer-events": "none",
"z-index": 99
},
"#toast.show": {
"opacity": 1
},
".item small.etq-col": {
"color": "#7f9ac0",
"font-size": 10,
"letter-spacing": 0.4,
"margin-right": 6
},
".cifra-ov": {
"position": "fixed",
"inset": [
0,
0,
0,
0
],
"background": "#e0060d1a",
"backdrop-filter": {
"blur": 3.0
},
"z-index": 320,
"display": "flex",
"align-items": "center",
"justify-content": "center",
"padding": [
20,
20,
20,
20
]
},
".cifra-ov.oculto": {
"display": "none"
},
".cifra-cx": {
"background": "#16233c",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 14,
"width": "min(880px,96vw)",
"height": "min(92vh,940px)",
"display": "flex",
"flex-direction": "column",
"overflow": "hidden",
"box-shadow": [
{
"x": 0,
"y": 24,
"blur": 70,
"spread": 0,
"cor": "#bb000000",
"inset": false
}
]
},
".cifra-cab": {
"display": "flex",
"align-items": "center",
"gap": 10,
"padding": [
10,
14,
10,
14
],
"background": "#101d33",
"border-bottom": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
".cifra-cab b": {
"font-size": 14,
"color": "#eaf0fb",
"overflow": "hidden",
"text-overflow": "ellipsis",
"white-space": "nowrap",
"flex": 1
},
".cifra-cab .ico": {
"color": "#d4761c",
"font-size": 17
},
".cifra-x": {
"background": "transparent",
"color": "#8fa8cf",
"font-size": 16,
"padding": [
4,
8,
4,
8
],
"border-radius": 7
},
".cifra-x:hover": {
"background": "#a31a1a",
"color": "#ffffff"
},
".cifra-zoom": {
"display": "flex",
"gap": 6,
"align-items": "center"
},
".cifra-zoom button": {
"background": "#16233c",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#cfe0f5",
"border-radius": 7,
"width": 30,
"height": 28,
"font-size": 13,
"font-weight": 600
},
".cifra-zoom button:hover": {
"background": "#26375a"
},
".folha": {
"flex": 1,
"overflow": "auto",
"padding": [
14,
16,
26,
16
],
"background": "#0b1526"
},
".folha pre": {
"font-family": "ui-monospace,Consolas,\"Courier New\",monospace",
"font-size": "var(--cf,14px)",
"line-height": 1.45,
"color": "#e7edf7",
"margin": [
0,
0,
0,
0
],
"white-space": "pre"
},
".folha .tr": {
"display": "inline-block",
"width": 0,
"margin-right": -1,
"border-left": {
"w": 1,
"cor": "rgba(245,215,110,.5)",
"tracejado": false
},
"height": {
"em": 1.05
},
"vertical-align": {
"em": -0.2
}
},
".folha .ac": {
"color": "#f5d76e",
"font-weight": 700
},
".folha .rot": {
"color": "#f5d76e",
"font-weight": 700,
"letter-spacing": {
"em": 0.08
},
"text-transform": "uppercase"
},
".folha .intro": {
"color": "#79c0ff",
"font-style": "italic"
},
".folha .rep": {
"color": "#f5d76e",
"font-style": "italic"
},
".folha .cab": {
"color": "#7f9ac0",
"font-size": 12,
"margin": [
0,
0,
10,
0
],
"line-height": 1.5
},
".folha .cab b": {
"color": "#f5d76e"
},
".gnum.alvo-busca": {
"outline": {
"w": 2,
"cor": "#f5d76e",
"tracejado": false
},
"outline-offset": -2
},
".niv-cx": {
"display": "inline-flex",
"gap": 0,
"margin": [
0,
0,
10,
0
],
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 8,
"overflow": "hidden"
},
".niv-cx button": {
"background": "#101d33",
"border": {
"w": 0,
"cor": "transparent"
},
"color": "#7f9ac0",
"padding": [
6,
12,
6,
12
],
"font-size": 12,
"cursor": "pointer"
},
".niv-cx button.on": {
"background": "#16233c",
"color": "#f5d76e",
"font-weight": 700
},
".tom-cx": {
"display": "flex",
"gap": 4,
"align-items": "center"
},
".tom-btn": {
"background": "#16233c",
"border": {
"w": 1,
"cor": "#f5d76e",
"tracejado": false
},
"color": "#f5d76e",
"border-radius": 8,
"padding": [
5,
13,
5,
13
],
"font-size": 13.5,
"font-weight": 700,
"min-width": 46
},
".tom-btn:hover": {
"background": "#1b2941"
},
".tom-painel": {
"background": "#101d33",
"border-bottom": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"padding": [
10,
14,
10,
14
],
"display": "flex",
"flex-direction": "column",
"gap": 7
},
".tom-linha": {
"display": "flex",
"gap": 7
},
".tom-linha button": {
"flex": 1,
"background": "#1b2941",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#cfe0f5",
"border-radius": 8,
"padding": [
8,
8,
8,
8
],
"font-size": 12.5,
"font-weight": 600
},
".tom-linha button:hover": {
"background": "#26375a"
},
".tom-grade": {
"display": "grid",
"grid-template-columns": "repeat(12,1fr)",
"gap": 6
},
".tom-op": {
"background": "#16233c",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#cfe0f5",
"border-radius": 8,
"padding": [
9,
2,
9,
2
],
"font-size": 12.5,
"font-weight": 600
},
".tom-op:hover": {
"background": "#26375a"
},
".tom-op.on": {
"background": "#f5d76e",
"color": "#101d33",
"border-color": "#f5d76e"
},
".tom-restaura": {
"background": "none",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#9db3d6",
"border-radius": 8,
"padding": [
8,
8,
8,
8
],
"font-size": 12
},
".tom-restaura:hover": {
"background": "#26375a",
"color": "#cfe0f5"
},
".pn-filtros": {
"display": "flex",
"gap": 6,
"margin": [
10,
0,
14,
0
],
"flex-wrap": "wrap"
},
".pn-f": {
"padding": [
6,
13,
6,
13
],
"border-radius": 8,
"background": "#16233c",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#9db3d6",
"font-size": 12,
"font-weight": 600
},
".pn-f:hover": {
"background": "#26375a"
},
".pn-f.ativo": {
"background": "#14487a",
"color": "#ffffff",
"border-color": "#14487a"
},
".pn-resumo": {
"display": "flex",
"gap": 10,
"flex-wrap": "wrap",
"margin-bottom": 6
},
".pn-cx": {
"flex": 1,
"min-width": 120,
"background": "#101d33",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 10,
"padding": [
11,
13,
11,
13
]
},
".pn-cx b": {
"display": "block",
"font-size": 22,
"color": "#f5d76e",
"font-variant-numeric": "tabular-nums",
"line-height": 1.1
},
".pn-cx span": {
"font-size": 11,
"color": "#7f9ac0",
"letter-spacing": 0.4
},
".pn-tit": {
"font-size": 11,
"text-transform": "uppercase",
"letter-spacing": 1.1,
"color": "#8fa8cf",
"margin": [
16,
0,
7,
0
]
},
".pn-lista": {
"display": "flex",
"flex-direction": "column",
"gap": 4
},
".pn-l": {
"display": "flex",
"align-items": "center",
"gap": 9,
"padding": [
7,
11,
7,
11
],
"border-radius": 8,
"background": "#16233c",
"font-size": 12.5,
"position": "relative",
"overflow": "hidden"
},
".pn-l .pos": {
"color": "#7f9ac0",
"font-size": 11,
"min-width": 20,
"font-variant-numeric": "tabular-nums"
},
".pn-l .nm": {
"flex": 1,
"overflow": "hidden",
"text-overflow": "ellipsis",
"white-space": "nowrap"
},
".pn-l .vl": {
"color": "#f5d76e",
"font-weight": 700,
"font-variant-numeric": "tabular-nums"
},
".pn-l .bar": {
"position": "absolute",
"left": 0,
"top": 0,
"bottom": 0,
"background": "#5514487a",
"border-radius": 8,
"z-index": 0
},
".pn-l>*": {
"position": "relative",
"z-index": 1
},
".pn-vazio": {
"padding": [
20,
20,
20,
20
],
"text-align": "center",
"color": "#6f86a8",
"font-style": "italic",
"font-size": 13
},
".sug": {
"border-top": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"background": "#101d33",
"padding": [
8,
12,
10,
12
],
"flex": "0 0 auto"
},
".sug.oculto": {
"display": "none"
},
".sug-cab": {
"display": "flex",
"align-items": "center",
"gap": 7,
"font-size": 10.5,
"text-transform": "uppercase",
"letter-spacing": 1,
"color": "#8fa8cf",
"margin-bottom": 7
},
".sug-cab b": {
"font-weight": 700,
"flex": 1
},
".sug-cab .ico": {
"color": "#f5d76e",
"font-size": 13
},
".sug-mais": {
"background": "#16233c",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#9db3d6",
"border-radius": 7,
"padding": [
3,
10,
3,
10
],
"font-size": 10.5,
"font-weight": 600,
"text-transform": "none",
"letter-spacing": 0
},
".sug-mais:hover": {
"background": "#26375a",
"color": "#ffffff"
},
".sug-lista": {
"display": "flex",
"flex-direction": "column",
"gap": 4,
"max-height": 132,
"overflow-y": "auto"
},
".sug-l": {
"display": "flex",
"align-items": "center",
"gap": 8,
"padding": [
6,
10,
6,
10
],
"border-radius": 7,
"background": "#16233c",
"font-size": 12.5,
"cursor": "pointer"
},
".sug-l:hover": {
"background": "#26375a"
},
".sug-l small": {
"color": "#7f9ac0",
"min-width": 58,
"font-variant-numeric": "tabular-nums"
},
".sug-l .nm": {
"flex": 1,
"overflow": "hidden",
"text-overflow": "ellipsis",
"white-space": "nowrap"
},
".sug-l .add": {
"background": "#1e2d49",
"color": "#f5d76e",
"border-radius": 6,
"padding": [
2,
9,
2,
9
],
"font-size": 13,
"font-weight": 700,
"line-height": 1.2
},
".sug-l .add:hover": {
"background": "#14487a",
"color": "#ffffff"
},
".cred-bloco": {
"background": "#131c2b",
"border": {
"w": 1,
"cor": "#1f2c40",
"tracejado": false
},
"border-radius": 10,
"padding": [
13,
15,
13,
15
],
"color": "#7e93b4",
"font-size": 12,
"line-height": 1.55
},
".cred-bloco p": {
"margin": [
0,
0,
9,
0
]
},
".cred-bloco p:last-child": {
"margin": [
0,
0,
0,
0
]
},
".cred-bloco b": {
"color": "#a9bcd8",
"font-weight": 600
},
".cred-mais-btn": {
"background": "none",
"border": {
"w": 0,
"cor": "transparent"
},
"color": "#4e6a9a",
"font-size": 11,
"cursor": "pointer",
"padding": [
3,
0,
0,
0
],
"display": "block",
"letter-spacing": 0.3
},
".cred-mais-btn:hover": {
"color": "#a9bcd8"
},
".busca-trecho .trecho-cab": {
"padding": [
8,
12,
8,
12
],
"font-size": 11.5,
"letter-spacing": 0.4,
"text-transform": "uppercase",
"color": "#f5d76e",
"background": "#08ffffff"
},
".item-trecho": {
"cursor": "pointer",
"padding": [
9,
12,
9,
12
]
},
".item-trecho b": {
"display": "block",
"color": "#f5d76e",
"font-size": 12.5,
"margin-bottom": 2
},
".item-trecho small": {
"display": "block",
"color": "#a9bcd8",
"font-size": 12,
"line-height": 1.35,
"-webkit-user-select": "text",
"user-select": "text"
},
".item-trecho:hover": {
"background": "#10ffffff"
},
".pulso": {
"animation": "pulso-btn .4s ease"
},
".timer-display.pausado": {
"opacity": 0.75,
"color": "#f5d76e"
},
".big-btn.ativo": {
"background": "#3a2f12",
"border-color": "#f5d76e",
"color": "#f5d76e"
},
".passo-num": {
"display": "flex",
"align-items": "center",
"gap": 4,
"background": "#0f1c31",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 10,
"padding": [
0,
4,
0,
4
],
"height": 36,
"box-sizing": "border-box"
},
".passo-num input[type=number]": {
"width": 42,
"text-align": "right",
"border": {
"w": 0,
"cor": "transparent"
},
"background": "transparent",
"font-size": 15,
"font-weight": 600,
"color": "#eaf0fb",
"padding": [
0,
0,
0,
0
],
"-moz-appearance": "textfield"
},
".passo-num input[type=number]::-webkit-outer-spin-button": {
"-webkit-appearance": "none",
"margin": [
0,
0,
0,
0
]
},
".passo-num input[type=number]::-webkit-inner-spin-button": {
"-webkit-appearance": "none",
"margin": [
0,
0,
0,
0
]
},
".pn-b": {
"width": 28,
"height": 28,
"border-radius": 7,
"background": "#16253c",
"color": "#cfe0f5",
"font-size": 17,
"font-weight": 700,
"line-height": 1,
"display": "flex",
"align-items": "center",
"justify-content": "center",
"flex": "0 0 28px",
"transition": "background .13s,transform .13s"
},
".pn-b:hover": {
"background": "#22385a"
},
".pn-b:active": {
"transform": "scale(.92)"
},
".pn-un": {
"font-size": 12.5,
"color": "#f5d76e",
"font-weight": 600,
"white-space": "nowrap",
"margin-right": 3
},
".view[data-aba=\"timer\"] .row input[type=text]": {
"height": 36,
"box-sizing": "border-box",
"padding-top": 0,
"padding-bottom": 0
},
"input": {
"-webkit-user-select": "text",
"user-select": "text"
},
".cifra-folha": {
"-webkit-user-select": "text",
"user-select": "text"
},
"#cifra-folha pre": {
"-webkit-user-select": "text",
"user-select": "text"
},
"[hidden]": {
"display": "none"
},
".reset-row.melhor": {
"background": {
"ang": 90.0,
"paradas": [
{
"p": 0.0,
"c": "#2a2312"
},
{
"p": 0.62,
"c": "#1a1710"
},
{
"p": 1.0,
"c": "transparent"
}
]
},
"border-color": "#6b5620",
"box-shadow": [
{
"x": 3,
"y": 0,
"blur": 0,
"spread": 0,
"cor": "#f5d76e",
"inset": true
}
]
},
".reset-row.melhor b": {
"color": "#f5d76e"
},
".reset-row.melhor .big-btn": {
"background": "#20304a",
"color": "#8fa8cf",
"opacity": 0.62,
"font-weight": 500
},
".reset-row.melhor .big-btn:hover": {
"opacity": 1,
"background": "#2a3d5c",
"color": "#cfe0f5"
},
".fundo-card .ap-info": {
"display": "block",
"margin-top": 3,
"font-size": 11,
"opacity": 0.65,
"letter-spacing": {
"em": 0.02
}
},
".fundo-card .nome .ap-nome": {
"display": "block"
},
".sis-grupo": {
"background": "#0c1830",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 10,
"margin": [
10,
0,
10,
0
],
"overflow": "hidden"
},
".sis-grupo>summary": {
"list-style": "none",
"cursor": "pointer",
"display": "flex",
"align-items": "baseline",
"gap": 12,
"padding": [
13,
16,
13,
16
],
"user-select": "none"
},
".sis-grupo>summary::-webkit-details-marker": {
"display": "none"
},
".sis-grupo>summary::after": {
"content": "'▸'",
"margin-left": "auto",
"color": "#7f96b8",
"transition": "transform .2s"
},
".sis-grupo[open]>summary::after": {
"transform": "rotate(90deg)"
},
".sis-grupo>summary:hover": {
"background": "#55122440"
},
".sis-grupo .sg-tit": {
"font-size": 15,
"font-weight": 700,
"color": "#e6eefb"
},
".sis-grupo>summary small": {
"color": "#7f96b8",
"font-size": 11.5
},
".sis-grupo[open]": {
"padding-bottom": 6
},
".sis-grupo .reset-row": {
"margin": [
0,
10,
8,
10
]
},
".sis-grupo .cred-bloco": {
"margin": [
0,
10,
8,
10
]
},
"#grupo-desinstalar>summary .sg-tit": {
"color": "#f0a0a0"
},
".sis-grupo.melhor": {
"border-color": "#6b5620",
"box-shadow": [
{
"x": 3,
"y": 0,
"blur": 0,
"spread": 0,
"cor": "#f5d76e",
"inset": true
}
]
},
".sis-grupo.melhor>summary": {
"background": {
"ang": 90.0,
"paradas": [
{
"p": 0.0,
"c": "#2a2312"
},
{
"p": 0.62,
"c": "#1a1710"
},
{
"p": 1.0,
"c": "transparent"
}
]
}
},
".sis-grupo.melhor>summary .sg-tit": {
"color": "#f5d76e"
},
".sis-grupo.melhor>summary small": {
"color": "#e8b93c"
},
".reset-row.destaque": {
"border-color": "#2e8b57"
},
".sis-assina": {
"text-align": "center",
"color": "#7e93b4",
"font-size": 12,
"margin": [
18,
0,
4,
0
],
"letter-spacing": {
"em": 0.02
}
},
".sis-assina b": {
"color": "#a9bcd8",
"font-weight": 600
},
".reset-row small b": {
"display": "inline",
"font-size": "inherit",
"margin": [
0,
0,
0,
0
]
},
".view[data-aba=\"slides\"].apr-on>.card": {
"display": "none"
},
".apr": {
"position": "absolute",
"inset": [
0,
0,
0,
0
],
"z-index": 2,
"overflow": "hidden",
"color": "#eaf0fb",
"background": "radial-gradient(ellipse at 50% 50%,#18305a 0%,#0b1526 70%)"
},
".apr.oculto": {
"display": "none"
},
".apr-palco": {
"position": "absolute",
"top": 0,
"bottom": 0,
"right": 0,
"left": 236,
"display": "flex",
"align-items": "center",
"justify-content": "center",
"gap": 18,
"padding": [
0,
12,
0,
12
],
"transition": "left .25s ease-out",
"container-type": "size"
},
".apr.escondida .apr-palco": {
"left": 46
},
".apr-grande": {
"flex": "none",
"position": "relative",
"width": "min(64.64cqw,calc((100cqh - 90px) * 16 / 9))",
"transition": "width .25s ease-out"
},
".apr.escondida .apr-grande": {
"width": "min(67.51cqw,calc((100cqh - 90px) * 16 / 9))"
},
".apr-lado": {
"flex": "none",
"position": "relative",
"cursor": "pointer",
"width": "14.78cqw",
"transition": "width .25s ease-out"
},
".apr.escondida .apr-lado": {
"width": "14.35cqw"
},
".apr-q": {
"position": "relative"
},
".apr-q img": {
"display": "block",
"width": {
"pct": 100.0
},
"aspect-ratio": "16/9",
"object-fit": "contain",
"background": "#000000",
"border-radius": "inherit"
},
".apr-grande .apr-q": {
"border-radius": 10,
"outline": {
"w": 3,
"cor": "#f5d76e",
"tracejado": false
},
"outline-offset": 3,
"box-shadow": [
{
"x": 0,
"y": 18,
"blur": 60,
"spread": 0,
"cor": "#cc000000",
"inset": false
}
]
},
".apr-lado .apr-q": {
"border-radius": 6,
"box-shadow": [
{
"x": 0,
"y": 6,
"blur": 18,
"spread": 0,
"cor": "#99000000",
"inset": false
}
]
},
".apr-tag": {
"position": "absolute",
"top": -22,
"left": -30,
"right": -30,
"font-size": 11,
"letter-spacing": 0.8,
"text-transform": "uppercase",
"color": "#9fb0cc",
"text-align": "center",
"white-space": "nowrap"
},
".apr-grande .apr-tag": {
"color": "#f5d76e",
"font-weight": 600
},
".apr-lado.ant img": {
"opacity": 0.38,
"filter": "saturate(.6)"
},
".apr-lado.px .apr-tag": {
"color": "#e6eefb"
},
".apr-hint": {
"position": "absolute",
"inset": [
0,
0,
0,
0
],
"border-radius": 6,
"display": "none",
"align-items": "center",
"justify-content": "center",
"flex-direction": "column",
"gap": 2,
"background": "#b00b1526",
"border": {
"w": 2,
"cor": "#f5d76e",
"tracejado": false
},
"font-size": 12,
"font-weight": 600,
"color": "#f5d76e",
"text-align": "center",
"line-height": 1.2
},
".apr-hint big .ico": {
"font-size": 24
},
".apr-lado:hover .apr-hint": {
"display": "flex"
},
".apr-lado.vazio": {
"visibility": "hidden"
},
".apr-lado.fim": {
"cursor": "default"
},
".apr-lado.fim .apr-hint": {
"display": "none"
},
".apr-fim-q": {
"display": "flex",
"align-items": "center",
"justify-content": "center",
"aspect-ratio": "16/9",
"padding": [
6,
6,
6,
6
],
"border-radius": 6,
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": true
},
"background": "#0b1526",
"color": "#8396b6",
"font-size": 11,
"text-align": "center"
},
".apr-fim-q[hidden]": {
"display": "none"
},
".apr-preto": {
"position": "absolute",
"inset": [
0,
0,
0,
0
],
"display": "none",
"align-items": "center",
"justify-content": "center",
"border-radius": "inherit",
"background": "rgba(0,0,0,.86)",
"color": "#f5d76e",
"font-weight": 700,
"font-size": 17,
"letter-spacing": 0.3
},
".apr.preto .apr-preto": {
"display": "flex"
},
".apr-col": {
"position": "absolute",
"left": 0,
"top": 0,
"bottom": 0,
"width": 236,
"z-index": 10,
"display": "flex",
"flex-direction": "column",
"background": "#16233c",
"border-right": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"transition": "transform .25s ease-out"
},
".apr.escondida .apr-col": {
"transform": "translateX(-102%)"
},
".apr-ctopo": {
"display": "flex",
"flex-direction": "column",
"gap": 9,
"padding": [
10,
10,
9,
10
],
"border-bottom": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
".apr-lk": {
"align-self": "flex-start",
"display": "flex",
"align-items": "center",
"gap": 4,
"margin-left": -3,
"padding": [
2,
7,
2,
2
],
"border-radius": 6,
"background": "none",
"font-size": 12.5,
"font-weight": 600,
"color": "#9fb0cc"
},
".apr-lk .ico": {
"font-size": 15
},
".apr-lk:hover": {
"color": "#ffffff",
"background": "#10ffffff"
},
".apr-l1": {
"display": "flex",
"align-items": "center",
"gap": 6
},
".apr-nm": {
"flex": 1,
"min-width": 0,
"font-size": 13,
"line-height": 1.25,
"font-weight": 600,
"color": "#eaf0fb",
"overflow-wrap": "anywhere"
},
".apr-ib": {
"flex": "none",
"width": 30,
"height": 30,
"border-radius": 8,
"display": "flex",
"align-items": "center",
"justify-content": "center",
"background": "none",
"color": "#8fa2c2"
},
".apr-ib .ico": {
"font-size": 17
},
".apr-ib:hover": {
"background": "#10ffffff",
"color": "#dfe8f7"
},
".apr-ib.on": {
"color": "#f5d76e"
},
".apr-ib.on:hover": {
"color": "#f5d76e"
},
".apr-achar": {
"display": "flex",
"align-items": "center",
"gap": 6,
"padding": [
6,
8,
6,
8
],
"border-radius": 8,
"background": "#0a1526",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"font-size": 12.5,
"color": "#7f90ad",
"cursor": "text"
},
".apr-achar:focus-within": {
"border-color": "#f5d76e"
},
".apr-achar .ico": {
"font-size": 14,
"color": "#7f90ad"
},
".apr-achar input": {
"flex": 1,
"min-width": 0,
"width": "auto",
"padding": [
0,
0,
0,
0
],
"margin": [
0,
0,
0,
0
],
"border": {
"w": 0,
"cor": "transparent"
},
"border-radius": 0,
"background": "none",
"font": "inherit",
"font-size": 12.5,
"color": "#ffffff",
"outline": {
"w": 0,
"cor": "transparent"
},
"box-shadow": []
},
".apr-achar input:focus": {
"flex": 1,
"min-width": 0,
"width": "auto",
"padding": [
0,
0,
0,
0
],
"margin": [
0,
0,
0,
0
],
"border": {
"w": 0,
"cor": "transparent"
},
"border-radius": 0,
"background": "none",
"font": "inherit",
"font-size": 12.5,
"color": "#ffffff",
"outline": {
"w": 0,
"cor": "transparent"
},
"box-shadow": []
},
".apr-achar input::placeholder": {
"color": "#7f90ad"
},
".apr-lista": {
"position": "relative",
"flex": 1,
"min-height": 0,
"overflow-y": "auto",
"overflow-x": "hidden",
"padding": [
10,
6,
10,
6
],
"display": "flex",
"flex-direction": "column",
"gap": 9,
"scrollbar-width": "thin",
"scrollbar-color": "#ffffff30 transparent"
},
".apr-lista::-webkit-scrollbar": {
"width": 6
},
".apr-lista::-webkit-scrollbar-thumb": {
"background": "#30ffffff",
"border-radius": 3
},
".apr-th": {
"flex": "none",
"display": "flex",
"gap": 6,
"align-items": "flex-start",
"transition": "opacity .15s"
},
".apr-th b": {
"width": 20,
"flex": "none",
"text-align": "right",
"font-size": 11,
"color": "#9fb0cc",
"padding-top": 2
},
".apr-th .im": {
"position": "relative",
"width": 172,
"margin-left": 8,
"border-radius": 5,
"border": {
"w": 2,
"cor": "transparent",
"tracejado": false
},
"cursor": "pointer",
"transition": "width .15s,margin .15s"
},
".apr-th .im img": {
"display": "block",
"width": {
"pct": 100.0
},
"aspect-ratio": "16/9",
"object-fit": "contain",
"border-radius": 3,
"background": "#000000"
},
".apr-th.passou .im": {
"opacity": 0.5
},
".apr-th.on .im": {
"border-color": "#f5d76e"
},
".apr-th.on b": {
"color": "#f5d76e",
"font-weight": 700
},
".apr-th:hover .im": {
"width": 194,
"margin-left": 0,
"border-color": "#ffffff",
"box-shadow": [
{
"x": 0,
"y": 8,
"blur": 24,
"spread": 0,
"cor": "#aa000000",
"inset": false
}
],
"opacity": 1
},
".apr-th:hover .im::after": {
"content": "'clique: projetar'",
"position": "absolute",
"right": 5,
"bottom": 5,
"font-size": 10.5,
"color": "#ffffff",
"background": "#cc000000",
"padding": [
1,
6,
1,
6
],
"border-radius": 4
},
".apr-th.achou .im": {
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 3,
"cor": "#f5d76e",
"inset": false
}
]
},
".apr-th.fora": {
"opacity": 0.28
},
".apr-sem": {
"font-size": 12,
"line-height": 1.35,
"color": "#9fb0cc",
"padding": [
2,
6,
4,
6
]
},
".apr-sem[hidden]": {
"display": "none"
},
".apr-trilho": {
"position": "absolute",
"left": 0,
"top": 0,
"bottom": 0,
"width": 46,
"z-index": 9,
"display": "none",
"flex-direction": "column",
"align-items": "center",
"gap": 12,
"padding-top": 14,
"background": "#16233c",
"border-right": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"cursor": "pointer"
},
".apr.escondida .apr-trilho": {
"display": "flex"
},
".apr-ic3": {
"width": 32,
"height": 32,
"border-radius": 8,
"display": "flex",
"align-items": "center",
"justify-content": "center",
"background": "#1e2d49",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#dfe8f7"
},
".apr-ic3 .ico": {
"font-size": 17
},
".apr-trilho b": {
"writing-mode": "vertical-rl",
"transform": "rotate(180deg)",
"font-size": 13,
"font-weight": 600,
"letter-spacing": 0.4,
"color": "#dfe8f7"
},
".apr-trilho:hover .apr-ic3": {
"background": "#26375a",
"border-color": "#f5d76e",
"color": "#f5d76e"
},
".apr-num": {
"position": "absolute",
"left": {
"pct": 50.0
},
"top": {
"pct": 50.0
},
"transform": "translate(-50%,-50%)",
"z-index": 20,
"text-align": "center",
"padding": [
14,
26,
14,
26
],
"border-radius": 14,
"background": "#ee0b1526",
"border": {
"w": 1,
"cor": "#f5d76e",
"tracejado": false
},
"box-shadow": [
{
"x": 0,
"y": 10,
"blur": 40,
"spread": 0,
"cor": "#000000",
"inset": false
}
]
},
".apr-num[hidden]": {
"display": "none"
},
".apr-num big": {
"display": "block",
"font-size": 44,
"font-weight": 700,
"line-height": 1,
"color": "#f5d76e",
"font-variant-numeric": "tabular-nums"
},
".apr-num small": {
"font-size": 12.5,
"color": "#c8d3e6"
},
".fila-item .rot .ico": {
"font-size": 13,
"margin-right": 4,
"vertical-align": -2
},
".fila-agora": {
"margin-left": "auto",
"flex": "none",
"font-size": 11,
"color": "#9fe3b9",
"white-space": "nowrap"
},
".fila-agora i": {
"display": "inline-block",
"width": 7,
"height": 7,
"border-radius": {
"pct": 50.0
},
"background": "#3ecf7a",
"margin-right": 4,
"vertical-align": 1
},
".fila-agora+.fila-btns": {
"margin-left": 6
},
".sis-botoes": {
"display": "grid",
"grid-template-columns": "1fr 1fr",
"gap": 10,
"margin": [
12,
0,
12,
0
]
},
".sis-bt": {
"display": "flex",
"flex-direction": "column",
"align-items": "flex-start",
"gap": 4,
"text-align": "left",
"cursor": "pointer",
"background": "#0c1830",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 12,
"padding": [
16,
18,
16,
18
],
"color": "#e6eefb",
"font": "inherit",
"transition": "border-color .15s,background .15s"
},
".sis-op": {
"display": "flex",
"flex-direction": "column",
"align-items": "flex-start",
"gap": 4,
"text-align": "left",
"cursor": "pointer",
"background": "#0c1830",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"border-radius": 12,
"padding": [
16,
18,
16,
18
],
"color": "#e6eefb",
"font": "inherit",
"transition": "border-color .15s,background .15s"
},
".sis-bt:hover": {
"border-color": "#14487a",
"background": "#55122440"
},
".sis-op:hover": {
"border-color": "#14487a",
"background": "#55122440"
},
".sis-bt b": {
"font-size": 16,
"font-weight": 700
},
".sis-op b": {
"font-size": 14.5,
"font-weight": 700
},
".sis-bt small": {
"color": "#7f96b8",
"font-size": 11.5,
"line-height": 1.4
},
".sis-op small": {
"color": "#7f96b8",
"font-size": 11.5,
"line-height": 1.4
},
".sis-bt.perigo b": {
"color": "#f0a0a0"
},
".sis-op.perigo b": {
"color": "#f0a0a0"
},
".sis-op.perigo:hover": {
"border-color": "#7a2020"
},
".sis-bt.melhor": {
"border-color": "#6b5620",
"box-shadow": [
{
"x": 3,
"y": 0,
"blur": 0,
"spread": 0,
"cor": "#f5d76e",
"inset": true
}
],
"background": {
"ang": 90.0,
"paradas": [
{
"p": 0.0,
"c": "#2a2312"
},
{
"p": 0.62,
"c": "#1a1710"
},
{
"p": 1.0,
"c": "#0c1830"
}
]
}
},
".sis-bt.melhor b": {
"color": "#f5d76e"
},
".sis-bt.melhor small": {
"color": "#e8b93c"
},
".sis-pref": {
"display": "flex",
"align-items": "center",
"justify-content": "space-between",
"gap": 12,
"padding": [
10,
4,
10,
4
],
"margin-top": 6,
"border-top": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#9fb3d3",
"font-size": 12.5
},
".chave": {
"position": "relative",
"min-width": 74,
"padding": [
5,
12,
5,
30
],
"border-radius": 20,
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"background": "#0c1830",
"color": "#7f96b8",
"font": "inherit",
"font-size": 11.5,
"cursor": "pointer",
"text-align": "left"
},
".chave::before": {
"content": "''",
"position": "absolute",
"left": 6,
"top": {
"pct": 50.0
},
"width": 16,
"height": 16,
"margin-top": -8,
"border-radius": {
"pct": 50.0
},
"background": "#3a4a66",
"transition": "background .15s"
},
".chave.on": {
"color": "#cfe9d6",
"border-color": "#2c6b45",
"padding": [
5,
30,
5,
12
],
"text-align": "right"
},
".aviso-limitada": {
"background": "#3a2c08",
"border": {
"w": 1,
"cor": "#8a6a1c",
"tracejado": false
},
"color": "#f3d98a",
"border-radius": 8,
"padding": [
9,
11,
9,
11
],
"margin-bottom": 12,
"line-height": 1.4
},
".chave.on::before": {
"background": "#2e8b57",
"left": "auto",
"right": 6
},
".assist-box": {
"width": "min(560px,94vw)",
"max-width": 560
},
".assist-escolhas": {
"display": "flex",
"flex-direction": "column",
"gap": 8,
"margin": [
4,
0,
16,
0
]
},
".assist-escolhas:empty": {
"display": "none"
},
".assist-box .sis-painel": {
"margin": [
0,
0,
14,
0
]
},
".assist-box .sis-painel .reset-row": {
"margin": [
0,
0,
8,
0
]
},
".assist-box .ajuda-btns": {
"display": "flex",
"gap": 8,
"justify-content": "flex-end",
"flex-wrap": "wrap"
},
"#ap-grade .fundo-card.especial": {
"border-color": "#2e8b57",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 1,
"cor": "#662e8b57",
"inset": false
},
{
"x": 0,
"y": 6,
"blur": 18,
"spread": 0,
"cor": "#262e8b57",
"inset": false
}
]
},
"#ap-grade .fundo-card.especial:hover": {
"border-color": "#3fae6f"
},
".ap-mini": {
"position": "relative"
},
".selo-ultra": {
"position": "absolute",
"bottom": 6,
"right": 6,
"z-index": 2,
"width": 28,
"height": 28,
"border-radius": {
"pct": 50.0
},
"display": "flex",
"align-items": "center",
"justify-content": "center",
"background": "#e607090e",
"color": "#3fae6f",
"border": {
"w": 1,
"cor": "#26ffffff",
"tracejado": false
},
"box-shadow": [
{
"x": 0,
"y": 2,
"blur": 8,
"spread": 0,
"cor": "#aa000000",
"inset": false
},
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 1,
"cor": "#332e8b57",
"inset": true
}
],
"pointer-events": "none"
},
".selo-ultra svg": {
"display": "block",
"filter": "drop-shadow(0 0 3px #2e8b5780)"
},
"#ap-grade .fundo-card.especial .ap-info": {
"color": "#9fd3b4",
"opacity": 0.95
},
"#dt-veu": {
"position": "fixed",
"inset": [
0,
0,
0,
0
],
"z-index": 119,
"background": "#a6050a14",
"-webkit-backdrop-filter": "blur(3px)",
"backdrop-filter": {
"blur": 3.0
},
"animation": "dt-veu .2s ease-out"
},
"#dt-cartao": {
"position": "fixed",
"left": {
"pct": 50.0
},
"top": {
"pct": 50.0
},
"transform": "translate(-50%,-50%)",
"z-index": 120,
"width": 380,
"display": "flex",
"gap": 12,
"align-items": "flex-start",
"padding": [
14,
14,
12,
14
],
"border-radius": 14,
"border": {
"w": 2,
"cor": "#2e8b57",
"tracejado": false
},
"background": "radial-gradient(120% 60% at 50% 0%,#ffffff12 0%,#ffffff00 60%),linear-gradient(180deg,#1e2d49,#16233c)",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 1,
"cor": "#332e8b57",
"inset": false
},
{
"x": 0,
"y": 0,
"blur": 18,
"spread": 0,
"cor": "#402e8b57",
"inset": false
},
{
"x": 0,
"y": 18,
"blur": 50,
"spread": 0,
"cor": "#cc000000",
"inset": false
},
{
"x": 0,
"y": 1,
"blur": 0,
"spread": 0,
"cor": "#1affffff",
"inset": true
}
],
"animation": "dt-entra .25s ease-out"
},
"#dt-cartao .dt-ico": {
"flex": "none",
"width": 44,
"height": 44,
"border-radius": {
"pct": 50.0
},
"display": "flex",
"align-items": "center",
"justify-content": "center",
"background": "#e607090e",
"color": "#3fae6f",
"border": {
"w": 1,
"cor": "#26ffffff",
"tracejado": false
},
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 1,
"cor": "#332e8b57",
"inset": true
},
{
"x": 0,
"y": 2,
"blur": 8,
"spread": 0,
"cor": "#aa000000",
"inset": false
}
]
},
"#dt-cartao .dt-ico svg": {
"filter": "drop-shadow(0 0 3px #2e8b5780)"
},
"#dt-cartao .dt-corpo": {
"flex": 1,
"min-width": 0
},
"#dt-cartao .dt-tit": {
"font-size": 15,
"font-weight": 700,
"color": "#f5d76e",
"line-height": 1.35
},
"#dt-cartao .dt-txt": {
"font-size": 16,
"font-weight": 700,
"color": "#f5d76e",
"margin": [
4,
0,
10,
0
],
"line-height": 1.45
},
"#dt-cartao .dt-par": {
"font-size": 13,
"color": "#cdd9ee",
"margin": [
7,
0,
7,
0
],
"display": "flex",
"align-items": "center",
"gap": 8
},
"#dt-cartao .dt-n": {
"flex": "none",
"width": 22,
"height": 22,
"border-radius": {
"pct": 50.0
},
"display": "inline-flex",
"align-items": "center",
"justify-content": "center",
"font-weight": 800,
"font-size": 12,
"background": "#f5d76e",
"color": "#20242c"
},
"#dt-cartao .dt-n.dois": {
"background": "#2e8b57",
"color": "#ffffff"
},
"#dt-cartao .dt-acoes": {
"display": "flex",
"gap": 8,
"justify-content": "flex-end",
"flex-wrap": "wrap",
"margin-top": 10
},
"#dt-cartao .dt-acoes .big-btn": {
"padding": [
7,
13,
7,
13
]
},
"#dt-cartao.como": {
"width": 470,
"flex-direction": "column",
"align-items": "center",
"text-align": "center"
},
"#dt-cartao.como .dt-corpo": {
"width": {
"pct": 100.0
}
},
"#dt-cartao.como .dt-par": {
"justify-content": "center"
},
"#dt-cartao.como .dt-acoes": {
"justify-content": "center"
},
"#dt-cartao .dt-ops": {
"display": "flex",
"gap": 8,
"margin-top": 10
},
"#dt-cartao .dt-op": {
"flex": "1 1 0",
"min-width": 0,
"padding": [
8,
5,
6,
5
],
"border-radius": 10,
"background": "#16233c",
"border": {
"w": 1.5,
"cor": "#2c3d5c",
"tracejado": false
},
"display": "flex",
"justify-content": "center",
"transition": "border-color .15s,background .15s"
},
"#dt-cartao .dt-op:hover": {
"background": "#26375a",
"border-color": "#3b5680"
},
"#dt-cartao .dt-op.on": {
"border-color": "#f5d76e",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 1,
"cor": "#55f5d76e",
"inset": false
}
]
},
"#dt-cartao .dt-op svg": {
"display": "block",
"width": {
"pct": 100.0
},
"height": "auto"
},
"#dt-cartao .dt-redondo": {
"width": 42,
"height": 42,
"border-radius": {
"pct": 50.0
},
"display": "inline-flex",
"align-items": "center",
"justify-content": "center",
"background": "#1e2d49",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#eaf0fb"
},
"#dt-cartao .dt-redondo:hover": {
"background": "#26375a"
},
"#dt-cartao .dt-redondo.verde": {
"background": "#2e8b57",
"border-color": "transparent",
"color": "#ffffff"
},
"#dt-cartao .dt-redondo.verde:hover": {
"background": "#37a066"
},
"#dt-pilula": {
"display": "flex",
"align-items": "center",
"gap": 7,
"padding": [
7,
12,
7,
12
],
"border-radius": 999,
"font-size": 12.5,
"font-weight": 600,
"white-space": "nowrap"
},
"#dt-pilula.on": {
"background": "#16233c",
"border": {
"w": 1,
"cor": "#2e8b57",
"tracejado": false
},
"color": "#eaf0fb"
},
"#dt-pilula.on:hover": {
"background": "#26375a"
},
"#dt-pilula .dt-bola": {
"width": 8,
"height": 8,
"border-radius": {
"pct": 50.0
},
"background": "#2e8b57",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 3,
"cor": "#402e8b57",
"inset": false
}
]
},
"#dt-pilula.conectar": {
"background": "#16233c",
"border": {
"w": 1,
"cor": "#99f5d76e",
"tracejado": false
},
"color": "#f3e3a6",
"animation": "dt-pulsa 1.4s ease-out 1"
},
"#dt-pilula.conectar:hover": {
"background": "#26375a",
"border-color": "#f5d76e"
},
"#dt-pilula.reconectando": {
"background": "#16233c",
"border": {
"w": 1,
"cor": "#99d9a441",
"tracejado": false
},
"color": "#f3d98a"
},
"#dt-pilula.reconectando .dt-bola": {
"background": "#d9a441",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 3,
"cor": "#33d9a441",
"inset": false
}
]
},
".tabs .tab:focus": {
"outline": {
"w": 0,
"cor": "transparent"
}
},
".tabs .tab:focus-visible": {
"outline": {
"w": 0,
"cor": "transparent"
}
},
"body.pb-on #painel #estado-barra": {
"display": "none"
},
"body.pb-on #painel #agora": {
"display": "none"
},
"body.pb-on #painel .barra-extras": {
"display": "none"
},
".pb-n": {
"display": "none"
},
"body.pb-on .preview-box .pb-n": {
"display": "flex",
"position": "absolute",
"top": 7,
"left": 7,
"z-index": 4,
"width": 24,
"height": 24,
"border-radius": 7,
"align-items": "center",
"justify-content": "center",
"font-weight": 800,
"font-size": 14,
"color": "#f5d76e",
"background": {
"ang": 160.0,
"paradas": [
{
"p": 0.0,
"c": "#14487a"
},
{
"p": 1.0,
"c": "#0f2f5e"
}
]
},
"border": {
"w": 1.5,
"cor": "#f5d76e",
"tracejado": false
},
"box-shadow": [
{
"x": 0,
"y": 2,
"blur": 8,
"spread": 0,
"cor": "#aa000000",
"inset": false
}
]
},
"#pb-retorno": {
"display": "none"
},
"body.pb-on.pb-dupla #pb-retorno": {
"display": "block",
"margin-top": 8
},
"#pb-retorno .mini": {
"outline": {
"w": 2,
"cor": "#2e8b57",
"tracejado": false
},
"outline-offset": -2,
"background": "#0b1526"
},
"#pb-retorno iframe": {
"border": {
"w": 0,
"cor": "transparent"
},
"width": 1366,
"height": 768,
"transform-origin": "0 0",
"pointer-events": "none",
"position": "absolute",
"left": 0,
"top": 0
},
"#pb-retorno .prev-selo": {
"color": "#cfeedd"
},
"#pb-retorno .prev-selo b": {
"color": "#ffffff"
},
"body.pb-on #apr .apr-palco": {
"bottom": 64,
"flex-wrap": "wrap",
"align-content": "center",
"padding-top": 0,
"row-gap": 26,
"--d": "calc(100cqw - 64px)",
"gap": "calc(var(--d) * .025)",
"display": "grid",
"grid-template-columns": "60% 35%",
"grid-template-areas": "\"g p\" \"g a\" \"c a\"",
"grid-template-rows": "auto auto auto",
"column-gap": {
"pct": 4.0
},
"justify-content": "center",
"padding": [
0,
12,
0,
12
]
},
"body.pb-on #apr .apr-grande": {
"width": "auto",
"grid-area": "g",
"align-self": "start"
},
"body.pb-on #apr .apr-lado.px": {
"width": "auto",
"grid-area": "p",
"align-self": "start"
},
"body.pb-on #apr .apr-lado.ant": {
"width": {
"pct": 60.0
},
"grid-area": "a",
"justify-self": "center",
"align-self": "start",
"margin-top": 8
},
"body.pb-on #apr .apr-lado.px .apr-q": {
"outline": {
"w": 2,
"cor": "#66e6eefb",
"tracejado": false
},
"outline-offset": 3,
"border-radius": 8
},
"body.pb-on #apr .apr-lado.px .apr-tag": {
"color": "#ffffff",
"font-weight": 600
},
"body.pb-on #apr .apr-lado.ant .apr-tag": {
"color": "#d5deec",
"font-size": 12.5,
"font-weight": 600
},
"body.pb-on #apr .apr-lado.ant img": {
"opacity": 0.55
},
"body.pb-on #apr .apr-tag": {
"font-size": 12.5
},
"#pb-louvores": {
"display": "none"
},
"body.pb-on #pb-louvores": {
"display": "flex",
"flex": "0 0 100%",
"justify-content": "flex-start",
"gap": 10,
"flex-wrap": "wrap",
"grid-area": "c"
},
"body.pb-on #pb-louvores:empty": {
"display": "none"
},
"#pb-louvores .lv": {
"display": "flex",
"align-items": "center",
"gap": 8,
"padding": [
9,
14,
9,
14
],
"border-radius": 10,
"font-size": 12.5,
"font-weight": 600,
"background": "#1e2d49",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
},
"color": "#9fb0cc",
"letter-spacing": 0.3,
"cursor": "pointer"
},
"#pb-louvores .lv.agora": {
"background": "#2a2410",
"border-color": "#f5d76e",
"color": "#f5d76e"
},
"#pb-louvores .lv.prox": {
"color": "#ffffff",
"border-color": "#66e6eefb"
},
"#pb-louvores .lv small": {
"font-weight": 500,
"font-size": 10.5,
"opacity": 0.8,
"text-transform": "uppercase",
"letter-spacing": 0.8
},
".pb-selo": {
"position": "absolute",
"right": 8,
"bottom": 8,
"z-index": 3,
"display": "flex",
"align-items": "center",
"gap": 4,
"padding": [
2,
6,
2,
6
],
"border-radius": 3,
"font-size": 10.5,
"font-weight": 600,
"background": "#b307090e",
"color": "#9ff0bd",
"cursor": "default",
"user-select": "none"
},
".pb-selo svg": {
"display": "block"
},
"#pb-faixa": {
"display": "none"
},
"body.pb-on #pb-faixa": {
"display": "flex",
"position": "absolute",
"left": 236,
"right": 0,
"bottom": 0,
"height": 64,
"z-index": 5,
"align-items": "center",
"gap": 12,
"padding": [
0,
18,
0,
18
],
"background": "#16233c",
"border-top": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
"body.pb-on .apr.escondida #pb-faixa": {
"left": 46
},
"#pb-faixa .nav2": {
"flex": "0 1 320px",
"min-width": 0,
"margin": [
0,
0,
0,
0
]
},
"#pb-faixa .projetar": {
"min-width": 0,
"overflow": "hidden",
"white-space": "nowrap",
"text-overflow": "ellipsis"
},
"#pb-faixa .barra-ferr": {
"flex": "none",
"margin": [
0,
0,
0,
0
]
},
"#pb-faixa .pb-agora": {
"flex": "0 1 auto",
"min-width": 0,
"overflow": "hidden",
"text-overflow": "ellipsis",
"font-size": 12,
"color": "#b9c6dc",
"white-space": "nowrap"
},
"#pb-faixa.apertada": {
"gap": 8,
"padding": [
0,
10,
0,
10
]
},
"#pb-faixa.apertada .nav2": {
"flex-basis": 250
},
"#pb-faixa.apertada #btn-congelar": {
"font-size": 0,
"gap": 0
},
"#pb-faixa.apertada #btn-congelar .ico": {
"font-size": 14
},
"#pb-faixa.muito .pb-agora": {
"display": "none"
},
"#pb-faixa.muito .nav2": {
"flex-basis": 240
},
"#pb-faixa.muito .nav2 .nav": {
"flex-basis": 40
},
"#pb-faixa .pb-agora b": {
"color": "#f5d76e",
"font-weight": 600
},
"#pb-louvores .lv:hover": {
"border-color": "#3b5680",
"color": "#ffffff"
},
"#pb-louvores .lv.foi": {
"opacity": 0.55
},
"body.pb-on.pb-a2 #painel #pb-louvores": {
"display": "flex",
"flex-direction": "column",
"flex-wrap": "nowrap",
"gap": 4,
"margin-top": 6,
"justify-content": "flex-start"
},
"body.pb-on.pb-a2 #painel #pb-louvores .lv": {
"padding": [
7,
10,
7,
10
],
"border-radius": 6,
"font-size": 12
},
"body.pb-on.pb-a2 #painel #pb-louvores .lv small": {
"margin-left": "auto",
"order": 2
},
"body.pb-on.pb-a2 #apr .apr-grande": {
"width": "calc(var(--d) * .57)"
},
"body.pb-on.pb-a2 #apr .apr-lado.px": {
"width": "calc(var(--d) * .32)"
},
"body.pb-on.pb-a2 #apr .apr-lado.ant": {
"width": "calc(var(--d) * .07)"
},
"body.pb-on .fila-item": {
"background": "#1e2d49",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
"body.pb-on .fila-item.atual": {
"background": "#2a2410",
"border-color": "#f5d76e",
"box-shadow": [
{
"x": 3,
"y": 0,
"blur": 0,
"spread": 0,
"cor": "#f5d76e",
"inset": true
}
]
},
"body.pb-on.pb-a2 #apr .apr-palco": {
"grid-template-areas": "\"g p\" \"g a\""
},
"body.pb-on.pb-dupla #painel": {
"display": "grid",
"grid-template-columns": "minmax(0,1fr) minmax(0,1fr)",
"grid-template-rows": "auto auto minmax(0,1fr)",
"align-content": "stretch",
"column-gap": 8,
"row-gap": 6
},
"body.pb-on.pb-dupla #painel > *": {
"grid-column": "1 / -1"
},
"body.pb-on.pb-dupla #painel > .preview-box:not(#pb-retorno)": {
"grid-column": 1,
"grid-row": 1
},
"body.pb-on.pb-dupla #painel > #pb-retorno": {
"grid-column": 2,
"grid-row": 1,
"margin": [
0,
0,
0,
0
]
},
"body.pb-on.pb-dupla #painel > .preview-box .mini": {
"width": {
"pct": 100.0
}
},
"body.pb-on.pb-dupla #painel .prev-selo": {
"font-size": 9.5
},
"#lista-slides .item.anim": {
"display": "flex",
"align-items": "center",
"gap": 10
},
"#lista-slides .anim-mini": {
"flex": "none",
"width": 96,
"height": 54,
"border-radius": 4,
"background": "#0b1526",
"border": {
"w": 1,
"cor": "#2c3d5c",
"tracejado": false
}
},
"#pj-veu": {
"position": "fixed",
"inset": [
0,
0,
0,
0
],
"z-index": 119,
"background": "#a6050a14",
"-webkit-backdrop-filter": "blur(3px)",
"backdrop-filter": {
"blur": 3.0
}
},
"#pj-cartao": {
"position": "fixed",
"left": {
"pct": 50.0
},
"top": {
"pct": 50.0
},
"transform": "translate(-50%,-50%)",
"z-index": 120,
"width": 420,
"display": "flex",
"gap": 16,
"align-items": "flex-start",
"padding": [
20,
20,
16,
20
],
"border-radius": 14,
"border": {
"w": 2,
"cor": "#f5d76e",
"tracejado": false
},
"background": "radial-gradient(120% 60% at 50% 0%,#ffffff12 0%,#ffffff00 60%),linear-gradient(180deg,#1e2d49,#16233c)",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 1,
"cor": "#33f5d76e",
"inset": false
},
{
"x": 0,
"y": 0,
"blur": 18,
"spread": 0,
"cor": "#40f5d76e",
"inset": false
},
{
"x": 0,
"y": 18,
"blur": 50,
"spread": 0,
"cor": "#cc000000",
"inset": false
},
{
"x": 0,
"y": 1,
"blur": 0,
"spread": 0,
"cor": "#1affffff",
"inset": true
}
]
},
"#pj-cartao .pj-roda": {
"flex": "none",
"width": 34,
"height": 34,
"border-radius": {
"pct": 50.0
},
"border": {
"w": 3,
"cor": "#44f5d76e",
"tracejado": false
},
"border-top-color": "#f5d76e"
},
"#pj-cartao .pj-corpo": {
"flex": 1,
"min-width": 0
},
"#pj-cartao .pj-tit": {
"font-size": 17,
"font-weight": 700,
"color": "#f5d76e"
},
"#pj-cartao .pj-txt": {
"font-size": 13.5,
"color": "#cdd9ee",
"margin": [
6,
0,
14,
0
],
"line-height": 1.5
},
"#pj-cartao .pj-acoes": {
"display": "flex",
"align-items": "center",
"justify-content": "center",
"gap": 10
},
"#pj-cartao .pj-acoes .big-btn": {
"flex": "1 1 0"
},
"#pj-cartao .pj-ensaio": {
"font-size": 12,
"color": "#7f90ad",
"text-decoration": "underline"
},
"#saude-selo": {
"display": "none",
"position": "fixed",
"left": {
"pct": 50.0
},
"bottom": 10,
"transform": "translateX(-50%)",
"z-index": 110,
"max-width": "min(92vw,620px)",
"padding": [
7,
14,
7,
14
],
"border-radius": 999,
"font-size": 12.5,
"font-weight": 600,
"line-height": 1.35,
"text-align": "center",
"box-shadow": [
{
"x": 0,
"y": 6,
"blur": 20,
"spread": 0,
"cor": "#aa000000",
"inset": false
}
],
"pointer-events": "auto"
},
"#saude-selo.on": {
"display": "block"
},
"#saude-selo.atencao": {
"background": "#3a2f0b",
"color": "#f5d76e",
"border": {
"w": 1,
"cor": "#88f5d76e",
"tracejado": false
}
},
"#saude-selo.perigo": {
"background": "#4a0f0f",
"color": "#ffd5d5",
"border": {
"w": 1,
"cor": "#ff6b6b",
"tracejado": false
}
},
".ajuda-box.pj-aura": {
"border-color": "#88f5d76e",
"box-shadow": [
{
"x": 0,
"y": 0,
"blur": 0,
"spread": 1,
"cor": "#33f5d76e",
"inset": false
},
{
"x": 0,
"y": 0,
"blur": 18,
"spread": 0,
"cor": "#40f5d76e",
"inset": false
},
{
"x": 0,
"y": 18,
"blur": 50,
"spread": 0,
"cor": "#cc000000",
"inset": false
}
]
}
}
var SPEC = {"*": [0, 0], "html": [1, 1], "body": [1, 2], "button": [1, 3], ".st-ouro": [100, 4], ".ico": [100, 5], ".ico svg": [101, 6], "#app": [10000, 7], "header": [1, 8], "header .logo": [101, 9], ".marca": [100, 10], ".marca svg": [101, 11], ".marca-igreja": [100, 12], ".bv-overlay": [100, 13], ".bv-overlay.oculto": [200, 14], ".bv-box": [100, 15], ".bv-passos": [100, 16], ".bv-ponto": [100, 17], ".bv-ponto.on": [200, 18], ".bv-corpo": [100, 19], ".bv-corpo h2": [101, 20], ".bv-sub": [100, 21], ".bv-corpo p": [101, 22], ".bv-marca": [100, 23], ".bv-verso": [100, 24], ".bv-verso span": [101, 25], ".bv-lista": [100, 26], ".bv-lista li": [101, 27], ".bv-lista li::before": [301, 28], ".bv-lista b": [101, 29], ".bv-igreja": [100, 30], ".bv-igreja input[type=text]": [201, 31], ".bv-cultos": [100, 32], ".bv-dia h4": [101, 33], ".bv-rodape": [100, 34], ".bv-pular": [100, 35], ".bv-pular:hover": [200, 36], ".bv-navs": [100, 37], ".tabs": [100, 38], ".tabs::-webkit-scrollbar": [300, 39], ".tab": [100, 40], ".tab .ico": [200, 41], ".tab:hover": [200, 42], ".tab.ativo": [200, 43], ".estilo-btn": [100, 44], ".estilo-btn:hover": [200, 45], ".estilo-btn .ico": [200, 46], "body.modo-apr #btn-estilo": [10101, 47], "main": [1, 48], "#conteudo": [10000, 49], ".view": [100, 50], ".view.ativo": [200, 51], ".view[data-aba=\"louvor\"].ativo": [300, 52], ".view[data-aba=\"biblia\"].ativo": [300, 53], ".col": [100, 54], ".col:last-child": [200, 55], ".col h3": [101, 56], ".busca": [100, 57], ".busca input": [101, 58], ".lista": [100, 59], ".item": [100, 60], ".item.col-lista": [200, 61], ".item:hover": [200, 62], ".item.sel": [200, 63], ".item.na-lista": [200, 64], ".grupo-col": [100, 65], ".grupo-col:first-child": [200, 66], ".grupo-col.cias": [200, 67], ".item.cias": [200, 68], ".item.cias:hover": [300, 69], ".item.cias.sel": [300, 70], ".marca-lista": [100, 71], ".item small": [101, 72], "#lista-slides .item": [10100, 73], ".vazio": [100, 74], ".grid-num .vazio": [200, 75], ".grid-num": [100, 76], ".col-cv h3": [101, 77], ".col-cv h3:first-child": [201, 78], "#grid-caps": [10000, 79], "#grid-vers": [10000, 80], ".gnum": [100, 81], ".gnum:hover": [200, 82], ".gnum.sel": [200, 83], ".centro": [100, 84], ".card": [100, 85], ".card h2": [101, 86], ".card h2+.dica": [201, 87], ".row": [100, 88], ".big-btn": [100, 89], ".big-btn:hover": [200, 90], ".big-btn.ouro": [200, 91], ".big-btn.ouro:hover": [300, 92], ".big-btn.verde": [200, 93], ".big-btn.verde:hover": [300, 94], ".big-btn.vermelho": [200, 95], ".big-btn.vermelho:hover": [300, 96], "input[type=number]": [101, 97], "input[type=text]": [101, 98], "select": [1, 99], "textarea": [1, 100], "input:focus": [101, 101], "select:focus": [101, 102], "textarea:focus": [101, 103], ".timer-display": [100, 104], ".dica": [100, 105], ".dica b": [101, 106], ".sl-status": [100, 107], ".sl-status.erro": [200, 108], ".sl-grade": [100, 109], ".sl-card": [100, 110], ".sl-card:hover": [200, 111], ".sl-card.sel": [200, 112], ".sl-card img": [101, 113], ".sl-card span": [101, 114], ".sl-card.sel span": [201, 115], ".fundo-cats": [100, 116], ".fcat": [100, 117], ".fcat:hover": [200, 118], ".fcat.on": [200, 119], ".grid-fundos": [100, 120], ".fundo-card": [100, 121], ".fundo-card:hover": [200, 122], ".fundo-card.espera": [200, 123], ".fundo-card.projetando": [200, 124], ".fundo-card img": [101, 125], ".fundo-card .nome": [200, 126], ".fundo-acoes": [100, 127], ".fundo-card:hover .fundo-acoes": [300, 128], ".fa": [100, 129], ".fa-espera:hover": [200, 130], ".fa-del:hover": [200, 131], ".badge-espera": [100, 132], ".add-card": [100, 133], ".add-card:hover": [200, 134], ".add-inner": [100, 135], ".add-inner .plus": [200, 136], ".campo-lbl": [100, 137], ".fundos-liso": [100, 138], ".liso-card": [100, 139], ".liso-card:hover": [200, 140], ".liso-card.sel": [200, 141], ".liso-card img": [101, 142], ".liso-card span": [101, 143], ".liso-card.sel span": [201, 144], ".add-form": [100, 145], ".add-form input[type=file]": [201, 146], ".af-prev": [100, 147], "#painel": [10000, 148], "#painel>*:not(.fila-itens)": [10200, 149], ".ctrl-linha:not(.tam)": [300, 150], ".fila-tit-row": [100, 151], ".estado-barra": [100, 152], ".estado-barra.aovivo": [200, 153], ".estado-barra.espera": [200, 154], ".estado-barra.espera .dot": [300, 155], ".prev-selo.espera": [200, 156], ".estado-barra.congelado": [200, 157], ".estado-barra .dot": [200, 158], ".estado-barra.aovivo .dot": [300, 159], ".estado-barra.congelado .dot": [300, 160], ".preview-box .mini": [200, 161], ".prev-selo": [100, 162], ".prev-selo.aovivo": [200, 163], ".prev-selo.congelado": [200, 164], ".dot": [100, 165], ".dot.on": [200, 166], ".dot.espera": [200, 167], ".preview-box": [100, 168], ".preview-box iframe": [101, 169], ".agora": [100, 170], ".ctrl": [100, 171], ".ctrl:hover": [200, 172], ".ctrl .ico": [200, 173], ".ctrl.projetar": [200, 174], ".ctrl.projetar.on": [300, 175], ".ctrl.projetar.on.em-espera": [400, 176], ".barra-extras": [100, 177], ".barra-extras.oculto": [200, 178], ".ff.extra.oculto": [300, 179], ".ff.extra": [200, 180], ".ff.extra:hover": [300, 181], ".ff.extra.cifra.on": [400, 182], ".ff.extra.cias.on": [400, 183], ".ctrl-linha": [100, 184], ".ctrl-linha .ctrl": [200, 185], ".nav2": [100, 186], ".nav2 .projetar": [200, 187], ".nav2 .nav": [200, 188], ".nav2 .nav:hover": [300, 189], ".nav2 .nav .ico": [300, 190], ".ctrl-linha.tam": [200, 191], ".tam-label": [100, 192], ".tam-label:hover": [200, 193], ".freeze-on": [100, 194], ".fila-tit": [100, 195], ".fila-itens": [100, 196], ".fila-itens::-webkit-scrollbar": [300, 197], ".fila-itens::-webkit-scrollbar-thumb": [300, 198], ".fila-itens::-webkit-scrollbar-track": [300, 199], ".fila-item": [100, 200], ".fila-item:hover": [200, 201], ".fila-item:hover .fila-btns": [300, 202], ".fila-item.atual": [200, 203], ".fila-item.ja-foi": [200, 204], ".fila-item.ja-foi .rot": [300, 205], ".fila-item.ja-foi:hover": [300, 206], ".fila-item.arrastando": [200, 207], ".fila-item.drop-alvo": [200, 208], ".fila-btns": [100, 209], ".fila-item:focus-within .fila-btns": [300, 210], ".fila-btns .fb": [200, 211], ".fila-btns .fb:hover": [300, 212], ".fila-btns .fb.x:hover": [400, 213], ".gnum.na-fila": [200, 214], ".fila-tit-row .fila-tit": [200, 215], ".mini-btn": [100, 216], ".mini-btn:hover": [200, 217], ".mini-btn.destaque": [200, 218], ".mini-btn.destaque:hover": [300, 219], ".fila-item .rot": [200, 220], ".fila-item .chk": [200, 221], ".fila-item .chk.on": [300, 222], ".fila-item .chk:hover": [300, 223], ".fila-dica": [100, 224], ".fila-num": [100, 225], ".fila-item.atual .fila-num": [300, 226], ".fila-grupo": [100, 227], ".fila-grupo:first-child": [200, 228], ".barra-ferr": [100, 229], ".ff": [100, 230], ".ff:hover": [200, 231], ".ff .ico": [200, 232], ".ff.mini": [200, 233], ".ff.tam-label": [200, 234], ".ff.freeze-on": [200, 235], ".sep": [100, 236], ".mini-btn.destaque.ativo": [300, 237], ".fila-item.agrupado": [200, 238], ".fila-item.agrupado .chk.on": [400, 239], ".modo-juntos": [100, 240], ".hamb": [100, 241], ".hamb span": [101, 242], ".hamb:hover": [200, 243], ".hamb:hover span": [201, 244], ".menu-overlay": [100, 245], ".menu-overlay.oculto": [200, 246], ".menu-lateral": [100, 247], ".menu-topo": [100, 248], ".menu-topo h2": [101, 249], ".menu-x": [100, 250], ".menu-x:hover": [200, 251], ".menu-abas": [100, 252], ".menu-aba": [100, 253], ".menu-aba:hover": [200, 254], ".menu-aba.ativo": [200, 255], ".menu-corpo": [100, 256], ".menu-sec": [100, 257], ".menu-sec.ativo": [200, 258], ".menu-sec input[type=text]": [201, 259], ".menu-h3": [100, 260], ".ed-lista": [100, 261], ".av-lista": [100, 262], ".ed-item": [100, 263], ".ed-item small": [101, 264], ".ed-btns": [100, 265], ".ed-btns .fb": [200, 266], ".ed-btns .fb:hover": [300, 267], ".ed-btns .fb.x:hover": [400, 268], ".ini-marca": [100, 269], ".ini-tit": [100, 270], ".ini-sub": [100, 271], ".ini-cards": [100, 272], ".ini-card": [100, 273], ".ini-card:hover": [200, 274], ".ini-card b": [101, 275], ".ini-card small": [101, 276], ".ini-rodape": [100, 277], ".ini-autor": [100, 278], ".ini-autor b": [101, 279], ".ig-rodape": [100, 280], ".ig-salvo": [100, 281], ".ig-salvo.on": [200, 282], ".ig-salvo.piscar": [200, 283], ".cel-caixa": [100, 284], ".cel-qr img": [101, 285], ".cel-semqr": [100, 286], ".cel-info": [100, 287], ".cel-url": [100, 288], ".cel-passos": [100, 289], ".cel-passos b": [101, 290], ".ig-dia": [100, 291], ".ig-dia h4": [101, 292], ".ig-linha": [100, 293], ".ig-linha:hover": [200, 294], ".ig-linha span": [101, 295], ".ig-linha input[type=time]": [201, 296], ".ig-linha input[type=checkbox]": [201, 297], ".mus-bloco": [100, 298], ".mus-bloco p": [101, 299], ".mus-bloco p:last-child": [201, 300], ".mus-bloco b": [101, 301], ".mus-bloco code": [101, 302], ".mus-lista": [100, 303], ".mus-lista li": [101, 304], ".mus-lista li:last-child": [201, 305], ".ig-dia h4 small": [102, 306], ".ig-linha input[type=date]": [201, 307], ".ig-movel": [100, 308], ".ig-movel span": [101, 309], ".av-chip": [100, 310], ".av-chip:hover": [200, 311], ".av-chip.auto": [200, 312], ".reset-row": [100, 313], ".reset-row div": [101, 314], ".reset-row b": [101, 315], ".reset-row small": [101, 316], ".reset-row.perigo": [200, 317], ".ajuda-overlay": [100, 318], ".ajuda-box": [100, 319], ".ajuda-box h3": [101, 320], ".ajuda-box p": [101, 321], ".ajuda-box p:last-of-type": [201, 322], ".ajuda-box b": [101, 323], ".teclas": [100, 324], ".teclas .mais": [200, 325], ".ajuda-box kbd": [101, 326], "#pj-cartao kbd": [10001, 327], ".ajuda-box kbd.win": [201, 328], "#pj-cartao kbd.win": [10101, 329], ".ajuda-box kbd.win svg": [202, 330], "#pj-cartao kbd.win svg": [10102, 331], ".ajuda-box kbd.win span": [202, 332], "#pj-cartao kbd.win span": [10102, 333], ".ajuda-box ol": [101, 334], ".ajuda-box ol b": [102, 335], ".ajuda-btns": [100, 336], "#toast": [10000, 337], "#toast.show": [10100, 338], ".item small.etq-col": [201, 339], ".cifra-ov": [100, 340], ".cifra-ov.oculto": [200, 341], ".cifra-cx": [100, 342], ".cifra-cab": [100, 343], ".cifra-cab b": [101, 344], ".cifra-cab .ico": [200, 345], ".cifra-x": [100, 346], ".cifra-x:hover": [200, 347], ".cifra-zoom": [100, 348], ".cifra-zoom button": [101, 349], ".cifra-zoom button:hover": [201, 350], ".folha": [100, 351], ".folha pre": [101, 352], ".folha .tr": [200, 353], ".folha .ac": [200, 354], ".folha .rot": [200, 355], ".folha .intro": [200, 356], ".folha .rep": [200, 357], ".folha .cab": [200, 358], ".folha .cab b": [201, 359], ".gnum.alvo-busca": [200, 360], ".niv-cx": [100, 361], ".niv-cx button": [101, 362], ".niv-cx button.on": [201, 363], ".tom-cx": [100, 364], ".tom-btn": [100, 365], ".tom-btn:hover": [200, 366], ".tom-painel": [100, 367], ".tom-linha": [100, 368], ".tom-linha button": [101, 369], ".tom-linha button:hover": [201, 370], ".tom-grade": [100, 371], ".tom-op": [100, 372], ".tom-op:hover": [200, 373], ".tom-op.on": [200, 374], ".tom-restaura": [100, 375], ".tom-restaura:hover": [200, 376], ".pn-filtros": [100, 377], ".pn-f": [100, 378], ".pn-f:hover": [200, 379], ".pn-f.ativo": [200, 380], ".pn-resumo": [100, 381], ".pn-cx": [100, 382], ".pn-cx b": [101, 383], ".pn-cx span": [101, 384], ".pn-tit": [100, 385], ".pn-lista": [100, 386], ".pn-l": [100, 387], ".pn-l .pos": [200, 388], ".pn-l .nm": [200, 389], ".pn-l .vl": [200, 390], ".pn-l .bar": [200, 391], ".pn-l>*": [100, 392], ".pn-vazio": [100, 393], ".sug": [100, 394], ".sug.oculto": [200, 395], ".sug-cab": [100, 396], ".sug-cab b": [101, 397], ".sug-cab .ico": [200, 398], ".sug-mais": [100, 399], ".sug-mais:hover": [200, 400], ".sug-lista": [100, 401], ".sug-l": [100, 402], ".sug-l:hover": [200, 403], ".sug-l small": [101, 404], ".sug-l .nm": [200, 405], ".sug-l .add": [200, 406], ".sug-l .add:hover": [300, 407], ".cred-bloco": [100, 408], ".cred-bloco p": [101, 409], ".cred-bloco p:last-child": [201, 410], ".cred-bloco b": [101, 411], ".cred-mais-btn": [100, 412], ".cred-mais-btn:hover": [200, 413], ".busca-trecho .trecho-cab": [200, 414], ".item-trecho": [100, 415], ".item-trecho b": [101, 416], ".item-trecho small": [101, 417], ".item-trecho:hover": [200, 418], ".pulso": [100, 419], ".timer-display.pausado": [200, 420], ".big-btn.ativo": [200, 421], ".passo-num": [100, 422], ".passo-num input[type=number]": [201, 423], ".passo-num input[type=number]::-webkit-outer-spin-button": [401, 424], ".passo-num input[type=number]::-webkit-inner-spin-button": [401, 425], ".pn-b": [100, 426], ".pn-b:hover": [200, 427], ".pn-b:active": [200, 428], ".pn-un": [100, 429], ".view[data-aba=\"timer\"] .row input[type=text]": [401, 430], "input": [1, 431], ".cifra-folha": [100, 432], "#cifra-folha pre": [10001, 433], "[hidden]": [100, 434], ".reset-row.melhor": [200, 435], ".reset-row.melhor b": [201, 436], ".reset-row.melhor .big-btn": [300, 437], ".reset-row.melhor .big-btn:hover": [400, 438], ".fundo-card .ap-info": [200, 439], ".fundo-card .nome .ap-nome": [300, 440], ".sis-grupo": [100, 441], ".sis-grupo>summary": [101, 442], ".sis-grupo>summary::-webkit-details-marker": [301, 443], ".sis-grupo>summary::after": [301, 444], ".sis-grupo[open]>summary::after": [401, 445], ".sis-grupo>summary:hover": [201, 446], ".sis-grupo .sg-tit": [200, 447], ".sis-grupo>summary small": [102, 448], ".sis-grupo[open]": [200, 449], ".sis-grupo .reset-row": [200, 450], ".sis-grupo .cred-bloco": [200, 451], "#grupo-desinstalar>summary .sg-tit": [10101, 452], ".sis-grupo.melhor": [200, 453], ".sis-grupo.melhor>summary": [201, 454], ".sis-grupo.melhor>summary .sg-tit": [301, 455], ".sis-grupo.melhor>summary small": [202, 456], ".reset-row.destaque": [200, 457], ".sis-assina": [100, 458], ".sis-assina b": [101, 459], ".reset-row small b": [102, 460], ".view[data-aba=\"slides\"].apr-on>.card": [400, 461], ".apr": [100, 462], ".apr.oculto": [200, 463], ".apr-palco": [100, 464], ".apr.escondida .apr-palco": [300, 465], ".apr-grande": [100, 466], ".apr.escondida .apr-grande": [300, 467], ".apr-lado": [100, 468], ".apr.escondida .apr-lado": [300, 469], ".apr-q": [100, 470], ".apr-q img": [101, 471], ".apr-grande .apr-q": [200, 472], ".apr-lado .apr-q": [200, 473], ".apr-tag": [100, 474], ".apr-grande .apr-tag": [200, 475], ".apr-lado.ant img": [201, 476], ".apr-lado.px .apr-tag": [300, 477], ".apr-hint": [100, 478], ".apr-hint big .ico": [201, 479], ".apr-lado:hover .apr-hint": [300, 480], ".apr-lado.vazio": [200, 481], ".apr-lado.fim": [200, 482], ".apr-lado.fim .apr-hint": [300, 483], ".apr-fim-q": [100, 484], ".apr-fim-q[hidden]": [200, 485], ".apr-preto": [100, 486], ".apr.preto .apr-preto": [300, 487], ".apr-col": [100, 488], ".apr.escondida .apr-col": [300, 489], ".apr-ctopo": [100, 490], ".apr-lk": [100, 491], ".apr-lk .ico": [200, 492], ".apr-lk:hover": [200, 493], ".apr-l1": [100, 494], ".apr-nm": [100, 495], ".apr-ib": [100, 496], ".apr-ib .ico": [200, 497], ".apr-ib:hover": [200, 498], ".apr-ib.on": [200, 499], ".apr-ib.on:hover": [300, 500], ".apr-achar": [100, 501], ".apr-achar:focus-within": [200, 502], ".apr-achar .ico": [200, 503], ".apr-achar input": [101, 504], ".apr-achar input:focus": [201, 505], ".apr-achar input::placeholder": [301, 506], ".apr-lista": [100, 507], ".apr-lista::-webkit-scrollbar": [300, 508], ".apr-lista::-webkit-scrollbar-thumb": [300, 509], ".apr-th": [100, 510], ".apr-th b": [101, 511], ".apr-th .im": [200, 512], ".apr-th .im img": [201, 513], ".apr-th.passou .im": [300, 514], ".apr-th.on .im": [300, 515], ".apr-th.on b": [201, 516], ".apr-th:hover .im": [300, 517], ".apr-th:hover .im::after": [500, 518], ".apr-th.achou .im": [300, 519], ".apr-th.fora": [200, 520], ".apr-sem": [100, 521], ".apr-sem[hidden]": [200, 522], ".apr-trilho": [100, 523], ".apr.escondida .apr-trilho": [300, 524], ".apr-ic3": [100, 525], ".apr-ic3 .ico": [200, 526], ".apr-trilho b": [101, 527], ".apr-trilho:hover .apr-ic3": [300, 528], ".apr-num": [100, 529], ".apr-num[hidden]": [200, 530], ".apr-num big": [101, 531], ".apr-num small": [101, 532], ".fila-item .rot .ico": [300, 533], ".fila-agora": [100, 534], ".fila-agora i": [101, 535], ".fila-agora+.fila-btns": [200, 536], ".sis-botoes": [100, 537], ".sis-bt": [100, 538], ".sis-op": [100, 539], ".sis-bt:hover": [200, 540], ".sis-op:hover": [200, 541], ".sis-bt b": [101, 542], ".sis-op b": [101, 543], ".sis-bt small": [101, 544], ".sis-op small": [101, 545], ".sis-bt.perigo b": [201, 546], ".sis-op.perigo b": [201, 547], ".sis-op.perigo:hover": [300, 548], ".sis-bt.melhor": [200, 549], ".sis-bt.melhor b": [201, 550], ".sis-bt.melhor small": [201, 551], ".sis-pref": [100, 552], ".chave": [100, 553], ".chave::before": [300, 554], ".chave.on": [200, 555], ".aviso-limitada": [100, 556], ".chave.on::before": [400, 557], ".assist-box": [100, 558], ".assist-escolhas": [100, 559], ".assist-escolhas:empty": [200, 560], ".assist-box .sis-painel": [200, 561], ".assist-box .sis-painel .reset-row": [300, 562], ".assist-box .ajuda-btns": [200, 563], "#ap-grade .fundo-card.especial": [10200, 564], "#ap-grade .fundo-card.especial:hover": [10300, 565], ".ap-mini": [100, 566], ".selo-ultra": [100, 567], ".selo-ultra svg": [101, 568], "#ap-grade .fundo-card.especial .ap-info": [10300, 569], "#dt-veu": [10000, 570], "#dt-cartao": [10000, 571], "#dt-cartao .dt-ico": [10100, 572], "#dt-cartao .dt-ico svg": [10101, 573], "#dt-cartao .dt-corpo": [10100, 574], "#dt-cartao .dt-tit": [10100, 575], "#dt-cartao .dt-txt": [10100, 576], "#dt-cartao .dt-par": [10100, 577], "#dt-cartao .dt-n": [10100, 578], "#dt-cartao .dt-n.dois": [10200, 579], "#dt-cartao .dt-acoes": [10100, 580], "#dt-cartao .dt-acoes .big-btn": [10200, 581], "#dt-cartao.como": [10100, 582], "#dt-cartao.como .dt-corpo": [10200, 583], "#dt-cartao.como .dt-par": [10200, 584], "#dt-cartao.como .dt-acoes": [10200, 585], "#dt-cartao .dt-ops": [10100, 586], "#dt-cartao .dt-op": [10100, 587], "#dt-cartao .dt-op:hover": [10200, 588], "#dt-cartao .dt-op.on": [10200, 589], "#dt-cartao .dt-op svg": [10101, 590], "#dt-cartao .dt-redondo": [10100, 591], "#dt-cartao .dt-redondo:hover": [10200, 592], "#dt-cartao .dt-redondo.verde": [10200, 593], "#dt-cartao .dt-redondo.verde:hover": [10300, 594], "#dt-pilula": [10000, 595], "#dt-pilula.on": [10100, 596], "#dt-pilula.on:hover": [10200, 597], "#dt-pilula .dt-bola": [10100, 598], "#dt-pilula.conectar": [10100, 599], "#dt-pilula.conectar:hover": [10200, 600], "#dt-pilula.reconectando": [10100, 601], "#dt-pilula.reconectando .dt-bola": [10200, 602], ".tabs .tab:focus": [300, 603], ".tabs .tab:focus-visible": [300, 604], "body.pb-on #painel #estado-barra": [20101, 605], "body.pb-on #painel #agora": [20101, 606], "body.pb-on #painel .barra-extras": [10201, 607], ".pb-n": [100, 608], "body.pb-on .preview-box .pb-n": [301, 609], "#pb-retorno": [10000, 610], "body.pb-on.pb-dupla #pb-retorno": [10201, 611], "#pb-retorno .mini": [10100, 612], "#pb-retorno iframe": [10001, 613], "#pb-retorno .prev-selo": [10100, 614], "#pb-retorno .prev-selo b": [10101, 615], "body.pb-on #apr .apr-palco": [10201, 616], "body.pb-on #apr .apr-grande": [10201, 617], "body.pb-on #apr .apr-lado.px": [10301, 618], "body.pb-on #apr .apr-lado.ant": [10301, 619], "body.pb-on #apr .apr-lado.px .apr-q": [10401, 620], "body.pb-on #apr .apr-lado.px .apr-tag": [10401, 621], "body.pb-on #apr .apr-lado.ant .apr-tag": [10401, 622], "body.pb-on #apr .apr-lado.ant img": [10302, 623], "body.pb-on #apr .apr-tag": [10201, 624], "#pb-louvores": [10000, 625], "body.pb-on #pb-louvores": [10101, 626], "body.pb-on #pb-louvores:empty": [10201, 627], "#pb-louvores .lv": [10100, 628], "#pb-louvores .lv.agora": [10200, 629], "#pb-louvores .lv.prox": [10200, 630], "#pb-louvores .lv small": [10101, 631], ".pb-selo": [100, 632], ".pb-selo svg": [101, 633], "#pb-faixa": [10000, 634], "body.pb-on #pb-faixa": [10101, 635], "body.pb-on .apr.escondida #pb-faixa": [10301, 636], "#pb-faixa .nav2": [10100, 637], "#pb-faixa .projetar": [10100, 638], "#pb-faixa .barra-ferr": [10100, 639], "#pb-faixa .pb-agora": [10100, 640], "#pb-faixa.apertada": [10100, 641], "#pb-faixa.apertada .nav2": [10200, 642], "#pb-faixa.apertada #btn-congelar": [20100, 643], "#pb-faixa.apertada #btn-congelar .ico": [20200, 644], "#pb-faixa.muito .pb-agora": [10200, 645], "#pb-faixa.muito .nav2": [10200, 646], "#pb-faixa.muito .nav2 .nav": [10300, 647], "#pb-faixa .pb-agora b": [10101, 648], "#pb-louvores .lv:hover": [10200, 649], "#pb-louvores .lv.foi": [10200, 650], "body.pb-on.pb-a2 #painel #pb-louvores": [20201, 651], "body.pb-on.pb-a2 #painel #pb-louvores .lv": [20301, 652], "body.pb-on.pb-a2 #painel #pb-louvores .lv small": [20302, 653], "body.pb-on.pb-a2 #apr .apr-grande": [10301, 654], "body.pb-on.pb-a2 #apr .apr-lado.px": [10401, 655], "body.pb-on.pb-a2 #apr .apr-lado.ant": [10401, 656], "body.pb-on .fila-item": [201, 657], "body.pb-on .fila-item.atual": [301, 658], "body.pb-on.pb-a2 #apr .apr-palco": [10301, 659], "body.pb-on.pb-dupla #painel": [10201, 660], "body.pb-on.pb-dupla #painel > *": [10201, 661], "body.pb-on.pb-dupla #painel > .preview-box:not(#pb-retorno)": [20401, 662], "body.pb-on.pb-dupla #painel > #pb-retorno": [20201, 663], "body.pb-on.pb-dupla #painel > .preview-box .mini": [10401, 664], "body.pb-on.pb-dupla #painel .prev-selo": [10301, 665], "#lista-slides .item.anim": [10200, 666], "#lista-slides .anim-mini": [10100, 667], "#pj-veu": [10000, 668], "#pj-cartao": [10000, 669], "#pj-cartao .pj-roda": [10100, 670], "#pj-cartao .pj-corpo": [10100, 671], "#pj-cartao .pj-tit": [10100, 672], "#pj-cartao .pj-txt": [10100, 673], "#pj-cartao .pj-acoes": [10100, 674], "#pj-cartao .pj-acoes .big-btn": [10200, 675], "#pj-cartao .pj-ensaio": [10100, 676], "#saude-selo": [10000, 677], "#saude-selo.on": [10100, 678], "#saude-selo.atencao": [10100, 679], "#saude-selo.perigo": [10100, 680], ".ajuda-box.pj-aura": [200, 681]}

// uma propriedade de um seletor (com o que vier por cascata: "a.b" herda de "a" se não tiver)
function p(sel, prop, padrao) {
    var r = R[sel]
    if (r && r[prop] !== undefined) return r[prop]
    return padrao
}
function c(sel, prop, padrao) { var v = p(sel, prop, padrao); return (v && v.paradas) ? v.paradas[0].c : v }
function n(sel, prop, padrao) { var v = p(sel, prop, padrao); return typeof v === "number" ? v : padrao }
function pad(sel, k, padrao) { var v = p(sel, "padding", null); return v ? (typeof v[k] === "number" ? v[k] : padrao) : padrao }
function borda(sel, padrao) { return p(sel, "border", padrao || { w: 0, cor: "transparent" }) }
function sombra(sel) { var v = p(sel, "box-shadow", []); return v.length ? v[0] : null }
function grad(sel) { var v = p(sel, "background", null); return (v && v.paradas) ? v.paradas : null }
// o ESTILO de um elemento com estas classes (do geral ao específico), com ou sem o mouse em cima:
// junta as regras na ordem do navegador (especificidade, depois a ordem no app.css) e devolve um objeto só
var _memoria = {}
function estilo(lista, sobre) {
    // a mesma combinação de classes devolve o MESMO objeto (já juntado): sem refazer a cascata a cada clique
    var chave = lista.join("|") + (sobre ? "|:hover" : "")
    var m = _memoria[chave]
    if (m) return m
    var cand = []
    for (var i = 0; i < lista.length; i++) {
        var s = lista[i]
        if (R[s]) cand.push(s)
        if (sobre && R[s + ":hover"]) cand.push(s + ":hover")
    }
    cand.sort(function (a, b) { var A = SPEC[a], B = SPEC[b]; return (A[0] - B[0]) || (A[1] - B[1]) })
    var out = {}
    for (var j = 0; j < cand.length; j++) { var r = R[cand[j]]; for (var k in r) out[k] = r[k] }
    _memoria[chave] = out
    return out
}
// A LETRA DO PAINEL (decisão dele 07/11 08h57): a 3.0.13 escreve 'Segoe UI'; o nativo usa a "Painel ICM" (a Selawik com o
// J na linha de base), EMBUTIDA, encaixada na Segoe pela altura do x e pela largura (prancha justa):
//   tamanho = px do app.css x 1,032 · espaçamento = o do app.css (o avanço de cada letra da Painel ICM já é o da Segoe / 1,032)
// reforco = a 2a passada da letra, em px, que iguala a TINTA do texto claro à do Edge (calibrada pela medida)
var FONTE = { familia: "Painel ICM", escala: 1.032, espacoEm: 0, reforco: 0.1, reforcoPeso: 700, opac600: 0.15, opac400: 0.52, quente: 0.4, franjaDx: 0.7, opacQuente: 0.25, reforcoMinPx: 12,
             asc: 2210 / 2048, desc: 514 / 2048,
             // os <input> sem type: o navegador desenha em Arial; a Liberation Sans tem as mesmas larguras e a mesma linha
             campo: { familia: "Liberation Sans", asc: 1854 / 2048, desc: 434 / 2048 } }   // a linha da Segoe (hhea): o navegador mede a linha por ela
function tam(px) { return px * FONTE.escala }
function espaco(lsCss, px) { return (lsCss || 0) + FONTE.espacoEm * tam(px) }
// a cor de um valor de fundo (cor, gradiente ou "none")
function fundo(v) { if (!v || v === "none" || v === "transparent") return "transparent"; return v.paradas ? v.paradas[0].c : v }
