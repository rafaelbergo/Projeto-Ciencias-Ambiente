#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse(r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario2\map\curitiba_centro.net.xml')
root = tree.getroot()

edges = root.findall('edge')
tls = root.findall('.//tlLogic')
junctions = root.findall('junction')
loc = root.find('location')

print(f"Total edges: {len(edges)}")
non_int = [e for e in edges if not e.get('id','').startswith(':')]
print(f"Non-internal edges: {len(non_int)}")
print(f"Total tlLogics: {len(tls)}")
print(f"Total junctions: {len(junctions)}")
if loc:
    print(f"origBoundary: {loc.get('origBoundary','')}")
    print(f"convBoundary: {loc.get('convBoundary','')}")

def priority(etype):
    if 'primary' in etype and 'link' not in etype: return 5
    if 'secondary' in etype and 'link' not in etype: return 4
    if 'tertiary' in etype and 'link' not in etype: return 3
    if 'primary_link' in etype or 'secondary_link' in etype: return 2
    if 'residential' in etype: return 1
    return 0

prim = [] 
sec = []
tert = []
for edge in edges:
    eid = edge.get('id','')
    etype = edge.get('type','')
    p = priority(etype)
    if p == 5: prim.append(eid)
    elif p == 4: sec.append(eid)
    elif p == 3: tert.append(eid)

print(f"Primary: {len(prim)}, Secondary: {len(sec)}, Tertiary: {len(tert)}")
print(f"Total main: {len(prim)+len(sec)+len(tert)}")

# Show TLS count with phases
phase_counts = {}
for tl in tls:
    n = len(tl.findall('phase'))
    phase_counts[n] = phase_counts.get(n, 0) + 1
print(f"TLS by phase count: {dict(sorted(phase_counts.items()))}")
