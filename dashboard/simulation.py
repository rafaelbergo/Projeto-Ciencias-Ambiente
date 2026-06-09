#!/usr/bin/env python3
"""
Traffic simulation orchestrator.
Generates demand, creates configurations, runs SUMO for As-Is and To-Be scenarios.
"""

import shutil
import xml.etree.ElementTree as ET
import random
from pathlib import Path

from config import SimulationConfig, CENTRO_PATH, DASHBOARD_PATH
from sumo_bridge import run_sumo, run_duarouter, ensure_dirs

random.seed(42)

# ============================================================
# VEHICLE TYPES (from project specification)
# ============================================================
VEHICLE_TYPES = {
    "carro_gasolina": {
        "accel": 2.6, "decel": 4.5, "sigma": 0.5,
        "length": 4.3, "minGap": 2.5, "maxSpeed": 16.67,
        "color": "0.2,0.2,0.8",
    },
    "carro_etanol": {
        "accel": 2.6, "decel": 4.5, "sigma": 0.5,
        "length": 4.3, "minGap": 2.5, "maxSpeed": 16.67,
        "color": "0.1,0.7,0.1",
    },
    "moto": {
        "accel": 3.5, "decel": 6.0, "sigma": 0.7,
        "length": 2.0, "minGap": 1.5, "maxSpeed": 18.06,
        "color": "0.9,0.3,0.1",
    },
    "onibus": {
        "accel": 1.3, "decel": 3.5, "sigma": 0.3,
        "length": 12.0, "minGap": 3.0, "maxSpeed": 13.89,
        "color": "0.8,0.8,0.0",
    },
    "vuc": {
        "accel": 1.5, "decel": 3.8, "sigma": 0.4,
        "length": 7.0, "minGap": 3.0, "maxSpeed": 13.89,
        "color": "0.5,0.5,0.5",
    },
}


def _get_main_edges(net_path):
    """Extract primary/secondary/tertiary edges from a SUMO .net.xml."""
    tree = ET.parse(net_path)
    root = tree.getroot()

    def edge_priority(etype):
        if "primary" in etype and "link" not in etype:
            return 5
        if "secondary" in etype and "link" not in etype:
            return 4
        if "tertiary" in etype and "link" not in etype:
            return 3
        if "primary_link" in etype or "secondary_link" in etype:
            return 2
        if "residential" in etype:
            return 1
        return 0

    main_edges = []
    for edge in root.findall("edge"):
        eid = edge.get("id", "")
        if eid.startswith(":"):
            continue
        lanes = edge.findall("lane")
        if not lanes:
            continue
        etype = edge.get("type", "")
        if edge_priority(etype) >= 3:
            main_edges.append(eid)

    return main_edges


def generate_demand(config, working_dir, net_path):
    """Generate .rou.xml with parameterized vehicle demand."""
    main_edges = _get_main_edges(net_path)
    if not main_edges:
        raise RuntimeError("No main edges found in network. Check the .net.xml file.")

    sim_end = config.duration_s

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '',
        '<!-- Demanda veicular gerada pelo Dashboard de Simulacao -->',
        '',
        '<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">',
        '',
        '    <!-- Tipos veiculares -->',
    ]

    for vtype_id, props in VEHICLE_TYPES.items():
        lines.append(
            f'    <vType id="{vtype_id}" '
            f'accel="{props["accel"]}" decel="{props["decel"]}" sigma="{props["sigma"]}" '
            f'length="{props["length"]}" minGap="{props["minGap"]}" '
            f'maxSpeed="{props["maxSpeed"]}" color="{props["color"]}"/>'
        )
    lines.append("")

    lines.append('    <!-- Fluxos de veiculos -->')
    origens = random.sample(main_edges, min(30, len(main_edges)))
    destinos = random.sample(main_edges, min(30, len(main_edges)))

    flow_id = 0
    total_allocated = 0

    for vtype_id, pct in config.vehicle_mix.items():
        vph_per_type = int(config.total_flow_veh_h * pct / 100)
        if vph_per_type <= 0:
            continue
        n_flows = min(20, len(origens))
        vph_per_flow = max(1, vph_per_type // n_flows)

        for i in range(n_flows):
            orig = origens[i]
            dest = destinos[(i + 3) % len(destinos)]
            if dest == orig:
                dest = destinos[(i + 7) % len(destinos)]
            lines.append(
                f'    <flow id="flow{flow_id}" type="{vtype_id}" '
                f'from="{orig}" to="{dest}" '
                f'begin="0.0" end="{sim_end:.0f}" '
                f'vehsPerHour="{vph_per_flow}" '
                f'departSpeed="random"/>'
            )
            flow_id += 1
            total_allocated += vph_per_flow

    lines.append("")
    lines.append("</routes>")

    rou_path = Path(working_dir) / "quadrilatero.rou.xml"
    rou_path.write_text("\n".join(lines), encoding="utf-8")
    return rou_path


def optimize_network(config, net_path, output_path):
    """Copy network and adjust green phases to configured duration."""
    tree = ET.parse(net_path)
    root = tree.getroot()

    tl_count = 0
    modified = 0
    for tl in root.findall(".//tlLogic"):
        tl_count += 1
        for phase in tl.findall("phase"):
            state = phase.get("state", "")
            if "G" in state or "g" in state:
                if "y" not in state.lower() or state.lower().count("g") > state.lower().count("y"):
                    phase.set("duration", str(config.tobe_green_time))
                    modified += 1

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)
    return tl_count, modified


