# Guia Completo: Criando uma Simulação SUMO a partir de um Mapa .osm

## Projeto Ciências do Ambiente - UTFPR 2026/1
## Quadrilátero Central de Curitiba

---

## Pré-requisitos

### 1. Instalar o SUMO

Baixe em: https://sumo.dlr.de/docs/Installing/index.html

Após instalar, configure a variável de ambiente `SUMO_HOME`:
```bash
setx SUMO_HOME "C:\Program Files (x86)\Eclipse\Sumo"
```

Verifique:
```bash
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" --version
```

### 2. Instalar pacotes Python

```bash
pip install pandas matplotlib numpy
```

(Opcional para controlador fuzzy: `pip install scikit-fuzzy`)

---

## Passo 1 — Obter o mapa .osm

Vá em https://www.openstreetmap.org/export e selecione a área desejada, ou use o já existente `map.osm` na pasta `centro/`.

O arquivo deve estar na pasta do projeto.

---

## Passo 2 — Gerar a rede viária (.net.xml)

```bash
cd centro

"C:\Program Files (x86)\Eclipse\Sumo\bin\netconvert.exe" ^
  --osm-files map.osm ^
  --output-file quadrilatero.net.xml ^
  --tls.guess true ^
  --tls.guess.threshold 3 ^
  --geometry.remove ^
  --no-turnarounds true ^
  --proj.utm
```

**O que isso faz:**
- Converte o mapa OSM em uma rede SUMO
- `--tls.guess true`: adivinha onde colocar semáforos (interseções com 3+ vias)
- `--geometry.remove`: simplifica a geometria (reduce nós desnecessários)
- `--no-turnarounds true`: remove retornos
- `--proj.utm`: projeta em coordenadas UTM

**Resultado:** `quadrilatero.net.xml`

---

## Passo 3 — Criar os tipos de veículos e a demanda (.rou.xml)

Crie um arquivo `quadrilatero.rou.xml` com os tipos veiculares e fluxos. Exemplo baseado no projeto:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">

    <!-- Tipos veiculares conforme Tabela do projeto -->
    <vType id="carro_gasolina" accel="2.6" decel="4.5" sigma="0.5"
           length="4.3" minGap="2.5" maxSpeed="16.67" color="0.2,0.2,0.8"/>
    <vType id="carro_etanol"   accel="2.6" decel="4.5" sigma="0.5"
           length="4.3" minGap="2.5" maxSpeed="16.67" color="0.1,0.7,0.1"/>
    <vType id="moto"           accel="3.5" decel="6.0" sigma="0.7"
           length="2.0" minGap="1.5" maxSpeed="18.06" color="0.9,0.3,0.1"/>
    <vType id="onibus"         accel="1.3" decel="3.5" sigma="0.3"
           length="12.0" minGap="3.0" maxSpeed="13.89" color="0.8,0.8,0.0"/>
    <vType id="vuc"            accel="1.5" decel="3.8" sigma="0.4"
           length="7.0" minGap="3.0" maxSpeed="13.89" color="0.5,0.5,0.5"/>

    <!-- Fluxos: from="edge_origem" to="edge_destino" -->
    <!-- Substitua edge_origem e edge_destino pelos IDs reais da sua rede -->
    <flow id="cg1" type="carro_gasolina" from="EDGE_A" to="EDGE_B"
          begin="0" end="3600" vehsPerHour="250" departSpeed="random"/>
    <flow id="ce1" type="carro_etanol"   from="EDGE_A" to="EDGE_B"
          begin="0" end="3600" vehsPerHour="68"  departSpeed="random"/>
    <!-- ... adicionar mais fluxos ... -->

</routes>
```

**Como descobrir os IDs dos edges da sua rede:**

```bash
python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('quadrilatero.net.xml')
root = tree.getroot()
for edge in root.findall('edge'):
    eid = edge.get('id','')
    if not eid.startswith(':'):
        lanes = edge.findall('lane')
        print(f'{eid}: {len(lanes)} lanes, speed={lanes[0].get(\"speed\",\"?\")}')
"
```

**OU** use o script `gerar_demanda.py` que faz isso automaticamente:
```bash
python gerar_demanda.py
```

---

## Passo 4 — Routear a demanda (converter flows em rotas)

Flows com `from`/`to` precisam ser roteados pelo `duarouter`:

```bash
"C:\Program Files (x86)\Eclipse\Sumo\bin\duarouter.exe" ^
  --net-file quadrilatero.net.xml ^
  --route-files quadrilatero.rou.xml ^
  --output-file quadrilatero.rou.xml ^
  --ignore-errors ^
  --no-warnings ^
  --routing-threads 6
```

**Resultado:** `quadrilatero.rou.xml` agora contém rotas completas (sequências de edges).

---

## Passo 5 — Criar as configurações de simulação (.sumocfg)

### Cenário As-Is (linha de base — semáforos fixos)

Arquivo `quadrilatero_asis.sumocfg`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="quadrilatero.net.xml"/>
        <route-files value="quadrilatero.rou.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="3600"/>
    </time>
    <processing>
        <step-length value="0.1"/>
        <time-to-teleport value="-1"/>
        <ignore-route-errors value="true"/>
    </processing>
    <output>
        <tripinfo-output value="results/tripinfo_asis.xml"/>
        <tripinfo-output.write-unfinished value="true"/>
        <emission-output value="results/emissions_asis.xml"/>
        <emission-output.precision value="4"/>
    </output>
    <report>
        <verbose value="false"/>
        <no-step-log value="true"/>
        <duration-log.disable value="true"/>
    </report>
    <random>
        <seed value="42"/>
    </random>
</configuration>
```

