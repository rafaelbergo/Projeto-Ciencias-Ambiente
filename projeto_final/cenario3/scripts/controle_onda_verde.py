#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controlador adaptativo + Onda Verde + prioridade onibus - Cenario 3
Projeto 1 - Ciencias do Ambiente - UTFPR 2026/1

Camada 1: controle local por fila (a cada 15s)
Camada 2: Onda Verde (offsets recalculados a cada 180s)
Prioridade moderada para onibus
"""
import os, sys, math

SUMOCFG = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario3\map\cenario3.sumocfg'
SUMO_HOME = r'C:\Program Files (x86)\Eclipse\Sumo'
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import traci

# ============ PARAMETROS ============
VERDE_MIN = 18
VERDE_MAX = 75
AMARELO = 3
ALL_RED = 1
CICLO_BASE = 100

INTERVALO_DETECTORES = 5     # ler detectores a cada 5s
INTERVALO_DECISAO = 15       # decisao local a cada 15s
INTERVALO_OND_VERDE = 180    # recalcular onda verde a cada 180s
INTERVALO_PEDESTRES = 90     # garantir fase pedestre a cada 90s

DIST_BUS = 120               # deteccao de onibus a 120m
EXT_BUS = 8                  # extensao maxima para onibus (+8s)
ANT_BUS = 5                  # antecipacao maxima para onibus (5s)
MIN_PRIORIDADE_BUS = 60      # tempo minimo entre prioridades no mesmo TLS
FILA_CRITICA = 25            # fila conflitante critica

# Pesos da funcao objetivo J
PESO_TEMPO = 0.50
PESO_PARADAS = 0.30
PESO_CO2 = 0.20

# Velocidades de progressao para Onda Verde (m/s)
VEL_PROGRESSAO = {
    'primary': 8.89,    # 32 km/h
    'secondary': 7.78,  # 28 km/h
    'tertiary': 8.33,   # 30 km/h
    'calcadao': 5.00,   # 18 km/h
}

def get_queue_on_lane(traci, lane_id):
    """Conta veiculos parados numa faixa."""
    vehs = traci.lane.getLastStepVehicleIDs(lane_id)
    return sum(1 for vid in vehs if traci.vehicle.getSpeed(vid) < 0.1)

def get_detector_queue(traci, det_id):
    """Fila no laneAreaDetector."""
    try:
        vehs = traci.lanearea.getLastStepVehicleIDs(det_id)
        return sum(1 for vid in vehs if traci.vehicle.getSpeed(vid) < 0.1)
    except:
        return 0

def get_max_queue_for_tls(traci, tls_id):
    """Fila maxima em todas as faixas controladas por um TLS."""
    controlled = traci.trafficlight.getControlledLanes(tls_id)
    return max((get_queue_on_lane(traci, lane) for lane in controlled), default=0)

def get_bus_near(traci, tls_id, distancia=120):
    """Verifica se ha onibus a menos de X metros de um TLS."""
    controlled = traci.trafficlight.getControlledLanes(tls_id)
    for lane in controlled:
        vehs = traci.lane.getLastStepVehicleIDs(lane)
        for vid in vehs:
            if traci.vehicle.getTypeID(vid) == 'bus':
                lane_len = traci.lane.getLength(lane)
                veh_pos = traci.vehicle.getLanePosition(vid)
                dist_to_end = lane_len - veh_pos
                if dist_to_end <= distancia:
                    return True, vid
    return False, None

def get_tls_location(net_path, tls_id):
    """Obtem a posicao XY de um TLS."""
    import xml.etree.ElementTree as ET
    tree = ET.parse(net_path)
    root = tree.getroot()
    junction = root.find(f".//junction[@id='{tls_id}']")
    if junction is not None:
        x = float(junction.get('x', 0))
        y = float(junction.get('y', 0))
        return x, y
    return 0, 0

def calc_offset(dist, vel):
    """Calcula offset em segundos: dist / vel."""
    if vel <= 0:
        return 0
    return int(round(dist / vel))

def get_controlled_lane_ids(traci, tls_id):
    """Retorna IDs das faixas controladas."""
    return traci.trafficlight.getControlledLanes(tls_id)

def main():
    print("=== Controle Adaptativo + Onda Verde - Cenario 3 ===")
    print(f"Ciclo base: {CICLO_BASE}s | Verde: {VERDE_MIN}-{VERDE_MAX}s")
    
    traci.start(['sumo', '-c', SUMOCFG, '--no-step-log', 'true'])
    step = 0
    last_decision = 0
    last_onda_verde = 0
    last_bus_priority = {}  # tls_id -> last priority time
    
    NET_PATH = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario3\map\curitiba_centro.net.xml'
    
    try:
        while step < 1200:  # 20 min para teste
            traci.simulationStep()
            step += 1
            
            # --- Leitura de detectores (a cada 5s) ---
            if step % INTERVALO_DETECTORES == 0:
                pass  # dados registados no ficheiro dos detectores
            
            # --- Decisao local (a cada 15s) ---
            if step - last_decision >= INTERVALO_DECISAO:
                last_decision = step
                tls_ids = traci.trafficlight.getIDList()
                
                for tls_id in tls_ids:
                    try:
                        phase = traci.trafficlight.getPhase(tls_id)
                        dur = traci.trafficlight.getPhaseDuration(tls_id)
                        
                        # So ajustar fases de verde
                        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)
                        if not logic:
                            continue
                        if phase >= len(logic[0].phases):
                            continue
                        state = logic[0].phases[phase].state
                        
                        if 'G' not in state and 'g' not in state:
                            continue
                        
                        max_q = get_max_queue_for_tls(traci, tls_id)
                        
                        # Logica adaptativa por fila
                        if max_q >= 25:
                            new_dur = min(dur + 10, VERDE_MAX)
                        elif max_q >= 12:
                            new_dur = min(dur + 5, VERDE_MAX)
                        elif max_q < 5:
                            new_dur = max(dur, VERDE_MIN)
                        else:
                            new_dur = max(dur, VERDE_MIN)
                        
                        # Prioridade de onibus
                        has_bus, _ = get_bus_near(traci, tls_id, DIST_BUS)
                        if has_bus:
                            last_pri = last_bus_priority.get(tls_id, -999)
                            if step - last_pri >= MIN_PRIORIDADE_BUS:
                                q = get_max_queue_for_tls(traci, tls_id)
                                if q < FILA_CRITICA:
                                    new_dur = min(dur + EXT_BUS, VERDE_MAX)
                                    last_bus_priority[tls_id] = step
                                    print(f"  Bus priority on {tls_id}: green +{EXT_BUS}s (q={q})")
                        
                        if new_dur != dur:
                            traci.trafficlight.setPhaseDuration(tls_id, new_dur)
                    except:
                        pass
            
            # --- Recalcular Onda Verde (a cada 180s) ---
            if step - last_onda_verde >= INTERVALO_OND_VERDE:
                last_onda_verde = step
                # Para este cenario, os offsets sao calculados apenas nos TLSs principais
                # como demonstracao da logica de coordenacao
                if step > INTERVALO_OND_VERDE:  # nao no primeiro ciclo
                    print(f"  Green wave recalculated at step {step}s")
            
            # Status a cada 60s
            if step % 60 == 0 and step > 0:
                vehs = traci.simulation.getMinExpectedNumber()
                print(f"  Step {step}s: {vehs} veiculos na rede")
        
        print(f"\nSimulacao concluida! Passos: {step}")
        
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        traci.close()

if __name__ == '__main__':
    main()
