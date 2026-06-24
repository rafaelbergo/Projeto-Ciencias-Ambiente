# Fase 1 — Diagnóstico Estimado para Simulação no SUMO  
## Mobilidade Urbana e Sustentabilidade no Centro de Curitiba

**Projeto:** Mobilidade Urbana e Sustentabilidade no Centro de Curitiba  
**Unidade Curricular:** Ciências do Ambiente  
**Área de estudo:** Quadrilátero Central / Setor Especial Estrutural — Curitiba, PR  
**Objetivo da Fase 1:** levantar e estimar dados de tráfego, gargalos, obstáculos e ruído para criar o cenário-base `As-Is` em simulação SUMO.

> **Observação metodológica:**  
> Como não foi possível realizar medições em campo, esta Fase 1 usa **dados públicos, estudos similares e estimativas técnicas** para construir uma base defensável de simulação. Os valores abaixo não devem ser apresentados como contagens reais, mas como **estimativas calibradas para modelagem computacional**.

---

## 1. Fontes e bases usadas

| Fonte | Uso no projeto |
|---|---|
| TomTom Traffic Index 2025 — Curitiba | Velocidade média, tempo de viagem e congestionamento nos horários de pico. |
| SENATRAN 2026 | Frota municipal por tipo de veículo e combustível. |
| Dados locais baseados em Detran-PR | Estimativa de frota total de Curitiba em 2026. |
| IPPUC — Contagem de Tráfego Georreferenciada | Referência metodológica para contagens em intervalos de 15 minutos e composição veicular. |
| URBS / Dados Abertos Curitiba | Linhas, pontos, itinerários e horários do transporte coletivo. |
| Central 156 / SIAC | Reclamações urbanas relacionadas a trânsito, ruído, calçadas, carga e descarga. |
| Estudos de ruído urbano no Centro de Curitiba | Estimativa de níveis de pressão sonora em vias centrais. |
| ABNT NBR 10151:2019 | Referência para avaliação de ruído ambiental em áreas habitadas. |

---

## 2. Dados urbanos gerais usados como calibração

| Indicador | Valor adotado |
|---|---:|
| Congestionamento médio em Curitiba | 54% |
| Velocidade média nos horários de pico | 16,3 km/h |
| Velocidade média no pico da manhã | 17,8 km/h |
| Velocidade média no pico da tarde | 15,1 km/h |
| Tempo médio para 10 km no pico da manhã | 33 min 42 s |
| Tempo médio para 10 km no pico da tarde | 39 min 44 s |
| Frota estimada de Curitiba em janeiro de 2026 | 1.815.014 veículos |
| Automóveis estimados | 1.087.054 |
| Motocicletas estimadas | 289.863 |

---

## 3. Premissas gerais para simulação

| Parâmetro | Valor adotado | Uso no SUMO |
|---|---:|---|
| Fator de hora-pico sobre VPD | 10% | Converter VPD em veículos/hora |
| Pico da tarde | 100% do pico estimado | Cenário crítico principal |
| Pico da manhã | 80% a 90% do pico da tarde | Cenário secundário |
| Fator de hora-pico, FHP | 0,85 | Estimar concentração em 15 minutos |
| Velocidade livre em vias principais | 40 km/h | `speed="11.11"` em m/s |
| Velocidade média no pico | 15 a 18 km/h | Calibração do cenário congestionado |
| Tempo de simulação recomendado | 2 horas | Janela crítica do pico da tarde |
| Horário simulado recomendado | 17h00–19h00 | Pico mais crítico |

### Fórmulas adotadas

```text
VHP = VPD × 0,10
```

```text
Volume máximo em 15 min = VHP / 4 / FHP
```

Com `FHP = 0,85`:

```text
Volume máximo em 15 min ≈ VHP / 3,4
```

---

## 4. Vias e demanda estimada

Os trechos abaixo representam os principais eixos do quadrilátero central considerado no projeto.

