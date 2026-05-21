#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analisador Comparativo As-Is vs To-Be - Quadrilatero Central de Curitiba
========================================================================
Le os XMLs de tripinfo e emissions das duas simulacoes e gera relatorio.

Uso:
  python comparar_simulacoes.py
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError:
    print("ERRO: Instale: pip install pandas matplotlib numpy")
    sys.exit(1)

plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

RESULTS_DIR = Path('results')
OUTPUT_DIR = Path('output')

# ============================================================
# PARSING
# ============================================================
def parse_tripinfo(filepath):
    if not os.path.exists(filepath):
        print(f"  [AVISO] Nao encontrado: {filepath}")
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
            wait_steps = float(trip.get('waitSteps', 0))
            time_loss = float(trip.get('timeLoss', 0))
            vtype = trip.get('vType', '')

            speed_ms = route_len / duration if duration > 0 else 0
            speed_kmh = speed_ms * 3.6

            registros.append({
                'id': tid, 'depart': depart, 'arrival': arrival,
                'duration': duration, 'route_length': route_len,
                'wait_steps': wait_steps, 'wait_time': wait_steps * 0.1,
                'time_loss': time_loss, 'speed_kmh': speed_kmh,
                'vtype': vtype,
            })
        except (ValueError, TypeError):
            continue
    return pd.DataFrame(registros)

def parse_emissions(filepath):
    if not os.path.exists(filepath):
        print(f"  [AVISO] Nao encontrado: {filepath}")
        return None
    tree = ET.parse(filepath)
    root = tree.getroot()
    registros = []
    # Formato SUMO: <timestep time="..."><vehicle id="..." .../></timestep>
    for ts in root.findall('timestep'):
        t = float(ts.get('time', 0))
        for veh in ts.findall('vehicle'):
            try:
                registros.append({
                    'vehicle_id': veh.get('id', ''),
                    'time': t,
                    'CO2_mgs': float(veh.get('CO2', 0)),
                    'CO_mgs': float(veh.get('CO', 0)),
                    'NOx_mgs': float(veh.get('NOx', 0)),
                    'PMx_mgs': float(veh.get('PMx', 0)),
                    'HC_mgs': float(veh.get('HC', 0)),
                    'fuel_mls': float(veh.get('fuel', 0)),
                    'speed_ms': float(veh.get('speed', 0)),
                })
            except (ValueError, TypeError, KeyError):
                continue
    return pd.DataFrame(registros)

# ============================================================
# ANALISE
# ============================================================
def analisar_tripinfo(df_asis, df_tobe):
    if df_asis is None or df_tobe is None or df_asis.empty or df_tobe.empty:
        return {}
    m = {}
    t_a = df_asis['duration'].mean()
    t_t = df_tobe['duration'].mean()
    m['tempo_medio_asis'] = t_a
    m['tempo_medio_tobe'] = t_t
    m['delta_tempo_pct'] = ((t_t - t_a) / t_a) * 100 if t_a > 0 else 0

    v_a = df_asis['speed_kmh'].mean()
    v_t = df_tobe['speed_kmh'].mean()
    m['velocidade_media_asis'] = v_a
    m['velocidade_media_tobe'] = v_t
    m['delta_velocidade_pct'] = ((v_t - v_a) / v_a) * 100 if v_a > 0 else 0

    w_a = df_asis['wait_time'].mean()
    w_t = df_tobe['wait_time'].mean()
    m['espera_media_asis'] = w_a
    m['espera_media_tobe'] = w_t
    m['delta_espera_pct'] = ((w_t - w_a) / w_a) * 100 if w_a > 0 else 0

    m['time_loss_asis'] = df_asis['time_loss'].mean()
    m['time_loss_tobe'] = df_tobe['time_loss'].mean()

    m['n_veiculos_asis'] = len(df_asis)
    m['n_veiculos_tobe'] = len(df_tobe)

    return m

