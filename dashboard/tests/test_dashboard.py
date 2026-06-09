#!/usr/bin/env python3
"""
Unit tests for dashboard modules.
Run with: python -m pytest dashboard/tests/ -v
Or:      cd dashboard && python -m pytest tests/ -v
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure dashboard/ is importable from tests/
DASHBOARD_PATH = Path(__file__).parent.parent
if str(DASHBOARD_PATH) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_PATH))

import pytest
import pandas as pd
import numpy as np


# ============================================================
# Helpers
# ============================================================
@pytest.fixture
def sample_metrics_trip():
    return {
        "tempo_medio_asis": 45.2,
        "tempo_medio_tobe": 41.8,
        "delta_tempo_pct": -7.5,
        "velocidade_media_asis": 22.1,
        "velocidade_media_tobe": 24.3,
        "delta_velocidade_pct": 9.95,
        "espera_media_asis": 12.5,
        "espera_media_tobe": 8.9,
        "delta_espera_pct": -28.8,
        "time_loss_asis": 15.3,
        "time_loss_tobe": 12.1,
        "n_veiculos_asis": 450,
        "n_veiculos_tobe": 455,
    }


@pytest.fixture
def sample_metrics_emis():
    return {
        "CO2_kg_h_asis": 125.4,
        "CO2_kg_h_tobe": 118.2,
        "delta_CO2_pct": -5.74,
        "NOx_g_h_asis": 8.2,
        "NOx_g_h_tobe": 7.5,
        "delta_NOx_pct": -8.54,
        "PMx_g_h_asis": 1.2,
        "PMx_g_h_tobe": 1.0,
        "delta_PMx_pct": -16.67,
        "fuel_L_h_asis": 42.3,
        "fuel_L_h_tobe": 39.8,
        "delta_fuel_pct": -5.91,
    }


@pytest.fixture
def sample_tripinfo_df():
    return pd.DataFrame({
        "id": [f"veh_{i}" for i in range(10)],
        "depart": np.linspace(0, 900, 10),
        "arrival": np.linspace(50, 1000, 10),
        "duration": np.random.uniform(30, 80, 10),
        "route_length": np.random.uniform(500, 2000, 10),
        "wait_steps": np.random.randint(0, 200, 10),
        "wait_time": np.random.uniform(0, 20, 10),
        "time_loss": np.random.uniform(5, 25, 10),
        "speed_kmh": np.random.uniform(15, 45, 10),
        "vtype": ["carro_gasolina"] * 5 + ["carro_etanol"] * 5,
    })


@pytest.fixture
def sample_emissions_df():
    return pd.DataFrame({
        "vehicle_id": [f"veh_{i}" for i in range(10) for _ in range(5)],
        "time": np.tile(np.arange(0, 500, 100), 10),
        "CO2_mgs": np.random.uniform(100, 5000, 50),
        "CO_mgs": np.random.uniform(1, 50, 50),
        "NOx_mgs": np.random.uniform(0.1, 10, 50),
        "PMx_mgs": np.random.uniform(0.01, 1, 50),
        "HC_mgs": np.random.uniform(0.1, 5, 50),
        "fuel_mls": np.random.uniform(1, 50, 50),
        "speed_ms": np.random.uniform(0, 15, 50),
    })


# ============================================================
# config.py tests
# ============================================================
class TestSimulationConfig:
    def test_default_values(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "config", Path(__file__).parent.parent / "config.py"
        )
        config_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_mod)
        SimulationConfig = config_mod.SimulationConfig

        config = SimulationConfig()
        assert config.duration_s == 3600
        assert config.step_length_s == 0.1
        assert config.seed == 42
        assert config.total_flow_veh_h == 459
        assert config.tobe_green_time == 35
        assert config.vehicle_mix["carro_gasolina"] == 55

    def test_validation_passes_with_valid_config(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "config", Path(__file__).parent.parent / "config.py"
        )
        config_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_mod)
        SimulationConfig = config_mod.SimulationConfig

        config = SimulationConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validation_fails_bad_mix(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "config", Path(__file__).parent.parent / "config.py"
        )
        config_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_mod)
        SimulationConfig = config_mod.SimulationConfig

        config = SimulationConfig(vehicle_mix={"carro_gasolina": 50, "carro_etanol": 30})
        errors = config.validate()
        assert any("sum to 100" in e for e in errors)

    def test_validation_fails_negative_duration(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "config", Path(__file__).parent.parent / "config.py"
        )
        config_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_mod)
        SimulationConfig = config_mod.SimulationConfig

        config = SimulationConfig(duration_s=-100)
        errors = config.validate()
        assert any("duration_s" in e for e in errors)


# ============================================================
# charts.py tests
# ============================================================
class TestCharts:
    def test_traffic_chart_returns_figure(self, sample_metrics_trip):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "charts", Path(__file__).parent.parent / "charts.py"
        )
        charts_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(charts_mod)

        fig = charts_mod.create_traffic_chart(sample_metrics_trip)
        assert fig is not None
        assert len(fig.data) == 2  # As-Is and To-Be traces

    def test_traffic_chart_empty_metrics(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "charts", Path(__file__).parent.parent / "charts.py"
        )
        charts_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(charts_mod)

        fig = charts_mod.create_traffic_chart({})
        assert len(fig.data) == 0

    def test_emissions_chart_returns_figure(self, sample_metrics_emis):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "charts", Path(__file__).parent.parent / "charts.py"
        )
        charts_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(charts_mod)

        fig = charts_mod.create_emissions_chart(sample_metrics_emis)
        assert fig is not None
        assert len(fig.data) == 2

    def test_emissions_chart_empty_metrics(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "charts", Path(__file__).parent.parent / "charts.py"
        )
        charts_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(charts_mod)

        fig = charts_mod.create_emissions_chart({})
        assert len(fig.data) == 0


# ============================================================
# report.py tests
# ============================================================
class TestReport:
    def test_markdown_generation(self, sample_metrics_trip, sample_metrics_emis):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "report", Path(__file__).parent.parent / "report.py"
        )
        report_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(report_mod)

        md = report_mod.generate_markdown(sample_metrics_trip, sample_metrics_emis)
        assert "Relatório Comparativo" in md
        assert "Quadrilátero Central" in md
        assert "Indicadores de Tráfego" in md
        assert "Indicadores de Emissões" in md
        assert "45.2" in md
        assert "125.4" in md

    def test_markdown_empty_metrics(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "report", Path(__file__).parent.parent / "report.py"
        )
        report_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(report_mod)

        md = report_mod.generate_markdown({}, {})
        assert "Relatório Comparativo" in md

    def test_json_generation(self, sample_metrics_trip, sample_metrics_emis):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "report", Path(__file__).parent.parent / "report.py"
        )
        report_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(report_mod)

        js = report_mod.generate_json(sample_metrics_trip, sample_metrics_emis)
        data = json.loads(js)
        assert "trafego" in data
        assert "emissoes" in data
        assert data["trafego"]["tempo_medio_asis"] == 45.2
        assert data["emissoes"]["CO2_kg_h_asis"] == 125.4


# ============================================================
# sumo_bridge.py tests
# ============================================================
class TestSumoBridge:
    def test_find_executable_none_found(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "sumo_bridge", Path(__file__).parent.parent / "sumo_bridge.py"
        )
        bridge_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bridge_mod)

        result = bridge_mod.find_executable("nonexistent_executable_xyz123")
        assert result is None

    def test_ensure_dirs(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "sumo_bridge", Path(__file__).parent.parent / "sumo_bridge.py"
        )
        bridge_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bridge_mod)

        with tempfile.TemporaryDirectory() as tmp:
            created = bridge_mod.ensure_dirs(tmp, "results", "output")
            assert len(created) == 2
            assert Path(tmp, "results").is_dir()
            assert Path(tmp, "output").is_dir()

    def test_parse_sumo_progress(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "sumo_bridge", Path(__file__).parent.parent / "sumo_bridge.py"
        )
        bridge_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bridge_mod)

        step = bridge_mod.parse_sumo_progress("Simulation step 1500 completed")
        assert step == 1500

        assert bridge_mod.parse_sumo_progress("Loading network...") is None

    @patch("subprocess.run")
    def test_run_sumo_version(self, mock_run, tmp_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "sumo_bridge", Path(__file__).parent.parent / "sumo_bridge.py"
        )
        bridge_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bridge_mod)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "SUMO Version 1.20.0\n"
        mock_run.return_value = mock_result

        version = bridge_mod.run_sumo_version("fake_sumo.exe")
        assert version is not None
        assert "SUMO" in version


# ============================================================
# simulation.py unit tests (logic only, no actual SUMO)
# ============================================================
class TestSimulationLogic:
    def test_generate_demand_creates_file(self, tmp_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "config", Path(__file__).parent.parent / "config.py"
        )
        config_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_mod)
        SimulationConfig = config_mod.SimulationConfig

        config = SimulationConfig(duration_s=600)

        # Create a minimal .net.xml for testing
        net_path = tmp_path / "test_net.xml"
        net_xml = """<?xml version="1.0"?>