| ID SUMO sugerido | Trecho | Função viária | VPD estimado | Pico manhã estimado | Pico tarde estimado | Volume máx. 15 min no pico tarde |
|---|---|---|---:|---:|---:|---:|
| `pres_kennedy` | Av. Pres. Kennedy | Arterial de entrada/saída | 38.000–52.000 veh/dia | 3.200–4.500 veh/h | 3.800–5.200 veh/h | 1.120–1.530 veh/15min |
| `mal_floriano` | Mal. Floriano Peixoto | Eixo central com ônibus e pedestres | 24.000–34.000 veh/dia | 2.000–2.900 veh/h | 2.400–3.400 veh/h | 705–1.000 veh/15min |
| `mariano_torres` | Mariano Torres | Corredor de ligação central | 22.000–32.000 veh/dia | 1.900–2.700 veh/h | 2.200–3.200 veh/h | 650–940 veh/15min |
| `mario_tourinho` | Mário Tourinho | Via de borda/distribuição | 18.000–28.000 veh/dia | 1.500–2.400 veh/h | 1.800–2.800 veh/h | 530–825 veh/15min |
| `martim_afonso` | Martim Afonso | Coletora/ligação | 12.000–20.000 veh/dia | 1.000–1.700 veh/h | 1.200–2.000 veh/h | 350–590 veh/15min |
| `calcadao_xv_acessos` | Acessos ao Calçadão da XV | Tráfego restrito/serviço | 1.000–4.000 veh/dia | 80–250 veh/h | 100–400 veh/h | 30–120 veh/15min |

---

## 5. Valores centrais recomendados para o cenário-base

Para montar o primeiro cenário `As-Is`, recomenda-se usar o valor médio de cada faixa.

| ID SUMO sugerido | VPD médio | Pico manhã médio | Pico tarde médio |
|---|---:|---:|---:|
| `pres_kennedy` | 45.000 veh/dia | 3.850 veh/h | 4.500 veh/h |
| `mal_floriano` | 29.000 veh/dia | 2.450 veh/h | 2.900 veh/h |
| `mariano_torres` | 27.000 veh/dia | 2.300 veh/h | 2.700 veh/h |
| `mario_tourinho` | 23.000 veh/dia | 1.950 veh/h | 2.300 veh/h |
| `martim_afonso` | 16.000 veh/dia | 1.350 veh/h | 1.600 veh/h |
| `calcadao_xv_acessos` | 2.500 veh/dia | 165 veh/h | 250 veh/h |

### Demanda total estimada

```text
VPD total estimado nos principais trechos = 115.000 a 170.000 passagens/dia
Pico tarde total estimado = 11.500 a 17.000 veículos/h
Pico tarde médio adotado = aproximadamente 14.250 veículos/h
```

> Atenção: o total representa **passagens veiculares por trecho**, não veículos únicos. Um mesmo veículo pode atravessar mais de um trecho do quadrilátero.

---

## 6. Composição veicular adotada

| Classe | Percentual mínimo | Percentual máximo | Percentual central adotado |
|---|---:|---:|---:|
| Veículos leves | 68% | 76% | 72% |
| Motocicletas | 12% | 18% | 15% |
| Ônibus | 4% | 8% | 6% |
| Carga urbana / VUC / caminhões | 4% | 7% | 6% |
| Bicicletas / e-bikes | 0,5% | 2% | 1% |

Para simplificar a primeira simulação no SUMO, usar quatro classes motorizadas principais:

```text
passenger = 72%
motorcycle = 15%
bus = 6%
truck = 6%
bike = 1%
```

---

## 7. Tipos de veículos sugeridos para o SUMO

Exemplo de definição para arquivo `.rou.xml`:

```xml
<vType id="passenger" vClass="passenger" accel="2.6" decel="4.5" sigma="0.5" length="4.5" minGap="2.5" maxSpeed="13.89" guiShape="passenger"/>
<vType id="motorcycle" vClass="motorcycle" accel="3.5" decel="5.0" sigma="0.7" length="2.2" minGap="1.0" maxSpeed="13.89" guiShape="motorcycle"/>
<vType id="bus" vClass="bus" accel="1.2" decel="4.0" sigma="0.5" length="12.0" minGap="3.0" maxSpeed="11.11" guiShape="bus"/>
<vType id="truck" vClass="truck" accel="1.0" decel="3.5" sigma="0.6" length="8.0" minGap="3.0" maxSpeed="11.11" guiShape="truck"/>
<vType id="bike" vClass="bicycle" accel="1.2" decel="3.0" sigma="0.8" length="1.8" minGap="1.0" maxSpeed="6.94" guiShape="bicycle"/>
```

### Conversão de velocidades

| Velocidade | m/s |
|---:|---:|
| 25 km/h | 6,94 m/s |
| 40 km/h | 11,11 m/s |
| 50 km/h | 13,89 m/s |

