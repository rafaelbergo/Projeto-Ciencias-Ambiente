# Cenário 3 — Onda Verde Adaptativa Sustentável no SUMO

## 1. Objetivo do cenário

Este cenário representa a intervenção principal do projeto: um **Sistema Integrado de Onda Verde Adaptativa Sustentável**.

A proposta combina:

- controle semafórico adaptativo;
- sincronização por Onda Verde;
- sensores simulados;
- prioridade moderada para ônibus;
- restrição de carga e descarga no pico;
- redução de conflitos com pedestres no Calçadão da XV;
- zona de baixa velocidade em área sensível;
- análise de emissões, consumo e ruído estimado.

Este é o cenário `To-Be` mais completo e deve ser comparado diretamente com o `As-Is` e com o Cenário 2.

### Nome recomendado do cenário

```text
cenario_3_onda_verde_adaptativa_sustentavel
```

### Hipótese técnica

A intervenção integrada deve reduzir o ciclo `para-e-anda`, melhorar a progressão veicular nos eixos principais e reduzir impactos ambientais.

---

## Base comum de demanda para os cenários 2 e 3

A simulação deve usar a mesma demanda do cenário-base `As-Is`, para permitir comparação direta. A janela recomendada é o pico da tarde, de `17h00` a `19h00`, representada no SUMO por `begin="0"` e `end="7200"`.

| ID lógico da rota | Via/trecho | VPD médio estimado | Pico tarde adotado |
|---|---|---:|---:|
| `r_pres_kennedy` | Av. Pres. Kennedy | 45.000 veh/dia | 4.500 veh/h |
| `r_mal_floriano` | Mal. Floriano Peixoto | 29.000 veh/dia | 2.900 veh/h |
| `r_mariano_torres` | Mariano Torres | 27.000 veh/dia | 2.700 veh/h |
| `r_mario_tourinho` | Mário Tourinho | 23.000 veh/dia | 2.300 veh/h |
| `r_martim_afonso` | Martim Afonso | 16.000 veh/dia | 1.600 veh/h |
| `r_calcadao_xv` | Acessos ao Calçadão da XV | 2.500 veh/dia | 250 veh/h |

**Demanda total média no pico da tarde:** `14.250 veh/h`.

### Composição veicular adotada

| Classe SUMO | Descrição | Percentual | Uso |
|---|---|---:|---|
| `passenger` | Automóveis e veículos leves | 72% | Classe predominante |
| `motorcycle` | Motocicletas | 15% | Ruído e aceleração elevada |
| `bus` | Ônibus urbanos | 6% | Transporte coletivo |
| `truck` | Caminhões leves, VUCs e entregas | 6% | Carga e descarga |
| `bike` | Bicicletas e e-bikes | 1% | Mobilidade ativa |

### Fluxos por rota e classe no pico da tarde

| Rota | Total veh/h | passenger | motorcycle | bus | truck | bike |
|---|---:|---:|---:|---:|---:|---:|
| `r_pres_kennedy` | 4.500 | 3.240 | 675 | 270 | 270 | 45 |
| `r_mal_floriano` | 2.900 | 2.088 | 435 | 174 | 174 | 29 |
| `r_mariano_torres` | 2.700 | 1.944 | 405 | 162 | 162 | 27 |
| `r_mario_tourinho` | 2.300 | 1.656 | 345 | 138 | 138 | 23 |
| `r_martim_afonso` | 1.600 | 1.152 | 240 | 96 | 96 | 16 |
| `r_calcadao_xv` | 250 | 180 | 38 | 15 | 15 | 2 |

### Tipos de veículos sugeridos

```xml
<vType id="passenger" vClass="passenger" accel="2.6" decel="4.5" sigma="0.5" length="4.5" minGap="2.5" maxSpeed="13.89" emissionClass="HBEFA3/PC_G_EU4"/>
<vType id="motorcycle" vClass="motorcycle" accel="3.5" decel="5.0" sigma="0.7" length="2.2" minGap="1.0" maxSpeed="13.89" emissionClass="HBEFA3/LDV_G_EU4"/>
<vType id="bus" vClass="bus" accel="1.2" decel="4.0" sigma="0.5" length="12.0" minGap="3.0" maxSpeed="11.11" emissionClass="HBEFA3/Bus"/>
<vType id="truck" vClass="truck" accel="1.0" decel="3.5" sigma="0.6" length="8.0" minGap="3.0" maxSpeed="11.11" emissionClass="HBEFA3/HDV"/>
<vType id="bike" vClass="bicycle" accel="1.2" decel="3.0" sigma="0.8" length="1.8" minGap="1.0" maxSpeed="6.94"/>
```

