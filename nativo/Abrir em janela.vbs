' Abre o Sistema Nativo com o telão numa JANELA (não vai para a 2a tela/TV). Bom para testar.
Set sh = CreateObject("WScript.Shell")
pasta = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = pasta
sh.Run """C:\Projetos\Sistema\App\venv_qt\Scripts\pythonw.exe"" """ & pasta & "\sistema_nativo.py"" --janela", 0, False
