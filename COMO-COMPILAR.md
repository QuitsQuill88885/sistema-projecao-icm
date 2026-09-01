# Como compilar o Sistema

Precisa de Python 3 no Windows e destas bibliotecas:

```bash
pip install pywebview pywin32 pyinstaller pillow qrcode cryptography
```

> Este arquivo estava desatualizado ate 31/08/2026: mandava digitar as linhas
> do PyInstaller na mao, sem `controle.html`, sem `cacert.pem` e sem os
> arquivos `.spec` que ja existem. **Use os `.spec`.** Eles sao a verdade — as
> linhas soltas saem de sincronia sem ninguem perceber.

## 1. Gerar os dados (so quando mudar a fonte dos louvores/Biblia)

```bash
python "..\biblia\gen_louvores.py"    # gera dados/louvores.js
python "..\biblia\build_dados.py"     # gera dados/biblia.js e dados/fundos.js
python "..\biblia\gen_galeria.py"     # gera dados/galeria.js e copia os fundos
python ferramentas\aplicar_consertos_louvores.py   # repoe os consertos manuais
```

## 2. Subir a versao em DOIS lugares

Esquecer um dos dois faz o programa mentir sobre si mesmo:

| arquivo | o que |
|---|---|
| `sistema.py` | `VERSAO = "x.y.z"` — e o que o botao de atualizar compara |
| `versao_exe.txt` | `filevers`, `prodvers`, `FileVersion`, `ProductVersion` |

## 3. A cadeia de compilacao, nesta ordem

```bash
python -m PyInstaller --noconfirm --clean "Sistema.spec"

rm -rf build_inst/programa && mkdir -p build_inst
cp -r dist/Sistema build_inst/programa

python -m PyInstaller --noconfirm --clean "Instalar o Sistema.spec"
python -m PyInstaller --noconfirm --clean "Instalar o Sistema completo.spec"
python -m PyInstaller --noconfirm --clean "Baixar o Sistema.spec"
```

**A ordem importa.** O "completo" embute `dist/Instalar o Sistema.exe` — com
espacos no nome. Se voce RENOMEAR em vez de COPIAR para o nome com hifen que
vai para a release, o passo seguinte falha. Ja derrubou a v2.7.7.

Sai em `dist/`, com espacos no nome. Para a release, **copie** (nao mova):

```bash
cd dist
cp "Baixar o Sistema.exe"            "Baixar-o-Sistema.exe"
cp "Instalar o Sistema.exe"          "Instalar-o-Sistema.exe"
cp "Instalar o Sistema completo.exe" "Instalar-o-Sistema-completo.exe"
```

## 4. O Conteudo.zip

As cifras, as melodias e as animacoes **nao vao dentro do .exe**: viajam no
pacote de conteudo, que o instalador copia para `%APPDATA%\Sistema Projecao`.
Se elas mudaram, o zip precisa sair de novo:

```bash
python scratchpad/refazer_conteudo_zip.py
```

O script comprime `.json` de verdade e guarda `.webp` **sem comprimir** (webp
ja e comprimido: deflate por cima ganhava 1,8% e custava o tempo todo), e no
fim confere que nenhum backup entrou e que o banco de cifras e mesmo o novo.

## 5. Publicar, e CONFERIR

```bash
gh release create vX.Y.Z --title "..." --notes-file notas.md \
  "dist/Instalar-o-Sistema.exe" "dist/Baixar-o-Sistema.exe" \
  "dist/Instalar-o-Sistema-completo.exe" "../../Pacote completo/Conteudo.zip"
```

A release pode existir com o arquivo pela metade. Conferir os quatro enderecos:

```bash
for f in Instalar-o-Sistema.exe Baixar-o-Sistema.exe \
         Instalar-o-Sistema-completo.exe Conteudo.zip; do
  curl -sIL -r 0-0 -o /dev/null -w "$f -> %{http_code}\n" \
    "https://github.com/QuitsQuill88885/sistema-projecao-icm/releases/latest/download/$f"
done
```

Tem que dar **206** nos quatro. 200 ou 404 significa que nao esta servindo o
arquivo certo.

## Regras que custaram caro

- **`--onedir`, nunca `--onefile`** para o programa. Com `--onefile` ele
  descompacta 28 MB a cada abertura e demora ~8 s; com `--onedir` abre em 0,2 s.
- **Nunca empacotar uma pasta INTEIRA no `.spec`.** Em 31/08/2026 havia 44 MB
  de backups dentro do `.exe` porque o spec pegava `dados/` inteira. Agora ele
  lista arquivo por arquivo e avisa se sobrar. **Arquivo de dados novo tem que
  entrar na lista `_DADOS` do `Sistema.spec`.**
- **Testar o `.exe` compilado, nao o codigo-fonte.** E, ao testar, conferir
  QUEM respondeu: o Sistema procura porta livre sozinho (8765 a 8785), entao um
  processo velho na 8765 responde no lugar dele e o teste mente.

## Onde ficam as coisas

| O que | Onde |
|---|---|
| Programa instalado | `%LOCALAPPDATA%\Programs\Sistema` |
| Configuracoes e conteudo do usuario | `%APPDATA%\Sistema Projecao` |
| Cifras que o programa le | `%APPDATA%\Sistema Projecao\cifras` |
| Apresentacoes convertidas | `%APPDATA%\Sistema Projecao\slides_importados` |

As configuracoes ficam **fora** do programa de proposito: ao atualizar, nada
se perde.
