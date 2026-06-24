# Cenário 2 — Semáforo Adaptativo por Fila no SUMO

## 1. Objetivo do cenário

Este cenário representa uma intervenção intermediária: substituir semáforos fixos por um **controle semafórico adaptativo simples baseado em filas**.

A proposta é mais simples que uma Onda Verde completa, mas já atende ao conceito de **semáforo inteligente** e **controle em malha fechada**. A lógica usa sensores simulados no SUMO para medir filas, ocupação e tempo de espera em cada aproximação. Com esses dados, o controlador aumenta ou reduz o tempo de verde de cada fase.

Este cenário deve ser comparado com o cenário-base `As-Is`.

### Nome recomendado do cenário

```text
cenario_2_semaforo_adaptativo_fila
```

### Hipótese técnica

Se o semáforo responder ao tamanho da fila em tempo quase real, haverá:

- redução do tempo parado;
- redução de filas máximas;
- aumento da velocidade média;
- menor número de paradas;
- redução moderada de consumo e emissões.

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

## 2. Intervenção simulada

### O que muda em relação ao As-Is

| Elemento | As-Is | Cenário 2 |
|---|---|---|
| Semáforos | Ciclos fixos | Ciclos adaptativos por fila |
| Demanda veicular | Igual | Igual |
| Rotas | Iguais | Iguais |
| Composição da frota | Igual | Igual |
| Carga/descarga | Mantida | Mantida |
| Prioridade a ônibus | Não | Não, ou apenas indiretamente pela fila |
| Onda Verde | Não | Não |
| Pedestres | Mantidos | Mantidos |
| Objetivo | Representar situação atual | Reduzir filas locais |

O cenário 2 não altera a rede viária, não muda sentidos de rua e não reduz demanda. A única mudança principal é a lógica semafórica.

---

## 3. Interseções controladas

A IA que gerar a simulação deve criar ou identificar os semáforos principais da rede e associar cada um a um `tls_id`.

| ID lógico sugerido | Local aproximado | Prioridade |
|---|---|---|
| `tls_01_pres_kennedy` | Eixo Av. Pres. Kennedy | Muito alta |
| `tls_02_mal_floriano` | Eixo Mal. Floriano Peixoto | Alta |
| `tls_03_mariano_torres` | Eixo Mariano Torres | Alta |
| `tls_04_mario_tourinho` | Eixo Mário Tourinho | Média |
| `tls_05_martim_afonso` | Eixo Martim Afonso | Média |
| `tls_06_calcadao_xv` | Acessos ao Calçadão da XV | Alta para pedestres |

> Caso a rede importada do OSM tenha mais semáforos, aplicar a lógica apenas nos cruzamentos internos ou mais carregados. O ideal é controlar entre 5 e 8 interseções.

---

## 4. Sensores simulados

Para cada aproximação semafórica, inserir detectores do tipo `laneAreaDetector` ou `inductionLoop`.

### Configuração recomendada de sensores

| Tipo | Finalidade | Valor recomendado |
|---|---|---|
| `laneAreaDetector` | Medir fila e ocupação | 1 por faixa de aproximação |
| `inductionLoop` | Medir fluxo por faixa | 1 por faixa, antes do cruzamento |
| Distância do cruzamento | Posição do detector | 50 m antes da linha de retenção |
| Frequência de leitura | Atualização da lógica | 5 s |
| Janela de decisão | Ajuste semafórico | a cada 15 s ou no fim de cada fase |

### Exemplo genérico de detector

```xml
<additional>
    <laneAreaDetector id="det_tls01_norte" lane="EDGE_ID_0" pos="-50" length="50" freq="5" file="outputs/detectores_cenario2.xml"/>
    <laneAreaDetector id="det_tls01_sul" lane="EDGE_ID_1" pos="-50" length="50" freq="5" file="outputs/detectores_cenario2.xml"/>
    <laneAreaDetector id="det_tls01_leste" lane="EDGE_ID_2" pos="-50" length="50" freq="5" file="outputs/detectores_cenario2.xml"/>
    <laneAreaDetector id="det_tls01_oeste" lane="EDGE_ID_3" pos="-50" length="50" freq="5" file="outputs/detectores_cenario2.xml"/>
</additional>
```

---