<net version="1.20">
    <edge id="edgeA" from="n1" to="n2" type="highway.primary">
        <lane id="edgeA_0" speed="13.89" length="200"/>
    </edge>
    <edge id="edgeB" from="n2" to="n3" type="highway.secondary">
        <lane id="edgeB_0" speed="13.89" length="150"/>
    </edge>
    <edge id="edgeC" from="n3" to="n4" type="highway.tertiary">
        <lane id="edgeC_0" speed="13.89" length="180"/>
    </edge>
    <edge id=":internal_1" function="internal"/>
</net>"""
        net_path.write_text(net_xml)

        from simulation import generate_demand
        rou_path = generate_demand(config, tmp_path, net_path)

        assert rou_path.exists()
        content = rou_path.read_text()
        assert "<routes" in content
        assert "carro_gasolina" in content
        assert "flow" in content

    def test_optimize_network(self, tmp_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "config", Path(__file__).parent.parent / "config.py"
        )
        config_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_mod)
        SimulationConfig = config_mod.SimulationConfig

        config = SimulationConfig(tobe_green_time=25)

        net_path = tmp_path / "test_net.xml"
        net_xml = """<?xml version="1.0"?>
<net version="1.20">
    <tlLogic id="J1" type="static" programID="0" offset="0">
        <phase duration="31" state="GGggrrrrGGggrrrr"/>
        <phase duration="3" state="yyggrrrryyggrrrr"/>
        <phase duration="31" state="rrrrGGggrrrrGGgg"/>
        <phase duration="3" state="rrrryyggrrrryygg"/>
    </tlLogic>
    <edge id="edgeA" from="n1" to="n2">
        <lane id="edgeA_0" speed="13.89" length="200"/>
    </edge>
