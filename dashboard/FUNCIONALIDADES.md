# Funcionalidades do Dashboard

## O que o dashboard faz

O dashboard é uma interface web que **substitui completamente o fluxo de terminal** descrito nos arquivos `PASSO_A_PASSO.md` e `COMO_CRIAR_SIMULACAO.md`. Em vez de rodar comandos manualmente, editar XMLs ou depender de arquivos `.bat`, tudo é feito pela interface gráfica.

---

## Tela principal

### Sidebar (lateral esquerda)

A sidebar concentra **toda a configuração** da simulação:

| Seção | O que faz |
|-------|-----------|
| **Status SUMO** | Mostra se o SUMO foi detectado automaticamente e qual versão. Se não encontrar, exibe instruções. |
| **⚙️ Simulação** | Duração da simulação (em segundos), precisão do passo (step length) e seed aleatória. |
| **🚗 Demanda Veicular** | Volume total de veículos por hora (slider de 50 a 2000) e composição percentual da frota: gasolina, etanol, moto, ônibus, VUC. A soma deve ser 100% — o dashboard avisa se não for. |
| **🚦 Cenário To-Be** | Tempo verde fixo (em segundos) aplicado a todos os semáforos na rede otimizada. |
| **Botões de ação** | `▶️ Rodar Pipeline` executa a simulação completa. `📊 Analisar Resultados` lê simulações já rodadas sem reexecutar. |

### Área principal

Durante a execução, mostra uma **barra de progresso** com a etapa atual (gerando demanda, roteando, simulando As-Is, simulando To-Be, analisando).

Após a conclusão, exibe:

1. **Cards de métricas** — comparação numérica lado a lado com variação percentual colorida:
   - ⏱ Tempo médio de viagem (s)
   - 🚗 Velocidade média (km/h)
   - ⏳ Tempo de espera médio (s)
   - 🌿 CO₂ (kg/h)
   - 💨 NOx (g/h)
   - 🌫️ PMx (g/h)
   - ⛽ Combustível (L/h)

2. **Gráfico de Tráfego** — barras agrupadas As-Is vs To-Be para tempo de viagem, velocidade e espera, com anotações da variação percentual em cada barra.

3. **Gráfico de Emissões** — barras agrupadas para CO₂, NOx, PMx e combustível, com anotações de variação.

4. **Download** — botões para baixar relatório em Markdown e métricas em JSON.

---

## Cenários simulados

| Cenário | Descrição |
|---------|-----------|
| **As-Is** | Rede original do OpenStreetMap com tempos semafóricos padrão do SUMO (~31s). Representa a situação atual do quadrilátero central. |
| **To-Be** | Rede com tempos verdes otimizados (configurável, default 35s). Representa a proposta de melhoria. |

---

## O que acontece nos bastidores

Quando o usuário clica em **Rodar Pipeline**, o dashboard:

1. Lê a rede viária (`quadrilatero.net.xml`) gerada do `map.osm`
2. Identifica as vias principais (primary, secondary, tertiary)
3. Gera um arquivo `.rou.xml` com fluxos de veículos parametrizados (volume total × mix da frota)
4. Executa o `duarouter.exe` do SUMO para converter os fluxos em rotas completas
5. Cria um `.sumocfg` temporário para o cenário As-Is
6. Roda o `sumo.exe` para simular o cenário As-Is (gera `tripinfo_asis.xml` + `emissions_asis.xml`)
7. Copia a rede e ajusta os tempos verdes de todos os semáforos
8. Cria um `.sumocfg` temporário para o cenário To-Be
9. Roda o `sumo.exe` para simular o cenário To-Be (gera `tripinfo_tobe.xml` + `emissions_tobe.xml`)
10. Analisa os XMLs gerados, extrai métricas e exibe os resultados

---

## Parâmetros configuráveis

| Parâmetro | Default | Range | Descrição |
|-----------|---------|-------|-----------|
| Duração | 3600s (1h) | 600–10800s | Tempo total da simulação |
| Precisão | 0.1s | 0.05–1.0s | Passo de simulação do SUMO |
| Seed | 42 | qualquer | Semente aleatória para reprodutibilidade |
| Volume total | 459 veh/h | 50–2000 | Fluxo veicular total nas vias principais |
| Gasolina | 55% | 0–100% | Proporção de carros a gasolina |
| Etanol | 15% | 0–100% | Proporção de carros a etanol |
| Moto | 12% | 0–100% | Proporção de motocicletas |
| Ônibus | 13% | 0–100% | Proporção de ônibus |
| VUC | 5% | 0–100% | Proporção de veículos utilitários |
| Tempo verde To-Be | 35s | 10–90s | Duração da fase verde nos semáforos otimizados |

---

## Tipos de veículos simulados

Conforme especificação do projeto (Projeto 1 CA 2026/1):

| Tipo | Aceleração | Desaceleração | Comprimento | Velocidade máx |
|------|-----------|---------------|-------------|----------------|
| Carro gasolina | 2.6 m/s² | 4.5 m/s² | 4.3 m | 60 km/h |
| Carro etanol | 2.6 m/s² | 4.5 m/s² | 4.3 m | 60 km/h |
| Moto | 3.5 m/s² | 6.0 m/s² | 2.0 m | 65 km/h |
| Ônibus | 1.3 m/s² | 3.5 m/s² | 12.0 m | 50 km/h |
| VUC | 1.5 m/s² | 3.8 m/s² | 7.0 m | 50 km/h |

---

## Métricas extraídas

### Tráfego
- Tempo médio de viagem por veículo (s)
- Velocidade média (km/h)
- Tempo médio de espera em semáforos (s)
- Time loss médio (s)
- Número de veículos que completaram o trajeto

### Emissões
- CO₂ emitido (kg/h)
- NOx emitido (g/h)
- PMx emitido (g/h)
- Combustível consumido (L/h)

Todas as métricas são comparadas entre As-Is e To-Be com **variação percentual**.

---

## Diferenças em relação ao fluxo antigo

| Antes (CLI/.bat) | Agora (Dashboard) |
|-------------------|-------------------|
| 6+ comandos manuais no terminal | 1 clique no botão "Rodar Pipeline" |
| Editar XML manualmente | Sliders e inputs numéricos na sidebar |
| Gráficos matplotlib estáticos (PNG) | Gráficos Plotly interativos (zoom, hover, anotações) |
| Progresso invisível (terminal) | Barra de progresso com etapa atual |
| Relatório só em Markdown | Relatório Markdown + JSON + cards visuais |
| Depende de `run_all.bat` no Windows | Roda em qualquer SO com Python |
| Parâmetros fixos no código | Tudo configurável pela interface |
