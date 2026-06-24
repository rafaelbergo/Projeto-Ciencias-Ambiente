#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Geracao de viagens para o Cenario 3 usando randomTrips.py + duarouter."""
import subprocess, os, sys

NET_PATH = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario3\map\curitiba_centro.net.xml'
OUT_DIR = r'C:\Users\rafa1\Desktop\ciencias\Projeto-Ciencias-Ambiente\projeto_final\cenario3\map'
SUMO_HOME = r'C:\Program Files (x86)\Eclipse\Sumo'
TOOLS = os.path.join(SUMO_HOME, 'tools')

TOTAL_VPH = 14250
BEGIN = 60.0
END = 7200.0

COMP = {
    'passenger':  {'pct': 0.74, 'vph': int(TOTAL_VPH * 0.74)},
    'motorcycle': {'pct': 0.15, 'vph': int(TOTAL_VPH * 0.15)},
    'bus':        {'pct': 0.06, 'vph': int(TOTAL_VPH * 0.06)},
    'truck':      {'pct': 0.04, 'vph': int(TOTAL_VPH * 0.04)},
    'bike':       {'pct': 0.01, 'vph': int(TOTAL_VPH * 0.01)},
}
total_vph = sum(v['vph'] for v in COMP.values())
COMP['passenger']['vph'] += TOTAL_VPH - total_vph

def main():
    print("=== Geracao de Viagens - Cenario 3 ===")
    print(f"Demanda: {TOTAL_VPH} veh/h | Composicao: 74/15/6/4/1")
    print(f"Periodo: {BEGIN}s - {END}s")
    
    randomTrips = os.path.join(TOOLS, 'randomTrips.py')
    dua = os.path.join(SUMO_HOME, 'bin', 'duarouter.exe')
    
    # Juntar todas as trips num unico ficheiro
    all_trips = os.path.join(OUT_DIR, 'all_trips.xml')
    
    # Escrever cabecalho
    with open(all_trips, 'w', encoding='ascii') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<routes>\n')
    
    # Gerar trips para cada classe e concatenar
    for cls, cfg in COMP.items():
        period = 3600.0 / cfg['vph']
        print(f"\n  {cls}: {cfg['vph']} veh/h period={period:.2f}s")
        
        trips_file = os.path.join(OUT_DIR, f'trips_{cls}.xml')
        
        cmd = [
            sys.executable, randomTrips,
            '-n', NET_PATH,
            '-o', trips_file,
            '-b', str(BEGIN),
            '-e', str(END),
            '-p', str(period),
            '--trip-attributes', f'type="{cls}"',
            '--prefix', cls,
            '--validate'
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Extrair trips do ficheiro
        content = open(trips_file, 'r', encoding='ascii', errors='ignore').read()
        trips_lines = []
        for l in content.split('\n'):
            if '<trip' in l:
                trips_lines.append(l)
        
        # Adicionar ao ficheiro consolidado
        with open(all_trips, 'a', encoding='ascii') as f:
            for l in trips_lines:
                f.write('  ' + l.strip() + '\n')
    
    # Fechar routes
    with open(all_trips, 'a', encoding='ascii') as f:
        f.write('</routes>\n')
    
    # Router com duarouter
    print(f"\nExecutando duarouter...")
    rou_out = os.path.join(OUT_DIR, 'cenario3.rou.xml')
    subprocess.run([
        dua, '-n', NET_PATH, '-r', all_trips, '-o', rou_out,
        '--routing-threads', '4', '--ignore-errors', 'true', '--no-warnings', 'true'
    ], check=True)
    
    # Adicionar vTypes ao ficheiro final
    vtypes = '''  <vType id="passenger" vClass="passenger" accel="2.6" decel="4.5" sigma="0.5" length="4.5" minGap="2.5" maxSpeed="13.89" emissionClass="HBEFA3/PC_G_EU4" color="1,1,0"/>
  <vType id="motorcycle" vClass="motorcycle" accel="3.5" decel="5.0" sigma="0.7" length="2.2" minGap="1.0" maxSpeed="13.89" emissionClass="HBEFA3/LDV_G_EU4" color="0,0,1"/>
  <vType id="bus" vClass="bus" accel="1.2" decel="4.0" sigma="0.5" length="12.0" minGap="3.0" maxSpeed="11.11" emissionClass="HBEFA3/Bus" color="1,0,0"/>
  <vType id="truck" vClass="truck" accel="1.0" decel="3.5" sigma="0.6" length="8.0" minGap="3.0" maxSpeed="11.11" emissionClass="HBEFA3/HDV" color="0.5,0.5,0.5"/>
  <vType id="bike" vClass="bicycle" accel="1.2" decel="3.0" sigma="0.8" length="1.8" minGap="1.0" maxSpeed="6.94" color="0,1,0"/>
'''
    with open(rou_out, 'r', encoding='ascii') as f:
        content = f.read()
    # Inserir vTypes depois do primeiro <routes> (que pode ter atributos)
    idx = content.find('<routes')
    idx_end = content.find('>', idx) + 1
    content = content[:idx_end] + '\n' + vtypes + content[idx_end:]
    with open(rou_out, 'w', encoding='ascii') as f:
        f.write(content)
    
    print(f"Ficheiro final: {rou_out}")
    
    # Limpar temporarios
    for cls in COMP:
        f = os.path.join(OUT_DIR, f'trips_{cls}.xml')
        if os.path.exists(f): os.remove(f)
    if os.path.exists(all_trips): os.remove(all_trips)

if __name__ == '__main__':
    main()