> Os IDs das rotas e edges devem ser substituídos pelos IDs reais importados do OpenStreetMap. A outra IA deve manter os valores de demanda, proporções e regras de controle.


---

## 2. Intervenções aplicadas

### Resumo das mudanças

| Intervenção | Aplicada? | Como representar no SUMO |
|---|---|---|
| Semáforo adaptativo por fila | Sim | Script TraCI com detectores |
| Onda Verde entre interseções | Sim | Offset calculado por distância e velocidade de progressão |
| Prioridade moderada para ônibus | Sim | Extensão/antecipação de verde quando ônibus se aproxima |
| Restrição de carga/descarga no pico | Sim | Redução de trucks em vias críticas ou remoção de paradas |
| Zona de baixa velocidade no Calçadão | Sim | Reduzir `maxSpeed` nas edges sensíveis |
| Proteção de pedestres | Sim | Fases pedestres garantidas e limite máximo de espera |
| Redistribuição leve de rotas | Sim | Desviar parte do tráfego de passagem |
| Emissões e consumo | Sim | `emission-output` com classes HBEFA |
| Ruído | Estimado fora do SUMO | Usar velocidade, aceleração e composição como proxy |

---

## 3. Estratégia de controle semafórico

O cenário 3 usa uma lógica em duas camadas.

### Camada 1 — Controle local adaptativo

Cada semáforo ajusta o verde conforme fila, ocupação, tempo de espera e presença de ônibus.

### Camada 2 — Coordenação por Onda Verde

A cada 180 s, o sistema recalcula as defasagens entre semáforos consecutivos nos corredores principais.

Este intervalo de 180 s representa o controlador mestre recalculando o sincronismo a cada 3 minutos.

---

## 4. Velocidade de progressão da Onda Verde

A Onda Verde deve usar uma velocidade de progressão menor que a velocidade livre, pois a área é central e congestionada.

| Corredor | Velocidade livre | Velocidade de progressão adotada |
|---|---:|---:|
| Av. Pres. Kennedy | 40 km/h | 32 km/h |
| Mal. Floriano Peixoto | 40 km/h | 28 km/h |
| Mariano Torres | 40 km/h | 30 km/h |
| Mário Tourinho | 40 km/h | 30 km/h |
| Martim Afonso | 40 km/h | 28 km/h |
| Acessos ao Calçadão da XV | 25 km/h | 18 km/h |

Conversão:

```text
32 km/h = 8,89 m/s
30 km/h = 8,33 m/s
28 km/h = 7,78 m/s
18 km/h = 5,00 m/s
```

### Fórmula de defasagem

```text
offset = distância_entre_semafóros / velocidade_de_progressão
```

Exemplo:

```text
distância = 280 m
velocidade de progressão = 8,33 m/s
offset = 280 / 8,33 = 33,6 s
offset adotado = 34 s
```

---

## 5. Offsets sugeridos para a Onda Verde

Como a rede real importada pode ter distâncias diferentes, estes valores são iniciais. A IA deve recalcular se conseguir medir as distâncias reais entre os semáforos.

| Par de semáforos | Distância estimada | Velocidade de progressão | Offset inicial |
|---|---:|---:|---:|
| `tls_01_pres_kennedy` → `tls_02_mal_floriano` | 300 m | 8,33 m/s | 36 s |
| `tls_02_mal_floriano` → `tls_03_mariano_torres` | 260 m | 8,33 m/s | 31 s |
| `tls_03_mariano_torres` → `tls_04_mario_tourinho` | 320 m | 8,33 m/s | 38 s |
| `tls_04_mario_tourinho` → `tls_05_martim_afonso` | 240 m | 7,78 m/s | 31 s |
| `tls_05_martim_afonso` → `tls_06_calcadao_xv` | 220 m | 5,00 m/s | 44 s |

### Ciclo coordenado inicial

