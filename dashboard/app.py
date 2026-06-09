#!/usr/bin/env python3
"""
Dashboard de Simulacao de Trafego — Quadrilatero Central de Curitiba
====================================================================
Streamlit web app that replaces the complex CLI/bat workflow with an
interactive dashboard for SUMO traffic simulations.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from config import SimulationConfig, detect_sumo, CENTRO_PATH, DASHBOARD_PATH
from charts import create_traffic_chart, create_emissions_chart
from report import generate_markdown, generate_json
from simulation import run_full_pipeline, analyze_existing_results

st.set_page_config(
    page_title="Simulação de Tráfego — Quadrilátero Central",
    page_icon="🚦",
    layout="wide",
)

# ============================================================
# SESSION STATE INIT — each parameter is its own key
# ============================================================
# Non-widget keys only (widgets manage their own session_state via key=)
_NON_WIDGET_KEYS = {
    "sumo_detected": None,
    "pipeline_running": False,
    "pipeline_progress": 0.0,
    "pipeline_status": "",
    "metrics_trip": {},
    "metrics_emis": {},
    "pipeline_error": None,
    "pipeline_done": False,
}

for key, val in _NON_WIDGET_KEYS.items():
    if key not in st.session_state:
        st.session_state[key] = val


def build_config():
    """Build a SimulationConfig from current session state values."""
    sumo = st.session_state["sumo_detected"] or {}
    return SimulationConfig(
        sumo_exe=sumo.get("sumo_exe", ""),
        duarouter_exe=sumo.get("duarouter_exe", ""),
        duration_s=st.session_state["duration_s"],
        step_length_s=st.session_state["step_length_s"],
        seed=st.session_state["seed"],
        total_flow_veh_h=st.session_state["total_flow_veh_h"],
        vehicle_mix={
            "carro_gasolina": st.session_state["mix_gasolina"],
            "carro_etanol": st.session_state["mix_etanol"],
            "moto": st.session_state["mix_moto"],
            "onibus": st.session_state["mix_onibus"],
            "vuc": st.session_state["mix_vuc"],
        },
        tobe_green_time=st.session_state["tobe_green_time"],
    )


# ============================================================
# SUMO DETECTION (once)
# ============================================================
if st.session_state["sumo_detected"] is None:
    st.session_state["sumo_detected"] = detect_sumo()

sumo = st.session_state["sumo_detected"]

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("🚦 Simulação de Tráfego")
    st.caption("Quadrilátero Central de Curitiba")
    st.caption("UTFPR — Ciências do Ambiente 2026/1")

    # SUMO status
    if sumo.get("sumo_exe"):
        from sumo_bridge import run_sumo_version
        version = run_sumo_version(sumo["sumo_exe"])
        st.success(f"✅ SUMO detectado")
        if version:
            st.caption(version)
    else:
        st.error("❌ SUMO não encontrado")
        st.caption(sumo.get("error", ""))

    st.divider()

    # Simulation parameters — bound directly to session_state keys
    st.subheader("⚙️ Simulação")
    st.number_input(
        "Duração (s)", min_value=600, max_value=10800,
        value=3600, step=600, key="duration_s",
    )
    st.number_input(
        "Precisão (s)", min_value=0.05, max_value=1.0,
        value=0.1, step=0.05, format="%.2f", key="step_length_s",
    )
    st.number_input("Seed", value=42, step=1, key="seed")

    st.divider()

    # Vehicle demand
    st.subheader("🚗 Demanda Veicular")
    st.slider(
        "Volume total (veh/h)", 50, 2000, 459, 10,
        key="total_flow_veh_h",
    )

    cols = st.columns(5)
    cols[0].number_input("Gasolina%", 0, 100, value=55, key="mix_gasolina")
    cols[1].number_input("Etanol%", 0, 100, value=15, key="mix_etanol")
    cols[2].number_input("Moto%", 0, 100, value=12, key="mix_moto")
    cols[3].number_input("Ônibus%", 0, 100, value=13, key="mix_onibus")
    cols[4].number_input("VUC%", 0, 100, value=5, key="mix_vuc")

    total_pct = (
        st.session_state["mix_gasolina"]
        + st.session_state["mix_etanol"]
        + st.session_state["mix_moto"]
        + st.session_state["mix_onibus"]
        + st.session_state["mix_vuc"]
    )
    if total_pct != 100:
        st.warning(f"⚠️ Soma = {total_pct}% (deve ser 100%)")

    st.divider()

    # To-Be configuration
    st.subheader("🚦 Cenário To-Be")
    st.slider(
        "Tempo verde fixo (s)", 10, 90, 35, 5,
        key="tobe_green_time",
    )
    st.caption("To-Be usa tempos verdes otimizados em todos os semáforos.")

    st.divider()

    # Action buttons
    col1, col2 = st.columns(2)
    run_full = col1.button(
        "▶️ Rodar Pipeline",
        width="stretch",
        type="primary",
        disabled=not sumo.get("sumo_exe"),
    )
    analyze_existing = col2.button(
        "📊 Analisar Resultados",
        width="stretch",
    )

    st.divider()
    st.caption(f"Mapa: {CENTRO_PATH / 'quadrilatero.net.xml'}")
    st.caption(f"Resultados: {DASHBOARD_PATH / 'results'}")


# ============================================================
# MAIN AREA
# ============================================================
st.title("🏙️ Simulação de Tráfego — Quadrilátero Central")
st.caption("Comparação de cenários As-Is vs To-Be")

progress_placeholder = st.empty()
status_placeholder = st.empty()


def update_progress(p, msg):
    st.session_state["pipeline_progress"] = p
    st.session_state["pipeline_status"] = msg


if st.session_state["pipeline_running"]:
    p = st.session_state["pipeline_progress"]
    msg = st.session_state["pipeline_status"]
    progress_placeholder.progress(p, text=msg)

# Show stored error
if st.session_state["pipeline_error"]:
    status_placeholder.error(st.session_state["pipeline_error"])

if st.session_state["pipeline_done"]:
    status_placeholder.success("✅ Pipeline concluído com sucesso!")


# ============================================================
# ACTION: Run Full Pipeline
# ============================================================
if run_full:
    config = build_config()
    errors = config.validate()
    total_pct_widget = (
        st.session_state["mix_gasolina"]
        + st.session_state["mix_etanol"]
        + st.session_state["mix_moto"]
        + st.session_state["mix_onibus"]
        + st.session_state["mix_vuc"]
    )
    if total_pct_widget != 100:
        errors.append(f"vehicle_mix percentages must sum to 100, got {total_pct_widget}")

    if errors:
        for e in errors:
            st.error(e)
    else:
        st.session_state["pipeline_running"] = True
        st.session_state["pipeline_done"] = False
        st.session_state["pipeline_error"] = None
        st.session_state["metrics_trip"] = {}
        st.session_state["metrics_emis"] = {}

        with st.spinner("Executando pipeline..."):
            results = run_full_pipeline(config, update_progress)

        st.session_state["metrics_trip"] = results.get("metrics_trip", {})
        st.session_state["metrics_emis"] = results.get("metrics_emis", {})
        st.session_state["pipeline_running"] = False

        if results["success"]:
            st.session_state["pipeline_done"] = True
            st.session_state["pipeline_error"] = None
            st.balloons()
        else:
            st.session_state["pipeline_done"] = False
            st.session_state["pipeline_error"] = f"❌ Erro: {results['error']}"
        st.rerun()


# ============================================================
# ACTION: Analyze Existing Results
# ============================================================
if analyze_existing:
    with st.spinner("Analisando resultados existentes..."):
        results = analyze_existing_results()
    st.session_state["metrics_trip"] = results.get("metrics_trip", {})
    st.session_state["metrics_emis"] = results.get("metrics_emis", {})
    if results["success"]:
        st.session_state["pipeline_error"] = None
        status_placeholder.success("✅ Resultados analisados!")
    else:
        st.session_state["pipeline_error"] = f"❌ {results['error']}"
        status_placeholder.error(st.session_state["pipeline_error"])


# ============================================================
# DISPLAY RESULTS
# ============================================================
mt = st.session_state.get("metrics_trip", {})
me = st.session_state.get("metrics_emis", {})

if mt or me:
    st.divider()

    st.subheader("📈 Resumo Comparativo")

    if mt:
        cols = st.columns(3)
        dt = mt.get("delta_tempo_pct", 0)
        dv = mt.get("delta_velocidade_pct", 0)
        dw = mt.get("delta_espera_pct", 0)

        cols[0].metric(
            "⏱ Tempo Médio (s)",
            f"{mt.get('tempo_medio_tobe', 0):.1f}",
            f"{dt:+.1f}% vs As-Is",
            delta_color="normal" if dt < 0 else "inverse",
        )
        cols[1].metric(
            "🚗 Velocidade Média (km/h)",
            f"{mt.get('velocidade_media_tobe', 0):.1f}",
            f"{dv:+.1f}% vs As-Is",
            delta_color="normal" if dv > 0 else "inverse",
        )
        cols[2].metric(
            "⏳ Espera Média (s)",
            f"{mt.get('espera_media_tobe', 0):.1f}",
            f"{dw:+.1f}% vs As-Is",
            delta_color="normal" if dw < 0 else "inverse",
        )

    if me:
        cols = st.columns(4)
        dc = me.get("delta_CO2_pct", 0)
        dn = me.get("delta_NOx_pct", 0)
        dp = me.get("delta_PMx_pct", 0)
        df = me.get("delta_fuel_pct", 0)

        cols[0].metric(
            "🌿 CO₂ (kg/h)",
            f"{me.get('CO2_kg_h_tobe', 0):.1f}",
            f"{dc:+.1f}%",
            delta_color="normal" if dc < 0 else "inverse",
        )
        cols[1].metric(
            "💨 NOx (g/h)",
            f"{me.get('NOx_g_h_tobe', 0):.1f}",
            f"{dn:+.1f}%",
            delta_color="normal" if dn < 0 else "inverse",
        )
        cols[2].metric(
            "🌫️ PMx (g/h)",
            f"{me.get('PMx_g_h_tobe', 0):.1f}",
            f"{dp:+.1f}%",
            delta_color="normal" if dp < 0 else "inverse",
        )
        cols[3].metric(
            "⛽ Combustível (L/h)",
            f"{me.get('fuel_L_h_tobe', 0):.1f}",
            f"{df:+.1f}%",
            delta_color="normal" if df < 0 else "inverse",
        )

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📊 Tráfego")
        fig_traffic = create_traffic_chart(mt)
        st.plotly_chart(fig_traffic, width="stretch")
        if mt:
            st.caption(
                f"Veículos: As-Is = {mt.get('n_veiculos_asis', '?')} | "
                f"To-Be = {mt.get('n_veiculos_tobe', '?')}"
            )

    with col_right:
        st.subheader("🌿 Emissões")
        fig_emissions = create_emissions_chart(me)
        st.plotly_chart(fig_emissions, width="stretch")

    st.divider()

    st.subheader("📥 Exportar Resultados")
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        report_md = generate_markdown(mt, me)
        st.download_button(
            "⬇️ Relatório (.md)",
            data=report_md,
            file_name="relatorio_comparativo.md",
            mime="text/markdown",
        )

    with col_dl2:
        report_json = generate_json(mt, me)
        st.download_button(
            "⬇️ Métricas (.json)",
            data=report_json,
            file_name="metricas.json",
            mime="application/json",
        )
