#!/usr/bin/env python3
"""Extrai edges principais da rede SUMO para usar como origens/destinos."""
import xml.etree.ElementTree as ET
import sys

net_path = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario2\map\curitiba_centro.net.xml'
tree = ET.parse(net_path)
root = tree.getroot()

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
    nlanes = len(lanes)
    length = float(lanes[0].get('length', 0))
    edges_info[eid] = {
        'type': etype,
        'speed': speed,
        'lanes': nlanes,
        'length': length
    }

def priority(etype):
    if 'primary' in etype and 'link' not in etype: return 5
    if 'secondary' in etype and 'link' not in etype: return 4
    if 'tertiary' in etype and 'link' not in etype: return 3
    if 'primary_link' in etype or 'secondary_link' in etype: return 2
    if 'residential' in etype: return 1
    return 0

# All primary+secondary edges
main_edges = [eid for eid, info in edges_info.items() if priority(info['type']) >= 4]
print(f"Primary+secondary edges: {len(main_edges)}")

# Also tertiary for more routes
tertiary_edges = [eid for eid, info in edges_info.items() if priority(info['type']) >= 3]
print(f"Primary+secondary+tertiary edges: {len(tertiary_edges)}")

# Print edge IDs for verification
print("\n=== ALL PRIMARY EDGES ===")
for eid in main_edges:
    info = edges_info[eid]
    spd = info['speed'] * 3.6
    print(f"  Edge {eid:35s} type={info['type']:30s} speed={spd:.0f}km/h lanes={info['lanes']} length={info['length']:.0f}m")

print("\n=== ALL SECONDARY EDGES ===")
for eid, info in edges_info.items():
    if priority(info['type']) == 4:
        spd = info['speed'] * 3.6
        print(f"  Edge {eid:35s} type={info['type']:30s} speed={spd:.0f}km/h lanes={info['lanes']} length={info['length']:.0f}m")