def analisar_emissions(df_asis, df_tobe):
    if df_asis is None or df_tobe is None or df_asis.empty or df_tobe.empty:
        return {}
    m = {}
    dur_a = df_asis['time'].max() - df_asis['time'].min()
    dur_t = df_tobe['time'].max() - df_tobe['time'].min()
    h_a = dur_a / 3600 if dur_a > 0 else 1
    h_t = dur_t / 3600 if dur_t > 0 else 1

    co2_a = df_asis['CO2_mgs'].sum() / 1e6
    co2_t = df_tobe['CO2_mgs'].sum() / 1e6
    m['CO2_kg_h_asis'] = co2_a / h_a
    m['CO2_kg_h_tobe'] = co2_t / h_t
    m['delta_CO2_pct'] = ((co2_t/h_t - co2_a/h_a) / (co2_a/h_a)) * 100 if co2_a > 0 else 0

    nox_a = df_asis['NOx_mgs'].sum() / 1000
    nox_t = df_tobe['NOx_mgs'].sum() / 1000
    m['NOx_g_h_asis'] = nox_a / h_a
    m['NOx_g_h_tobe'] = nox_t / h_t
    m['delta_NOx_pct'] = ((nox_t/h_t - nox_a/h_a) / (nox_a/h_a)) * 100 if nox_a > 0 else 0

    pm_a = df_asis['PMx_mgs'].sum() / 1000
    pm_t = df_tobe['PMx_mgs'].sum() / 1000
    m['PMx_g_h_asis'] = pm_a / h_a
    m['PMx_g_h_tobe'] = pm_t / h_t
    m['delta_PMx_pct'] = ((pm_t/h_t - pm_a/h_a) / (pm_a/h_a)) * 100 if pm_a > 0 else 0

    fuel_a = df_asis['fuel_mls'].sum() / 1000
    fuel_t = df_tobe['fuel_mls'].sum() / 1000
    m['fuel_L_h_asis'] = fuel_a / h_a
    m['fuel_L_h_tobe'] = fuel_t / h_t
    m['delta_fuel_pct'] = ((fuel_t/h_t - fuel_a/h_a) / (fuel_a/h_a)) * 100 if fuel_a > 0 else 0

    return m

# ============================================================
# GRAFICOS E RELATORIO
# ============================================================
def gerar_graficos(m_trip, m_emis, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cats = ['As-Is', 'To-Be']
    cores = ['#E74C3C', '#27AE60']

    # Trafego
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    pares = [
        ('Tempo Medio de Viagem (s)', 'tempo_medio_asis', 'tempo_medio_tobe'),
        ('Velocidade Media (km/h)', 'velocidade_media_asis', 'velocidade_media_tobe'),
        ('Tempo de Espera Medio (s)', 'espera_media_asis', 'espera_media_tobe'),
    ]
    for ax, (tit, k_a, k_t) in zip(axes, pares):
        vals = [m_trip.get(k_a, 0), m_trip.get(k_t, 0)]
        bars = ax.bar(cats, vals, color=cores, edgecolor='black', linewidth=0.8)
        ax.set_title(tit)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + max(vals)*0.02,
                    f'{v:.1f}', ha='center', fontweight='bold')
    fig.suptitle('Indicadores de Trafego - Quadrilatero Central', fontsize=16, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'comparativo_trafego.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # Emissoes
    if m_emis:
        fig, axes = plt.subplots(1, 4, figsize=(18, 5))
        pares_emis = [
            ('CO2 (kg/h)', 'CO2_kg_h_asis', 'CO2_kg_h_tobe'),
            ('NOx (g/h)', 'NOx_g_h_asis', 'NOx_g_h_tobe'),
            ('PMx (g/h)', 'PMx_g_h_asis', 'PMx_g_h_tobe'),
            ('Combustivel (L/h)', 'fuel_L_h_asis', 'fuel_L_h_tobe'),
        ]
        for ax, (tit, k_a, k_t) in zip(axes, pares_emis):
            vals = [m_emis.get(k_a, 0), m_emis.get(k_t, 0)]
            bars = ax.bar(cats, vals, color=cores, edgecolor='black', linewidth=0.8)
            ax.set_title(tit)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width()/2, b.get_height() + max(vals)*0.02,
                        f'{v:.1f}', ha='center', fontweight='bold')
        fig.suptitle('Indicadores de Emissoes - Quadrilatero Central', fontsize=16, fontweight='bold')
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, 'comparativo_emissoes.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)

    print(f"  Graficos salvos em: {out_dir}/")