---

## 8. Demanda horária por classe no pico da tarde

Valores calculados com base no pico tarde médio.

### Av. Pres. Kennedy — `pres_kennedy`

| Classe | Percentual | Fluxo estimado |
|---|---:|---:|
| Veículos leves | 72% | 3.240 veh/h |
| Motocicletas | 15% | 675 veh/h |
| Ônibus | 6% | 270 veh/h |
| Carga urbana | 6% | 270 veh/h |
| Bicicletas | 1% | 45 veh/h |
| **Total** | **100%** | **4.500 veh/h** |

### Mal. Floriano Peixoto — `mal_floriano`

| Classe | Percentual | Fluxo estimado |
|---|---:|---:|
| Veículos leves | 72% | 2.088 veh/h |
| Motocicletas | 15% | 435 veh/h |
| Ônibus | 6% | 174 veh/h |
| Carga urbana | 6% | 174 veh/h |
| Bicicletas | 1% | 29 veh/h |
| **Total** | **100%** | **2.900 veh/h** |

### Mariano Torres — `mariano_torres`

| Classe | Percentual | Fluxo estimado |
|---|---:|---:|
| Veículos leves | 72% | 1.944 veh/h |
| Motocicletas | 15% | 405 veh/h |
| Ônibus | 6% | 162 veh/h |
| Carga urbana | 6% | 162 veh/h |
| Bicicletas | 1% | 27 veh/h |
| **Total** | **100%** | **2.700 veh/h** |

### Mário Tourinho — `mario_tourinho`

| Classe | Percentual | Fluxo estimado |
|---|---:|---:|
| Veículos leves | 72% | 1.656 veh/h |
| Motocicletas | 15% | 345 veh/h |
| Ônibus | 6% | 138 veh/h |
| Carga urbana | 6% | 138 veh/h |
| Bicicletas | 1% | 23 veh/h |
| **Total** | **100%** | **2.300 veh/h** |

### Martim Afonso — `martim_afonso`

| Classe | Percentual | Fluxo estimado |
|---|---:|---:|
| Veículos leves | 72% | 1.152 veh/h |
| Motocicletas | 15% | 240 veh/h |
| Ônibus | 6% | 96 veh/h |
| Carga urbana | 6% | 96 veh/h |
| Bicicletas | 1% | 16 veh/h |
| **Total** | **100%** | **1.600 veh/h** |

### Acessos ao Calçadão da XV — `calcadao_xv_acessos`

| Classe | Percentual | Fluxo estimado |
|---|---:|---:|
| Veículos leves | 72% | 180 veh/h |
| Motocicletas | 15% | 38 veh/h |
| Ônibus | 6% | 15 veh/h |
| Carga urbana | 6% | 15 veh/h |
| Bicicletas | 1% | 2 veh/h |
| **Total** | **100%** | **250 veh/h** |

---

## 9. Exemplo de fluxo SUMO para cenário de pico da tarde

O exemplo abaixo usa `begin="0"` e `end="7200"`, representando 2 horas de simulação.

> No SUMO, `vehsPerHour` representa demanda por hora.  
> Caso o fluxo esteja muito alto para a rede importada do OSM, testar fatores de escala: `0.75`, `0.50` ou `0.35`.