</net>"""
        net_path.write_text(net_xml)

        from simulation import optimize_network
        output_path = tmp_path / "tobe_net.xml"
        tl_count, modified = optimize_network(config, net_path, output_path)

        assert tl_count == 1
        assert modified > 0
        assert output_path.exists()

        import xml.etree.ElementTree as ET
        tree = ET.parse(str(output_path))
        root = tree.getroot()
        phases = root.findall(".//phase")
        for phase in phases:
            state = phase.get("state", "")
            if "G" in state:
                assert phase.get("duration") == "25"

    def test_create_sumocfg(self, tmp_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "config", Path(__file__).parent.parent / "config.py"
        )
        config_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_mod)
        SimulationConfig = config_mod.SimulationConfig

        config = SimulationConfig(duration_s=1800, seed=999)

        from simulation import create_sumocfg
        cfg_path = create_sumocfg(
            config, "asis", tmp_path,
            "test.net.xml", "test.rou.xml", "results",
        )

        assert cfg_path.exists()
        content = cfg_path.read_text()
        assert "1800" in content
        assert "999" in content
        assert "tripinfo_asis.xml" in content


# ============================================================
# Integration test on analysis wrappers
# ============================================================
class TestAnalysisIntegration:
    def test_analisar_tripinfo_with_data(self, sample_tripinfo_df):
        # Directly test the functions from centro/ if available
        try:
            from analysis import analisar_tripinfo
            metrics = analisar_tripinfo(sample_tripinfo_df, sample_tripinfo_df)
            assert "tempo_medio_asis" in metrics
            assert "delta_tempo_pct" in metrics
        except ImportError:
            pytest.skip("centro/comparar_simulacoes.py not available")

    def test_analisar_emissions_with_data(self, sample_emissions_df):
        try:
            from analysis import analisar_emissions
            metrics = analisar_emissions(sample_emissions_df, sample_emissions_df)
            assert "CO2_kg_h_asis" in metrics
            assert "delta_CO2_pct" in metrics
        except ImportError:
            pytest.skip("centro/comparar_simulacoes.py not available")
