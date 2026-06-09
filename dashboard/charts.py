#!/usr/bin/env python3
"""
Interactive Plotly charts for traffic simulation comparison.
Replaces the static matplotlib charts from centro/comparar_simulacoes.py.
"""

import plotly.graph_objects as go
import plotly.express as px

COLORS = {"As-Is": "#E74C3C", "To-Be": "#27AE60"}
CARD_STYLE = dict(padding="1.5rem", border_radius="0.5rem")


def create_traffic_chart(metrics):
    """Bar chart comparing traffic indicators: duration, speed, wait time."""
    if not metrics:
        return go.Figure()

    categories = ["Tempo de Viagem (s)", "Velocidade (km/h)", "Tempo de Espera (s)"]
    asis_vals = [
        metrics.get("tempo_medio_asis", 0),
        metrics.get("velocidade_media_asis", 0),
        metrics.get("espera_media_asis", 0),
    ]
    tobe_vals = [
        metrics.get("tempo_medio_tobe", 0),
        metrics.get("velocidade_media_tobe", 0),
        metrics.get("espera_media_tobe", 0),
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="As-Is",
        x=categories,
        y=asis_vals,
        marker_color=COLORS["As-Is"],
        text=[f"{v:.1f}" for v in asis_vals],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="To-Be",
        x=categories,
        y=tobe_vals,
        marker_color=COLORS["To-Be"],
        text=[f"{v:.1f}" for v in tobe_vals],
        textposition="outside",
    ))

    # Variação percentual anotada
    deltas = [
        metrics.get("delta_tempo_pct", 0),
        metrics.get("delta_velocidade_pct", 0),
        metrics.get("delta_espera_pct", 0),
    ]
    for i, (cat, d) in enumerate(zip(categories, deltas)):
        sign = "↑" if d >= 0 else "↓"
        color = "green" if (
            (cat.startswith("Tempo") and d < 0) or
            (cat.startswith("Velocidade") and d > 0)
        ) else "red"
        fig.add_annotation(
            x=cat, y=max(asis_vals[i], tobe_vals[i]) * 1.08,
            text=f"<span style='color:{color}'>{sign} {abs(d):.1f}%</span>",
            showarrow=False,
            font=dict(size=12),
        )

    fig.update_layout(
        title="Indicadores de Tráfego — As-Is vs To-Be",
        barmode="group",
        yaxis_title="Valor",
        template="plotly_white",
        legend=dict(orientation="h", y=1.12),
        height=400,
    )

    return fig


def create_emissions_chart(metrics):
    """Bar chart comparing emissions: CO2, NOx, PMx, fuel."""
    if not metrics:
        return go.Figure()

    categories = ["CO₂ (kg/h)", "NOx (g/h)", "PMx (g/h)", "Combustível (L/h)"]
    asis_vals = [
        metrics.get("CO2_kg_h_asis", 0),
        metrics.get("NOx_g_h_asis", 0),
        metrics.get("PMx_g_h_asis", 0),
        metrics.get("fuel_L_h_asis", 0),
    ]
    tobe_vals = [
        metrics.get("CO2_kg_h_tobe", 0),
        metrics.get("NOx_g_h_tobe", 0),
        metrics.get("PMx_g_h_tobe", 0),
        metrics.get("fuel_L_h_tobe", 0),
    ]
    deltas = [
        metrics.get("delta_CO2_pct", 0),
        metrics.get("delta_NOx_pct", 0),
        metrics.get("delta_PMx_pct", 0),
        metrics.get("delta_fuel_pct", 0),
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="As-Is",
        x=categories,
        y=asis_vals,
        marker_color=COLORS["As-Is"],
        text=[f"{v:.1f}" for v in asis_vals],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="To-Be",
        x=categories,
        y=tobe_vals,
        marker_color=COLORS["To-Be"],
        text=[f"{v:.1f}" for v in tobe_vals],
        textposition="outside",
    ))

    for i, (cat, d) in enumerate(zip(categories, deltas)):
        sign = "↑" if d >= 0 else "↓"
        color = "green" if d < 0 else "red"
        fig.add_annotation(
            x=cat, y=max(asis_vals[i], tobe_vals[i]) * 1.08,
            text=f"<span style='color:{color}'>{sign} {abs(d):.1f}%</span>",
            showarrow=False,
            font=dict(size=12),
        )

    fig.update_layout(
        title="Indicadores de Emissões — As-Is vs To-Be",
        barmode="group",
        yaxis_title="Valor",
        template="plotly_white",
        legend=dict(orientation="h", y=1.12),
        height=400,
    )

    return fig
