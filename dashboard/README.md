# Dashboard de Simulação de Tráfego

## Quadrilátero Central de Curitiba — UTFPR Ciências do Ambiente 2026/1

Dashboard web interativo que substitui o fluxo complexo de CLI/.bat da pasta `centro/`, permitindo simular tráfego no SUMO, comparar cenários As-Is vs To-Be e visualizar resultados — tudo com alguns cliques.

---

## Requisitos

- **Python 3.11+**
- **SUMO** instalado (https://sumo.dlr.de/docs/Installing/index.html)
  - O dashboard detecta automaticamente via `SUMO_HOME` ou `C:\Program Files (x86)\Eclipse\Sumo\`
- **Pacotes Python:** instale com o comando abaixo

```bash
cd dashboard
pip install -r requirements.txt
```

## Como rodar

```bash
cd dashboard
streamlit run app.py
```

O navegador abre automaticamente em `http://localhost:8501`.

## Estrutura

```
dashboard/
├── app.py                # UI Streamlit (entrada principal)
├── config.py             # SimulationConfig + detecção automática do SUMO
├── sumo_bridge.py        # Wrappers subprocess para sumo.exe e duarouter.exe
├── simulation.py         # Orquestrador: gera demanda, otimiza rede, roda pipeline
├── analysis.py           # Importa parse/análise do centro/comparar_simulacoes.py
├── charts.py             # Gráficos Plotly interativos
├── report.py             # Export Markdown + JSON
├── requirements.txt      # Dependências Python
├── tests/                # Testes unitários (pytest)
│   └── test_dashboard.py
├── results/              # XMLs de saída das simulações (criado automaticamente)
└── output/               # Gráficos e relatórios exportados (criado automaticamente)
```

## Testes

```bash
cd Projeto-Ciencias-Ambiente
python -m pytest dashboard/tests/ -v
```

## Funcionalidades

- **Detecção automática do SUMO** (variável de ambiente ou caminhos padrão Windows)
- **Configuração completa pela sidebar:** duração, volume de veículos, mix da frota, tempo verde
- **Pipeline completo:** geração de demanda → duarouter → simulação As-Is → otimização To-Be → simulação To-Be → análise
- **Métricas em tempo real:** cards com tempo de viagem, velocidade, espera, CO₂, NOx, PMx, combustível
- **Gráficos Plotly interativos** com zoom, hover e variação percentual anotada
- **Export:** relatório Markdown + métricas JSON
- **Fallback:** botão "Analisar Resultados Existentes" para simulações já rodadas
