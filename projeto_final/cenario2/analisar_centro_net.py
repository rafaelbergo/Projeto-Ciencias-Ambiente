#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse(r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\centro\quadrilatero.net.xml')
root = tree.getroot()

edges = root.findall('edge')
print(f"Total edges: {len(edges)}")
non_internal = [e for e in edges if not e.get('id','').startswith(':')]
print(f"Non-internal edges: {len(non_internal)}")

tls = root.findall('.//tlLogic')
print(f"Total tlLogics: {len(tls)}")

# Check location
loc = root.find('location')
if loc is not None:
    print(f"Location: {loc.get('origBoundary','')}")
    print(f"  Size: {loc.get('convBoundary','')}")

# Show some edges with their types
for edge in edges[:30]:
    eid = edge.get('id','')
    if eid.startswith(':'):
        continue
    etype = edge.get('type','')
    speed = ""
    lanes_elem = edge.findall('lane')
    if lanes_elem:
        speed = f"{float(lanes_elem[0].get('speed',0))*3.6:.0f}km/h"
    print(f"  Edge {eid:35s} type={etype:30s} {speed}")

print("\n--- TLS examples ---")
for tl in tls[:10]:
    print(f"  TLS {tl.get('id')} phases={len(tl.findall('phase'))}")
