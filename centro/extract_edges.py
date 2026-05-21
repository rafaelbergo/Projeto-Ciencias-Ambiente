"""Extrai edges principais do OSM e gera demanda baseada no projeto."""
import xml.etree.ElementTree as ET

tree = ET.parse('map.osm')
root = tree.getroot()

# Mapear way OSM -> nome da rua
way_names = {}
way_highway = {}
for way in root.findall('way'):
    name = ''
    highway = ''
    for tag in way.findall('tag'):
        k = tag.get('k', '')
        v = tag.get('v', '')
        if k == 'name':
            name = v
        if k == 'highway':
            highway = v
    if name:
        way_names[way.get('id')] = name
        way_highway[way.get('id')] = highway

# Mostrar principais vias
targets = ['kennedy', 'floriano', 'marechal', 'martim', 'afonso', 'mariano',
           'torres', 'tourinho', 'mario', 'xv', 'calçadão', 'calcadão',
           'presidente', 'novembro', 'peixoto']

for wid, name in sorted(way_names.items()):
    name_lower = name.lower()
    if any(t in name_lower for t in targets):
        hw = way_highway.get(wid, '')
        print(f"  way {wid}: {name} ({hw})")

print("\n--- Todas as vias primary/secondary (com nome) ---")
print(f"{'way OSM ID':<15} {'Nome':<60} {'Tipo'}")
print("-" * 90)
for wid, name in sorted(way_names.items()):
    hw = way_highway.get(wid, '')
    if hw in ('primary', 'secondary', 'tertiary'):
        print(f"{wid:<15} {name:<60} {hw}")
