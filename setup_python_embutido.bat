@echo off
setlocal
title Setup - STI_Extrator

:: ════════════════════════════════════════════════════════════════════
:: VARIÁVEIS BASE
:: %~dp0 = caminho absoluto da pasta onde este .bat está localizado.
:: Todas as referências de pasta partem daqui, tornando o projeto
:: portátil independente de onde for colocado no disco.
:: ════════════════════════════════════════════════════════════════════
set BASE_DIR=%~dp0
set PYTHON_DIR=%BASE_DIR%python_embutido
set PYTHON_EXE=%PYTHON_DIR%\python.exe
set BROWSERS_DIR=%BASE_DIR%browsers

:: ════════════════════════════════════════════════════════════════════
:: PLAYWRIGHT_BROWSERS_PATH (CORREÇÃO PROBLEMA 1)
:: Por padrão, o Playwright instala o Chromium na pasta do perfil
:: do usuário (%APPDATA%\ms-playwright), o que significa que cada
:: usuário precisaria baixar o browser separadamente.
:: Apontando para uma pasta dentro do projeto, o Chromium fica
:: junto com os demais arquivos e é compartilhado por todos.
:: ════════════════════════════════════════════════════════════════════
set PLAYWRIGHT_BROWSERS_PATH=%BROWSERS_DIR%


:: ════════════════════════════════════════════════════════════════════
:: CHECK 1 — PYTHON EMBARCADO
:: Verifica se o python.exe já existe na pasta do projeto.
:: Se sim, pula todo o processo de download e extração (~25MB).
:: ════════════════════════════════════════════════════════════════════
if exist "%PYTHON_EXE%" (
    echo [OK] Python embarcado ja encontrado. Pulando download.
    goto check_deps
)

echo [1/5] Baixando Python embarcado...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '%BASE_DIR%python_emb.zip'"

echo [2/5] Extraindo Python...
powershell -Command "Expand-Archive -Path '%BASE_DIR%python_emb.zip' -DestinationPath '%PYTHON_DIR%' -Force"
del "%BASE_DIR%python_emb.zip"

:: ════════════════════════════════════════════════════════════════════
:: HABILITANDO IMPORT DE PACOTES NO MODO EMBARCADO
:: O Python embarcado vem com um arquivo ._pth que, por padrão,
:: comenta a linha "import site", impedindo que pacotes instalados
:: via pip sejam encontrados. Esta linha descomenta isso.
:: ════════════════════════════════════════════════════════════════════
echo [3/5] Ativando suporte a pacotes externos...
for %%f in ("%PYTHON_DIR%\python311._pth") do (
    powershell -Command "(Get-Content '%%f') -replace '#import site', 'import site' | Set-Content '%%f'"
)

echo [4/5] Instalando pip...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%BASE_DIR%get-pip.py'"
"%PYTHON_EXE%" "%BASE_DIR%get-pip.py"
del "%BASE_DIR%get-pip.py"


:: ════════════════════════════════════════════════════════════════════
:: CHECK 2 — DEPENDÊNCIAS PYTHON
:: Tenta importar os três pacotes principais. Se qualquer um falhar,
:: o errorlevel será 1 e o pip reinstala tudo pelo requirements.txt.
:: ════════════════════════════════════════════════════════════════════
:check_deps
echo [INFO] Verificando dependencias Python...
"%PYTHON_EXE%" -c "import pandas, openpyxl, playwright" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Dependencias ja instaladas. Pulando pip install.
    goto check_playwright
)

echo [INFO] Instalando dependencias faltantes...
"%PYTHON_EXE%" -m pip install -r "%BASE_DIR%requirements.txt" --no-warn-script-location


:: ════════════════════════════════════════════════════════════════════
:: CHECK 3 — CHROMIUM DO PLAYWRIGHT
:: Verifica se o Chromium já está presente na pasta /browsers/.
:: A checagem é feita tentando iniciar e encerrar o Playwright
:: via linha de comando Python. Se funcionar, pula o download
:: do Chromium (~150MB).
:: ════════════════════════════════════════════════════════════════════
:check_playwright
echo [INFO] Verificando Chromium...
"%PYTHON_EXE%" -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.stop()" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Playwright e Chromium ja configurados. Pulando instalacao.
    goto fim
)

echo [5/5] Instalando Chromium (pode demorar alguns minutos)...
"%PYTHON_EXE%" -m playwright install chromium


:fim
echo.
echo ═══════════════════════════════════════════
echo  SETUP CONCLUIDO COM SUCESSO!
echo  Os usuarios ja podem usar o launcher.bat
echo ═══════════════════════════════════════════
pause