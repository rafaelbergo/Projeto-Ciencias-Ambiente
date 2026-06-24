#!/usr/bin/env python3
"""
Gera demanda veicular para o Cenário 2 (Semáforo Adaptativo por Fila).
Projeto 1 - Ciências do Ambiente - UTFPR 2026/1
Quadrilátero Central de Curitiba - Pico Tarde 17h-19h (7200s)
14.250 veh/h distribuídos em 6 rotas principais + viagens difusas.
"""
import xml.etree.ElementTree as ET
import random
import sys

random.seed(42)

NET_PATH = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario2\map\curitiba_centro.net.xml'
OUTPUT_DIR = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario2\map'

# Increase n_flows for better distribution
N_FLOWS = 50   # fewer flows for faster testing

# ======================= PARÂMETROS =======================
SIM_END = 7200.0  # 17h-19h
WARMUP = 60.0     # 1 min warmup (reduzido para testes rápidos)

# Demanda total: 14.250 veh/h
TOTAL_VPH = 14250

# Composição veicular
FROTA = {
    'passenger':  {'pct': 0.72, 'accel': 2.6, 'decel': 4.5, 'sigma': 0.5,
                   'length': 4.5, 'minGap': 2.5, 'maxSpeed': 13.89,
                   'emissionClass': 'HBEFA3/PC_G_EU4', 'vClass': 'passenger'},
    'motorcycle': {'pct': 0.15, 'accel': 3.5, 'decel': 5.0, 'sigma': 0.7,
                   'length': 2.2, 'minGap': 1.0, 'maxSpeed': 13.89,
                   'emissionClass': 'HBEFA3/LDV_G_EU4', 'vClass': 'motorcycle'},
    'bus':        {'pct': 0.06, 'accel': 1.2, 'decel': 4.0, 'sigma': 0.5,
                   'length': 12.0, 'minGap': 3.0, 'maxSpeed': 11.11,
                   'emissionClass': 'HBEFA3/Bus', 'vClass': 'bus'},
    'truck':      {'pct': 0.06, 'accel': 1.0, 'decel': 3.5, 'sigma': 0.6,
                   'length': 8.0, 'minGap': 3.0, 'maxSpeed': 11.11,
                   'emissionClass': 'HBEFA3/HDV', 'vClass': 'truck'},
    'bike':       {'pct': 0.01, 'accel': 1.2, 'decel': 3.0, 'sigma': 0.8,
                   'length': 1.8, 'minGap': 1.0, 'maxSpeed': 6.94,
                   'emissionClass': 'HBEFA3/LDV_G_EU4', 'vClass': 'bicycle'},
}

# ======================= EXTRAIR EDGES =======================
tree = ET.parse(NET_PATH)
root = tree.getroot()

def edge_priority(etype):
    if 'primary' in etype and 'link' not in etype: return 5
    if 'secondary' in etype and 'link' not in etype: return 4
    if 'tertiary' in etype and 'link' not in etype: return 3
    if 'primary_link' in etype or 'secondary_link' in etype: return 2
    if 'residential' in etype: return 1
    return 0

edges_info = {}
for edge in root.findall('edge'):
    eid = edge.get('id', '')
    if eid.startswith(':'):
        continue
    lanes = edge.findall('lane')
    if not lanes:
        continue
    speed = float(lanes[0].get('speed', 13.89))
    etype = edge.get('type', '')
    edges_info[eid] = {
        'type': etype,
        'speed': speed,
        'lanes': len(lanes),
        'length': float(lanes[0].get('length', 0)),
        'priority': edge_priority(etype)
    }

# Separar edges por categoria
primary_edges = [eid for eid, info in edges_info.items() if info['priority'] == 5]
secondary_edges = [eid for eid, info in edges_info.items() if info['priority'] == 4]
tertiary_edges = [eid for eid, info in edges_info.items() if info['priority'] == 3]
all_main = primary_edges + secondary_edges + tertiary_edges

print(f"Primary edges: {len(primary_edges)}")
print(f"Secondary edges: {len(secondary_edges)}")
print(f"Tertiary edges: {len(tertiary_edges)}")
print(f"Total main edges: {len(all_main)}")

# ======================= GERAR TRIPS =======================
def gerar_trips(vtype, prefix, vph_total, n_flows=N_FLOWS):
    """Gera trips (from-to) para um tipo veicular."""
    vph = int(vph_total * FROTA[vtype]['pct'])
    if vph < 1:
        return []
    
    flows = []
    vph_per_flow = max(1, vph // n_flows)
    remaining = vph - (vph_per_flow * n_flows)
    
    used_edges = random.sample(all_main, min(n_flows * 2, len(all_main)))
    
    for i in range(n_flows):
        orig = used_edges[i % len(used_edges)]
        dest = used_edges[(i + n_flows // 3) % len(used_edges)]
        if dest == orig:
            dest = used_edges[(i + n_flows // 2) % len(used_edges)]
        
        extra = 1 if i < remaining else 0
        this_vph = vph_per_flow + extra
        if this_vph < 1:
            continue
        
        flows.append(f'    <flow id="{prefix}_f{i}" type="{vtype}" '
                     f'from="{orig}" to="{dest}" '
                     f'begin="{WARMUP:.0f}" end="{SIM_END:.0f}" '
                     f'vehsPerHour="{this_vph}" '
                     f'departSpeed="random" departLane="best"/>')
    
    return flows

# ======================= GERAR ARQUIVO =======================
lines = []
lines.append('<?xml version="1.0" encoding="UTF-8"?>')
lines.append('')
lines.append('<!-- Demanda veicular - Cenário 2 (Semáforo Adaptativo por Fila) -->')
lines.append('<!-- Quadrilátero Central de Curitiba - Pico Tarde 17h-19h -->')
lines.append('<!-- 14.250 veh/h | Projeto 1 CA - UTFPR 2026/1 -->')
lines.append('')
lines.append('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
             'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">')
lines.append('')

# Tipos veiculares
for vtype, params in FROTA.items():
    attrs = ' '.join(f'{k}="{v}"' for k, v in params.items() if k != 'pct')
    lines.append(f'    <vType id="{vtype}" {attrs}/>')
lines.append('')

# Gerar flows para cada tipo
for vtype in FROTA:
    flows = gerar_trips(vtype, vtype[:3], TOTAL_VPH)
    for f in flows:
        lines.append(f)
    lines.append('')

lines.append('</routes>')

output_path = OUTPUT_DIR + '/cenario2.rou.xml'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

# Summary
print(f"\nArquivo gerado: {output_path}")
print(f"Demanda total: {TOTAL_VPH} veh/h x 2h = {TOTAL_VPH * 2} veículos")
for vtype, params in FROTA.items():
    vph = int(TOTAL_VPH * params['pct'])
    print(f"  {vtype}: {vph} veh/h ({params['pct']*100:.0f}%)")
