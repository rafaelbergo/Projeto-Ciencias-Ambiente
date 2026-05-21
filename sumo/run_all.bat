@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   SIMULACAO SUMO - Quadrilatero Central de Curitiba
echo   UTFPR - Ciencias do Ambiente - 2026/1
echo ============================================================
echo.

REM ===== PASSO 1: Construir a rede =====
echo [PASSO 1/5] Construindo a rede viaria...
call build_net.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERRO ao construir a rede. Abortando.
    pause
    exit /b 1
)
echo.

REM ===== PASSO 2: Criar pasta de resultados =====
echo [PASSO 2/5] Criando pasta de resultados...
if not exist "results" mkdir results
echo.
REM ===== PASSO 2: Criar pasta de resultados =====
echo [PASSO 2/5] Criando pasta de resultados...
if not exist "output" mkdir output

REM ===== PASSO 3: Rodar simulacao As-Is =====
echo [PASSO 3/5] Executando simulacao do cenario As-Is (semafóros fixos)...
echo            Isso pode levar alguns minutos...
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" -c quadrilatero_asis.sumocfg --no-warnings 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo AVISO: Simulacao As-Is concluida com warnings (normal).
)
echo            Simulacao As-Is concluida.
echo.

REM ===== PASSO 4: Rodar simulacao To-Be com controlador adaptativo =====
echo [PASSO 4/5] Executando simulacao do cenario To-Be (controlador adaptativo)...
echo            Iniciando SUMO em modo servidor...

REM Inicia SUMO em background escutando na porta 8813
start "SUMO_ToBe" /MIN "C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" -c quadrilatero_tobe.sumocfg --remote-port 8813 --no-warnings

REM Aguarda o SUMO inicializar
echo            Aguardando SUMO iniciar... (5s)
timeout /t 5 /nobreak >nul

REM Executa o controlador Python
echo            Iniciando controlador adaptativo...
python controlador_adaptativo.py
echo            Simulacao To-Be concluida.
echo.

REM ===== PASSO 5: Analisar resultados =====
echo [PASSO 5/5] Analisando resultados...
python analisar_resultados.py
echo.

echo ============================================================
echo   SIMULACAO CONCLUIDA!
echo.
echo   Resultados gerados em:
echo     - results/tripinfo_asis.xml
echo     - results/tripinfo_tobe.xml
echo     - results/emissions_asis.xml
echo     - results/emissions_tobe.xml
echo     - output/comparativo_trafego.png
echo     - output/comparativo_emissoes.png
echo     - output/relatorio_comparativo.md
echo     - output/metricas.json
echo ============================================================
echo.
pause