| Parâmetro | Valor |
|---|---:|
| Ciclo coordenado base | 100 s |
| Recalcular offsets | a cada 180 s |
| Verde mínimo | 18 s |
| Verde máximo | 75 s |
| Amarelo | 3 s |
| All-red | 1 s |
| Tolerância de quebra da Onda Verde | até 10 s |

---

## 6. Lógica adaptativa com pesos ambientais

A função objetivo deve equilibrar tempo de viagem, número de paradas e emissões.

```text
J = 0,50 × tempo_de_viagem_normalizado
  + 0,30 × número_de_paradas_normalizado
  + 0,20 × CO2_normalizado
```

A intervenção deve buscar minimizar `J`.

### Pesos por tipo de decisão

| Objetivo | Peso |
|---|---:|
| Reduzir tempo de viagem | 0,50 |
| Reduzir número de paradas | 0,30 |
| Reduzir emissões de CO2 | 0,20 |

### Regras locais

| Condição | Ação |
|---|---|
| Fila alta em via principal e Onda Verde próxima | estender verde até `+10 s` |
| Fila alta em via secundária | estender verde até `+5 s`, sem quebrar corredor principal |
| Ônibus detectado a menos de 120 m | antecipar ou estender verde em `+8 s` |
| Pedestre esperando há mais de 90 s | garantir fase pedestre no próximo ciclo |
| Caminhão parado em via crítica | penalizar rota/carga ou reduzir entrada de trucks |
| Vias todas saturadas | manter ciclo balanceado e evitar extensão excessiva |

---

## 7. Prioridade moderada para ônibus

A prioridade ao ônibus deve ser condicional, não absoluta.

### Parâmetros de prioridade

| Parâmetro | Valor |
|---|---:|
| Distância de detecção do ônibus | 120 m antes do cruzamento |
| Extensão máxima de verde para ônibus | +8 s |
| Antecipação máxima de verde | 5 s |
| Tempo mínimo entre prioridades no mesmo semáforo | 60 s |
| Cancelar prioridade se fila conflitante crítica | Sim |
| Fila conflitante crítica | `Q_conf >= 25 veh` |

### Regras

```text
Se ônibus está a menos de 120 m e fase atual está verde:
    estender verde em até 8 s

Se ônibus está a menos de 120 m e fase do ônibus será a próxima:
    antecipar a próxima fase em até 5 s

Se fila conflitante >= 25 veículos:
    limitar prioridade do ônibus para não travar a rede
```

---

## 8. Restrição de carga e descarga no pico

Neste cenário, a carga e descarga irregular deve ser reduzida no horário de pico.

### Estratégia simulada

| Item | As-Is | Cenário 3 |
|---|---:|---:|
| Trucks em Pres. Kennedy | 270 veh/h | 190 veh/h |
| Trucks em Mal. Floriano | 174 veh/h | 120 veh/h |
| Trucks em Mariano Torres | 162 veh/h | 115 veh/h |
| Trucks em Mário Tourinho | 138 veh/h | 125 veh/h |
| Trucks em Martim Afonso | 96 veh/h | 90 veh/h |
| Trucks em acessos ao Calçadão | 15 veh/h | 8 veh/h |

A redução de caminhões/VUCs nas vias críticas deve ser compensada por:

- deslocamento para rotas secundárias;
- antecipação das entregas para fora do pico;
- bolsões de carga e descarga fora das faixas principais.

### Nova composição de fluxo no cenário 3

No cenário 3, manter a demanda total semelhante, mas redistribuir parte dos trucks removidos para veículos leves ou rotas periféricas. Para simplificação:

| Classe | Cenário 2 | Cenário 3 |
|---|---:|---:|
| `passenger` | 72% | 74% |
| `motorcycle` | 15% | 15% |
| `bus` | 6% | 6% |
| `truck` | 6% | 4% |
| `bike` | 1% | 1% |

> Esta alteração representa a restrição operacional de carga pesada/VUCs no pico e deve reduzir bloqueios laterais, acelerações bruscas e ruído.

---

## 9. Fluxos ajustados para o cenário 3

