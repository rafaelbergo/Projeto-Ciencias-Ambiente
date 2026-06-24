# Cenário 3 — Onda Verde Adaptativa Sustentável

## Estrutura do Cenário

```
projeto_final/cenario3/
├── map/
│   ├── curitiba_centro.net.xml      — Rede viária (mesma do cenário 2, export.osm)
│   ├── cenario3.rou.xml             — 28.500 veículos (14.250 veh/h)
│   │                                  5 classes: passenger 74%, motorcycle 15%,
│   │                                  bus 6%, truck 4%, bike 1%
│   ├── cenario3.add.xml             — 37 laneAreaDetectors em 12 cruzamentos principais
│   └── cenario3.sumocfg             — Configuração para simulação
├── scripts/
│   ├── gerar_viagens.py             — Geração de rotas e demanda (randomTrips + duarouter)
│   ├── gerar_detectores.py          — Geração de detectores E1 nos cruzamentos
│   └── controle_onda_verde.py       — Controlador TraCI adaptativo + Onda Verde
├── saida/                           — Outputs (tripinfo, summary, queues, emissions, detectores)
└── README.md
```

## Diferenças para o Cenário 2

| Característica | Cenário 2 | Cenário 3 |
|---|---|---|
| Composição | 72/15/6/6/1 | 74/15/6/4/1 |
| Controlo | Adaptativo por fila | Adaptativo + Onda Verde |
| Prioridade ônibus | Não | Sim (+8s verde, antecipação 5s) |
| Verde mínimo | 20s | 18s |
| Verde máximo | 70s | 75s |
| Recalcular offsets | — | A cada 180s |

## Testes Realizados

**SUMO standalone:** 1576 veículos inseridos em 600s, 1361 em circulação, velocidade média 18.6 km/h.

**TraCI:** controlador com decisão local a cada 15s e Onda Verde a cada 180s.

## Como Executar

### Simulação completa

```bash
cd projeto_final\cenario3\map
sumo -c cenario3.sumocfg --no-step-log true --duration-log.statistics true
```

### Com controlador adaptativo + Onda Verde

```bash
cd projeto_final\cenario3
python scripts\controle_onda_verde.py
```
