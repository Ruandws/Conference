@echo off
setlocal EnableDelayedExpansion
title Automacao EBSERH


:: ════════════════════════════════════════════════════════════════════
:: VARIÁVEIS BASE
:: Mesma lógica do setup: tudo parte da pasta onde o .bat está.
:: Isso garante que funciona independente de onde foi colocado no C:.
:: ════════════════════════════════════════════════════════════════════
set BASE_DIR=%~dp0
set PYTHON_EXE=%BASE_DIR%python_embutido\python.exe
set MAIN_SCRIPT=%BASE_DIR%main.py
set BROWSERS_DIR=%BASE_DIR%browsers

:: ════════════════════════════════════════════════════════════════════
:: PLAYWRIGHT_BROWSERS_PATH (CORREÇÃO PROBLEMA 1)
:: Precisa ser definida aqui também — não basta definir no setup.
:: Variáveis de ambiente definidas em um .bat não persistem em outros
:: processos. Cada execução precisa setar novamente.
:: ════════════════════════════════════════════════════════════════════
set PLAYWRIGHT_BROWSERS_PATH=%BROWSERS_DIR%


:: ════════════════════════════════════════════════════════════════════
:: CORREÇÃO PROBLEMA 2 — FLAG LOCAL POR MÁQUINA
:: %LOCALAPPDATA% aponta para a pasta local do usuário na máquina
:: atual (ex: C:\Users\joao\AppData\Local).
:: Isso garante que a flag é verificada POR MÁQUINA, não por pasta
:: de rede — evitando que um usuário "ative" o ambiente para todos
:: os outros antes deles configurarem localmente.
:: ════════════════════════════════════════════════════════════════════
set FLAG_DIR=%LOCALAPPDATA%\AutomacaoEBSERH
set FIRST_RUN_FLAG=%FLAG_DIR%\.installed


:: ════════════════════════════════════════════════════════════════════
:: VERIFICAÇÃO DE INTEGRIDADE
:: Antes de qualquer coisa, confirma que o Python embarcado existe.
:: Se não existir, o setup nunca foi executado nesta máquina.
:: ════════════════════════════════════════════════════════════════════
if not exist "%PYTHON_EXE%" (
    echo.
    echo [ERRO] Ambiente nao configurado nesta maquina.
    echo Por favor, execute 'setup_python_embutido.bat' como Administrador.
    echo.
    pause
    exit /b 1
)


:: ════════════════════════════════════════════════════════════════════
:: PRIMEIRA EXECUÇÃO NA MÁQUINA
:: Se a flag local não existe, é a primeira vez nesta máquina.
:: Roda uma verificação rápida das dependências para garantir que
:: tudo está ok antes de abrir a interface para o usuário.
:: Ao final, cria a flag para não repetir nas próximas execuções.
:: ════════════════════════════════════════════════════════════════════
if not exist "%FIRST_RUN_FLAG%" (
    echo [INFO] Primeira execucao nesta maquina. Verificando ambiente...

    "%PYTHON_EXE%" -c "import pandas, openpyxl, playwright" 2>nul
    if !ERRORLEVEL! NEQ 0 (
        echo [INFO] Dependencias ausentes. Instalando...
        "%PYTHON_EXE%" -m pip install -r "%BASE_DIR%requirements.txt" --no-warn-script-location --quiet
    )

    "%PYTHON_EXE%" -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.stop()" 2>nul
    if !ERRORLEVEL! NEQ 0 (
        echo [INFO] Chromium ausente. Instalando...
        "%PYTHON_EXE%" -m playwright install chromium
    )

    :: Cria a pasta e a flag localmente
    if not exist "%FLAG_DIR%" mkdir "%FLAG_DIR%"
    echo. > "%FIRST_RUN_FLAG%"

    echo [INFO] Ambiente verificado com sucesso!
)


:: ════════════════════════════════════════════════════════════════════
:: EXECUÇÃO PRINCIPAL
:: Com tudo verificado, executa o script Python normalmente.
:: O errorlevel ao final captura se o script terminou com erro,
:: mantendo a janela aberta para o usuário conseguir ler a mensagem.
:: ════════════════════════════════════════════════════════════════════
echo [INFO] Iniciando automacao...
"%PYTHON_EXE%" "%MAIN_SCRIPT%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] A automacao terminou com falha. Codigo: %ERRORLEVEL%
    echo Entre em contato com o administrador.
    pause
)
```

---

## Fluxo final resumido
```
Administrador (1x):
└── Roda setup_python_embutido.bat
    ├── Python embarcado → /python_embutido/
    └── Chromium         → /browsers/          ← fica junto no projeto

Distribuição:
└── Cola a pasta inteira no C: de cada máquina via C$

Usuário - 1ª vez na máquina:
└── Clica launcher.bat
    ├── Detecta ausência da flag em %LOCALAPPDATA%
    ├── Faz verificação rápida das deps
    └── Cria flag local e abre a interface

Usuário - demais vezes:
└── Clica → abre direto