```xml
<routes>
    <vType id="passenger" vClass="passenger" accel="2.6" decel="4.5" sigma="0.5" length="4.5" minGap="2.5" maxSpeed="13.89"/>
    <vType id="motorcycle" vClass="motorcycle" accel="3.5" decel="5.0" sigma="0.7" length="2.2" minGap="1.0" maxSpeed="13.89"/>
    <vType id="bus" vClass="bus" accel="1.2" decel="4.0" sigma="0.5" length="12.0" minGap="3.0" maxSpeed="11.11"/>
    <vType id="truck" vClass="truck" accel="1.0" decel="3.5" sigma="0.6" length="8.0" minGap="3.0" maxSpeed="11.11"/>
    <vType id="bike" vClass="bicycle" accel="1.2" decel="3.0" sigma="0.8" length="1.8" minGap="1.0" maxSpeed="6.94"/>

    <!-- Rotas devem ser substituídas pelos IDs reais das edges importadas do OpenStreetMap. -->
    <route id="r_pres_kennedy" edges="EDGE_ORIGEM_KENNEDY EDGE_DESTINO_KENNEDY"/>
    <route id="r_mal_floriano" edges="EDGE_ORIGEM_FLORIANO EDGE_DESTINO_FLORIANO"/>
    <route id="r_mariano_torres" edges="EDGE_ORIGEM_MARIANO EDGE_DESTINO_MARIANO"/>
    <route id="r_mario_tourinho" edges="EDGE_ORIGEM_TOURINHO EDGE_DESTINO_TOURINHO"/>
    <route id="r_martim_afonso" edges="EDGE_ORIGEM_AFONSO EDGE_DESTINO_AFONSO"/>
    <route id="r_calcadao_xv" edges="EDGE_ORIGEM_CALCADAO EDGE_DESTINO_CALCADAO"/>

    <!-- Av. Pres. Kennedy -->
    <flow id="f_pres_kennedy_car" type="passenger" route="r_pres_kennedy" begin="0" end="7200" vehsPerHour="3240"/>
    <flow id="f_pres_kennedy_moto" type="motorcycle" route="r_pres_kennedy" begin="0" end="7200" vehsPerHour="675"/>
    <flow id="f_pres_kennedy_bus" type="bus" route="r_pres_kennedy" begin="0" end="7200" vehsPerHour="270"/>
    <flow id="f_pres_kennedy_truck" type="truck" route="r_pres_kennedy" begin="0" end="7200" vehsPerHour="270"/>
    <flow id="f_pres_kennedy_bike" type="bike" route="r_pres_kennedy" begin="0" end="7200" vehsPerHour="45"/>

    <!-- Mal. Floriano Peixoto -->
    <flow id="f_mal_floriano_car" type="passenger" route="r_mal_floriano" begin="0" end="7200" vehsPerHour="2088"/>
    <flow id="f_mal_floriano_moto" type="motorcycle" route="r_mal_floriano" begin="0" end="7200" vehsPerHour="435"/>
    <flow id="f_mal_floriano_bus" type="bus" route="r_mal_floriano" begin="0" end="7200" vehsPerHour="174"/>
    <flow id="f_mal_floriano_truck" type="truck" route="r_mal_floriano" begin="0" end="7200" vehsPerHour="174"/>
    <flow id="f_mal_floriano_bike" type="bike" route="r_mal_floriano" begin="0" end="7200" vehsPerHour="29"/>

    <!-- Mariano Torres -->
    <flow id="f_mariano_torres_car" type="passenger" route="r_mariano_torres" begin="0" end="7200" vehsPerHour="1944"/>
    <flow id="f_mariano_torres_moto" type="motorcycle" route="r_mariano_torres" begin="0" end="7200" vehsPerHour="405"/>
    <flow id="f_mariano_torres_bus" type="bus" route="r_mariano_torres" begin="0" end="7200" vehsPerHour="162"/>
    <flow id="f_mariano_torres_truck" type="truck" route="r_mariano_torres" begin="0" end="7200" vehsPerHour="162"/>
    <flow id="f_mariano_torres_bike" type="bike" route="r_mariano_torres" begin="0" end="7200" vehsPerHour="27"/>

    <!-- Mário Tourinho -->
    <flow id="f_mario_tourinho_car" type="passenger" route="r_mario_tourinho" begin="0" end="7200" vehsPerHour="1656"/>
    <flow id="f_mario_tourinho_moto" type="motorcycle" route="r_mario_tourinho" begin="0" end="7200" vehsPerHour="345"/>
    <flow id="f_mario_tourinho_bus" type="bus" route="r_mario_tourinho" begin="0" end="7200" vehsPerHour="138"/>
    <flow id="f_mario_tourinho_truck" type="truck" route="r_mario_tourinho" begin="0" end="7200" vehsPerHour="138"/>
    <flow id="f_mario_tourinho_bike" type="bike" route="r_mario_tourinho" begin="0" end="7200" vehsPerHour="23"/>

    <!-- Martim Afonso -->
    <flow id="f_martim_afonso_car" type="passenger" route="r_martim_afonso" begin="0" end="7200" vehsPerHour="1152"/>
    <flow id="f_martim_afonso_moto" type="motorcycle" route="r_martim_afonso" begin="0" end="7200" vehsPerHour="240"/>
    <flow id="f_martim_afonso_bus" type="bus" route="r_martim_afonso" begin="0" end="7200" vehsPerHour="96"/>
    <flow id="f_martim_afonso_truck" type="truck" route="r_martim_afonso" begin="0" end="7200" vehsPerHour="96"/>
    <flow id="f_martim_afonso_bike" type="bike" route="r_martim_afonso" begin="0" end="7200" vehsPerHour="16"/>

    <!-- Acessos ao Calçadão da XV -->
    <flow id="f_calcadao_car" type="passenger" route="r_calcadao_xv" begin="0" end="7200" vehsPerHour="180"/>
    <flow id="f_calcadao_moto" type="motorcycle" route="r_calcadao_xv" begin="0" end="7200" vehsPerHour="38"/>
    <flow id="f_calcadao_bus" type="bus" route="r_calcadao_xv" begin="0" end="7200" vehsPerHour="15"/>
    <flow id="f_calcadao_truck" type="truck" route="r_calcadao_xv" begin="0" end="7200" vehsPerHour="15"/>
    <flow id="f_calcadao_bike" type="bike" route="r_calcadao_xv" begin="0" end="7200" vehsPerHour="2"/>
</routes>
```

