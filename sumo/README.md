# Simulação SUMO — Quadrilátero Central de Curitiba

Projeto de Ciências do Ambiente — UTFPR 2026/1

---

## O que é esta simulação?

Esta simulação modela o tráfego veicular no **Quadrilátero Central de Curitiba** — perímetro delimitado pelas ruas Presidente Kennedy, Calçadão da XV de Novembro, Marechal Floriano Peixoto, Martim Afonso, Mariano Torres e Mário Tourinho — durante a **janela de pico matutina** (06h30 às 09h00).

A simulação contempla **dois cenários distintos**, exatamente como o projeto exige:

| Cenário | Arquivo de configuração | O que representa |
|---------|------------------------|------------------|
| **As-Is** (linha de base) | `quadrilatero_asis.sumocfg` | Situação **atual**, sem nenhuma intervenção — semáforos com tempos fixos de 25s, sem sincronização entre interseções. Serve para **diagnosticar gargalos** e medir o tráfego inicial. |
| **To-Be** (proposto) | `quadrilatero_tobe.sumocfg` | Situação **após aplicar as otimizações** — controlador adaptativo com lógica fuzzy, sincronização Onda Verde nas arteriais, sensoriamento virtual. Serve para **medir os ganhos** em fluidez e emissões. |

A análise comparativa entre os dois cenários quantifica o **impacto das intervenções propostas**.

---

## Estrutura de Arquivos

```
sumo/
├── quadrilatero.nod.xml          # Nós (interseções) da rede viária
├── quadrilatero.edg.xml          # Arestas (vias) da rede viária
├── quadrilatero.typ.xml          # Tipos de via (arterial, coletora)
├── quadrilatero.rou.xml          # Rotas e fluxos de demanda veicular
│
├── quadrilatero_asis.sumocfg     # ⬅️ Simulação do cenário INICIAL (As-Is)
├── quadrilatero_tobe.sumocfg     # ⬅️ Simulação do cenário OTIMIZADO (To-Be)
│
├── build_net.bat                 # Script para gerar a rede (.net.xml)
├── controlador_adaptativo.py     # Controlador fuzzy + Onda Verde (TraCI)
├── analisar_resultados.py        # Compara As-Is × To-Be e gera relatório
├── run_all.bat                   # Script que executa TUDO automaticamente
│
├── README.md                     # Este arquivo
│
├── results/                      # Saídas das simulações (criado automaticamente)
│   ├── tripinfo_asis.xml         # Dados de viagem do cenário inicial
│   ├── tripinfo_tobe.xml         # Dados de viagem do cenário otimizado
│   ├── emissions_asis.xml        # Emissões do cenário inicial
│   ├── emissions_tobe.xml        # Emissões do cenário otimizado
│   └── edgedata_*.xml            # Métricas por via
│
└── output/                       # Relatórios e gráficos (criado automaticamente)
    ├── comparativo_trafego.png   # Gráfico comparativo de tráfego
    ├── comparativo_emissoes.png  # Gráfico comparativo de emissões
    ├── relatorio_comparativo.md  # Relatório final com tabelas
    └── metricas.json             # Métricas em formato JSON
```

---

## Pré-requisitos

### 1. Instalar o SUMO

Faça o download em: https://sumo.dlr.de/docs/Installing/index.html

Após instalar, configure a variável de ambiente `SUMO_HOME`:
- **Windows:** `setx SUMO_HOME "C:\Program Files (x86)\Eclipse\Sumo"` (ajuste o caminho conforme sua instalação)
- Verifique com: `sumo --version`

### 2. Instalar pacotes Python

```bash
pip install sumo scikit-fuzzy pandas matplotlib numpy
```

> Se `scikit-fuzzy` falhar, o controlador usará um fallback linear — a simulação funcionará normalmente.

---

## Como Executar (2 cenários + análise comparativa)

### Opção 1: Script único (mais simples)

Abra um terminal na pasta `sumo` e execute:

```bash
run_all.bat
```

O script faz tudo automaticamente na ordem correta:
1. Gera a rede viária com `netconvert`
2. Roda a **simulação As-Is** (cenário inicial, sem otimizações)
3. Roda a **simulação To-Be** (cenário otimizado, com controlador adaptativo)
4. Executa o **analisador comparativo** (gera gráficos e relatório)

---

