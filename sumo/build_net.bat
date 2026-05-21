@echo off
echo ============================================================
echo  Construindo rede viaria do Quadrilatero Central de Curitiba
echo ============================================================

REM Gera o .net.xml a partir dos arquivos .nod.xml e .edg.xml
"C:\Program Files (x86)\Eclipse\Sumo\bin\netconvert.exe" ^
  --node-files=quadrilatero.nod.xml ^
  --edge-files=quadrilatero.edg.xml ^
  --type-files=quadrilatero.typ.xml ^
  --output-file=quadrilatero.net.xml ^
  --tls.guess=true ^
  --tls.guess.threshold=3 ^
  --tls.green.time=25 ^
  --tls.yellow.time=3 ^
  --tls.red-red.time=2 ^
  --tls.minor-left.max-speed=5.56 ^
  --roundabouts.guess=true ^
  --no-internal-links=false ^
  --no-turnarounds=true ^
  --geometry.remove ^
  --ramps.guess=false

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: Falha ao gerar a rede. Verifique se o SUMO esta instalado.
    pause
    exit /b 1
)

echo.
echo Rede gerada com sucesso: quadrilatero.net.xml
echo.
echo Para rodar a simulacao:
echo   sumo-gui -c quadrilatero.sumocfg
echo.
pause