## 5. Parâmetros semafóricos

### Ciclo base

| Parâmetro | Valor |
|---|---:|
| Ciclo base inicial | 90 s |
| Verde mínimo em via principal | 20 s |
| Verde mínimo em via secundária | 15 s |
| Verde máximo em via principal | 70 s |
| Verde máximo em via secundária | 55 s |
| Amarelo | 3 s |
| Vermelho total / all-red | 1 s |
| Intervalo de avaliação | 15 s |
| Extensão pequena | +5 s |
| Extensão grande | +10 s |
| Redução pequena | -5 s |
| Redução máxima por ciclo | -10 s |

### Tempos iniciais sugeridos

| Fase | Movimento | Verde inicial | Amarelo | Vermelho total |
|---|---|---:|---:|---:|
| `phase_0` | Eixo principal direto | 40 s | 3 s | 1 s |
| `phase_1` | Eixo secundário direto | 25 s | 3 s | 1 s |
| `phase_2` | Conversões protegidas, se existirem | 15 s | 3 s | 1 s |
| `phase_3` | Pedestres, se modelados | 20 s | 0 s | 1 s |

Se a rede não tiver fase exclusiva de conversão, usar apenas duas fases principais:

```text
Fase A: via principal
Fase B: via secundária
```

---

## 6. Regras de controle adaptativo

A lógica deve ser implementada por TraCI ou pela própria IA que gerar a simulação.

### Variáveis de entrada

| Variável | Símbolo | Unidade | Como obter no SUMO |
|---|---|---|---|
| Comprimento da fila | `Q` | veículos ou metros | detector / lane halting number |
| Tempo médio de espera | `W` | segundos | waiting time por lane |
| Ocupação da aproximação | `O` | % | laneAreaDetector |
| Fluxo recente | `F` | veh/min | inductionLoop |
| Fila conflitante máxima | `Q_conf` | veículos | detectores das aproximações em vermelho |

### Limiares adotados

| Situação | Condição | Ação |
|---|---|---|
| Fila baixa | `Q < 5 veh` e `O < 25%` | permitir encerramento no verde mínimo |
| Fila média | `5 <= Q < 12 veh` | manter verde atual |
| Fila alta | `12 <= Q < 25 veh` ou `W > 60 s` | estender verde em `+5 s` |
| Fila crítica | `Q >= 25 veh` ou `W > 90 s` | estender verde em `+10 s` |
| Via oposta crítica | `Q_conf >= 25 veh` | não estender além do verde base |
| Saturação geral | todas as aproximações com fila alta | manter ciclo balanceado e evitar favorecer só uma via |
| Pedestre esperando | fase pedestre sem atendimento por `> 90 s` | forçar fase de pedestres no próximo ciclo |

### Pseudocódigo recomendado

```python
for tls in semaforos:
    fase_atual = traci.trafficlight.getPhase(tls)
    tempo_fase = traci.trafficlight.getPhaseDuration(tls)

    Q = maior_fila_da_fase_verde(tls)
    W = maior_espera_da_fase_verde(tls)
    Q_conf = maior_fila_das_fases_vermelhas(tls)

    if tempo_verde_atual < verde_minimo:
        manter_fase()

    elif Q >= 25 or W > 90:
        if Q_conf < 25:
            estender_verde(10)
        else:
            encerrar_fase_no_tempo_base()

    elif Q >= 12 or W > 60:
        if Q_conf < 20:
            estender_verde(5)
        else:
            encerrar_fase()

    elif Q < 5 and Q_conf > 12:
        encerrar_fase()

    else:
        manter_tempo_base()
```

---

## 7. Distribuição dos parâmetros por via

| Via | Peso no controle | Verde máximo recomendado | Observação |
|---|---:|---:|---|
| Av. Pres. Kennedy | 1,25 | 70 s | Maior fluxo estimado |
| Mal. Floriano Peixoto | 1,15 | 65 s | Alto conflito ônibus/pedestres |
| Mariano Torres | 1,15 | 65 s | Corredor crítico |
| Mário Tourinho | 1,00 | 55 s | Distribuição média |
| Martim Afonso | 0,95 | 55 s | Coletora/ligação |
| Acessos ao Calçadão da XV | 0,80 veículos / 1,30 pedestres | 40 s veículos / 25 s pedestres | Priorizar segurança |

