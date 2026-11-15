// GERADO por ferramentas/conversor_312.py a partir de ICM Ipero Projecao (não editar à mão: rode o conversor de novo)
.pragma library
var SECOES = {
 "celular": [
  {
   "t": "p",
   "cls": "dica",
   "html": "Controle a projeção pelo celular, do banquinho do grupo de louvor. <b>Não precisa de internet</b> — só que os dois estejam na mesma rede."
  },
  {
   "t": "especial",
   "id": "cel-caixa"
  },
  {
   "t": "h3",
   "cls": "menu-h3",
   "html": "Como conectar"
  },
  {
   "t": "ol",
   "cls": "cel-passos",
   "itens": [
    "No celular, ligue o <b>roteador wi-fi</b> (ponto de acesso).",
    "No computador, conecte-se a essa rede do celular.",
    "Aponte a câmera do celular para o código acima — ou digite o endereço no navegador."
   ]
  },
  {
   "t": "p",
   "cls": "dica",
   "html": "Se a igreja tiver wi-fi, é mais simples ainda: deixe os dois na rede da igreja e pule os dois primeiros passos.",
   "mt": 14
  }
 ],
 "musica": [
  {
   "t": "p",
   "cls": "dica",
   "html": "Como funciona o lado do músico. Nada aqui precisa ser configurado — é para você saber o que o Sistema tem e por que ele se comporta assim."
  },
  {
   "t": "h3",
   "cls": "menu-h3",
   "html": "De onde vem a cifra"
  },
  {
   "t": "bloco",
   "cls": "mus-bloco",
   "itens": [
    {
     "t": "p",
     "cls": "",
     "html": "O Sistema não guarda figuras de cifra: ele guarda <b>o acorde e a coluna da letra em que ele cai</b>. Por isso a cifra pode ser transposta, aumentada e reescrita em qualquer tom sem perder o alinhamento."
    }
   ]
  },
  {
   "t": "h3",
   "cls": "menu-h3",
   "html": "Cada instrumento lê o seu"
  },
  {
   "t": "bloco",
   "cls": "mus-bloco",
   "itens": [
    {
     "t": "p",
     "cls": "",
     "html": "Quem toca violão recebe a folha de <b>acordes</b>. Quem toca sopro recebe o <b>caderno melódico</b>, já escrito na afinação do instrumento — o Si bemol do tenor e do soprano, o Mi bemol do alto e do barítono."
    },
    {
     "t": "p",
     "cls": "",
     "html": "Não é a mesma folha traduzida na hora: são cadernos diferentes, e o Sistema entrega o que é seu quando você diz o que toca."
    }
   ]
  },
  {
   "t": "h3",
   "cls": "menu-h3",
   "html": "Transpor"
  },
  {
   "t": "bloco",
   "cls": "mus-bloco",
   "itens": [
    {
     "t": "p",
     "cls": "",
     "html": "Os dois botões de tom sobem e descem meio tom, como no Cifra Club. O deslocamento é <b>do seu aparelho e do louvor aberto</b>: cada músico escolhe o seu, e isso não mexe no telão nem no que os outros estão lendo."
    },
    {
     "t": "p",
     "cls": "",
     "html": "A escrita segue a armadura do tom de chegada — tons de bemol saem com bemol, e não com sustenido. Escrever <code>A#</code> onde o músico espera <code>Bb</code> faz ele parar para pensar no meio do louvor."
    }
   ]
  },
  {
   "t": "h3",
   "cls": "menu-h3",
   "html": "O afinador, e as duas portas"
  },
  {
   "t": "bloco",
   "cls": "mus-bloco",
   "itens": [
    {
     "t": "p",
     "cls": "",
     "html": "O afinador fica na aba <b>Cifra</b> do celular, e roda <b>dentro do próprio aparelho</b>: o som não viaja até o computador e volta. Se viajasse, o atraso tornaria a agulha inútil. Vários músicos podem afinar ao mesmo tempo, cada um no seu."
    },
    {
     "t": "p",
     "cls": "",
     "html": "Por causa disso o Sistema abre <b>duas portas</b>:"
    },
    {
     "t": "ul",
     "cls": "mus-lista",
     "itens": [
      "a <b>porta de todo dia</b>, que é por onde tudo funciona e nunca pergunta nada;",
      "a <b>porta segura</b>, que só o afinador usa."
     ]
    },
    {
     "t": "p",
     "cls": "",
     "html": "A segunda existe porque o navegador só libera o microfone para uma página que chegou por endereço seguro. Não é sobre o que a página faz com o som — é sobre poder confiar que a página que chegou é a que o Sistema mandou."
    },
    {
     "t": "p",
     "cls": "",
     "html": "Como não existe autoridade dentro da igreja para assinar esse endereço, <b>o próprio Sistema assina</b>. Por isso o celular pergunta uma vez se confia — e só uma vez, por aparelho. O certificado se refaz sozinho se o computador ganhar um endereço novo na rede."
    }
   ]
  }
 ]
}
var CULTOS_PADRAO = [{"dia": 0, "nome": "Escola Bíblica Dominical", "hora": "10:00", "on": true}, {"dia": 0, "nome": "Culto Evangelístico", "hora": "19:00", "on": true}, {"dia": 1, "nome": "Culto de Glorificação", "hora": "19:30", "on": false}, {"dia": 2, "nome": "Culto de Doutrina", "hora": "19:30", "on": false}, {"dia": 3, "nome": "Culto de Senhoras", "hora": "19:30", "on": true}, {"dia": 4, "nome": "Culto de Oração", "hora": "19:30", "on": true}, {"dia": 4, "nome": "Madrugada", "hora": "06:00", "on": true}, {"dia": 5, "nome": "Culto no Lar", "hora": "19:30", "on": true}, {"dia": 6, "nome": "Culto de Doutrina", "hora": "19:30", "on": true}, {"dia": 6, "nome": "Madrugada", "hora": "06:00", "on": true}]
var DIAS_NOME = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
