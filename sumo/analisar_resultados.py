#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analisador de Resultados da Simulação SUMO
==========================================
Lê os arquivos tripinfo e emission gerados nas simulações As-Is e To-Be
e gera um relatório comparativo com os indicadores de desempenho.

Uso:
  python analisar_resultados.py

Requisitos:
  pip install pandas matplotlib numpy
"""

import os
import sys
import xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path

try:
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')  # não precisa de GUI
    import matplotlib.pyplot as plt
except ImportError:
    print("ERRO: Instale as dependências:")
    print("  pip install pandas matplotlib numpy")
    sys.exit(1)

# Configura matplotlib para português
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12


# ============================================================
# PARSING DOS ARQUIVOS XML DO SUMO
# ============================================================

def parse_tripinfo(filepath):
    """
    Lê o arquivo tripinfo-output.xml do SUMO.
    Retorna DataFrame com colunas:
      id, depart, arrival, duration, routeLength, waitSteps, timeLoss,
      speed (calculada), vType
    """
    if not os.path.exists(filepath):
        print(f"  [AVISO] Arquivo não encontrado: {filepath}")
        return None

    tree = ET.parse(filepath)
    root = tree.getroot()

    registros = []
    for trip in root.findall('tripinfo'):
        try:
            tid = trip.get('id', '')
            depart = float(trip.get('depart', 0))
            arrival = float(trip.get('arrival', 0))
            duration = float(trip.get('duration', 0))
            route_len = float(trip.get('routeLength', 0))
            wait_steps = float(trip.get('waitSteps', 0))  # número de steps parado
            time_loss = float(trip.get('timeLoss', 0))
            vtype = trip.get('vType', '')

            speed_ms = route_len / duration if duration > 0 else 0
            speed_kmh = speed_ms * 3.6

            registros.append({
                'id': tid,
                'depart': depart,
                'arrival': arrival,
                'duration': duration,
                'route_length': route_len,
                'wait_steps': wait_steps,
                'wait_time': wait_steps * 0.1,  # step-length = 0.1s
                'time_loss': time_loss,
                'speed_kmh': speed_kmh,
                'vtype': vtype,
            })
        except (ValueError, TypeError):
            continue

    return pd.DataFrame(registros)


def parse_emissions(filepath):
    """
    Lê o arquivo emission-output.xml do SUMO.
    Retorna DataFrame com emissões agregadas por poluente.
    """
    if not os.path.exists(filepath):
        print(f"  [AVISO] Arquivo não encontrado: {filepath}")
        return None

    tree = ET.parse(filepath)
    root = tree.getroot()

    registros = []
    for veh in root.findall('vehicle'):
        vid = veh.get('id', '')
        for step in veh.findall('timestep'):
            try:
                t = float(step.get('time', 0))
                co2 = float(step.get('CO2', 0))       # mg/s
                co  = float(step.get('CO', 0))
                nox = float(step.get('NOx', 0))
                pmx = float(step.get('PMx', 0))
                hc  = float(step.get('HC', 0))
                fuel = float(step.get('fuel', 0))      # ml/s
                speed = float(step.get('speed', 0))

                registros.append({
                    'vehicle_id': vid,
                    'time': t,
                    'CO2_mgs': co2,
                    'CO_mgs': co,
                    'NOx_mgs': nox,
                    'PMx_mgs': pmx,
                    'HC_mgs': hc,
                    'fuel_mls': fuel,
                    'speed_ms': speed,
                })
            except (ValueError, TypeError, KeyError):
                continue

    return pd.DataFrame(registros)


def parse_edgedata(filepath):
    """Lê edge-based output para métricas por via."""
    if not os.path.exists(filepath):
        return None

    tree = ET.parse(filepath)
    root = tree.getroot()

    registros = []
    for interval in root.findall('interval'):
        for edge in interval.findall('edge'):
            try:
                registros.append({
                    'interval_start': float(interval.get('begin', 0)),
                    'edge_id': edge.get('id', ''),
                    'entered': float(edge.get('entered', 0)),
                    'density': float(edge.get('density', 0)),
                    'occupancy': float(edge.get('occupancy', 0)),
                    'speed': float(edge.get('speed', 0)),
                    'waitingTime': float(edge.get('waitingTime', 0)),
                })
            except (ValueError, TypeError):
                continue

    return pd.DataFrame(registros)


# ============================================================
# ANÁLISE COMPARATIVA
# ============================================================

def analisar_tripinfo(df_asis, df_tobe):
    """Compara métricas de viagem entre os dois cenários."""
    if df_asis is None or df_tobe is None:
        return {}

    metricas = {}

    # Tempo médio de viagem
    t_asis = df_asis['duration'].mean()
    t_tobe = df_tobe['duration'].mean()
    delta_t = ((t_tobe - t_asis) / t_asis) * 100
    metricas['tempo_medio_asis'] = t_asis
    metricas['tempo_medio_tobe'] = t_tobe
    metricas['delta_tempo_pct'] = delta_t

    # Velocidade média
    v_asis = df_asis['speed_kmh'].mean()
    v_tobe = df_tobe['speed_kmh'].mean()
    delta_v = ((v_tobe - v_asis) / v_asis) * 100 if v_asis > 0 else 0
    metricas['velocidade_media_asis'] = v_asis
    metricas['velocidade_media_tobe'] = v_tobe
    metricas['delta_velocidade_pct'] = delta_v

    # Tempo de espera (parado)
    w_asis = df_asis['wait_time'].mean()
    w_tobe = df_tobe['wait_time'].mean()
    delta_w = ((w_tobe - w_asis) / w_asis) * 100 if w_asis > 0 else 0
    metricas['espera_media_asis'] = w_asis
    metricas['espera_media_tobe'] = w_tobe
    metricas['delta_espera_pct'] = delta_w

    # Time loss
    tl_asis = df_asis['time_loss'].mean()
    tl_tobe = df_tobe['time_loss'].mean()
    metricas['time_loss_asis'] = tl_asis
    metricas['time_loss_tobe'] = tl_tobe

    return metricas


def analisar_emissions(df_asis, df_tobe):
    """Compara emissões entre os cenários."""
    if df_asis is None or df_tobe is None:
        return {}

    metricas = {}

    # Total de CO2 por hora (mg → kg/h)
    duracao_asis = df_asis['time'].max() - df_asis['time'].min()
    duracao_tobe = df_tobe['time'].max() - df_tobe['time'].min()

    co2_total_asis = df_asis['CO2_mgs'].sum() / 1e6  # mg → kg
    co2_total_tobe = df_tobe['CO2_mgs'].sum() / 1e6

    horas_asis = duracao_asis / 3600 if duracao_asis > 0 else 1
    horas_tobe = duracao_tobe / 3600 if duracao_tobe > 0 else 1

    co2_kg_h_asis = co2_total_asis / horas_asis
    co2_kg_h_tobe = co2_total_tobe / horas_tobe
    delta_co2 = ((co2_kg_h_tobe - co2_kg_h_asis) / co2_kg_h_asis) * 100 if co2_kg_h_asis > 0 else 0

    metricas['CO2_kg_h_asis'] = co2_kg_h_asis
    metricas['CO2_kg_h_tobe'] = co2_kg_h_tobe
    metricas['delta_CO2_pct'] = delta_co2

    # NOx (g/h)
    nox_total_asis = df_asis['NOx_mgs'].sum() / 1000  # mg → g
    nox_total_tobe = df_tobe['NOx_mgs'].sum() / 1000
    metricas['NOx_g_h_asis'] = nox_total_asis / horas_asis
    metricas['NOx_g_h_tobe'] = nox_total_tobe / horas_tobe
    delta_nox = ((metricas['NOx_g_h_tobe'] - metricas['NOx_g_h_asis']) / metricas['NOx_g_h_asis']) * 100 if metricas['NOx_g_h_asis'] > 0 else 0
    metricas['delta_NOx_pct'] = delta_nox

    # PMx (g/h)
    pmx_total_asis = df_asis['PMx_mgs'].sum() / 1000
    pmx_total_tobe = df_tobe['PMx_mgs'].sum() / 1000
    metricas['PMx_g_h_asis'] = pmx_total_asis / horas_asis
    metricas['PMx_g_h_tobe'] = pmx_total_tobe / horas_tobe
    delta_pm = ((metricas['PMx_g_h_tobe'] - metricas['PMx_g_h_asis']) / metricas['PMx_g_h_asis']) * 100 if metricas['PMx_g_h_asis'] > 0 else 0
    metricas['delta_PMx_pct'] = delta_pm

    # Consumo de combustível (L/h)
    fuel_total_asis = df_asis['fuel_mls'].sum() / 1000  # ml → L
    fuel_total_tobe = df_tobe['fuel_mls'].sum() / 1000
    metricas['fuel_L_h_asis'] = fuel_total_asis / horas_asis
    metricas['fuel_L_h_tobe'] = fuel_total_tobe / horas_tobe
    delta_fuel = ((metricas['fuel_L_h_tobe'] - metricas['fuel_L_h_asis']) / metricas['fuel_L_h_asis']) * 100 if metricas['fuel_L_h_asis'] > 0 else 0
    metricas['delta_fuel_pct'] = delta_fuel

    return metricas


# ============================================================
# GERAÇÃO DE GRÁFICOS E RELATÓRIO
# ============================================================

def gerar_graficos(metricas_trip, metricas_emis, output_dir):
    """Gera gráficos comparativos."""
    os.makedirs(output_dir, exist_ok=True)

    # Figura 1: Indicadores de tráfego
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    categorias = ['As-Is', 'To-Be']
    cores = ['#E74C3C', '#27AE60']

    # Tempo médio de viagem
    ax = axes[0]
    tempos = [metricas_trip.get('tempo_medio_asis', 0), metricas_trip.get('tempo_medio_tobe', 0)]
    bars = ax.bar(categorias, tempos, color=cores, edgecolor='black', linewidth=0.8)
    ax.set_title('Tempo Médio de Viagem (s)')
    ax.set_ylabel('Segundos')
    for bar, val in zip(bars, tempos):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                f'{val:.1f}', ha='center', fontweight='bold')

    # Velocidade média
    ax = axes[1]
    velocidades = [metricas_trip.get('velocidade_media_asis', 0), metricas_trip.get('velocidade_media_tobe', 0)]
    bars = ax.bar(categorias, velocidades, color=cores, edgecolor='black', linewidth=0.8)
    ax.set_title('Velocidade Média (km/h)')
    ax.set_ylabel('km/h')
    for bar, val in zip(bars, velocidades):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f'{val:.1f}', ha='center', fontweight='bold')

    # Tempo de espera
    ax = axes[2]
    esperas = [metricas_trip.get('espera_media_asis', 0), metricas_trip.get('espera_media_tobe', 0)]
    bars = ax.bar(categorias, esperas, color=cores, edgecolor='black', linewidth=0.8)
    ax.set_title('Tempo de Espera Médio (s)')
    ax.set_ylabel('Segundos')
    for bar, val in zip(bars, esperas):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                f'{val:.1f}', ha='center', fontweight='bold')

    fig.suptitle('Indicadores de Tráfego — Quadrilátero Central de Curitiba', fontsize=16, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'comparativo_trafego.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # Figura 2: Emissões
    if metricas_emis:
        fig, axes = plt.subplots(1, 4, figsize=(18, 5))

        metricas_plot = [
            ('CO2 (kg/h)', 'CO2_kg_h_asis', 'CO2_kg_h_tobe'),
            ('NOx (g/h)', 'NOx_g_h_asis', 'NOx_g_h_tobe'),
            ('PMx (g/h)', 'PMx_g_h_asis', 'PMx_g_h_tobe'),
            ('Combustível (L/h)', 'fuel_L_h_asis', 'fuel_L_h_tobe'),
        ]

        for ax, (titulo, key_asis, key_tobe) in zip(axes, metricas_plot):
            vals = [metricas_emis.get(key_asis, 0), metricas_emis.get(key_tobe, 0)]
            bars = ax.bar(categorias, vals, color=cores, edgecolor='black', linewidth=0.8)
            ax.set_title(titulo)
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(vals) * 0.02,
                        f'{val:.1f}', ha='center', fontweight='bold')

        fig.suptitle('Indicadores de Emissões — Quadrilátero Central de Curitiba', fontsize=16, fontweight='bold')
        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, 'comparativo_emissoes.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)

    print(f"  Gráficos salvos em: {output_dir}/")


def gerar_relatorio_markdown(metricas_trip, metricas_emis, output_path):
    """Gera relatório em Markdown."""
    linhas = []
    linhas.append("# Relatório Comparativo da Simulação SUMO")
    linhas.append("## Quadrilátero Central de Curitiba — Projeto Ciências do Ambiente 2026/1")
    linhas.append("")
    linhas.append("---")
    linhas.append("")

    # Tabela de tráfego
    linhas.append("## Indicadores de Tráfego")
    linhas.append("")
    linhas.append("| Indicador | Cenário As-Is | Cenário To-Be | Variação (%) |")
    linhas.append("|-----------|:-------------:|:-------------:|:------------:|")

    if metricas_trip:
        delta_t = metricas_trip.get('delta_tempo_pct', 0)
        delta_v = metricas_trip.get('delta_velocidade_pct', 0)
        delta_w = metricas_trip.get('delta_espera_pct', 0)

        linhas.append(f"| Tempo médio de viagem (s) | {metricas_trip.get('tempo_medio_asis', 0):.1f} | {metricas_trip.get('tempo_medio_tobe', 0):.1f} | {delta_t:+.1f}% |")
        linhas.append(f"| Velocidade média (km/h) | {metricas_trip.get('velocidade_media_asis', 0):.1f} | {metricas_trip.get('velocidade_media_tobe', 0):.1f} | {delta_v:+.1f}% |")
        linhas.append(f"| Tempo de espera médio (s) | {metricas_trip.get('espera_media_asis', 0):.1f} | {metricas_trip.get('espera_media_tobe', 0):.1f} | {delta_w:+.1f}% |")
        linhas.append(f"| Time loss médio (s) | {metricas_trip.get('time_loss_asis', 0):.1f} | {metricas_trip.get('time_loss_tobe', 0):.1f} | — |")

    linhas.append("")
    linhas.append("## Indicadores de Emissões")
    linhas.append("")
    linhas.append("| Indicador | Cenário As-Is | Cenário To-Be | Variação (%) |")
    linhas.append("|-----------|:-------------:|:-------------:|:------------:|")

    if metricas_emis:
        d_co2 = metricas_emis.get('delta_CO2_pct', 0)
        d_nox = metricas_emis.get('delta_NOx_pct', 0)
        d_pm = metricas_emis.get('delta_PMx_pct', 0)
        d_fuel = metricas_emis.get('delta_fuel_pct', 0)

        linhas.append(f"| CO₂ (kg/h) | {metricas_emis.get('CO2_kg_h_asis', 0):.1f} | {metricas_emis.get('CO2_kg_h_tobe', 0):.1f} | {d_co2:+.1f}% |")
        linhas.append(f"| NOx (g/h) | {metricas_emis.get('NOx_g_h_asis', 0):.1f} | {metricas_emis.get('NOx_g_h_tobe', 0):.1f} | {d_nox:+.1f}% |")
        linhas.append(f"| PMx (g/h) | {metricas_emis.get('PMx_g_h_asis', 0):.1f} | {metricas_emis.get('PMx_g_h_tobe', 0):.1f} | {d_pm:+.1f}% |")
        linhas.append(f"| Combustível (L/h) | {metricas_emis.get('fuel_L_h_asis', 0):.1f} | {metricas_emis.get('fuel_L_h_tobe', 0):.1f} | {d_fuel:+.1f}% |")

    linhas.append("")
    linhas.append("---")
    linhas.append("*Relatório gerado automaticamente pelo script `analisar_resultados.py`*")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linhas))

    print(f"  Relatório Markdown salvo em: {output_path}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("  Analisador de Resultados SUMO")
    print("  Quadrilátero Central de Curitiba")
    print("=" * 60)
    print()

    results_dir = Path('results')
    output_dir = Path('output')

    # Cria diretório de saída
    os.makedirs(output_dir, exist_ok=True)

    # Arquivos de entrada
    tripinfo_asis = results_dir / 'tripinfo_asis.xml'
    tripinfo_tobe = results_dir / 'tripinfo_tobe.xml'
    emissions_asis = results_dir / 'emissions_asis.xml'
    emissions_tobe = results_dir / 'emissions_tobe.xml'

    # Parse
    print("[1/4] Lendo dados de tripinfo As-Is...")
    df_trip_asis = parse_tripinfo(str(tripinfo_asis))
    if df_trip_asis is not None:
        print(f"      {len(df_trip_asis)} viagens encontradas.")

    print("[2/4] Lendo dados de tripinfo To-Be...")
    df_trip_tobe = parse_tripinfo(str(tripinfo_tobe))
    if df_trip_tobe is not None:
        print(f"      {len(df_trip_tobe)} viagens encontradas.")

    print("[3/4] Lendo dados de emissões As-Is...")
    df_emis_asis = parse_emissions(str(emissions_asis))
    if df_emis_asis is not None:
        print(f"      {len(df_emis_asis)} registros de emissão.")

    print("[4/4] Lendo dados de emissões To-Be...")
    df_emis_tobe = parse_emissions(str(emissions_tobe))
    if df_emis_tobe is not None:
        print(f"      {len(df_emis_tobe)} registros de emissão.")

    print()

    # Análise
    print("Analisando métricas de tráfego...")
    metricas_trip = analisar_tripinfo(df_trip_asis, df_trip_tobe)

    print("Analisando métricas de emissões...")
    metricas_emis = analisar_emissions(df_emis_asis, df_emis_tobe)

    # Resultados no terminal
    print()
    print("=" * 60)
    print("  RESUMO DOS RESULTADOS")
    print("=" * 60)

    if metricas_trip:
        dt = metricas_trip.get('delta_tempo_pct', 0)
        dv = metricas_trip.get('delta_velocidade_pct', 0)
        dw = metricas_trip.get('delta_espera_pct', 0)
        print(f"  Tempo de viagem:   {dt:+.1f}%")
        print(f"  Velocidade média:  {dv:+.1f}%")
        print(f"  Tempo de espera:   {dw:+.1f}%")

    if metricas_emis:
        dc = metricas_emis.get('delta_CO2_pct', 0)
        dn = metricas_emis.get('delta_NOx_pct', 0)
        dp = metricas_emis.get('delta_PMx_pct', 0)
        df = metricas_emis.get('delta_fuel_pct', 0)
        print(f"  CO₂:               {dc:+.1f}%")
        print(f"  NOx:               {dn:+.1f}%")
        print(f"  PMx:               {dp:+.1f}%")
        print(f"  Combustível:       {df:+.1f}%")

    print("=" * 60)
    print()

    # Gera gráficos
    print("Gerando gráficos comparativos...")
    gerar_graficos(metricas_trip, metricas_emis, str(output_dir))

    # Gera relatório
    print("Gerando relatório...")
    gerar_relatorio_markdown(metricas_trip, metricas_emis, str(output_dir / 'relatorio_comparativo.md'))

    # Salva métricas em JSON para uso no LaTeX
    import json
    todas_metricas = {
        'trafego': {k: v for k, v in metricas_trip.items() if isinstance(v, (int, float))},
        'emissoes': {k: v for k, v in metricas_emis.items() if isinstance(v, (int, float))},
    }
    with open(output_dir / 'metricas.json', 'w', encoding='utf-8') as f:
        json.dump(todas_metricas, f, indent=2, ensure_ascii=False)
    print(f"  Métricas salvas em: {output_dir / 'metricas.json'}")

    print()
    print("Análise concluída!")
    print(f"Resultados em: {output_dir}/")


if __name__ == '__main__':
    main()
