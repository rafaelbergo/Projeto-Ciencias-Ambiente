# Cenário 2 - Simulação SUMO (Quadrilátero Central de Curitiba)

## Estrutura do Cenário

```
projeto_final/cenario2/
├── map/
│   ├── curitiba_centro.net.xml   — Rede viária gerada do OSM grande (projeto_final/),
│   │                                recortada ao quadrilátero central
│   │                                (13.850 edges, 1.489 semáforos)
│   ├── cenario2.rou.xml           — 28.500 veículos (14.250 veh/h)
│   │                                5 classes: passenger 72%, motorcycle 15%,
│   │                                bus 6%, truck 6%, bike 1%
│   ├── cenario2.add.xml           — 59 laneAreaDetectors em 15 cruzamentos principais
│   └── cenario2.sumocfg           — Configuração para simulação
├── scripts/
│   ├── gerar_viagens.py           — Geração de rotas e demanda
│   ├── gerar_detectores.py        — Geração de detectores E1 nos cruzamentos
│   └── controle_adaptativo_fila.py — Controlador adaptativo TraCI (ajusta verde por fila)
├── saida/                         — Outputs (tripinfo, summary, emissions, queues, detectores)
└── README.md
```

## Testes Realizados

**SUMO standalone:** 1934 veículos inseridos em 600s, 1642 em circulação, velocidade média 14.8 km/h, sem erros.

**TraCI:** controlador conecta e executa passo a passo com ajuste de semáforos.

## Como Executar

### Simulação completa (7200s)
Alterar `end` no `cenario2.sumocfg` para 7200 e executar:

```bash
cd projeto_final\cenario2\map
sumo -c cenario2.sumocfg --no-step-log true --duration-log.statistics true
```

### Com controlador adaptativo

```bash
cd projeto_final\cenario2
python scripts\controle_adaptativo_fila.py
```