def gerar_relatorio(m_trip, m_emis, out_path):
    lines = [
        "# Relatorio Comparativo As-Is vs To-Be",
        "## Quadrilatero Central de Curitiba - UTFPR Ciencias do Ambiente 2026/1",
        "",
        "---",
        "",
        "## Indicadores de Trafego",
        "",
        "| Indicador | Cenario As-Is | Cenario To-Be | Variacao (%) |",
        "|-----------|:-------------:|:-------------:|:------------:|",
    ]
    if m_trip:
        dt = m_trip.get('delta_tempo_pct', 0)
        dv = m_trip.get('delta_velocidade_pct', 0)
        dw = m_trip.get('delta_espera_pct', 0)
        lines.append(f"| Tempo medio de viagem (s) | {m_trip.get('tempo_medio_asis', 0):.1f} | {m_trip.get('tempo_medio_tobe', 0):.1f} | {dt:+.1f}% |")
        lines.append(f"| Velocidade media (km/h) | {m_trip.get('velocidade_media_asis', 0):.1f} | {m_trip.get('velocidade_media_tobe', 0):.1f} | {dv:+.1f}% |")
        lines.append(f"| Tempo de espera medio (s) | {m_trip.get('espera_media_asis', 0):.1f} | {m_trip.get('espera_media_tobe', 0):.1f} | {dw:+.1f}% |")
        lines.append(f"| Time loss medio (s) | {m_trip.get('time_loss_asis', 0):.1f} | {m_trip.get('time_loss_tobe', 0):.1f} | -- |")
        lines.append(f"| Veiculos completados | {m_trip.get('n_veiculos_asis', 0)} | {m_trip.get('n_veiculos_tobe', 0)} | -- |")

    lines += [
        "",
        "## Indicadores de Emissoes",
        "",
        "| Indicador | Cenario As-Is | Cenario To-Be | Variacao (%) |",
        "|-----------|:-------------:|:-------------:|:------------:|",
    ]
    if m_emis:
        dc = m_emis.get('delta_CO2_pct', 0)
        dn = m_emis.get('delta_NOx_pct', 0)
        dp = m_emis.get('delta_PMx_pct', 0)
        df = m_emis.get('delta_fuel_pct', 0)
        lines.append(f"| CO2 (kg/h) | {m_emis.get('CO2_kg_h_asis', 0):.1f} | {m_emis.get('CO2_kg_h_tobe', 0):.1f} | {dc:+.1f}% |")
        lines.append(f"| NOx (g/h) | {m_emis.get('NOx_g_h_asis', 0):.1f} | {m_emis.get('NOx_g_h_tobe', 0):.1f} | {dn:+.1f}% |")
        lines.append(f"| PMx (g/h) | {m_emis.get('PMx_g_h_asis', 0):.1f} | {m_emis.get('PMx_g_h_tobe', 0):.1f} | {dp:+.1f}% |")
        lines.append(f"| Combustivel (L/h) | {m_emis.get('fuel_L_h_asis', 0):.1f} | {m_emis.get('fuel_L_h_tobe', 0):.1f} | {df:+.1f}% |")

    lines += [
        "",
        "---",
        "*Relatorio gerado por comparar_simulacoes.py*",
    ]

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  Relatorio salvo em: {out_path}")

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("  Analisador Comparativo As-Is vs To-Be")
    print("  Quadrilatero Central de Curitiba")
    print("=" * 60)
    print()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ta = RESULTS_DIR / 'tripinfo_asis.xml'
    tt = RESULTS_DIR / 'tripinfo_tobe.xml'
    ea = RESULTS_DIR / 'emissions_asis.xml'
    et = RESULTS_DIR / 'emissions_tobe.xml'

    print("[1/4] Lendo tripinfo As-Is...")
    df_ta = parse_tripinfo(str(ta))
    print(f"      {len(df_ta) if df_ta is not None else 0} viagens.")

    print("[2/4] Lendo tripinfo To-Be...")
    df_tt = parse_tripinfo(str(tt))
    print(f"      {len(df_tt) if df_tt is not None else 0} viagens.")

    print("[3/4] Lendo emissoes As-Is...")
    df_ea = parse_emissions(str(ea))
    print(f"      {len(df_ea) if df_ea is not None else 0} registros.")

    print("[4/4] Lendo emissoes To-Be...")
    df_et = parse_emissions(str(et))
    print(f"      {len(df_et) if df_et is not None else 0} registros.")

    print()
    print("Analisando metricas...")
    mt = analisar_tripinfo(df_ta, df_tt)
    me = analisar_emissions(df_ea, df_et)

    print()
    print("=" * 60)
    print("  RESUMO")
    print("=" * 60)
    if mt:
        print(f"  Tempo de viagem:  {mt.get('delta_tempo_pct', 0):+.1f}%")
        print(f"  Velocidade media: {mt.get('delta_velocidade_pct', 0):+.1f}%")
        print(f"  Tempo de espera:  {mt.get('delta_espera_pct', 0):+.1f}%")
    if me:
        print(f"  CO2:              {me.get('delta_CO2_pct', 0):+.1f}%")
        print(f"  NOx:              {me.get('delta_NOx_pct', 0):+.1f}%")
        print(f"  PMx:              {me.get('delta_PMx_pct', 0):+.1f}%")
        print(f"  Combustivel:      {me.get('delta_fuel_pct', 0):+.1f}%")
    print("=" * 60)
    print()

    print("Gerando graficos...")
    gerar_graficos(mt, me, str(OUTPUT_DIR))

    print("Gerando relatorio...")
    gerar_relatorio(mt, me, str(OUTPUT_DIR / 'relatorio_comparativo.md'))

    # Salvar metricas JSON
    todas = {
        'trafego': {k: v for k, v in mt.items() if isinstance(v, (int, float))},
        'emissoes': {k: v for k, v in me.items() if isinstance(v, (int, float))},
    }
    with open(OUTPUT_DIR / 'metricas.json', 'w', encoding='utf-8') as f:
        json.dump(todas, f, indent=2, ensure_ascii=False)
    print(f"  Metricas JSON salvas em: {OUTPUT_DIR / 'metricas.json'}")

    print()
    print("Analise concluida!")

if __name__ == '__main__':
    main()
