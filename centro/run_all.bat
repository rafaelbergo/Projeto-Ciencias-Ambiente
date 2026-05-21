@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   SIMULACAO SUMO - Quadrilatero Central de Curitiba
echo   UTFPR - Ciencias do Ambiente - 2026/1
echo   Rede: OpenStreetMap (map.osm)
echo ============================================================
echo.

REM ===== PASSO 1: Criar pastas =====
echo [PASSO 1/6] Criando pastas de resultados...
if not exist "results" mkdir results
if not exist "output" mkdir output
echo            Pastas criadas.
echo.

REM ===== PASSO 2: Gerar demanda =====
echo [PASSO 2/6] Gerando demanda veicular baseada no projeto...
python gerar_demanda.py
if %ERRORLEVEL% NEQ 0 (
    echo ERRO ao gerar demanda. Abortando.
    pause
    exit /b 1
)
echo.

REM ===== PASSO 3: Rodar simulacao As-Is =====
echo [PASSO 3/6] Executando simulacao As-Is (semáforos fixos)...
echo            Isso pode levar alguns minutos...
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" -c quadrilatero_asis.sumocfg --no-warnings 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo AVISO: Simulacao As-Is concluida com warnings (normal).
)
echo            Simulacao As-Is concluida.
echo.

REM ===== PASSO 4: Rodar simulacao To-Be com controlador =====
echo [PASSO 4/6] Executando simulacao To-Be (controlador adaptativo)...
echo            Iniciando SUMO em modo servidor na porta 8813...

start "SUMO_ToBe" /MIN "C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" -c quadrilatero_tobe.sumocfg --remote-port 8813 --no-warnings

echo            Aguardando SUMO iniciar... (8s)
timeout /t 8 /nobreak >nul

echo            Iniciando controlador adaptativo fuzzy + Onda Verde...
python controlador_adaptativo.py
echo            Simulacao To-Be concluida.
echo.

REM ===== PASSO 5: Comparar resultados =====
echo [PASSO 5/6] Analisando e comparando resultados...
python comparar_simulacoes.py
echo.

REM ===== PASSO 6: Resumo =====
echo [PASSO 6/6] Limpando arquivos temporarios...
del quadrilatero.rou.alt.xml 2>nul
echo.

echo ============================================================
echo   SIMULACAO CONCLUIDA!
echo.
echo   Resultados:
echo     - results/tripinfo_asis.xml   (dados de viagem As-Is)
echo     - results/tripinfo_tobe.xml   (dados de viagem To-Be)
echo     - results/emissions_asis.xml  (emissoes As-Is)
echo     - results/emissions_tobe.xml  (emissoes To-Be)
echo     - output/comparativo_trafego.png
echo     - output/comparativo_emissoes.png
echo     - output/relatorio_comparativo.md
echo     - output/metricas.json
echo ============================================================
echo.
pause
