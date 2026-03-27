' ════════════════════════════════════════════════════
' Detecta a pasta onde este .vbs está localizado.
' Assim funciona independente de onde a pasta foi colocada.
' ════════════════════════════════════════════════════
Set objFSO = CreateObject(Scripting.FileSystemObject)
strBase = objFSO.GetParentFolderName(WScript.ScriptFullName)

' ════════════════════════════════════════════════════
' Define os caminhos do launcher e do ícone
' ════════════════════════════════════════════════════
strLauncher = strBase & launcher.bat
strIcone    = strBase & icone.ico

' ════════════════════════════════════════════════════
' Cria o atalho na área de trabalho do usuário atual
' ════════════════════════════════════════════════════
Set objShell   = CreateObject(WScript.Shell)
strDesktop     = objShell.SpecialFolders(Desktop)
Set objAtalho  = objShell.CreateShortcut(strDesktop & Extrator.lnk)

objAtalho.TargetPath       = strLauncher
objAtalho.WorkingDirectory = strBase
objAtalho.IconLocation     = strIcone
objAtalho.Description      = Extrator
objAtalho.Save

MsgBox Atalho criado na area de trabalho!, vbInformation, Extrator
```