| Rota | Total veh/h | passenger 74% | motorcycle 15% | bus 6% | truck 4% | bike 1% |
|---|---:|---:|---:|---:|---:|---:|
| `r_pres_kennedy` | 4.500 | 3.330 | 675 | 270 | 180 | 45 |
| `r_mal_floriano` | 2.900 | 2.146 | 435 | 174 | 116 | 29 |
| `r_mariano_torres` | 2.700 | 1.998 | 405 | 162 | 108 | 27 |
| `r_mario_tourinho` | 2.300 | 1.702 | 345 | 138 | 92 | 23 |
| `r_martim_afonso` | 1.600 | 1.184 | 240 | 96 | 64 | 16 |
| `r_calcadao_xv` | 250 | 185 | 38 | 15 | 10 | 2 |

---

## 10. Zona de baixa velocidade no Calçadão da XV

Nos acessos ao Calçadão da XV, a prioridade deve ser segurança e redução de conflitos com pedestres.

### Parâmetros

| Elemento | Valor |
|---|---:|
| Velocidade máxima dos acessos ao Calçadão | 18 km/h |
| Velocidade máxima de veículos de carga autorizados | 15 km/h |
| Velocidade de bicicletas/e-bikes | 20–25 km/h |
| Espera máxima de pedestres | 90 s |
| Fase pedestre mínima | 20 s |
| Fase pedestre recomendada em alto fluxo | 25 s |

No SUMO, aplicar:

```xml
<edge id="EDGE_CALCADAO_ACESSO" speed="5.00"/>
```

ou ajustar as lanes correspondentes para `speed="5.00"`.

---

## 11. Redistribuição leve de rotas

Para representar gestão operacional de tráfego, redistribuir pequena parcela do tráfego de passagem.

### Redistribuição recomendada

| Origem do fluxo | Percentual desviado | Destino sugerido |
|---|---:|---|
| Pres. Kennedy | 5% | rota periférica/borda |
| Mal. Floriano | 4% | rota paralela menos saturada |
| Mariano Torres | 4% | rota alternativa |
| Acessos ao Calçadão | 10% dos trucks | bolsão externo de carga |

Essa redistribuição não deve ser agressiva. O objetivo é aliviar gargalos sem apenas transferir congestionamento.

---

## 12. Sensores simulados

Usar detectores como no cenário 2, mas com mais funções.

| Sensor simulado | Quantidade lógica | Uso |
|---|---:|---|
| `laneAreaDetector` | 1 por faixa de aproximação | Fila, ocupação, halting |
| `inductionLoop` | 1 por faixa crítica | Fluxo e headway |
| Detecção de ônibus | por `vClass="bus"` ou rota | Prioridade semafórica |
| Detector de pedestres | opcional | Fase pedestre |
| Detector ambiental | virtual | Estimar ruído por tráfego |

### Frequências

| Processo | Frequência |
|---|---:|
| Leitura de detectores | 5 s |
| Decisão local semafórica | 15 s |
| Recalcular Onda Verde | 180 s |
| Salvar métricas ambientais | 60 s |
| Exportar resultados finais | fim da simulação |

---

## 13. Arquivos recomendados

```text
cenario_3_onda_verde_adaptativa_sustentavel/
├── curitiba_centro.net.xml
├── cenario3.rou.xml
├── cenario3.add.xml
├── cenario3.sumocfg
├── controle_onda_verde_sustentavel.py
└── outputs/
    ├── summary_cenario3.xml
    ├── tripinfo_cenario3.xml
    ├── queues_cenario3.xml
    ├── emissions_cenario3.xml
    ├── edge_data_cenario3.xml
    └── detectores_cenario3.xml
```

---

## 14. Configuração `.sumocfg` recomendada

```xml
<configuration>
    <input>
        <net-file value="curitiba_centro.net.xml"/>
        <route-files value="cenario3.rou.xml"/>
        <additional-files value="cenario3.add.xml"/>
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

    <output>
        <summary-output value="outputs/summary_cenario3.xml"/>
        <tripinfo-output value="outputs/tripinfo_cenario3.xml"/>
        <queue-output value="outputs/queues_cenario3.xml"/>
        <emission-output value="outputs/emissions_cenario3.xml"/>
        <edgedata-output value="outputs/edge_data_cenario3.xml"/>
    </output>
</configuration>
```

Rodar com TraCI:

```bash
python controle_onda_verde_sustentavel.py
```

---

## 15. Indicadores esperados

Estes valores servem como referência de plausibilidade. Os resultados reais devem sair da simulação.

