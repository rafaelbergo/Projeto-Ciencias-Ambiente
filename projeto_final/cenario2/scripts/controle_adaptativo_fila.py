#!/usr/bin/env python3
"""
Controlador adaptativo por fila - Cenário 2
Projeto 1 - Ciências do Ambiente - UTFPR 2026/1

Lógica: mede filas nos laneAreaDetectors e ajusta tempos de verde.
Ciclo base: 90s | Verde min: 20s | Verde max: 70s
"""
import os
import sys
import subprocess
import time
import xml.etree.ElementTree as ET

SUMO_HOME = r'C:\Program Files (x86)\Eclipse\Sumo\bin'
SUMOCFG = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario2\map\cenario2.sumocfg'

# Add SUMO to path
os.environ['SUMO_HOME'] = os.path.dirname(SUMO_HOME)
sys.path.append(os.path.join(os.path.dirname(SUMO_HOME), 'tools'))

import traci

# ============ PARÂMETROS DE CONTROLE ============
CICLO_BASE = 90
VERDE_MIN = 20
VERDE_MAX = 70
AMARELO = 3
ALL_RED = 1
INTERVALO_AVALIACAO = 5  # segundos entre avaliações

# Pesos por via (conforme especificação)
PESOS = {
    'primary': 1.25,
    'secondary': 1.15,
    'tertiary': 1.00,
}

# ============ FUNÇÕES AUXILIARES ============
def get_queue_on_lane(traci, lane_id):
    """Retorna número de veículos parados numa faixa."""
    veh_ids = traci.lane.getLastStepVehicleIDs(lane_id)
    queue = 0
    for vid in veh_ids:
        speed = traci.vehicle.getSpeed(vid)
        if speed < 0.1:  # parado
            queue += 1
    return queue

def get_detector_queue(traci, det_id):
    """Retorna número de veículos no laneAreaDetector (parados)."""
    try:
        veh_ids = traci.lanearea.getLastStepVehicleIDs(det_id)
        queue = 0
        for vid in veh_ids:
            speed = traci.vehicle.getSpeed(vid)
            if speed < 0.1:
                queue += 1
        return queue
    except:
        return 0

def get_max_queue_for_tls(traci, tls_id):
    """Retorna a fila máxima em todas as faixas controladas por um TLS."""
    controlled = traci.trafficlight.getControlledLanes(tls_id)
    max_q = 0
    for lane in controlled:
        q = get_queue_on_lane(traci, lane)
        if q > max_q:
            max_q = q
    return max_q

def adjust_green(traci, tls_id, current_phase_idx, phase_duration, max_queue):
    """Ajusta o tempo de verde baseado na fila."""
    if max_queue >= 25:
        # Crítica: estender +10s
        return min(phase_duration + 10, VERDE_MAX)
    elif max_queue >= 12:
        # Alta: estender +5s
        return min(phase_duration + 5, VERDE_MAX)
    elif max_queue < 5:
        # Baixa: encerrar no mínimo, mas permitir pelo menos VERDE_MIN
        return max(phase_duration, VERDE_MIN)
    else:
        # Média: manter
        return max(phase_duration, VERDE_MIN)

def run():
    """Executa a simulação com controle adaptativo."""
    print("=== Controle Adaptativo por Fila - Cenário 2 ===")
    print(f"Ciclo base: {CICLO_BASE}s | Verde: {VERDE_MIN}-{VERDE_MAX}s")
    print("Conectando ao SUMO...")
    
    traci.start(['sumo', '-c', SUMOCFG, '--no-step-log', 'true'])
    step = 0
    update_count = 0
    
    try:
        while step < 7400:
            traci.simulationStep()
            step += 1
            
            # A cada INTERVALO_AVALIACAO segundos, ajustar semáforos
            if step % INTERVALO_AVALIACAO == 0:
                update_count += 1
                tls_ids = traci.trafficlight.getIDList()
                
                for tls_id in tls_ids:
                    # Skip non-actuated traffic lights
                    logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)
                    if not logic:
                        continue
                    # Only adjust actuated/program phases
                    try:
                        phase_idx = traci.trafficlight.getPhase(tls_id)
                        current_dur = traci.trafficlight.getPhaseDuration(tls_id)
                        
                        # Só ajustar phases de verde (não amarelo/vermelho)
                        phases = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)
                        if not phases or phase_idx >= len(phases[0].phases):
                            continue
                        
                        phase_state = phases[0].phases[phase_idx].state
                        
                        # Se a fase atual tem verde ('G' ou 'g')
                        if 'G' in phase_state or 'g' in phase_state:
                            max_queue = get_max_queue_for_tls(traci, tls_id)
                            new_dur = adjust_green(traci, tls_id, phase_idx, current_dur, max_queue)
                            
                            if new_dur != current_dur:
                                traci.trafficlight.setPhaseDuration(tls_id, new_dur)
                    except:
                        pass
                
                if update_count % 20 == 0:  # A cada ~100s
                    vehs = traci.simulation.getMinExpectedNumber()
                    print(f"  Step {step}s: {vehs} veículos na rede")
        
        print(f"\nSimulação concluída! Passos: {step}")
        print(f"Atualizações realizadas: {update_count}")
        
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        traci.close()

if __name__ == '__main__':
    run()
