#!/usr/bin/env python3
"""
Cria arquivo adicional (add.xml) com detectores laneAreaDetector
para os cruzamentos principais do quadrilátero central.
"""
import xml.etree.ElementTree as ET

NET_PATH = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario2\map\curitiba_centro.net.xml'
ADD_PATH = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario2\map\cenario2.add.xml'

tree = ET.parse(NET_PATH)
root = tree.getroot()

# Build edge info
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
        'lanes': lanes,
    }

def edge_priority(etype):
    if 'primary' in etype and 'link' not in etype: return 5
    if 'secondary' in etype and 'link' not in etype: return 4
    if 'tertiary' in etype and 'link' not in etype: return 3
    if 'primary_link' in etype or 'secondary_link' in etype: return 2
    if 'residential' in etype: return 1
    return 0

# Build connection info per junction
# Find incoming edges for each junction
junction_edges = {}  # junction_id -> set of incoming edge IDs
for edge in root.findall('edge'):
    eid = edge.get('id', '')
    if eid.startswith(':'):
        continue
    to_j = edge.get('to', '')
    if to_j:
        if to_j not in junction_edges:
            junction_edges[to_j] = set()
        junction_edges[to_j].add(eid)

# Also get from edges
for edge in root.findall('edge'):
    eid = edge.get('id', '')
    if eid.startswith(':'):
        continue
    from_j = edge.get('from', '')
    if from_j:
        if from_j not in junction_edges:
            junction_edges[from_j] = set()

# Find traffic lights and their controlled junctions
tls_info = []
for tl in root.findall('.//tlLogic'):
    tl_id = tl.get('id', '')
    tl_type = tl.get('type', '')
    phases = tl.findall('phase')
    
    # Find which edges this TLS controls
    incoming = junction_edges.get(tl_id, set())
    
    # Categorize incoming edges
    priorities = [edge_priority(edges_info.get(e, {}).get('type', '')) for e in incoming if e in edges_info]
    max_pri = max(priorities) if priorities else 0
    min_pri = min(priorities) if priorities else 0
    
    tls_info.append({
        'id': tl_id,
        'type': tl_type,
        'phases': len(phases),
        'n_incoming': len(incoming),
        'max_pri': max_pri,
        'min_pri': min_pri,
        'incoming': incoming,
    })

# Select TLS at primary-primary or primary-secondary intersections (max_pri>=4 and min_pri>=3)
main_tls = [t for t in tls_info if t['max_pri'] >= 4 and t['min_pri'] >= 3 and t['n_incoming'] >= 3]
# Sort by number of incoming edges (most connected first)
main_tls.sort(key=lambda t: (-t['max_pri'], -t['n_incoming']))

print(f"Total TLS: {len(tls_info)}")
print(f"Main TLS (pri>=4 & sec>=3): {len(main_tls)}")

# Keep top 10-15
KEEP = 15
selected_tls = main_tls[:KEEP]
print(f"\nSelected {KEEP} TLS for detector placement:")
for t in selected_tls:
    incoming_names = []
    for e in t['incoming']:
        if e in edges_info:
            incoming_names.append(f"{edges_info[e]['type']}")
    print(f"  TLS {t['id']}: incoming={t['n_incoming']} pri={t['max_pri']}/{t['min_pri']} phases={t['phases']}")
    for e in sorted(list(t['incoming'])):
        if e in edges_info:
            info = edges_info[e]
            for lane in info['lanes']:
                lane_idx = lane.get('index', '0')
                lane_id = f"{e}_{lane_idx}"
                length = float(lane.get('length', 100))
                spd = info['speed'] * 3.6
                print(f"    Lane {lane_id:40s} type={info['type']:25s} speed={spd:.0f} len={length:.0f}m")

# Generate add.xml
lines = []
lines.append('<?xml version="1.0" encoding="UTF-8"?>')
lines.append('')
lines.append('<!-- Detectores de fila - Cenário 2 (Semáforo Adaptativo por Fila) -->')
lines.append('')
lines.append('<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
             'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">')
lines.append('')

det_count = 0
for t in selected_tls:
    for e in sorted(list(t['incoming'])):
        if e not in edges_info:
            continue
        info = edges_info[e]
        for lane in info['lanes']:
            lane_idx = lane.get('index', '0')
            lane_id = f"{e}_{lane_idx}"
            length = float(lane.get('length', 100))
            
            # Lane area detector: 50m from stop line
            det_len = min(50, length - 5)  # ensure we don't exceed lane length
            if det_len < 5:
                continue
            
            pos = -50  # 50m before stop line
            if length < 55:
                pos = -(length - 5)
            
            # Use shortened unique ID from lane
            edge_short = e.replace('#', '_').replace('-', 'm')[:20]
            det_id = f"det_{t['id']}_{edge_short}_{lane_idx}"
            lines.append(f'    <laneAreaDetector id="{det_id}" lane="{lane_id}" pos="{pos:.0f}" length="{det_len:.0f}" freq="5" file="../saida/detectores.xml"/>')
            det_count += 1

lines.append('')
lines.append('</additional>')

with open(ADD_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"\nGenerated {det_count} lane area detectors in {ADD_PATH}")
