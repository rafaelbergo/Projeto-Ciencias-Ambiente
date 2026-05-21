#!/usr/bin/env python3
"""
Gera quadrilatero_tobe.net.xml com semaforos otimizados.
Ajusta tempos verdes para 35s (vs 25-31s default).
"""
import xml.etree.ElementTree as ET

print("Carregando rede original...")
tree = ET.parse('quadrilatero.net.xml')
root = tree.getroot()

tl_logic = root.findall('.//tlLogic')
print(f"Total de semaforos: {len(tl_logic)}")

GREEN_TIME = 35

modificados = 0
for tl in tl_logic:
    phases = tl.findall('phase')
    for phase in phases:
        state = phase.get('state', '')
        if 'G' in state or 'g' in state:
            if 'y' not in state.lower() or state.lower().count('g') > state.lower().count('y'):
                phase.set('duration', str(GREEN_TIME))
                modificados += 1

print(f"Fases verdes ajustadas: {modificados}")
tree.write('quadrilatero_tobe.net.xml', encoding='UTF-8', xml_declaration=True)
print(f"Rede otimizada salva: quadrilatero_tobe.net.xml")
print(f"Tempo verde: {GREEN_TIME}s")
