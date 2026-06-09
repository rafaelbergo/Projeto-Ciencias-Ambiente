# Plano de Projeto — Dashboard de Simulação de Tráfego

## Objetivo

Criar um dashboard web em Python (Streamlit) que substitua todo o fluxo complexo de CLI/bat da pasta `centro/`, permitindo simular, comparar cenários e visualizar resultados de forma interativa.

---

## Decisões de Design

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Framework UI | **Streamlit** | Zero frontend, puro Python, progress bars nativas |
| Gráficos | **Plotly** (substitui matplotlib) | Interativos, exportáveis, nativos no Streamlit |
| Rede base | **centro/map.osm** (OSM real) | Mapa real do quadrilátero central de Curitiba |
| Pasta nova | **dashboard/** na raiz do projeto | Isolado, não altera nada existente |
| pasta centro/ | **Intocada** | Scripts CLI existentes continuam funcionando |
| Controlador fuzzy | **Deferido para v2** | Complexidade extra com TraCI/subprocess |
| duarouter após demanda | **Auto-executar** | UX mais fluida, sem passo manual |
| Visualização sumo-gui | **Não incluir** | CLI é mais rápido e simplifica a arquitetura |
| Outputs da simulação | **dashboard/results/ e dashboard/output/** | Isolado, não mistura saídas com centro/ |

---

## O Que Reutilizar vs Reescrever

### Reutilizar (import direto do `centro/`)

| De `centro/comparar_simulacoes.py` | Função |
|-------------------------------------|--------|
| `parse_tripinfo(filepath)` | XML → DataFrame de viagens |
| `parse_emissions(filepath)` | XML → DataFrame de emissões |
| `analisar_tripinfo(df_asis, df_tobe)` | DataFrames → dict métricas tráfego |
| `analisar_emissions(df_asis, df_tobe)` | DataFrames → dict métricas emissões |

### Reescrever (lógica adaptada para o dashboard)

| Original | Nova localização | Por que reescrever |
|----------|-------------------|-------------------|
| `gerar_demanda.py` | `simulation.py → generate_demand()` | VPH e mix de veículos parametrizáveis |
| `otimizar_rede.py` | `simulation.py → optimize_network()` | Tempo verde parametrizável |
| `*.sumocfg` (arquivos XML) | `simulation.py → create_sumocfg()` | Gerado dinamicamente via config |
| `comparar_simulacoes.py → gerar_graficos()` | `charts.py` | Matplotlib → Plotly interativo |
| `comparar_simulacoes.py → gerar_relatorio()` | `report.py` | Export modular |
| `run_all.bat` | `simulation.py` | Orquestração Python pura |

---

## Módulos

| Módulo | Responsabilidade |
|--------|-----------------|
| `config.py` | `SimulationConfig` dataclass com todos os parâmetros + detecção automática do SUMO |
| `sumo_bridge.py` | Wrappers `subprocess` para sumo.exe e duarouter.exe, parse de progresso |
| `analysis.py` | Importa funções puras do `centro/comparar_simulacoes.py` |
| `charts.py` | Gráficos Plotly: barras comparativas de tráfego e emissões com anotações de variação % |
| `report.py` | Gera relatório Markdown e métricas JSON para download |
| `simulation.py` | Orquestrador: gera demanda XML, roteia com duarouter, cria .sumocfg dinâmico, roda SUMO, analisa resultados |
| `app.py` | Interface Streamlit com sidebar de configuração e área principal de resultados |

---

## Fluxo da Simulação

```
1. Gerar demanda (.rou.xml)        → simulation.generate_demand()
2. Routear com duarouter            → sumo_bridge.run_duarouter()  
3. Criar config As-Is (.sumocfg)    → simulation.create_sumocfg()
4. Rodar simulação As-Is            → simulation.run_simulation()
5. Otimizar rede (tempos verdes)    → simulation.optimize_network()
6. Criar config To-Be (.sumocfg)    → simulation.create_sumocfg()
7. Rodar simulação To-Be            → simulation.run_simulation()
8. Analisar resultados              → analysis.analisar_tripinfo/emissoes()
9. Exibir gráficos e métricas       → charts + report
```

---

## Ordem de Implementação

1. **Fundação:** `config.py` + `sumo_bridge.py`
2. **Análise:** `analysis.py` + `charts.py` + `report.py`
3. **Simulação:** `generate_demand()`, `optimize_network()`, `create_sumocfg()`, `run_asis()`, `run_tobe()`
4. **UI:** `app.py` com sidebar, cards de métricas, gráficos Plotly, downloads
5. **Testes:** 20 testes unitários cobrindo todos os módulos
6. **Documentação:** README.md, PLANO.md, FUNCIONALIDADES.md

---

## Resumo

| Métrica | Valor |
|---------|-------|
| Novos arquivos | 9 (.py + .md + .txt) |
| Arquivos modificados no projeto | 0 |
| Linhas de código | ~1200 |
| Dependências novas | streamlit, plotly (pandas, numpy, matplotlib já existem) |
| Comando para rodar | `streamlit run dashboard/app.py` |
| Cobertura de testes | 20 testes unitários |