---

## 10. Gargalos estimados para representar no SUMO

| Ponto crítico | Tipo de problema | Como representar no SUMO |
|---|---|---|
| Av. Pres. Kennedy | Saturação de fluxo e filas semafóricas | Aumentar fluxo de entrada e configurar semáforos com ciclos conservadores. |
| Mal. Floriano Peixoto | Conflito entre ônibus, automóveis e pedestres | Incluir ônibus, paradas e travessias; reduzir velocidade em aproximações. |
| Mariano Torres | Retenção em cruzamentos semafóricos | Criar TLS com fases fixas e observar filas. |
| Acessos ao Calçadão da XV | Conflito pedestre–veículo e carga/descarga | Criar fluxo baixo de veículos, alto fluxo de pedestres e parada de carga urbana. |
| Martim Afonso | Perda de capacidade por estacionamento/conversões | Reduzir número de faixas efetivas ou velocidade. |
| Mário Tourinho | Fluxo de distribuição e retenção em cruzamentos | Usar demanda média e TLS nas interseções principais. |

---

## 11. Parâmetros de ruído para diagnóstico ambiental

| Trecho/ponto | LAeq estimado manhã | LAeq estimado tarde | Classificação |
|---|---:|---:|---|
| Av. Pres. Kennedy | 76–82 dB(A) | 78–84 dB(A) | Crítico |
| Mal. Floriano Peixoto | 78–84 dB(A) | 80–86 dB(A) | Muito crítico |
| Mariano Torres | 77–83 dB(A) | 79–85 dB(A) | Crítico |
| Mário Tourinho | 74–80 dB(A) | 76–82 dB(A) | Alto |
| Martim Afonso | 72–78 dB(A) | 74–80 dB(A) | Alto |
| Acessos ao Calçadão da XV | 64–72 dB(A) | 66–76 dB(A) | Moderado a alto |

Valores de referência para o relatório:

```text
Ruído médio em vias críticas = 78 a 86 dB(A)
Ruído médio em área de pedestres = 66 a 76 dB(A)
Valor de referência para vias críticas na simulação ambiental = 80 dB(A)
Valor de referência para acessos ao Calçadão da XV = 70 dB(A)
```

---

## 12. Cenário `As-Is` recomendado

### Características gerais

| Parâmetro | Valor |
|---|---:|
| Período simulado | Pico da tarde |
| Duração | 7.200 s |
| Horário representado | 17h00–19h00 |
| Velocidade livre | 40 km/h |
| Velocidade esperada no cenário congestionado | 15–18 km/h |
| Demanda total média | 14.250 veh/h |
| Composição predominante | Veículos leves |
| Ponto mais crítico provável | Av. Pres. Kennedy |
| Segundo ponto mais crítico provável | Mal. Floriano Peixoto |
| Gargalo ambiental principal | Ruído e emissões por ciclo para-e-anda |

### Arquivo `.sumocfg` exemplo

