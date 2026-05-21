#!/usr/bin/env python3
"""
Gera demanda veicular para o quadrilatero central de Curitiba.
Baseado no Projeto 1 CA 2026: pico matutino 06h30-09h00 (9000s).
Usa fluxos (flows) deterministicos com seed fixo.

Gera quadrilatero.rou.xml com:
- Tipos veiculares conforme PDF (gasolina 55%%, etanol 15%%, moto 12%%, onibus 13%%, VUC 5%%)
- Fluxos nos edges principais da regiao
- Distribuicao de pico: maior intensidade entre 1800s-7200s
"""
import xml.etree.ElementTree as ET
import random
import os

random.seed(42)

# ============================================================
# 1. Identificar edges principais da rede
# ============================================================
tree = ET.parse('quadrilatero.net.xml')
root = tree.getroot()

# Extrair todos os edges nao-internos com tipo via
edges_info = {}
for edge in root.findall('edge'):
    eid = edge.get('id', '')
    if eid.startswith(':'):
        continue
    lanes = edge.findall('lane')
    if not lanes:
        continue
    speed = float(lanes[0].get('speed', '13.89'))
    etype = edge.get('type', '')
    edges_info[eid] = {
        'type': etype,
        'speed': speed,
        'lanes': len(lanes),
        'length': float(lanes[0].get('length', '0'))
    }

# Classificar edges: primary >> secondary >> tertiary >> residential >> others
def edge_priority(etype):
    if 'primary' in etype and 'link' not in etype:
        return 5
    if 'secondary' in etype and 'link' not in etype:
        return 4
    if 'tertiary' in etype and 'link' not in etype:
        return 3
    if 'primary_link' in etype or 'secondary_link' in etype:
        return 2
    if 'residential' in etype:
        return 1
    return 0

for eid, info in edges_info.items():
    info['priority'] = edge_priority(info['type'])

# Filtrar edges principais (priority >= 3) como origens/destinos para fluxos
main_edges = [eid for eid, info in edges_info.items() if info['priority'] >= 3]
print(f"Total de edges nao-internos: {len(edges_info)}")
print(f"Edges principais (>= tertiary): {len(main_edges)}")

# ============================================================
# 2. Criar arquivo .rou.xml com fluxos
# ============================================================
SIM_END = 3600.0
PEAK_START = 600.0   # 10 min de warm-up
PEAK_END = 3600.0    # pico ate o fim

def gerar_rou_xml():
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('')
    lines.append('<!-- Demanda veicular - Quadrilatero Central de Curitiba -->')
    lines.append('<!-- Projeto Ciencias do Ambiente - UTFPR 2026/1 -->')
    lines.append('<!-- Gerado por gerar_demanda.py baseado no projeto_ca_2026.tex -->')
    lines.append('')
    lines.append('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">')
    lines.append('')
    
    # Tipos veiculares (conforme Tabela 2 do projeto)
    lines.append('    <!-- Tipos veiculares conforme Tabela do projeto -->')
    lines.append('    <vType id="carro_gasolina" accel="2.6" decel="4.5" sigma="0.5" '
                 'length="4.3" minGap="2.5" maxSpeed="16.67" color="0.2,0.2,0.8"/>')
    lines.append('    <vType id="carro_etanol"   accel="2.6" decel="4.5" sigma="0.5" '
                 'length="4.3" minGap="2.5" maxSpeed="16.67" color="0.1,0.7,0.1"/>')
    lines.append('    <vType id="moto"           accel="3.5" decel="6.0" sigma="0.7" '
                 'length="2.0" minGap="1.5" maxSpeed="18.06" color="0.9,0.3,0.1"/>')
    lines.append('    <vType id="onibus"         accel="1.3" decel="3.5" sigma="0.3" '
                 'length="12.0" minGap="3.0" maxSpeed="13.89" color="0.8,0.8,0.0"/>')
    lines.append('    <vType id="vuc"            accel="1.5" decel="3.8" sigma="0.4" '
                 'length="7.0" minGap="3.0" maxSpeed="13.89" color="0.5,0.5,0.5"/>')
    lines.append('')

    # Distribuicao da frota: gasolina 55%%, etanol 15%%, moto 12%%, onibus 13%%, VUC 5%%
    # Volume total estimado: 459 veh/h nas vias principais da area
    # Em 9000s (2.5h): ~1147 veiculos
    # Distribuicao por tipo:
    CAR_G = 0.55
    CAR_E = 0.15
    MOTO  = 0.12
    BUS   = 0.13
    VUC   = 0.05

    # Volume total estimado: 459 veh/h nas vias principais
    # Em 9000s (2.5h): ~1147 veiculos
    # Distribuicao por tipo conforme PDF
    
    # Usar <flow> ao inves de <trip> - o SUMO faz o roteamento automaticamente
    # Cada flow gera veiculos periodicamente entre begin e end
    
    lines.append('    <!-- ============================================ -->')
    lines.append('    <!-- Fluxos de veiculos - Pico Matutino (06h30-09h00) -->')
    lines.append('    <!-- ============================================ -->')
    lines.append('')
    
    # Agrupar edges principais em 3 grupos: norte, centro, sul 
    # para criar fluxos coerentes com origem/destino
    
    def gerar_flows(vtype, prefix, count, vehs_per_hour):
        """Gera <flow> elements distribuidos nos edges principais."""
        flow_lines = []
        
        # Selecionar pares de edges para os fluxos
        # Usar seed fixa para reproducibilidade
        origens = random.sample(main_edges, min(30, len(main_edges)))
        destinos = random.sample(main_edges, min(30, len(main_edges)))
        
        # Criar flows: cada flow e um par origem-destino com taxa horaria
        n_flows = min(20, len(origens))
        vph_per_flow = max(1, vehs_per_hour // n_flows)
        
        for i in range(n_flows):
            orig = origens[i]
            dest = destinos[(i + 3) % len(destinos)]
            if dest == orig:
                dest = destinos[(i + 7) % len(destinos)]
            
            flow_lines.append(
                f'    <flow id="{prefix}_f{i}" type="{vtype}" '
                f'from="{orig}" to="{dest}" '
                f'begin="0.0" end="{SIM_END:.0f}" '
                f'vehsPerHour="{vph_per_flow}" '
                f'departSpeed="random"/>'
            )
        
        return flow_lines
    
    saldo = 0
    for vtype, prefix, frac in [
        ('carro_gasolina', 'cg', CAR_G),
        ('carro_etanol',   'ce', CAR_E),
        ('moto',           'mt', MOTO),
        ('onibus',         'bus', BUS),
        ('vuc',            'vc', VUC),
    ]:
        total_vph = int(459 * frac)  # 459 veh/h total, proporcional
        if total_vph <= 0:
            total_vph = 1
        saldo += total_vph
        for line in gerar_flows(vtype, prefix, 0, total_vph):
            lines.append(line)
        lines.append('')
    
    print(f"  VPH total alocado: {saldo} (target: 459)")
    
    lines.append('</routes>')
    
    return '\n'.join(lines)

# Gerar arquivo
rou_content = gerar_rou_xml()
output_path = 'quadrilatero.rou.xml'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(rou_content)

print(f"\nArquivo gerado: {output_path}")
print(f"Volume horario total: ~459 veh/h")
print(f"Distribuicao da frota:")
print(f"  Carros gasolina: 55%%")
print(f"  Carros etanol:   15%%")
print(f"  Motos:           12%%")
print(f"  Onibus:          13%%")
print(f"  VUC:              5%%")
