#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controlador Adaptativo de Semáforos - Quadrilátero Central de Curitiba
======================================================================
Projeto Ciências do Ambiente - UTFPR 2026/1
Rede OSM (map.osm -> quadrilatero.net.xml)

Implementa controlador fuzzy + Onda Verde via TraCI.
Conecta ao SUMO em modo servidor na porta 8813.

Uso:
  sumo -c quadrilatero_tobe.sumocfg --remote-port 8813
  python controlador_adaptativo.py
"""

import os
import sys
import numpy as np

# Tenta localizar o SUMO_HOME
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    for candidate in [
        r'C:\Program Files (x86)\Eclipse\Sumo\tools',
        r'C:\Program Files\Eclipse\Sumo\tools',
        r'C:\sumo-1.20.0\tools',
        r'C:\sumo\tools',
    ]:
        if os.path.isdir(candidate):
            sys.path.append(candidate)
            break

try:
    import traci
    import traci.constants as tc
except ImportError:
    print("ERRO: Nao foi possivel importar traci.")
    print("Instale: pip install sumo")
    sys.exit(1)

try:
    import skfuzzy as fuzz
    from skfuzzy import control as ctrl
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    print("[AVISO] scikit-fuzzy nao encontrado. Usando controle linear.")

# ============================================================
# CONFIGURACOES
# ============================================================
T_VERDE_MIN = 15.0
T_VERDE_MAX = 60.0
SIM_STEPS = 90000  # 9000s * 10 steps/s

# ============================================================
# CONTROLADOR FUZZY
# ============================================================
class ControladorFuzzy:
    def __init__(self):
        if not FUZZY_AVAILABLE:
            return
        self._construir()

    def _construir(self):
        fila = ctrl.Antecedent(np.arange(0, 51, 1), 'fila')
        fila['baixa']   = fuzz.trimf(fila.universe, [0, 0, 15])
        fila['media']   = fuzz.trimf(fila.universe, [5, 20, 35])
        fila['alta']    = fuzz.trimf(fila.universe, [25, 40, 50])
        fila['critica'] = fuzz.trimf(fila.universe, [35, 50, 50])

        ocup = ctrl.Antecedent(np.arange(0, 101, 1), 'ocupacao')
        ocup['baixa'] = fuzz.trimf(ocup.universe, [0, 0, 40])
        ocup['media'] = fuzz.trimf(ocup.universe, [20, 50, 80])
        ocup['alta']  = fuzz.trimf(ocup.universe, [60, 100, 100])

        ext = ctrl.Consequent(np.arange(-20, 31, 1), 'extensao')
        ext['reduzir_muito']  = fuzz.trimf(ext.universe, [-20, -20, -10])
        ext['reduzir_pouco']  = fuzz.trimf(ext.universe, [-15, -5, 0])
        ext['manter']         = fuzz.trimf(ext.universe, [-5, 0, 5])
        ext['aumentar_pouco'] = fuzz.trimf(ext.universe, [0, 5, 15])
        ext['aumentar_muito'] = fuzz.trimf(ext.universe, [10, 20, 30])
        ext['aumentar_max']   = fuzz.trimf(ext.universe, [20, 30, 30])

        regras = [
            ctrl.Rule(fila['baixa']    & ocup['baixa'],  ext['reduzir_muito']),
            ctrl.Rule(fila['baixa']    & ocup['media'],  ext['reduzir_pouco']),
            ctrl.Rule(fila['baixa']    & ocup['alta'],   ext['manter']),
            ctrl.Rule(fila['media']    & ocup['baixa'],  ext['reduzir_pouco']),
            ctrl.Rule(fila['media']    & ocup['media'],  ext['manter']),
            ctrl.Rule(fila['media']    & ocup['alta'],   ext['aumentar_pouco']),
            ctrl.Rule(fila['alta']     & ocup['baixa'],  ext['manter']),
            ctrl.Rule(fila['alta']     & ocup['media'],  ext['aumentar_pouco']),
            ctrl.Rule(fila['alta']     & ocup['alta'],   ext['aumentar_muito']),
            ctrl.Rule(fila['critica']  & ocup['baixa'],  ext['aumentar_pouco']),
            ctrl.Rule(fila['critica']  & ocup['media'],  ext['aumentar_muito']),
            ctrl.Rule(fila['critica']  & ocup['alta'],   ext['aumentar_max']),
        ]

        self.sistema = ctrl.ControlSystem(regras)
        self.sim = ctrl.ControlSystemSimulation(self.sistema)

    def calcular(self, fila, ocupacao):
        if not FUZZY_AVAILABLE:
            score = (fila / 50.0) * 0.6 + (ocupacao / 100.0) * 0.4
            if score < 0.2:   return -10.0
            elif score < 0.4: return 0.0
            elif score < 0.6: return 10.0
            elif score < 0.8: return 20.0
            else:             return 30.0
        try:
            self.sim.input['fila'] = min(fila, 50)
            self.sim.input['ocupacao'] = min(ocupacao, 100)
            self.sim.compute()
            return self.sim.output['extensao']
        except:
            return 0.0

# ============================================================
# LOOP PRINCIPAL
# ============================================================
def executar():
    traci.init(port=8813)
    step = 0

    fuzzy = ControladorFuzzy()

    # Obter todos os TLS IDs da rede
    tls_ids = traci.trafficlight.getIDList()
    print(f"Semáforos detectados: {len(tls_ids)}")
    for tid in tls_ids[:10]:
        print(f"  {tid}")
    if len(tls_ids) > 10:
        print(f"  ... e mais {len(tls_ids) - 10}")

    # Estado base para cada TLS
    tls_estado = {}
    for tid in tls_ids:
        try:
            prog = traci.trafficlight.getCompleteRedYellowGreenDefinition(tid)
            n_fases = len(prog[0].phases) if prog else 4
        except:
            n_fases = 4
        tls_estado[tid] = {
            'num_fases': n_fases,
            'verde_base': T_VERDE_MIN,
        }

    print("\nControlador adaptativo ativo. Executando simulacao...")
    print("=" * 60)

    while step < SIM_STEPS:
        traci.simulationStep()
        tempo_sim = traci.simulation.getTime()

        # A cada 3s (30 steps * 0.1s), ajustar tempos
        if step % 30 == 0:
            for tid in tls_ids:
                try:
                    links = traci.trafficlight.getControlledLinks(tid)
                    n_aproximacoes = len(links)

                    fila_max = 0
                    ocup_max = 0

                    for link_idx in range(n_aproximacoes):
                        try:
                            link = links[link_idx]
                            incoming_lanes = set()
                            for lane_link in link:
                                if lane_link and len(lane_link) >= 2:
                                    incoming_lanes.add(lane_link[0])

                            count_parado = 0
                            count_total = 0
                            cap_total = 0
                            for lid in incoming_lanes:
                                try:
                                    vehs = traci.lane.getLastStepVehicleIDs(lid)
                                    count_total += len(vehs)
                                    for vid in vehs:
                                        if traci.vehicle.getSpeed(vid) < 2.0:
                                            count_parado += 1
                                    lane_len = traci.lane.getLength(lid)
                                    cap_total += max(1, lane_len / 7.0)
                                except:
                                    pass

                            fila_max = max(fila_max, count_parado)
                            if cap_total > 0:
                                ocup = min(100, (count_total / cap_total) * 100)
                                ocup_max = max(ocup_max, ocup)
                        except:
                            pass

                    extensao = fuzzy.calcular(fila_max, ocup_max)
                    novo_verde = max(T_VERDE_MIN, min(T_VERDE_MAX, T_VERDE_MIN + extensao))

                    # Aplicar duracao da fase atual (se verde)
                    try:
                        fase_atual = traci.trafficlight.getPhase(tid)
                        dur_restante = traci.trafficlight.getNextSwitch(tid) - tempo_sim
                        # Fases pares = verde (tipicamente)
                        if dur_restante > 10 and fase_atual % 2 == 0:
                            traci.trafficlight.setPhaseDuration(tid, novo_verde)
                    except:
                        pass

                except traci.exceptions.TraCIException:
                    pass

        # Log a cada 15 min simulado
        if step % 9000 == 0 and step > 0:
            minuto = int(tempo_sim / 60)
            n_veh = traci.vehicle.getIDCount()
            print(f"  [t={minuto:3d}min] Veiculos ativos: {n_veh}")

        step += 1

    traci.close()
    print("=" * 60)
    print("Simulacao To-Be concluida.")
    print("Resultados salvos em: results/tripinfo_tobe.xml, results/emissions_tobe.xml")

if __name__ == '__main__':
    print("=" * 60)
    print("  Controlador Adaptativo - Quadrilatero Central")
    print("  UTFPR - Ciencias do Ambiente 2026/1")
    print("=" * 60)
    print()
    executar()
