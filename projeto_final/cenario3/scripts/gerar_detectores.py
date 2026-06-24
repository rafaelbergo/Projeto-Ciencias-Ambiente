#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera detectores (laneAreaDetectors) para o Cenario 3."""
import xml.etree.ElementTree as ET

NET_PATH = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario3\map\curitiba_centro.net.xml'
OUT_PATH = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario3\map\cenario3.add.xml'

DETECTOR_LENGTH = 50  # comprimento do laco em metros
DETECTOR_POS = -50    # posicao relativa ao fim da faixa (50m antes)

def priority(etype):
    if 'primary' in etype and 'link' not in etype: return 5
    if 'secondary' in etype and 'link' not in etype: return 4
    if 'tertiary' in etype and 'link' not in etype: return 3
    return 0

def main():
    tree = ET.parse(NET_PATH)
    root = tree.getroot()
    
    # Mapa: edge -> (type, speed, lanes)
    edge_info = {}
    for edge in root.findall('edge'):
        eid = edge.get('id', '')
        if eid.startswith(':'):
            continue
        lanes = edge.findall('lane')
        if not lanes:
            continue
        etype = edge.get('type', '')
        speed = float(lanes[0].get('speed', 13.89))
        edge_info[eid] = {'type': etype, 'speed': speed, 'lanes': lanes}
    
    # Recolher TLSs
    tls_list = []
    for tl in root.findall('tlLogic'):
        tls_id = tl.get('id', '')
        tls_list.append({'id': tls_id})
    
    # Para cada TLS, encontrar edges de entrada
    for tl in tls_list:
        tls_id = tl['id']
        # Encontrar junction associada
        junction = root.find(f".//junction[@id='{tls_id}']")
        if junction is None:
            junction = root.find(f".//junction[@type='traffic_light'][@id='{tls_id}']")
        
        incomings = []
        if junction is not None:
            inc = junction.get('incLanes', '')
            if inc:
                incomings = [l.split('_')[0] for l in inc.split()]
        
        # Remover duplicados e internal edges
        seen = set()
        unique_edges = []
        for e in incomings:
            if e.startswith(':'):
                continue
            if e not in seen and e in edge_info:
                seen.add(e)
                unique_edges.append(e)
        
        tl['incoming'] = unique_edges
    
    # Filtrar TLSs com mais de 3 entradas e prioridade >= 4
    valid_tls = []
    for tl in tls_list:
        edges = tl['incoming']
        if len(edges) < 3:
            continue
        
        # Classificar entradas por prioridade
        max_pri = max(priority(edge_info[e]['type']) for e in edges if e in edge_info)
        sec_count = sum(1 for e in edges if e in edge_info and priority(edge_info[e]['type']) >= 4)
        
        if max_pri >= 4 and sec_count >= 3:
            nphases = len(root.findall(f".//tlLogic[@id='{tl['id']}']/phase"))
            tl['phases'] = nphases
            tl['pri'] = max_pri
            tl['sec'] = sec_count
            valid_tls.append(tl)
    
    # Gerar detectores
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<additional>')
    lines.append('')
    
    selected = []
    for tl in valid_tls:
        tls_id = tl['id']
        edges = tl['incoming']
        
        det_count = 0
        for e in edges:
            if e not in edge_info:
                continue
            info = edge_info[e]
            etype = info['type']
            
            for lane in info['lanes']:
                lane_id = lane.get('id', '')
                lane_len = float(lane.get('length', 100))
                
                # Posicao do detector: 50m antes do fim da faixa
                pos = max(0, lane_len - DETECTOR_LENGTH)
                det_len = min(DETECTOR_LENGTH, lane_len)
                
                # Nome do detector
                edge_short = e.replace('#', '_').replace('-', 'm')[:20]
                det_id = f"det_{tls_id}_{edge_short}_{lane_id.split('_')[-1]}"
                
                lines.append(f'    <laneAreaDetector id="{det_id}" lane="{lane_id}" pos="{-det_len}" length="{det_len}" freq="5" file="../saida/detectores.xml"/>')
                det_count += 1
        
        if det_count > 0:
            selected.append(tl)
    
    lines.append('')
    lines.append('</additional>')
    
    with open(OUT_PATH, 'w', encoding='ascii') as f:
        f.write('\n'.join(lines) + '\n')
    
    print(f"Total TLS: {len(tls_list)}")
    print(f"Selected TLS: {len(selected)}")
    print(f"\nGenerated {sum(len(tl['incoming']) for tl in selected)} detectors in {OUT_PATH}")
    
    # Mostrar detalhes
    for tl in selected:
        edges = tl['incoming']
        print(f"\n  TLS {tl['id']}: incoming={len(edges)} pri={tl['pri']}/{tl['sec']} phases={tl['phases']}")
        for e in edges:
            if e in edge_info:
                info = edge_info[e]
                spd = info['speed'] * 3.6
                nlanes = len(info['lanes'])
                print(f"    Lane {e:30s} type={info['type']:25s} speed={spd:.0f} lanes={nlanes}")

if __name__ == '__main__':
    main()