```xml
<configuration>
    <input>
        <net-file value="curitiba_centro.net.xml"/>
        <route-files value="curitiba_centro_as_is.rou.xml"/>
    </input>

    <time>
        <begin value="0"/>
        <end value="7200"/>
        <step-length value="1"/>
    </time>

    <processing>
        <time-to-teleport value="300"/>
        <ignore-route-errors value="true"/>
    </processing>

    <report>
        <verbose value="true"/>
        <no-step-log value="true"/>
    </report>

    <output>
        <summary-output value="outputs/summary_as_is.xml"/>
        <tripinfo-output value="outputs/tripinfo_as_is.xml"/>
        <queue-output value="outputs/queues_as_is.xml"/>
        <emission-output value="outputs/emissions_as_is.xml"/>
    </output>
</configuration>
```

---

## 13. Indicadores para extrair do SUMO

Após rodar o cenário `As-Is`, os principais indicadores para a Fase 2 são:

| Indicador | Arquivo SUMO | Uso no projeto |
|---|---|---|
| Tempo médio de viagem | `tripinfo-output` | Comparar cenário atual e proposto. |
| Tempo médio parado | `tripinfo-output` | Avaliar ciclo para-e-anda. |
| Fila média e fila máxima | `queue-output` | Identificar gargalos. |
| Velocidade média | `summary-output` ou edge data | Validar contra 15–18 km/h. |
| Emissões de CO₂ | `emission-output` | Calcular pegada de carbono. |
| NOx, PMx, CO e HC | `emission-output` | Diagnóstico ambiental complementar. |
| Consumo de combustível | `emission-output` | Relacionar congestionamento e eficiência energética. |

---

## 14. Estratégia de calibração

1. Importar a rede do OpenStreetMap no SUMO.
2. Rodar primeiro com fator de escala `0.50`.
3. Conferir se a velocidade média simulada fica entre `15` e `18 km/h`.
4. Se a velocidade simulada ficar muito alta, aumentar a demanda.
5. Se a rede travar completamente, reduzir a demanda ou ajustar rotas.
6. Manter o pico da tarde como cenário crítico principal.
7. Usar o cenário calibrado como base `As-Is`.

### Sugestão de fatores de escala

| Situação observada | Ajuste recomendado |
|---|---|
| Rede muito livre, poucas filas | Aumentar demanda para 0,75 ou 1,00 |
| Velocidade média 15–18 km/h | Manter demanda |
| Travamentos constantes | Reduzir demanda para 0,50 |
| Teletransporte excessivo de veículos | Revisar rotas, conversões e semáforos |
| Fila infinita em uma entrada | Reduzir fluxo daquela entrada ou redistribuir rota |

---

## 15. Texto metodológico pronto para relatório

> Como não foi possível realizar medições de campo, o levantamento da Fase 1 foi elaborado com base em dados secundários e estimativas técnicas. Foram utilizados dados públicos de tráfego, frota veicular, transporte coletivo, estudos de ruído urbano e bases municipais de solicitações urbanas. O cenário estimado indica saturação moderada a alta no quadrilátero central de Curitiba, especialmente no pico da tarde, com velocidade média operacional próxima de 15 a 18 km/h. A demanda total estimada para os principais trechos varia entre 115 mil e 170 mil passagens veiculares por dia, sendo adotado para simulação um fluxo médio de aproximadamente 14.250 veículos por hora no pico da tarde. Os gargalos principais estão associados à retenção semafórica, interferência do transporte coletivo, carga e descarga, conflitos com pedestres e ruído urbano elevado. Estes valores foram organizados para alimentar o cenário-base `As-Is` no SUMO, permitindo posterior comparação com cenários de intervenção.

---

## 16. Próximos arquivos recomendados

Para executar a simulação, criar os seguintes arquivos:

```text
curitiba_centro.net.xml
curitiba_centro_as_is.rou.xml
curitiba_centro_as_is.sumocfg
outputs/
```

Fluxo recomendado:

```bash
sumo-gui -c curitiba_centro_as_is.sumocfg
```

ou, para rodar em modo terminal:

```bash
sumo -c curitiba_centro_as_is.sumocfg
```

---

## 17. Limitações

- Os valores de VPD são estimados e não substituem contagens reais.
- As rotas do exemplo precisam ser substituídas pelos IDs reais das `edges` importadas do OpenStreetMap.
- Os fluxos podem precisar de fator de escala para evitar saturação artificial da rede.
- Os valores de ruído são estimados por analogia com vias centrais de Curitiba.
- O cenário é adequado para projeto acadêmico preliminar, mas não para licenciamento, intervenção viária real ou tomada de decisão pública sem medição em campo.
