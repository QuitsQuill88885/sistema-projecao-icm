' Abre o Sistema Nativo sem janela de terminal (o registro vai para nativo.log, nesta pasta).
' O telão vai para a 2a tela se houver; para testar sem tomar a TV, use "Abrir em janela.vbs".
Set sh = CreateObject("WScript.Shell")
pasta = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = pasta
sh.Run """C:\Projetos\Sistema\App\venv_qt\Scripts\pythonw.exe"" """ & pasta & "\sistema_nativo.py""", 0, False