### Opção 2: Passo a passo (mais controle)

#### Passo 1 — Gerar a rede viária

```bash
build_net.bat
```

Gera o arquivo `quadrilatero.net.xml` a partir dos nós e arestas.

#### Passo 2 — Simulação As-Is (cenário INICIAL, sem otimizações)

```bash
sumo -c quadrilatero_asis.sumocfg
```

Isto executa a simulação com **semáforos de tempos fixos** (25s verde, sem sincronização). Os resultados são salvos em `results/tripinfo_asis.xml` e `results/emissions_asis.xml`.

> Para visualizar graficamente: `sumo-gui -c quadrilatero_asis.sumocfg`

#### Passo 3 — Simulação To-Be (cenário OTIMIZADO, com intervenções)

Esta simulação usa o controlador adaptativo via TraCI. É necessário **dois terminais**:

**Terminal 1** — Inicia o SUMO em modo servidor:

```bash
sumo -c quadrilatero_tobe.sumocfg --remote-port 8813
```

**Terminal 2** — Executa o controlador Python:

```bash
python controlador_adaptativo.py
```

O controlador:
- Lê filas e ocupação das vias a cada 3 segundos
- Ajusta tempos de verde usando lógica fuzzy (27 regras)
- Sincroniza os semáforos em Onda Verde nas arteriais
- Opera durante toda a janela de pico (2,5h simuladas)

Resultados salvos em `results/tripinfo_tobe.xml` e `results/emissions_tobe.xml`.

> Para visualizar graficamente: no Terminal 1 use `sumo-gui` no lugar de `sumo`.

#### Passo 4 — Analisar resultados (comparação As-Is × To-Be)

```bash
python analisar_resultados.py
```

Este script:
- Lê os arquivos XML de ambas as simulações
- Calcula as métricas de tráfego e emissões
- Gera gráficos comparativos de barras
- Produz um relatório em Markdown com tabelas
- Salva as métricas em JSON

---

## Diferença entre os dois cenários

### Cenário As-Is — Diagnóstico Inicial

Este é o **ponto de partida**. Representa a situação **antes de qualquer intervenção**:

- Semáforos com **tempos fixos** (25s verde, 3s amarelo, 2s all-red)
- **Nenhuma sincronização** entre interseções — cada cruzamento opera isoladamente
- Tráfego flui de forma reativa, sem qualquer inteligência

**Objetivo:** medir o tráfego de base, identificar onde se formam as maiores filas, quais cruzamentos são gargalos críticos, e estabelecer a linha de base de emissões.

### Cenário To-Be — Intervenção Proposta

Este é o cenário **após aplicar as otimizações** de engenharia:

- **Controlador fuzzy:** ajusta dinamicamente o tempo de verde (15--60s) com base no comprimento da fila e na taxa de ocupação da via
- **Onda Verde:** semáforos consecutivos nas arteriais (Kennedy e Floriano) são sincronizados para que veículos a 45 km/h encontrem sinais verdes em sequência
- **Detecção virtual:** sensores simulados (detectores E2 do SUMO) em cada aproximação de interseção

**Objetivo:** reduzir tempo de viagem, eliminar paradas desnecessárias, diminuir emissões de CO₂, NOx e material particulado.

### Comparação

O script `analisar_resultados.py` compara **diretamente** os dois cenários e responde:

- Quanto o tempo médio de viagem reduziu?
- Qual o ganho de velocidade média?
- Quanto caiu o tempo parado em semáforos?
- Qual a redução percentual de CO₂, NOx e PMx?
- Quanto de combustível foi economizado?

---

## Topologia da Rede Modelada

A rede representa o quadrilátero delimitado por:

| Via | Classificação | Faixas por sentido | Velocidade |
|-----|---------------|-------------------|------------|
| Presidente Kennedy | Arterial | 3 | 50 km/h |
| Marechal Floriano Peixoto | Arterial | 3 | 50 km/h |
| Martim Afonso | Coletora | 2 | 40 km/h |
| Mariano Torres | Coletora | 2 | 40 km/h |
| Mário Tourinho | Coletora | 2 | 40 km/h |

O **Calçadão da XV de Novembro** é tratado como eixo de pedestres — as vias transversais o cruzam com travessias semaforizadas que geram conflitos com o fluxo veicular, exatamente como ocorre na realidade.