### Cenário To-Be (com otimizações)

Arquivo `quadrilatero_tobe.sumocfg`: **idêntico ao As-Is**, exceto:
- `<net-file value="quadrilatero_tobe.net.xml"/>` (rede com semáforos otimizados)
- `<tripinfo-output value="results/tripinfo_tobe.xml"/>`
- `<emission-output value="results/emissions_tobe.xml"/>`

---

## Passo 6 — Otimizar a rede para o cenário To-Be

Crie um script `otimizar_rede.py` que ajusta os tempos semafóricos:

```python
import xml.etree.ElementTree as ET

tree = ET.parse('quadrilatero.net.xml')
root = tree.getroot()

GREEN_TIME = 35  # tempo verde otimizado

for tl in root.findall('.//tlLogic'):
    for phase in tl.findall('phase'):
        state = phase.get('state', '')
        if 'G' in state or 'g' in state:
            phase.set('duration', str(GREEN_TIME))

tree.write('quadrilatero_tobe.net.xml', encoding='UTF-8', xml_declaration=True)
print("Rede otimizada salva!")
```

Execute:
```bash
python otimizar_rede.py
```

---

## Passo 7 — Executar as simulações

### Criar pasta de resultados:
```bash
mkdir results output
```

### Rodar As-Is:
```bash
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" -c quadrilatero_asis.sumocfg --no-warnings --duration-log.disable
```

### Rodar To-Be:
```bash
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" -c quadrilatero_tobe.sumocfg --no-warnings --duration-log.disable
```

---

## Passo 8 — Comparar os resultados

Crie um script `comparar_simulacoes.py` (use o já existente na pasta `centro/` como referência) ou copie-o:

```bash
python comparar_simulacoes.py
```

**Resultados gerados em `output/`:**
- `comparativo_trafego.png` — Gráfico comparativo de tráfego
- `comparativo_emissoes.png` — Gráfico comparativo de emissões
- `relatorio_comparativo.md` — Relatório com tabelas
- `metricas.json` — Métricas em JSON

---

## Passo 9 — (Opcional) Controlador adaptativo com TraCI

Para controle em tempo real com lógica fuzzy (como o projeto especifica):

**Terminal 1:**
```bash
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe" -c quadrilatero_tobe.sumocfg --remote-port 8813 --no-warnings --duration-log.disable
```

**Terminal 2:**
```bash
python controlador_adaptativo.py
```

O controlador conecta na porta 8813 e ajusta os tempos semafóricos dinamicamente com base em filas e ocupação.

---

## Resumo da estrutura final de arquivos

```
minha_simulacao/
├── map.osm                      # Mapa baixado do OpenStreetMap
├── quadrilatero.net.xml         # Rede gerada (Passo 2)
├── quadrilatero.rou.xml         # Rotas e demanda (Passos 3-4)
├── quadrilatero_asis.sumocfg    # Config As-Is (Passo 5)
├── quadrilatero_tobe.sumocfg    # Config To-Be (Passo 5)
├── quadrilatero_tobe.net.xml    # Rede otimizada (Passo 6)
├── gerar_demanda.py             # Gera demanda (Passo 3)
├── otimizar_rede.py             # Otimiza semáforos (Passo 6)
├── comparar_simulacoes.py       # Compara resultados (Passo 8)
├── controlador_adaptativo.py    # Controlador fuzzy (Passo 9)
├── results/                     # Saídas XML das simulações
│   ├── tripinfo_asis.xml
│   ├── tripinfo_tobe.xml
│   ├── emissions_asis.xml
│   └── emissions_tobe.xml
└── output/                      # Gráficos e relatórios
    ├── comparativo_trafego.png
    ├── comparativo_emissoes.png
    ├── relatorio_comparativo.md
    └── metricas.json
```

---

## Checklist rápido

- [ ] Baixar `map.osm` do OpenStreetMap
- [ ] `netconvert` → gera `quadrilatero.net.xml`
- [ ] `gerar_demanda.py` → gera `quadrilatero.rou.xml` com fluxos
- [ ] `duarouter` → roteia os fluxos
- [ ] Criar `quadrilatero_asis.sumocfg` e `quadrilatero_tobe.sumocfg`
- [ ] `otimizar_rede.py` → gera `quadrilatero_tobe.net.xml`
- [ ] Rodar `sumo -c quadrilatero_asis.sumocfg`
- [ ] Rodar `sumo -c quadrilatero_tobe.sumocfg`
- [ ] `python comparar_simulacoes.py`
- [ ] Ver resultados em `output/`

---

## Troubleshooting

| Erro | Solução |
|------|---------|
| `sumo` não encontrado | Use caminho completo: `"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"` |
| `netconvert` falha | Verifique se o `map.osm` é válido (tente abrir no JOSM) |
| `duarouter` não gera rotas | Verifique se os edge IDs no `.rou.xml` existem no `.net.xml` |
| Simulação não termina | Reduza `<end value="3600"/>` para 1800 ou 900 |
| `ParseError` no XML de saída | Delete os arquivos em `results/` e rode novamente |
| `emissionClass not found` | Remova o atributo `emissionClass` dos `<vType>` |
| Semáforos não aparecem | Adicione `--tls.guess true --tls.guess.threshold 2` ao `netconvert` |
