#!/usr/bin/env python3
"""
Analysis wrapper that imports parsing/comparison functions from centro/.
Provides a clean interface for the dashboard without duplicating logic.
"""

import sys
from pathlib import Path

CENTRO_PATH = Path(__file__).parent.parent / "centro"
if str(CENTRO_PATH) not in sys.path:
    sys.path.insert(0, str(CENTRO_PATH))


def _try_import():
    """Try to import from centro/comparar_simulacoes.py."""
    try:
        import comparar_simulacoes as _cs
        return _cs
    except ImportError as e:
        raise ImportError(
            f"Could not import centro/comparar_simulacoes.py: {e}\n"
            f"Ensure centro/ folder exists at {CENTRO_PATH} and has comparar_simulacoes.py\n"
            f"Required packages: pandas, numpy, matplotlib"
        )


_cs = _try_import()

parse_tripinfo = _cs.parse_tripinfo
parse_emissions = _cs.parse_emissions
analisar_tripinfo = _cs.analisar_tripinfo
analisar_emissions = _cs.analisar_emissions
