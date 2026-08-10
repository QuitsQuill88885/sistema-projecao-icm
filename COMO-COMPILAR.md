# Como compilar o Sistema

Precisa de Python 3 no Windows e destas bibliotecas:

```bash
pip install pywebview pywin32 pyinstaller pillow
```

## 1. Gerar os dados (só quando mudar a fonte dos louvores/Bíblia)

```bash
python "..\biblia\gen_louvores.py"    # gera dados/louvores.js
python "..\biblia\build_dados.py"     # gera dados/biblia.js e dados/fundos.js
python "..\biblia\gen_galeria.py"     # gera dados/galeria.js e copia os fundos
```

## 2. Compilar o programa

Importante: usar **`--onedir`**, não `--onefile`.
Com `--onefile` o programa descompacta 28 MB a cada abertura e demora ~8 segundos.
Com `--onedir` abre em **0,2 segundo**.

```bash
python -m PyInstaller --noconfirm --clean --onedir --noconsole ^
  --name "Sistema" --icon sistema.ico ^
  --add-data "index.html;." --add-data "projecao.html;." --add-data "carregando.html;." ^
  --add-data "app.js;." --add-data "app.css;." --add-data "icones.js;." ^
  --add-data "sistema.png;." --add-data "manifest.json;." ^
  --add-data "dados;dados" --add-data "fundos;fundos" --add-data "fontes;fontes" ^
  --hidden-import win32com.client --hidden-import tkinter ^
  --hidden-import webview --hidden-import webview.platforms.edgechromium --collect-all webview ^
  sistema.py
```

Resultado: `dist\Sistema\Sistema.exe`

## 3. Compilar o instalador

O instalador leva a pasta do programa dentro dele.

```bash
mkdir build_inst
xcopy /E /I /Y dist\Sistema build_inst\programa

python -m PyInstaller --noconfirm --clean --onefile --noconsole ^
  --name "Instalar o Sistema" --icon sistema.ico ^
  --add-data "build_inst/programa;programa" --add-data "icones.js;." ^
  --hidden-import win32com.client ^
  --hidden-import webview --hidden-import webview.platforms.edgechromium --collect-all webview ^
  --distpath dist_inst instalador.py
```

Resultado: `dist_inst\Instalar o Sistema.exe` — é esse arquivo que se entrega.

## Onde ficam as coisas

| O quê | Onde |
|---|---|
| Programa instalado | `%LOCALAPPDATA%\Programs\Sistema` |
| Configurações e dados do usuário | `%APPDATA%\Sistema Projecao` |
| Apresentações convertidas | `%APPDATA%\Sistema Projecao\slides_importados` |

As configurações ficam **fora** do programa de propósito: ao atualizar, nada se perde.
