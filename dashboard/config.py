#!/usr/bin/env python3
"""
Configuration for traffic simulation dashboard.
Handles SimulationConfig dataclass and SUMO auto-detection.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
CENTRO_PATH = PROJECT_ROOT / "centro"
DASHBOARD_PATH = PROJECT_ROOT / "dashboard"
DEFAULT_RESULTS_DIR = "results"
DEFAULT_OUTPUT_DIR = "output"

SUMO_CANDIDATES = [
    Path("C:/Program Files (x86)/Eclipse/Sumo"),
    Path("C:/Program Files/Eclipse/Sumo"),
    Path("C:/sumo-1.20.0"),
    Path("C:/sumo"),
    Path("C:/Program Files (x86)/DLR/Sumo"),
    Path("C:/Program Files/DLR/Sumo"),
]


@dataclass
class SimulationConfig:
    """All parameters for a traffic simulation run."""

    # SUMO
    sumo_exe: str = ""
    duarouter_exe: str = ""

    # Simulation
    duration_s: int = 3600
    step_length_s: float = 0.1
    seed: int = 42

    # Demand
    total_flow_veh_h: int = 459
    vehicle_mix: dict = field(default_factory=lambda: {
        "carro_gasolina": 55,
        "carro_etanol": 15,
        "moto": 12,
        "onibus": 13,
        "vuc": 5,
    })

    # To-Be strategy
    tobe_green_time: int = 35

    # Paths
    net_file: str = "quadrilatero.net.xml"
    routes_file: str = "quadrilatero.rou.xml"
    net_tobe_file: str = "quadrilatero_tobe.net.xml"

    # Working directory for simulations
    results_dir: str = DEFAULT_RESULTS_DIR
    output_dir: str = DEFAULT_OUTPUT_DIR

    def validate(self):
        errors = []
        if self.total_flow_veh_h <= 0:
            errors.append("total_flow_veh_h must be positive")
        if self.duration_s <= 0:
            errors.append("duration_s must be positive")
        if self.step_length_s <= 0:
            errors.append("step_length_s must be positive")
        total_pct = sum(self.vehicle_mix.values())
        if total_pct != 100:
            errors.append(f"vehicle_mix percentages must sum to 100, got {total_pct}")
        if self.tobe_green_time <= 0:
            errors.append("tobe_green_time must be positive")
        return errors


def detect_sumo() -> dict:
    """
    Auto-detect SUMO installation.
    Returns dict with:
        sumo_exe: path to sumo.exe or None
        duarouter_exe: path to duarouter.exe or None
        sumo_home: path to SUMO root or None
        error: message string or None
    """
    result = {
        "sumo_exe": None,
        "duarouter_exe": None,
        "sumo_home": None,
        "error": None,
    }

    sumo_home = os.environ.get("SUMO_HOME")

    if sumo_home:
        sumo_path = Path(sumo_home)
        if sumo_path.is_dir():
            sumo_exe = sumo_path / "bin" / "sumo.exe"
            dua_exe = sumo_path / "bin" / "duarouter.exe"
            if sumo_exe.is_file() and dua_exe.is_file():
                result["sumo_exe"] = str(sumo_exe)
                result["duarouter_exe"] = str(dua_exe)
                result["sumo_home"] = str(sumo_path)
                return result

    for candidate in SUMO_CANDIDATES:
        if candidate.is_dir():
            sumo_exe = candidate / "bin" / "sumo.exe"
            dua_exe = candidate / "bin" / "duarouter.exe"
            if sumo_exe.is_file() and dua_exe.is_file():
                result["sumo_exe"] = str(sumo_exe)
                result["duarouter_exe"] = str(dua_exe)
                result["sumo_home"] = str(candidate)
                return result

    result["error"] = (
        "SUMO not found. Please install SUMO or set SUMO_HOME environment variable.\n"
        "Download: https://sumo.dlr.de/docs/Installing/index.html\n"
        "Set: setx SUMO_HOME \"C:\\Program Files (x86)\\Eclipse\\Sumo\""
    )
    return result
