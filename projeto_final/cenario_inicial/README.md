# Cenário As-Is — Situação Atual (Semáforos Fixos)

## Estrutura do Cenário

```
projeto_final/cenario_inicial/
├── map/
│   ├── curitiba_centro.net.xml      — Rede viária (mesma dos cenários 2 e 3)
│   ├── cenario_inicial.rou.xml      — 28.500 veículos (14.250 veh/h)
│   │                                  5 classes: passenger 72%, motorcycle 15%,
│   │                                  bus 6%, truck 6%, bike 1%
│   └── cenario_inicial.sumocfg      — Configuração para simulação
├── scripts/
│   └── gerar_viagens.py             — Geração de rotas e demanda (randomTrips + duarouter)
├── saida/                           — Outputs (tripinfo, summary, queues, emissions)
└── README.md
```

## Características

**Sem controlo adaptativo** — os semáforos usam os planos fixos importados do OSM, representando a situação atual do trânsito no quadrilátero central de Curitiba.

| Parâmetro | Valor |
|---|---|
| Período simulado | Pico da tarde (17h-19h) |
| Duração | 7.200 s (2h) |
| Demanda total | 14.250 veh/h |
| Composição | 72/15/6/6/1 (passenger/motorcycle/bus/truck/bike) |
| Semáforos | Fixos (importados do OSM) |
| Controlo adaptativo | Não |
| Detetores | Não |

## Testes Realizados

**SUMO standalone:** 1702 veículos inseridos em 600s, 1425 em circulação, velocidade média 18.3 km/h (dentro dos 15-18 km/h esperados).

## Como Executar

```bash
cd projeto_final\cenario_inicial\map
sumo -c cenario_inicial.sumocfg --no-step-log true --duration-log.statistics true
```

Para simulação completa (7200s), alterar `end` no sumocfg:

```xml
<end value="7200"/>
```

## Comparação com os outros cenários

| Cenário | Controlo | Composição | Descrição |
|---|---|---|---|
| As-Is | Fixo (OSM) | 72/15/6/6/1 | Situação atual |
| Cenário 2 | Adaptativo por fila | 72/15/6/6/1 | Intervenção intermédia |
| Cenário 3 | Onda Verde + prioridade ônibus | 74/15/6/4/1 | Proposta principal |
