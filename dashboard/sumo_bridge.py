#!/usr/bin/env python3
"""
Bridge to SUMO CLI tools via subprocess.
Handles finding executables, running sumo/duarouter, and progress parsing.
"""

import subprocess
import re
from pathlib import Path


def find_executable(name, candidates=None):
    """
    Find an executable by name.
    Checks candidates first, then PATH.
    """
    if candidates:
        for cand in candidates:
            exe = Path(cand)
            if exe.is_file():
                return str(exe)

    import shutil
    found = shutil.which(name)
    return found


def run_sumo(
    sumo_exe,
    sumocfg_path,
    capture_output=True,
    timeout=600,
    extra_args=None,
):
    """
    Run SUMO simulation.
    Returns subprocess.CompletedProcess.
    """
    cmd = [sumo_exe, "-c", str(sumocfg_path), "--no-warnings", "--duration-log.disable"]
    if extra_args:
        cmd.extend(extra_args)

    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        timeout=timeout,
        cwd=str(Path(sumocfg_path).parent),
    )


def run_duarouter(
    duarouter_exe,
    net_file,
    route_files,
    output_file,
    timeout=300,
):
    """
    Run duarouter to convert flows into routes.
    """
    net = net_file if isinstance(net_file, list) else [net_file]
    routes = route_files if isinstance(route_files, list) else [route_files]

    cmd = [duarouter_exe]
    for n in net:
        cmd.extend(["--net-file", str(n)])
    for r in routes:
        cmd.extend(["--route-files", str(r)])
    cmd.extend([
        "--output-file", str(output_file),
        "--ignore-errors",
        "--no-warnings",
        "--routing-threads", "6",
    ])

    cwd = str(Path(output_file).parent) if output_file else "."
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )


def run_sumo_version(sumo_exe):
    """Check SUMO version."""
    try:
        result = subprocess.run(
            [sumo_exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "SUMO" in line and "Version" in line:
                    return line.strip()
            if result.stdout.strip():
                return result.stdout.splitlines()[0].strip()
        return None
    except Exception:
        return None


def ensure_dirs(base_path, *dirs):
    """Create directories if they don't exist."""
    created = []
    for d in dirs:
        p = Path(base_path) / d
        p.mkdir(parents=True, exist_ok=True)
        created.append(str(p))
    return created


SUMO_PROGRESS_RE = re.compile(r"Simulation step (\d+)")


def parse_sumo_progress(line):
    """Extract current step from a SUMO stderr/stdout line."""
    match = SUMO_PROGRESS_RE.search(line)
    if match:
        return int(match.group(1))
    return None
