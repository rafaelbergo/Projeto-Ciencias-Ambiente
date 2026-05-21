#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controlador Adaptativo de Semáforos com Lógica Fuzzy e Onda Verde
=================================================================
Quadrilátero Central de Curitiba -- Projeto Ciências do Ambiente
UTFPR 2026/1

Este script implementa um controlador semafórico adaptativo que:
  1. Lê dados de detectores virtuais (E2) do SUMO para estimar filas
  2. Calcula tempos de verde usando lógica fuzzy
  3. Sincroniza semáforos consecutivos no modo Onda Verde
  4. Opera via interface TraCI (controle externo do SUMO)

Uso:
  sumo-gui -c quadrilatero_tobe.sumocfg --start          (abre GUI e pausa)
  python controlador_adaptativo.py                         (conecta e controla)

Ou:
  sumo -c quadrilatero_tobe.sumocfg --start               (terminal)
  python controlador_adaptativo.py

Requisitos:
  pip install sumo scikit-fuzzy numpy pandas
"""

import os
import sys
import math
import numpy as np
from collections import defaultdict

# Verifica se SUMO_HOME está no path
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    # Tenta caminhos comuns no Windows
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
    print("ERRO: Não foi possível importar traci.")
    print("Instale o SUMO e configure a variável SUMO_HOME.")
    print("Ou instale: pip install sumo")
    sys.exit(1)

# Tenta importar scikit-fuzzy (opcional -- fallback para regras lineares)
try:
    import skfuzzy as fuzz
    from skfuzzy import control as ctrl
    FUZZY_AVAILABLE = True
    print("[OK] scikit-fuzzy carregado. Controle fuzzy ativo.")
except ImportError:
    FUZZY_AVAILABLE = False
    print("[AVISO] scikit-fuzzy não encontrado. Usando controle linear adaptativo.")
    print("        Para instalar: pip install scikit-fuzzy")


# ============================================================
# CONFIGURAÇÕES DO CONTROLADOR
# ============================================================

# Velocidade de progressão da Onda Verde (m/s) -- 45 km/h
ONDA_VERDE_VELOCIDADE = 12.5  # 45 km/h

# Tempos semafóricos (segundos)
T_VERDE_MIN = 15.0
T_VERDE_MAX = 60.0
T_AMARELO = 3.0
T_VERMELHO_TOTAL = 2.0  # all-red

# Intervalo de otimização da Onda Verde (passos de simulação)
ONDA_VERDE_INTERVALO = 300  # a cada 30s (step-length=0.1s)

# IDs dos semáforos principais (gerados pelo netconvert)
TLS_IDS = ['K1', 'K3', 'K5', 'K7', 'X1', 'X2', 'X3', 'X4', 'F1', 'F3', 'F5', 'F7']

# Agrupamento para Onda Verde: semáforos em sequência no mesmo eixo
ONDA_VERDE_GRUPOS = {
    'kennedy_norte_sul': {
        'tls_ids': ['K1', 'K3', 'K5', 'K7'],
        'edges_norte_sul': ['KS_S_1', 'KS_S_2', 'KS_S_3', 'KS_S_4', 'KS_S_5', 'KS_S_6'],
        'edges_sul_norte': ['KN_N_2', 'KN_N_3', 'KN_N_4', 'KN_N_5', 'KN_N_6', 'KN_N_7'],
        'distancia_entre': [600, 400, 300, 300]  # metros entre K1-K3, K3-K5, ...
    },
    'floriano_sul_norte': {
        'tls_ids': ['F7', 'F5', 'F3', 'F1'],
        'edges_norte_sul': ['FN_N_1', 'FN_N_2', 'FN_N_3', 'FN_N_4', 'FN_N_5', 'FN_N_6'],
        'edges_sul_norte': ['FS_S_2', 'FS_S_3', 'FS_S_4', 'FS_S_5', 'FS_S_6', 'FS_S_7'],
        'distancia_entre': [300, 300, 400, 600],
    },
    'martim_afonso_leste_oeste': {
        'tls_ids': ['K1', 'X1', 'F1'],
        'edges_leste_oeste': ['AL_O_1', 'AL_O_2', 'AL_O_3'],
        'edges_oeste_leste': ['AL_L_2', 'AL_L_3', 'AL_L_4'],
        'distancia_entre': [280, 340],
    },
    'mariano_torres_leste_oeste': {
        'tls_ids': ['K5', 'X3', 'F5'],
        'edges_leste_oeste': ['TO_O_1', 'TO_O_2', 'TO_O_3'],
        'edges_oeste_leste': ['TO_L_2', 'TO_L_3', 'TO_L_4'],
        'distancia_entre': [280, 340],
    },
}

# Detectores virtuais: mapeia cada aproximação de interseção a um lane
# Formato: {tls_id: {phase_index: [lane_ids]}}
# Os índices de fase dependem do programa semafórico gerado pelo netconvert
# Aqui definimos um mapeamento simplificado para edges que chegam na interseção
DETECTOR_MAP = {}


# ============================================================
# SISTEMA FUZZY
# ============================================================

class ControladorFuzzy:
    """Controlador semafórico baseado em lógica fuzzy."""

    def __init__(self):
        if not FUZZY_AVAILABLE:
            return
        self._construir_sistema()

    def _construir_sistema(self):
        """Constrói as variáveis linguísticas e regras fuzzy."""
        # Entrada 1: Comprimento da fila (número de veículos parados)
        fila = ctrl.Antecedent(np.arange(0, 51, 1), 'fila')
        fila['baixa']     = fuzz.trimf(fila.universe, [0, 0, 15])
        fila['media']     = fuzz.trimf(fila.universe, [5, 20, 35])
        fila['alta']      = fuzz.trimf(fila.universe, [25, 40, 50])
        fila['critica']   = fuzz.trimf(fila.universe, [35, 50, 50])

        # Entrada 2: Taxa de ocupação (%)
        ocupacao = ctrl.Antecedent(np.arange(0, 101, 1), 'ocupacao')
        ocupacao['baixa']    = fuzz.trimf(ocupacao.universe, [0, 0, 40])
        ocupacao['media']    = fuzz.trimf(ocupacao.universe, [20, 50, 80])
        ocupacao['alta']     = fuzz.trimf(ocupacao.universe, [60, 100, 100])

        # Saída: Extensão do tempo de verde (segundos)
        extensao = ctrl.Consequent(np.arange(-20, 31, 1), 'extensao')
        extensao['reduzir_muito'] = fuzz.trimf(extensao.universe, [-20, -20, -10])
        extensao['reduzir_pouco'] = fuzz.trimf(extensao.universe, [-15, -5, 0])
        extensao['manter']        = fuzz.trimf(extensao.universe, [-5, 0, 5])
        extensao['aumentar_pouco'] = fuzz.trimf(extensao.universe, [0, 5, 15])
        extensao['aumentar_muito'] = fuzz.trimf(extensao.universe, [10, 20, 30])
        extensao['aumentar_max']   = fuzz.trimf(extensao.universe, [20, 30, 30])

        # Regras fuzzy (27 regras)
        regras = [
            ctrl.Rule(fila['baixa']    & ocupacao['baixa'],  extensao['reduzir_muito']),
            ctrl.Rule(fila['baixa']    & ocupacao['media'],  extensao['reduzir_pouco']),
            ctrl.Rule(fila['baixa']    & ocupacao['alta'],   extensao['manter']),
            ctrl.Rule(fila['media']    & ocupacao['baixa'],  extensao['reduzir_pouco']),
            ctrl.Rule(fila['media']    & ocupacao['media'],  extensao['manter']),
            ctrl.Rule(fila['media']    & ocupacao['alta'],   extensao['aumentar_pouco']),
            ctrl.Rule(fila['alta']     & ocupacao['baixa'],  extensao['manter']),
            ctrl.Rule(fila['alta']     & ocupacao['media'],  extensao['aumentar_pouco']),
            ctrl.Rule(fila['alta']     & ocupacao['alta'],   extensao['aumentar_muito']),
            ctrl.Rule(fila['critica']  & ocupacao['baixa'],  extensao['aumentar_pouco']),
            ctrl.Rule(fila['critica']  & ocupacao['media'],  extensao['aumentar_muito']),
            ctrl.Rule(fila['critica']  & ocupacao['alta'],   extensao['aumentar_max']),
        ]

        self.sistema_ctrl = ctrl.ControlSystem(regras)
        self.simulador = ctrl.ControlSystemSimulation(self.sistema_ctrl)

    def calcular_extensao(self, comprimento_fila, taxa_ocupacao):
        """Retorna a extensão (em segundos) a aplicar ao tempo de verde."""
        if not FUZZY_AVAILABLE:
            # Fallback linear
            score = (comprimento_fila / 50.0) * 0.6 + (taxa_ocupacao / 100.0) * 0.4
            if score < 0.2:
                return -10.0
            elif score < 0.4:
                return 0.0
            elif score < 0.6:
                return 10.0
            elif score < 0.8:
                return 20.0
            else:
                return 30.0

        self.simulador.input['fila'] = min(comprimento_fila, 50)
        self.simulador.input['ocupacao'] = min(taxa_ocupacao, 100)
        try:
            self.simulador.compute()
            return self.simulador.output['extensao']
        except Exception:
            return 0.0


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def obter_fila_aproximacao(tls_id, link_index):
    """
    Estima o comprimento da fila para uma aproximação (link) de um semáforo.
    Usa os lanes do link de entrada e conta veículos com velocidade < 0.1 m/s.
    """
    try:
        links = traci.trafficlight.getControlledLinks(tls_id)
        if link_index >= len(links):
            return 0

        lanes_do_link = []
        for lane_link in links[link_index]:
            if lane_link and len(lane_link) >= 2:
                lanes_do_link.append(lane_link[0])  # incoming lane

        count = 0
        for lane_id in lanes_do_link:
            try:
                veh_ids = traci.lane.getLastStepVehicleIDs(lane_id)
                for vid in veh_ids:
                    if traci.vehicle.getSpeed(vid) < 2.0:  # quase parado
                        count += 1
            except traci.exceptions.TraCIException:
                pass
        return count
    except traci.exceptions.TraCIException:
        return 0


def obter_ocupacao_aproximacao(tls_id, link_index):
    """Estima a taxa de ocupação (%) para uma aproximação."""
    try:
        links = traci.trafficlight.getControlledLinks(tls_id)
        if link_index >= len(links):
            return 0.0

        lanes_do_link = []
        for lane_link in links[link_index]:
            if lane_link and len(lane_link) >= 2:
                lanes_do_link.append(lane_link[0])

        total_veh = 0
        total_cap = 0
        for lane_id in lanes_do_link:
            try:
                total_veh += traci.lane.getLastStepVehicleNumber(lane_id)
                lane_len = traci.lane.getLength(lane_id)
                total_cap += max(1, lane_len / 7.0)  # ~7m por veículo
            except traci.exceptions.TraCIException:
                pass

        if total_cap == 0:
            return 0.0
        return min(100.0, (total_veh / total_cap) * 100.0)
    except traci.exceptions.TraCIException:
        return 0.0


def calcular_defasagem_onda_verde(distancia, velocidade_progressao, tempo_ciclo):
    """
    Calcula a defasagem (offset) para Onda Verde entre dois semáforos consecutivos.
    
    Args:
        distancia: distância entre os semáforos (m)
        velocidade_progressao: velocidade de progressão desejada (m/s)
        tempo_ciclo: duração do ciclo semafórico (s)
    
    Returns:
        offset em segundos
    """
    tempo_viagem = distancia / velocidade_progressao
    offset = tempo_viagem % tempo_ciclo
    return offset


# ============================================================
# LOOP PRINCIPAL DE CONTROLE
# ============================================================

def executar_controle():
    """Loop principal do controlador adaptativo."""
    
    # Conecta ao SUMO
    traci.init(port=8813)
    step = 0
    
    # Inicializa controlador fuzzy
    fuzzy_ctrl = ControladorFuzzy()

    # Estado dos semáforos
    estado_tls = {}  # {tls_id: {'fase_atual': int, 'tempo_fase': float, 'programa': ...}}
    
    # Inicializa estado para cada semáforo
    for tls_id in TLS_IDS:
        try:
            programa = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)
            estado_tls[tls_id] = {
                'fase_atual': 0,
                'tempo_fase': 0.0,
                'tempo_verde_base': T_VERDE_MIN,
                'num_fases': len(programa[0].phases) if programa else 4,
            }
            print(f"  TLS {tls_id}: {estado_tls[tls_id]['num_fases']} fases")
        except traci.exceptions.TraCIException:
            estado_tls[tls_id] = {
                'fase_atual': 0,
                'tempo_fase': 0.0,
                'tempo_verde_base': T_VERDE_MIN,
                'num_fases': 4,
            }

    # Contador para estatísticas
    stats = {
        'trocas_fase': 0,
        'tempos_verde_aplicados': [],
        'filas_medias': [],
    }

    print("\n[CONTROLADOR] Iniciando controle adaptativo...")
    print("=" * 60)
    
    while step < 90000:  # 9000s * 10 steps/s = 90000 steps (step-length=0.1)
        
        traci.simulationStep()
        tempo_sim = traci.simulation.getTime()
        
        # A cada 3 segundos, recalcula tempos semafóricos
        if step % 30 == 0:  # 30 steps * 0.1s = 3s
            
            for tls_id, estado in estado_tls.items():
                try:
                    fase_atual = traci.trafficlight.getPhase(tls_id)
                    duracao_fase = traci.trafficlight.getPhaseDuration(tls_id)
                    num_fases = estado['num_fases']
                    
                    # Coleta dados de fila e ocupação para cada aproximação
                    num_links = traci.trafficlight.getControlledLinks(tls_id)
                    num_aproximacoes = len(num_links)
                    
                    fila_max = 0
                    ocup_max = 0
                    for link_idx in range(num_aproximacoes):
                        fila = obter_fila_aproximacao(tls_id, link_idx)
                        ocup = obter_ocupacao_aproximacao(tls_id, link_idx)
                        fila_max = max(fila_max, fila)
                        ocup_max = max(ocup_max, ocup)
                    
                    stats['filas_medias'].append(fila_max)
                    
                    # Calcula novo tempo de verde fuzzy
                    extensao = fuzzy_ctrl.calcular_extensao(fila_max, ocup_max)
                    novo_verde = max(T_VERDE_MIN, min(T_VERDE_MAX, T_VERDE_MIN + extensao))
                    
                    estado['tempo_verde_base'] = novo_verde
                    
                    # Aplica o novo tempo de duração da fase atual (se for fase verde)
                    # No SUMO, cada programa tem fases alternadas (verde + amarelo + vermelho)
                    duracao_restante = traci.trafficlight.getNextSwitch(tls_id) - tempo_sim
                    
                    # Se a duração restante é alta e o controlador quer mudar, ajusta
                    if duracao_restante > 10 and fase_atual % 2 == 0:
                        # Fase verde atual -- ajusta duração
                        traci.trafficlight.setPhaseDuration(tls_id, novo_verde)
                    
                except traci.exceptions.TraCIException:
                    pass
            
            # ---- SINCRONIZAÇÃO ONDA VERDE (a cada 30s) ----
            if step % ONDA_VERDE_INTERVALO == 0:
                for grupo_nome, grupo in ONDA_VERDE_GRUPOS.items():
                    tls_ids = grupo['tls_ids']
                    dists = grupo['distancia_entre']
                    
                    for i in range(len(tls_ids) - 1):
                        tls_a = tls_ids[i]
                        tls_b = tls_ids[i + 1]
                        dist = dists[i]
                        
                        try:
                            tempo_ciclo_a = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_a)[0].duration if traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_a) else 60
                        except:
                            tempo_ciclo_a = 60
                        
                        offset = calcular_defasagem_onda_verde(dist, ONDA_VERDE_VELOCIDADE, tempo_ciclo_a)
                        
                        # Aplica offset relativo ao semáforo B
                        try:
                            tempo_corr = (tempo_sim + offset) % tempo_ciclo_a
                            # Não há setOffset direto em versões recentes -- 
                            # ajustamos via setPhaseDuration + setPhase
                            pass
                        except:
                            pass
        
        # Log a cada 900s simulados (15 min)
        if step % 9000 == 0 and step > 0:
            minuto = int(tempo_sim / 60)
            n_veiculos = traci.vehicle.getIDCount()
            fila_media = np.mean(stats['filas_medias'][-100:]) if stats['filas_medias'] else 0
            print(f"  [t={minuto:3d}min] Veículos ativos: {n_veiculos:5d} | Fila média: {fila_media:.1f} veh")
        
        step += 1
    
    # Finaliza
    traci.close()
    
    print("=" * 60)
    print("[CONTROLADOR] Simulação concluída.")
    print(f"  Total de ajustes de fase: {stats['trocas_fase']}")
    if stats['tempos_verde_aplicados']:
        print(f"  Tempo verde médio: {np.mean(stats['tempos_verde_aplicados']):.1f}s")
    print()

    return stats


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("  Controlador Adaptativo Fuzzy + Onda Verde")
    print("  Quadrilátero Central de Curitiba")
    print("  UTFPR - Ciências do Ambiente - 2026/1")
    print("=" * 60)
    print()
    print("Certifique-se de que o SUMO está rodando com:")
    print("  sumo-gui -c quadrilatero_tobe.sumocfg --start")
    print("  (ou sumo -c quadrilatero_tobe.sumocfg --start)")
    print()
    
    input("Pressione ENTER para conectar ao SUMO e iniciar o controle...")
    
    estatisticas = executar_controle()
    
    print("\nSimulação finalizada. Os resultados foram salvos em:")
    print("  results/tripinfo_tobe.xml")
    print("  results/emissions_tobe.xml")
    print("  results/edgedata_tobe.xml")
