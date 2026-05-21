# Guia de Execucao - Simulacoes SUMO

## Projeto Ciencias do Ambiente - UTFPR 2026/1
## Quadrilatero Central de Curitiba

---

## Pasta `centro/` - Simulacao com mapa OSM real

### Pre-requisitos
- SUMO instalado em `C:\Program Files (x86)\Eclipse\Sumo\`
- Python 3.11+ com pacotes: `pip install pandas matplotlib numpy`

### Passo a passo

#### 1. Gerar demanda e rodar simulacoes

```bash
cd centro
run_all.bat
```

**Ou manualmente:**

```bash
cd centro

# 1. Criar pastas
mkdir results output

# 2. Gerar demanda veicular (baseada no projeto - 459 veh/h, composicao da frota conforme PDF)
python gerar_demanda.py

# 3. Routear com duarouter
"C:\Program Files (x86)\Eclipse\Sumo\bin\duarouter.exe" --net-file quadrilatero.net.xml --route-files quadrilatero.rou.xml --output-file quadrilatero.rou.xml --ignore-errors --no-warnings --routing-threads 6

# 4. Rodar simulacao As-Is (semáforos fixos - cenario base)
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" -c quadrilatero_asis.sumocfg --no-warnings --duration-log.disable

# 5. Gerar rede otimizada para To-Be (tempos verdes ajustados)
python otimizar_rede.py

# 6. Rodar simulacao To-Be (semáforos otimizados)
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" -c quadrilatero_tobe.sumocfg --no-warnings --duration-log.disable

# 7. Comparar resultados
python comparar_simulacoes.py
```

### Resultados em `centro/output/`:
- `comparativo_trafego.png` - Grafico de barras: tempo de viagem, velocidade, espera
- `comparativo_emissoes.png` - Grafico de barras: CO2, NOx, PMx, combustivel
- `relatorio_comparativo.md` - Relatorio com tabelas
- `metricas.json` - Metricas em JSON

---

## Pasta `sumo/` - Simulacao com rede manual simplificada + controlador adaptativo fuzzy

### Pre-requisitos adicionais
- `pip install scikit-fuzzy` (opcional, fallback linear se nao instalar)

### Passo a passo

#### Opcao A: Script automatizado

```bash
cd sumo
run_all.bat
```

#### Opcao B: Manual (2 terminais necessarios)

**Terminal 1 - Iniciar SUMO como servidor:**
```bash
cd sumo
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" -c quadrilatero_tobe.sumocfg --remote-port 8813 --no-warnings --duration-log.disable
```

**Terminal 2 - Executar controlador:**
```bash
cd sumo
python controlador_adaptativo.py
```

> O controlador conecta automaticamente na porta 8813 e ajusta os tempos semaforicos em tempo real.

#### Apos as simulacoes, comparar:

```bash
cd sumo
python analisar_resultados.py
```

### Resultados em `sumo/output/`:
- `comparativo_trafego.png`
- `comparativo_emissoes.png`
- `relatorio_comparativo.md`
- `metricas.json`

---

## Estrutura do Projeto

```
CA/
├── centro/                         # Simulacao com mapa OSM real
│   ├── map.osm                     # Mapa do OpenStreetMap (quadrilatero central)
│   ├── quadrilatero.net.xml        # Rede viaria gerada
│   ├── quadrilatero_asis.sumocfg   # Config: cenario As-Is
│   ├── quadrilatero_tobe.sumocfg   # Config: cenario To-Be
│   ├── quadrilatero_tobe.net.xml   # Rede otimizada para To-Be
│   ├── gerar_demanda.py            # Gera demanda veicular baseada no projeto
│   ├── otimizar_rede.py            # Otimiza tempos semaforicos
│   ├── comparar_simulacoes.py      # Script de comparacao
│   ├── run_all.bat                 # Script automatizado
│   ├── results/                    # Saidas das simulacoes
│   └── output/                     # Graficos e relatorios
│
├── sumo/                           # Simulacao com rede manual + controlador fuzzy
│   ├── quadrilatero.nod.xml        # Nos da rede
│   ├── quadrilatero.edg.xml        # Arestas da rede
│   ├── quadrilatero.typ.xml        # Tipos de via
│   ├── quadrilatero.rou.xml        # Rotas e fluxos (baseados em VPD real)
│   ├── quadrilatero_asis.sumocfg   # Config: cenario As-Is
│   ├── quadrilatero_tobe.sumocfg   # Config: cenario To-Be
│   ├── controlador_adaptativo.py   # Controlador fuzzy + TraCI
│   ├── analisar_resultados.py      # Script de comparacao
│   ├── run_all.bat                 # Script automatizado
│   ├── build_net.bat               # Gera a rede
│   ├── results/                    # Saidas das simulacoes
│   └── output/                     # Graficos e relatorios
│
├── projeto_ca_2026.tex             # Documento LaTeX do projeto
└── Projeto 1 CA 2026_1.pdf         # PDF do projeto
```

---

## Diferenca entre os cenarios

| Aspecto | As-Is | To-Be (centro/) | To-Be (sumo/) |
|---------|-------|-----------------|---------------|
| Semaforos | Tempos fixos (~31s) | Tempos otimizados (35s) | Controlador fuzzy adaptativo |
| Sincronizacao | Nenhuma | Nenhuma (offsets mantidos) | Fuzzy: fila + ocupacao → ajuste dinamico 15-60s |
| Rede | OSM real (2466 edges) | OSM real | Manual simplificada |
| Demanda | 459 veh/h, 5 tipos | 459 veh/h, 5 tipos | Fluxos por via (VPD URBS) |

---

## Troubleshooting

| Erro | Solucao |
|------|---------|
| `sumo` nao encontrado | Verifique PATH ou use caminho completo |
| `ImportError: traci` | `pip install sumo` |
| Porta 8813 em uso | `netstat -ano | findstr 8813` → `taskkill /PID <PID>` |
| `emissionClass not found` | Remova atributo `emissionClass` dos vType |
| Simulacao muito lenta | Use `sumo` (CLI) em vez de `sumo-gui` |
| `duarouter` falha | Verifique se os edges existem no .net.xml |