| Indicador | As-Is esperado | Cenário 3 esperado | Variação esperada |
|---|---:|---:|---:|
| Tempo médio de viagem | 18,0–19,5 min | 14,2–15,8 min | -18% a -25% |
| Velocidade média | 11–13 km/h | 15–17 km/h | +30% a +45% |
| Tempo médio parado | 7,0–8,5 min | 4,5–5,8 min | -25% a -40% |
| Fila máxima | 100% base | 60%–80% base | -20% a -40% |
| Número médio de paradas | 100% base | 65%–80% base | -20% a -35% |
| CO2 total | 100% base | 78%–86% base | -14% a -22% |
| NOx total | 100% base | 78%–87% base | -13% a -22% |
| PMx total | 100% base | 80%–88% base | -12% a -20% |
| Consumo de combustível | 100% base | 78%–86% base | -14% a -22% |
| Ruído estimado em vias críticas | 78–86 dB(A) | 74–80 dB(A) | -3 a -6 dB(A) |

---

## 16. Critério de sucesso do cenário 3

O cenário 3 deve ser considerado bem-sucedido se atingir pelo menos:

```text
redução do tempo médio de viagem >= 15%
aumento da velocidade média >= 25%
redução do tempo parado >= 25%
redução de CO2 >= 12%
redução de consumo >= 12%
redução perceptível de filas nos eixos Pres. Kennedy, Mal. Floriano e Mariano Torres
sem aumento grave de espera de pedestres
sem travamento das vias secundárias
```

---

## 17. Comparação recomendada com os outros cenários

| Cenário | Descrição | Função no projeto |
|---|---|---|
| `As-Is` | Situação atual com semáforos fixos | Base de comparação |
| `Cenário 2` | Semáforo adaptativo por fila | Intervenção intermediária |
| `Cenário 3` | Onda Verde adaptativa sustentável | Proposta principal |

A análise final deve mostrar que o cenário 3 tem desempenho superior ao cenário 2 porque combina fluidez, coordenação entre cruzamentos, transporte coletivo, carga/descarga e sustentabilidade.

---

## 18. Prompt para a IA gerar a simulação

```text
Crie uma simulação SUMO para o quadrilátero central de Curitiba chamada "cenario_3_onda_verde_adaptativa_sustentavel". Use a mesma rede do cenário As-Is e a mesma demanda média total de 14.250 veículos/h no pico da tarde, das 17h às 19h, mas ajuste a composição para 74% passenger, 15% motorcycle, 6% bus, 4% truck e 1% bike, representando restrição de carga e descarga no pico.

Implemente controle semafórico adaptativo via Python/TraCI com duas camadas: controle local por fila e coordenação por Onda Verde. Use laneAreaDetectors a 50 m das linhas de retenção e leitura a cada 5 s. A decisão local deve ocorrer a cada 15 s, com verde mínimo de 18 s, verde máximo de 75 s, amarelo de 3 s e all-red de 1 s. Recalcule os offsets da Onda Verde a cada 180 s usando velocidade de progressão de 28 a 32 km/h nos eixos principais e 18 km/h nos acessos ao Calçadão da XV.

Inclua prioridade moderada para ônibus: se um ônibus estiver a menos de 120 m do cruzamento, estender o verde em até 8 s ou antecipar a próxima fase em até 5 s, desde que a fila conflitante não seja crítica. Inclua espera máxima de pedestres de 90 s e fase pedestre mínima de 20 s nos acessos ao Calçadão. Reduza a velocidade máxima dos acessos ao Calçadão para 18 km/h. Gere outputs de tripinfo, summary, queues, emissions, edgedata e detectores. Compare os resultados com As-Is e Cenário 2.
```

---

## 19. Observações finais

Este cenário deve ser usado como a proposta principal do trabalho. Ele é tecnicamente mais forte porque integra os conceitos de Computação, Elétrica/Automação e Mecânica:

- Computação: controle adaptativo, TraCI, lógica de decisão e otimização;
- Elétrica/Automação: sensores, detecção, controle em malha fechada e sincronização;
- Mecânica: emissões, consumo, ruído e redução do ciclo `para-e-anda`.

A demanda deve permanecer próxima da base original para que a melhoria venha da intervenção e não de uma redução artificial do tráfego.
