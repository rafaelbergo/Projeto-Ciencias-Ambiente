#!/usr/bin/env python3
"""
Report generators for traffic simulation comparison.
Produces Markdown reports and JSON metrics files.
"""

import json


def generate_markdown(metrics_trip, metrics_emis):
    """Generate a comparative Markdown report string."""
    lines = [
        "# Relatório Comparativo As-Is vs To-Be",
        "## Quadrilátero Central de Curitiba — UTFPR Ciências do Ambiente 2026/1",
        "",
        "---",
        "",
        "## Indicadores de Tráfego",
        "",
        "| Indicador | Cenário As-Is | Cenário To-Be | Variação (%) |",
        "|-----------|:-------------:|:-------------:|:------------:|",
    ]

    if metrics_trip:
        lines.append(
            f"| Tempo médio de viagem (s) | {metrics_trip.get('tempo_medio_asis', 0):.1f} "
            f"| {metrics_trip.get('tempo_medio_tobe', 0):.1f} "
            f"| {metrics_trip.get('delta_tempo_pct', 0):+.1f}% |"
        )
        lines.append(
            f"| Velocidade média (km/h) | {metrics_trip.get('velocidade_media_asis', 0):.1f} "
            f"| {metrics_trip.get('velocidade_media_tobe', 0):.1f} "
            f"| {metrics_trip.get('delta_velocidade_pct', 0):+.1f}% |"
        )
        lines.append(
            f"| Tempo de espera médio (s) | {metrics_trip.get('espera_media_asis', 0):.1f} "
            f"| {metrics_trip.get('espera_media_tobe', 0):.1f} "
            f"| {metrics_trip.get('delta_espera_pct', 0):+.1f}% |"
        )
        lines.append(
            f"| Time loss médio (s) | {metrics_trip.get('time_loss_asis', 0):.1f} "
            f"| {metrics_trip.get('time_loss_tobe', 0):.1f} | — |"
        )
        lines.append(
            f"| Veículos completados | {metrics_trip.get('n_veiculos_asis', 0)} "
            f"| {metrics_trip.get('n_veiculos_tobe', 0)} | — |"
        )

    lines += [
        "",
        "## Indicadores de Emissões",
        "",
        "| Indicador | Cenário As-Is | Cenário To-Be | Variação (%) |",
        "|-----------|:-------------:|:-------------:|:------------:|",
    ]

    if metrics_emis:
        lines.append(
            f"| CO₂ (kg/h) | {metrics_emis.get('CO2_kg_h_asis', 0):.1f} "
            f"| {metrics_emis.get('CO2_kg_h_tobe', 0):.1f} "
            f"| {metrics_emis.get('delta_CO2_pct', 0):+.1f}% |"
        )
        lines.append(
            f"| NOx (g/h) | {metrics_emis.get('NOx_g_h_asis', 0):.1f} "
            f"| {metrics_emis.get('NOx_g_h_tobe', 0):.1f} "
            f"| {metrics_emis.get('delta_NOx_pct', 0):+.1f}% |"
        )
        lines.append(
            f"| PMx (g/h) | {metrics_emis.get('PMx_g_h_asis', 0):.1f} "
            f"| {metrics_emis.get('PMx_g_h_tobe', 0):.1f} "
            f"| {metrics_emis.get('delta_PMx_pct', 0):+.1f}% |"
        )
        lines.append(
            f"| Combustível (L/h) | {metrics_emis.get('fuel_L_h_asis', 0):.1f} "
            f"| {metrics_emis.get('fuel_L_h_tobe', 0):.1f} "
            f"| {metrics_emis.get('delta_fuel_pct', 0):+.1f}% |"
        )

    lines += [
        "",
        "---",
        "*Relatório gerado pelo Dashboard de Simulação de Tráfego*",
    ]

    return "\n".join(lines)


def generate_json(metrics_trip, metrics_emis):
    """Generate a JSON string with all metrics."""
    data = {
        "trafego": {
            k: v for k, v in (metrics_trip or {}).items()
            if isinstance(v, (int, float))
        },
        "emissoes": {
            k: v for k, v in (metrics_emis or {}).items()
            if isinstance(v, (int, float))
        },
    }
    return json.dumps(data, indent=2, ensure_ascii=False)