def create_sumocfg(config, scenario, working_dir, net_file, route_file, results_dir):
    """Generate a .sumocfg XML file for a given scenario (asis or tobe)."""
    trip_file = f"tripinfo_{scenario}.xml"
    emission_file = f"emissions_{scenario}.xml"

    root = ET.Element("configuration")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/sumoConfiguration.xsd")

    inp = ET.SubElement(root, "input")
    ET.SubElement(inp, "net-file", value=str(net_file))
    ET.SubElement(inp, "route-files", value=str(route_file))

    time_e = ET.SubElement(root, "time")
    ET.SubElement(time_e, "begin", value="0")
    ET.SubElement(time_e, "end", value=str(config.duration_s))

    proc = ET.SubElement(root, "processing")
    ET.SubElement(proc, "step-length", value=str(config.step_length_s))
    ET.SubElement(proc, "time-to-teleport", value="-1")
    ET.SubElement(proc, "ignore-route-errors", value="true")

    out = ET.SubElement(root, "output")
    ET.SubElement(out, "tripinfo-output", value=str(Path(results_dir) / trip_file))
    ET.SubElement(out, "tripinfo-output.write-unfinished", value="true")
    ET.SubElement(out, "emission-output", value=str(Path(results_dir) / emission_file))
    ET.SubElement(out, "emission-output.precision", value="4")

    report = ET.SubElement(root, "report")
    ET.SubElement(report, "verbose", value="false")
    ET.SubElement(report, "no-step-log", value="true")
    ET.SubElement(report, "duration-log.disable", value="true")

    rnd = ET.SubElement(root, "random")
    ET.SubElement(rnd, "seed", value=str(config.seed))

    cfg_path = Path(working_dir) / f"quadrilatero_{scenario}.sumocfg"
    tree = ET.ElementTree(root)
    tree.write(cfg_path, encoding="UTF-8", xml_declaration=True)
    return cfg_path


def run_simulation(config, sumo_exe, sumocfg_path, progress_callback=None):
    """Run SUMO simulation and return the process result."""
    import subprocess

    cmd = [
        sumo_exe, "-c", str(sumocfg_path),
        "--no-warnings", "--duration-log.disable",
    ]

    if progress_callback:
        progress_callback(0.0, f"Iniciando simulação...")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(sumocfg_path.parent),
    )

    stdout_lines = []
    stderr_lines = []

    import threading
    import time

    def read_stream(stream, collector):
        for line in iter(stream.readline, ""):
            collector.append(line)

    t_stdout = threading.Thread(target=read_stream, args=(proc.stdout, stdout_lines), daemon=True)
    t_stderr = threading.Thread(target=read_stream, args=(proc.stderr, stderr_lines), daemon=True)
    t_stdout.start()
    t_stderr.start()

    total_steps = int(config.duration_s / config.step_length_s)
    last_progress = 0

    # Poll for completion with progress estimation
    while proc.poll() is None:
        time.sleep(0.5)
        if progress_callback:
            # Estimate progress from elapsed time vs total
            elapsed = len(stderr_lines) * 0.1  # rough heuristic
            progress = min(0.99, len(stderr_lines) / max(1, total_steps / 10))
            if progress > last_progress + 0.01:
                last_progress = progress
                progress_callback(progress, f"Simulando... {int(progress * 100)}%")

    t_stdout.join(timeout=5)
    t_stderr.join(timeout=5)

    class Result:
        def __init__(self, returncode, stdout, stderr):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    if progress_callback:
        progress_callback(1.0, "Simulação concluída.")

    return Result(
        returncode=proc.returncode,
        stdout="".join(stdout_lines),
        stderr="".join(stderr_lines),
    )