**Total:** 12 interseções semaforizadas + 26 nós de rede

---

## Demanda Veicular

A demanda é baseada em estimativas do Volume Plano Diário (VPD) da URBS e IPPUC, escalada para a janela de simulação (2,5h de pico matutino).

### Volume por via (veículos/hora na simulação)

| Via | Sentido principal | Fluxo (veh/h) |
|-----|-------------------|---------------|
| Pres. Kennedy | Norte → Sul | 78 |
| Pres. Kennedy | Sul → Norte | 72 |
| Mal. Floriano | Sul → Norte | 65 |
| Mal. Floriano | Norte → Sul | 60 |
| Martim Afonso | Leste → Oeste | 31 |
| Martim Afonso | Oeste → Leste | 30 |
| Mariano Torres | Leste → Oeste | 38 |
| Mariano Torres | Oeste → Leste | 36 |
| Mário Tourinho | Leste → Oeste | 25 |
| Mário Tourinho | Oeste → Leste | 24 |

### Composição da frota

| Categoria | % | Norma PROCONVE | Fator CO₂ (g/km) |
|-----------|----|----------------|------------------|
| Automóvel gasolina | 55% | L7 (EURO 6) | 130 |
| Automóvel etanol | 15% | L7 | 115 |
| Motocicleta | 12% | L5 (EURO 4) | 90 |
| Ônibus urbano | 13% | P7 (EURO 6) | 820 |
| VUC (caminhão leve) | 5% | P7 | 250 |

---

## Controlador Adaptativo (Detalhes Técnicos)

O script `controlador_adaptativo.py` implementa:

### Lógica Fuzzy (27 regras)
- **Entrada 1:** comprimento da fila (0--50 veículos)
- **Entrada 2:** taxa de ocupação da via (0--100%)
- **Saída:** extensão do tempo de verde (−20 a +30 segundos)
- **Classes linguísticas:** baixa, média, alta, crítica
- **Defuzzificação:** centróide

### Sincronização Onda Verde
- Velocidade de progressão: 45 km/h (12,5 m/s)
- Cálculo de defasagem: $\Delta t = d / v_p$, aplicado a cada 30s
- Grupos sincronizados:
  - Kennedy Norte→Sul: K1 → K3 → K5 → K7
  - Floriano Sul→Norte: F7 → F5 → F3 → F1
  - Martim Afonso Leste→Oeste: K1 → X1 → F1
  - Mariano Torres Leste→Oeste: K5 → X3 → F5

### Intervalo de controle
- Coleta de dados: a cada 3 segundos
- Reconfiguração Onda Verde: a cada 30 segundos
- Passo de simulação: 0,1 segundo

---

## Métricas Coletadas e Comparadas

### Tráfego
- Tempo médio de viagem (s)
- Velocidade média (km/h)
- Tempo de espera / parado em semáforo (s)
- *Time loss* (perda de tempo em relação ao *free-flow*)

### Emissões (modelo HBEFA4)
- CO₂ (kg/h)
- NOx (g/h)
- PMx — material particulado (g/h)
- HC — hidrocarbonetos (g/h)
- CO — monóxido de carbono (g/h)
- Consumo de combustível (L/h)

### Por via (edge-based, a cada 5 min)
- Densidade (veh/km)
- Ocupação (%)
- Velocidade média por trecho (km/h)
- Tempo de espera acumulado (s)

---

## Solução de Problemas

| Problema | Solução |
|----------|---------|
| `netconvert` não encontrado | Verifique se o SUMO está no PATH ou se `SUMO_HOME` está definido |
| `ImportError: No module named 'traci'` | Instale `pip install sumo` ou configure `SUMO_HOME` |
| `scikit-fuzzy` não instalou | O controlador usará fallback linear — funciona normalmente |
| Porta 8813 já em uso | Altere `--remote-port` no `.sumocfg` e no script Python |
| Simulação muito lenta | Use `sumo` (terminal) em vez de `sumo-gui` para velocidade máxima |

---

## Referências

- **SUMO Documentation:** https://sumo.dlr.de/docs/
- **TraCI Python API:** https://sumo.dlr.de/docs/TraCI.html
- **HBEFA Emission Model:** https://www.hbefa.net/
- **URBS Dados Abertos:** https://www.urbs.curitiba.pr.gov.br/
- **IPPUC:** https://www.ippuc.org.br/