O peso pode ser usado para ponderar a fila:

```text
fila_ponderada = fila_observada × peso_da_via
```

---

## 8. Arquivos recomendados

```text
cenario_2_semaforo_adaptativo_fila/
├── curitiba_centro.net.xml
├── cenario2.rou.xml
├── cenario2.add.xml
├── cenario2.sumocfg
├── controle_adaptativo_fila.py
└── outputs/
    ├── summary_cenario2.xml
    ├── tripinfo_cenario2.xml
    ├── queues_cenario2.xml
    ├── emissions_cenario2.xml
    └── detectores_cenario2.xml
```

---

## 9. Configuração `.sumocfg` recomendada

```xml
<configuration>
    <input>
        <net-file value="curitiba_centro.net.xml"/>
        <route-files value="cenario2.rou.xml"/>
        <additional-files value="cenario2.add.xml"/>
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
        <summary-output value="outputs/summary_cenario2.xml"/>
        <tripinfo-output value="outputs/tripinfo_cenario2.xml"/>
        <queue-output value="outputs/queues_cenario2.xml"/>
        <emission-output value="outputs/emissions_cenario2.xml"/>
    </output>
</configuration>
```

Rodar com TraCI:

```bash
python controle_adaptativo_fila.py
```

---

## 10. Indicadores esperados

Estes valores não são resultados finais. São **faixas esperadas** para validar se a simulação está coerente.

| Indicador | As-Is esperado | Cenário 2 esperado | Variação esperada |
|---|---:|---:|---:|
| Tempo médio de viagem | 18,0–19,5 min | 15,8–17,2 min | -8% a -15% |
| Velocidade média | 11–13 km/h | 13–15 km/h | +12% a +25% |
| Tempo médio parado | 7,0–8,5 min | 5,5–6,8 min | -15% a -25% |
| Fila máxima | 100% base | 75%–90% base | -10% a -25% |
| Número médio de paradas | 100% base | 80%–90% base | -10% a -20% |
| CO2 total | 100% base | 88%–94% base | -6% a -12% |
| NOx total | 100% base | 89%–95% base | -5% a -11% |
| Consumo de combustível | 100% base | 88%–94% base | -6% a -12% |
| Ruído estimado | 78–86 dB(A) | 76–84 dB(A) | -1 a -2 dB(A) |

---

## 11. Critério de sucesso do cenário 2

O cenário 2 deve ser considerado bem-sucedido se atingir pelo menos:

```text
redução do tempo médio de viagem >= 10%
redução do tempo parado >= 15%
redução de CO2 >= 6%
velocidade média final >= 13 km/h
sem aumento expressivo de fila nas vias secundárias
```

---

## 12. Prompt para a IA gerar a simulação

```text
Crie uma simulação SUMO para o quadrilátero central de Curitiba usando a rede importada do OpenStreetMap. Gere o cenário 2 chamado "semaforo_adaptativo_fila". Use a mesma demanda do cenário As-Is: 14.250 veículos/h no pico da tarde, distribuídos entre Pres. Kennedy, Mal. Floriano, Mariano Torres, Mário Tourinho, Martim Afonso e acessos ao Calçadão da XV. Use composição veicular de 72% passenger, 15% motorcycle, 6% bus, 6% truck e 1% bike.

Implemente semáforos adaptativos por fila via Python/TraCI. Insira laneAreaDetectors a 50 m das linhas de retenção, com leitura a cada 5 s. A cada 15 s ou no fim de cada fase, ajuste o verde conforme filas: Q < 5 encerra no mínimo, 12 <= Q < 25 estende +5 s, Q >= 25 ou W > 90 s estende +10 s, respeitando verde mínimo de 15–20 s e verde máximo de 55–70 s. Use amarelo de 3 s e all-red de 1 s. Mantenha a demanda igual ao As-Is para comparação direta. Gere outputs de tripinfo, summary, queues, emissions e detectores.
```

---

## 13. Observações finais

Este cenário é ideal como intervenção intermediária. Ele mostra controle inteligente sem exigir implementação completa de Onda Verde, fuzzy ou prioridade explícita ao ônibus. Serve como ponte entre o cenário base e o cenário 3 integrado.