def run_full_pipeline(config, progress_callback=None):
    """
    Execute the complete simulation pipeline.
    Returns dict with metrics and paths.
    """
    results = {
        "success": False,
        "error": None,
        "metrics_trip": {},
        "metrics_emis": {},
        "results_dir": None,
        "output_dir": None,
    }

    try:
        sumo_exe = config.sumo_exe
        dua_exe = config.duarouter_exe

        if not sumo_exe or not dua_exe:
            raise RuntimeError("SUMO executables not configured. Run detect_sumo() first.")

        # Prepare directories
        work_dir = DASHBOARD_PATH
        results_dir = DASHBOARD_PATH / "results"
        output_dir = DASHBOARD_PATH / "output"
        ensure_dirs(DASHBOARD_PATH, "results", "output")

        results["results_dir"] = str(results_dir)
        results["output_dir"] = str(output_dir)

        # Step 1: Generate demand
        if progress_callback:
            progress_callback(0.05, "Gerando demanda veicular...")
        net_path = CENTRO_PATH / config.net_file
        rou_path = generate_demand(config, work_dir, net_path)

        # Step 2: Run duarouter
        if progress_callback:
            progress_callback(0.15, "Roteando fluxos (duarouter)...")
        dua_result = run_duarouter(dua_exe, net_path, rou_path, rou_path)
        if dua_result.returncode != 0:
            raise RuntimeError(f"duarouter failed:\n{dua_result.stderr}")

        # Step 3: Create As-Is sumocfg and run
        if progress_callback:
            progress_callback(0.25, "Configurando cenário As-Is...")
        asis_cfg = create_sumocfg(
            config, "asis", work_dir,
            net_path, rou_path, results_dir,
        )

        if progress_callback:
            progress_callback(0.30, "Executando simulação As-Is...")

        def asis_progress(p, msg):
            if progress_callback:
                progress_callback(0.30 + p * 0.25, f"As-Is: {msg}")

        result_asis = run_simulation(config, sumo_exe, asis_cfg, asis_progress)
        if result_asis.returncode != 0 and result_asis.returncode is not None:
            raise RuntimeError(f"As-Is simulation failed:\n{result_asis.stderr}")

        # Step 4: Optimize network and run To-Be
        if progress_callback:
            progress_callback(0.55, "Otimizando rede To-Be...")
        tobe_net = work_dir / "quadrilatero_tobe.net.xml"
        tl_count, modified = optimize_network(config, net_path, tobe_net)

        if progress_callback:
            progress_callback(0.60, f"Configurando cenário To-Be ({tl_count} semáforos)...")
        tobe_cfg = create_sumocfg(
            config, "tobe", work_dir,
            tobe_net, rou_path, results_dir,
        )

        if progress_callback:
            progress_callback(0.65, "Executando simulação To-Be...")

        def tobe_progress(p, msg):
            if progress_callback:
                progress_callback(0.65 + p * 0.20, f"To-Be: {msg}")

        result_tobe = run_simulation(config, sumo_exe, tobe_cfg, tobe_progress)
        if result_tobe.returncode != 0 and result_tobe.returncode is not None:
            raise RuntimeError(f"To-Be simulation failed:\n{result_tobe.stderr}")

        # Step 5: Analyze results
        if progress_callback:
            progress_callback(0.85, "Analisando resultados...")

        from analysis import (
            parse_tripinfo, parse_emissions,
            analisar_tripinfo, analisar_emissions,
        )

        trip_asis = results_dir / "tripinfo_asis.xml"
        trip_tobe = results_dir / "tripinfo_tobe.xml"
        emis_asis = results_dir / "emissions_asis.xml"
        emis_tobe = results_dir / "emissions_tobe.xml"

        df_ta = parse_tripinfo(str(trip_asis))
        df_tt = parse_tripinfo(str(trip_tobe))
        df_ea = parse_emissions(str(emis_asis))
        df_et = parse_emissions(str(emis_tobe))

        metrics_trip = analisar_tripinfo(df_ta, df_tt)
        metrics_emis = analisar_emissions(df_ea, df_et)

        results["metrics_trip"] = metrics_trip
        results["metrics_emis"] = metrics_emis
        results["success"] = True

        if progress_callback:
            progress_callback(1.0, "Pipeline concluído!")

    except Exception as e:
        results["error"] = str(e)
        if progress_callback:
            progress_callback(1.0, f"Erro: {e}")

    return results


def analyze_existing_results(results_dir=None):
    """Analyze existing simulation results without re-running."""
    if results_dir is None:
        results_dir = DASHBOARD_PATH / "results"

    from analysis import (
        parse_tripinfo, parse_emissions,
        analisar_tripinfo, analisar_emissions,
    )

    trip_asis = Path(results_dir) / "tripinfo_asis.xml"
    trip_tobe = Path(results_dir) / "tripinfo_tobe.xml"
    emis_asis = Path(results_dir) / "emissions_asis.xml"
    emis_tobe = Path(results_dir) / "emissions_tobe.xml"

    results = {"success": False, "error": None, "metrics_trip": {}, "metrics_emis": {}}

    if not trip_asis.exists() or not trip_tobe.exists():
        results["error"] = "Arquivos de resultados não encontrados. Execute a simulação primeiro."
        return results

    try:
        df_ta = parse_tripinfo(str(trip_asis))
        df_tt = parse_tripinfo(str(trip_tobe))
        df_ea = parse_emissions(str(emis_asis)) if emis_asis.exists() else None
        df_et = parse_emissions(str(emis_tobe)) if emis_tobe.exists() else None

        results["metrics_trip"] = analisar_tripinfo(df_ta, df_tt)
        results["metrics_emis"] = analisar_emissions(df_ea, df_et)
        results["success"] = True
    except Exception as e:
        results["error"] = str(e)

    return results
