#!/usr/bin/env python3
"""Analisa a rede gerada e mostra edges das ruas principais e semaforos."""
import xml.etree.ElementTree as ET
import sys

tree = ET.parse('curitiba_centro.net.xml')
root = tree.getroot()

# 1. Contagens basicas
edges = root.findall('edge')
junctions = root.findall('junction')
tls_list = root.findall('.//tlLogic')

print("=== ESTATISTICAS DA REDE ===")
print(f"Total edges: {len(edges)}")
print(f"Total junctions: {len(junctions)}")
print(f"Total tlLogics: {len(tls_list)}")

# 2. Semforos com IDs
print("\n=== SEMAFOROS DETECTADOS ===")
for tl in tls_list:
    tl_id = tl.get('id','')
    tl_type = tl.get('type','')
    phases = tl.findall('phase')
    print(f"  TLS {tl_id} (type={tl_type}, phases={len(phases)})")

# 3. Ruas principais com nome
print("\n=== RUAS PRINCIPAIS ===")
targets = ['kennedy','floriano','martim','afonso','mariano','torres','tourinho','mario','xv','calcadao','presidente','peixoto']
for edge in edges:
    eid = edge.get('id','')
    name = edge.get('name','')
    if name:
        nl = name.lower().replace('ç','c').replace('ã','a')
        if any(t in nl for t in targets):
            lanes = edge.findall('lane')
            nlanes = len(lanes) if lanes else 0
            speed = float(lanes[0].get('speed',0))*3.6 if lanes else 0
            length = float(lanes[0].get('length',0)) if lanes else 0
            print(f"  {eid:30s} {name:45s} {speed:5.0f}km/h {nlanes}faixas {length:.0f}m")

# 4. Todas as edges com nome (para ver mais opcoes)
print("\n=== TODAS AS EDGES COM NOME (primeiras 50) ===")
count = 0
for edge in edges:
    name = edge.get('name','')
    if name:
        eid = edge.get('id','')
        lanes = edge.findall('lane')
        nlanes = len(lanes) if lanes else 0
        speed = float(lanes[0].get('speed',0))*3.6 if lanes else 0
        print(f"  {eid:30s} {name:45s} {speed:5.0f}km/h {nlanes}faixas")
        count += 1
        if count >= 50:
            break

# 5. Ver edges sem nome mas com highway type (arterial, etc)
print("\n=== VIAS RAPIDAS (speed > 40km/h) ===")
count = 0
for edge in edges:
    eid = edge.get('id','')
    if eid.startswith(':'):
        continue
    name = edge.get('name','')
    lanes = edge.findall('lane')
    if not lanes:
        continue
    speed = float(lanes[0].get('speed',0))*3.6
    if speed >= 40:
        print(f"  {eid:30s} name={name:45s} speed={speed:.0f}km/h")
        count += 1
        if count >= 30:
            break
