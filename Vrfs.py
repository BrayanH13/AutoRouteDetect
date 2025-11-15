    # ---------------------------------------------------------------
# Cisco VRF Route Reader
# Developed by: Brayan David Herrera Diaz
# Title: Electronics Engineer
# Contact: herreradiaz13@gmail.com
# Description: This script extracts VRF configurations from Cisco devices,
#              including VRF name, IP gateway, and route counts for OSPF, BGP, and RIP.
# ---------------------------------------------------------------

# ---------------------------------------------------------------
#AGREGARLE MULTIPROCESSING PARA CADA ROUTER DE COLOMBIA
# ---------------------------------------------------------------
from netmiko import ConnectHandler
import pandas as pd
import re
from collections import defaultdict
import requests
import json
import time
import threading

#Curacavi
rtcur01="10.255.242.147"
rtcur02="10.255.242.148"
#Ascenty
rtinet01="10.255.242.1"
rtinet02="10.255.242.2"
#Lurin RTCORE
lur_rtcore01 = "LUR-RTCORE-1"
lur_rtcore02 = "LUR-RTCORE-2"
lur_dist01="172.24.40.10"
lur_dist02="172.24.40.102"
#Distribution Lurin

#Equinix
dist01="172.25.5.4"
dist02="172.25.5.5"
#credenciales
user="brayan.herrera.apr"
password="Hispan0c2025***"
user_col="brayan.herrera"
password_col="Ice2307#"
secret="c0r3Q1ip"

#VRF Chile
ch_vrf=["PROJECT_801"
     ,"PROJECT_802"
     ,"PROJECT_803"
]
#VRF Colombia
col_vrf=["VLAN806"
     ,"VLAN807"
     ,"VLAN808"
]
#VRF Lurin
lur_rtcore_vrf=["PROJECT_581"
     ,"PROJECT_582"
     ,"PROJECT_583"
]
lur_vrf=["VLAN1560"
     ,"VLAN1561"
     ,"VLAN1562"
]
headers = {"Content-Type": "application/json"}
    # Lista de dispositivos Cisco
equipos = {
    "rtcur01": {
        "IP":rtcur01,
        "user":user,
        "password":password,
        "vrf":ch_vrf,
        "pattern_hub_sn2": [
            r'^O\s+10\.1\.56\.2/32',
        ],
        "pattern_sat_sn2": [
            r'O N2[^\n]*\n\s*\[.*\] via 10\.68\.\d+\.2',
            r'B[^\n]*\n\s*\[.*\] via 10\.68\.\d+\.2'
        ],
        "pattern_hub_sn4": [
            r'^O\s+10\.1\.56\.4/32'
        ],
        "pattern_sat_sn4": [
            r'O N2[^\n]*\n\s*\[.*\] via 10\.68\.\d+\.4',
            r'B[^\n]*\n\s*\[.*\] via 10\.68\.\d+\.4'
        ],
        "urls": [
            "http://172.20.1.161:5050/1EECE6E2-8239-46BF-AA2E-1F7001FA68A4?value=0",
        ]
    },
    "rtcur02": {
        "IP":rtcur02,
        "user":user,
        "password":password,
        "vrf":ch_vrf,
        "pattern_hub_sn2": [
            r'^O\s+10\.1\.56\.2/32',
        ],
        "pattern_sat_sn2": [
            r'^B\s+10\.234.*via\s+10\.53\.10\.3'
        ],
        "pattern_hub_sn4": [
            r'^O\s+10\.1\.56\.4/32'
        ],
        "pattern_sat_sn4": [
            r'^B\s+10\.234.*via\s+10\.53\.10\.3'
        ],
        "urls": [
            "http://172.20.1.161:5051/6EF9606C-3604-4A0E-A396-8B385C9ECA56?value=0",
        ]
    },
    "rtinet01": {
        "IP":rtinet01,
        "user":user,
        "password":password,
        "vrf": ch_vrf,
        "pattern_hub_sn2": [
            r'^B\s+10\.1\.56\.2/32',
        ],
        "pattern_sat_sn2": [
            r'^B\s+10\.234.*via\s+10\.53\.10\.3',
            r'^B\s+10\.234.*via\s+10\.53\.10\.3'
        ],
        "pattern_hub_sn4": [
            r'^B\s+10\.1\.56\.4/32'
        ],
        "pattern_sat_sn4": [
            r'^B\s+10\.234.*via\s+10\.53\.10\.3',
            r'^B\s+10\.234.*via\s+10\.53\.10\.3'
        ],
        "urls": ["http://172.20.1.161:5050/2A832CA9-B043-4ED4-A48E-552172C55C2B?value=0"]
    },
    "rtinet02": {
        "IP":rtinet02,
        "user":user,
        "password":password,
        "vrf": ch_vrf,
        "pattern_hub_sn2": [
            r'^B\s+10\.1\.56\.2/32',
        ],
        "pattern_sat_sn2": [
            r'^B\s+10\.234.*via\s+10\.53\.10\.3',
            r'^B\s+10\.234.*via\s+10\.53\.10\.3'
        ],
        "pattern_hub_sn4": [
            r'^B\s+10\.1\.56\.4/32'
        ],
        "pattern_sat_sn4": [
            r'^B\s+10\.234.*via\s+10\.53\.10\.3',
            r'^B\s+10\.234.*via\s+10\.53\.10\.3'
        ],
        "urls": ["http://172.20.1.161:5051/4D985BD6-394E-4E5A-8155-4048C4B1E93E?value=0"]
    },
    "lur_rtcore01": {
        "IP":lur_rtcore01,
        "user":user,
        "password":password,
        "vrf": lur_rtcore_vrf,
        "pattern_hub_sn2": [
            r'^C\s+10\.65\.83\.0/24',
        ],
        "pattern_sat_sn2": [
            r'^R\s+10\.234.*via\s+10\.65\.83\.2',
            r'^R\s+10\.234.*via\s+10\.65\.81\.2',
            r'^R\s+10\.234.*via\s+10\.65\.82\.2',
        ],
        "pattern_hub_sn4": [
        ],
        "pattern_sat_sn4": [
        ],
        "urls": ["http://172.20.1.161:5050/AAD9C9E0-27F0-47A1-BDF7-69EADD4BAC73?value=0"]
    },
    "lur_rtcore02": {
        "IP":lur_rtcore02,
        "user":user,
        "password":password,
        "vrf": lur_rtcore_vrf,
        "pattern_hub_sn2": [
            r'^C\s+10\.65\.81\.0/24',
        ],
        "pattern_sat_sn2": [
            r'^R\s+10\.234.*via\s+10\.65\.83\.2',
            r'^R\s+10\.234.*via\s+10\.65\.81\.2',
            r'^R\s+10\.234.*via\s+10\.65\.82\.2',
        ],
        "pattern_hub_sn4": [
        ],
        "pattern_sat_sn4": [
        ],
        "urls": ["http://172.20.1.161:5051/64185E0E-EAF7-4166-9574-B3975D5715E9?value=0"]
    },
    "lur_dist01": {
        "IP":lur_dist01,
        "user":user,
        "password":password,
        "vrf": lur_vrf,
        "pattern_hub_sn2": [
            r'^O\s+1\.1\.14\.1/24'
        ],
        "pattern_sat_sn2": [
            r'^O E2\s+10\.234.*via\s+10\.144\.146\.195',#SEIIc
            r'^B\s+10\.234.*via\s+10\.48\.163\.211',
            r'^B\s+10\.234.*via\s+10\.48\.163\.227'
        ],
        "pattern_hub_sn4": [
            r'^O\s+1\.1\.22\.4/24'
        ],
        "pattern_sat_sn4": [
            r'^O N2\s+10\.234.*via\s+10\.154\.146\.196', #Dialog,
            r'^O E2\s+10\.234.*via\s+10\.154\.146\.212',
            r'^O E2\s+10\.234.*via\s+10\.154\.146\.228'
        ],
        "urls": ["http://172.20.1.161:5050/6926A93D-1630-476C-BB0E-E87447F9D4CA?value=0"]
    },
    "lur_dist02": {
        "IP":lur_dist02,
        "user":user,
        "password":password,
        "vrf": lur_vrf,
        "pattern_hub_sn2": [
            r'^O IA\s+1\.1\.14\.1'
        ],
        "pattern_sat_sn2": [
            r'^B\s+10\.234.*via\s+10\.48\.163\.22',#SEIIc
            r'^B\s+10\.234.*via\s+10\.48\.163\.48',
            r'^B\s+10\.234.*via\s+10\.48\.163\.54'
        ],
        "pattern_hub_sn4": [
            r'^O IA\s+1\.1\.22\.4'
        ],
        "pattern_sat_sn4": [
            r'^O E2\s+10\.234.*via\s+10\.154\.146\.194',#Dialog
            r'^O E2\s+10\.234.*via\s+10\.154\.146\.210',
            r'^O E2\s+10\.234.*via\s+10\.154\.146\.226'
        ],
        "urls": ["http://172.20.1.161:5051/10A9CEF7-E155-4DDF-937E-91461877A366?value=0"]
    },
    "dist01": {
        "IP":dist01,
        "user":user_col,
        "password":password_col,
        "vrf": col_vrf,
        "pattern_hub_sn2": [
            r'^B\s+10\.1\.56\.2/32'
        ],
        "pattern_sat_sn2": [
            r'^B\s+10\.234.*via\s+10\.181\.0\.1',
            r'^B\s+10\.234.*via\s+10\.181\.1\.5',           
            r'^B\s+10\.234.*via\s+10\.181\.0\.9'
        ],
        "pattern_hub_sn4": [
            r'^B\s+10\.1\.56\.4/32'
        ],
        "pattern_sat_sn4": [
            r'^B\s+10\.234.*via\s+10\.181\.0\.1',
             r'^B\s+10\.234.*via\s+10\.181\.1\.5',           
            r'^B\s+10\.234.*via\s+10\.181\.0\.9'
        ],
        "urls": ["http://172.20.1.161:5050/5F65E346-9825-4715-BB6C-90F95E99F433?value=0"]
    },
    "dist02": {
        "IP":dist02,
        "user":user_col,
        "password":password_col,
        "vrf": col_vrf,
        "pattern_hub_sn2": [
            r'^B\s+10\.1\.56\.2/32'
        ],
        "pattern_sat_sn2": [
            r'^B\s+10\.234.*via\s+10\.181\.0\.1',
            r'^B\s+10\.234.*via\s+10\.181\.1\.5',           
            r'^B\s+10\.234.*via\s+10\.181\.1\.9'
        ],
        "pattern_hub_sn4": [
            r'^B\s+10\.1\.56\.4/32'
        ],
        "pattern_sat_sn4": [
            r'^B\s+10\.234.*via\s+10\.181\.0\.1',
            r'^B\s+10\.234.*via\s+10\.181\.1\.5',           
            r'^B\s+10\.234.*via\s+10\.181\.1\.9'
        ],
        "urls": ["http://172.20.1.161:5051/9C65F9FB-B8FF-4E41-8F11-A0A95123F933?value=0"]
    }
}


def conect(host,user,password,secret):
        # Datos del equipo
        cisco_device = {
        'device_type': 'cisco_ios',
        'host': host,
        'username': user,
        'password': password,
        'secret': secret,
        }

        # Conexión
        net_connect = ConnectHandler(**cisco_device)
        net_connect.enable()
        return net_connect

#FUNCIONES DE ANALISIS

def gateway_ip(text, vrf_name):
        # Captura el bloque que sigue a "Routing Table: {vrf_name}"
        pattern = re.finditer(rf'Routing Table: {(vrf_name)}\n(?:.*\n)*?Gateway of last resort is (\d+\.\d+\.\d+\.\d+) to',text)
        for match in pattern:
            gateway = match.group(1).strip()
        # Agrega solo el ID, no el diccionario completo
        if not match:
            return {
                "vrf": vrf_name,
                "gateway": "No encontrado",
                "total_routes": 0,
                "bgp_count": 0,
                "bgp_routes": []
            }


        return {
            "vrf": vrf_name,
            "gateway": gateway,
        }

def to_prtg(url_prtg, canales):

    payload_prtg = {
        "prtg": {
            "result": [
                {
                    "channel": nombre,
                    "value": valor,
                    "unit": "Rutas"
                } for nombre, valor in canales.items()
            ]
        }
    }

    try:
        response = requests.post(
            url_prtg,
            headers=headers,
            data=json.dumps(payload_prtg),
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al enviar datos a PRTG: {e}")

#SE BORRO EL URL PARA PRUEBAS ACORDARSE AGREGARLO
def procesar_equipo(equipo,user,password,vrf_list,pattern_hub_sn2,pattern_hub_sn4,pattern_sat_sn2,pattern_sat_sn4,urls):
    try:
        net_connect = conect(equipo,user,password,secret)
        text = ""
        canales_acumulados = {}
        for vrf in vrf_list:
            try:
                route_output = net_connect.send_command(f"show ip route vrf {vrf}")
                text += f"\nRutas de VRF {vrf}\n{route_output}\n"
            except:
                print(f"{equipo}: LA VRF NO ESTA CONFIGURADA{vrf}")
            try:
                routes = gateway_ip(text, vrf)
                gateway = routes.get("gateway", "No encontrado")
                print(f"Gateway: {gateway}")
            except:
                print("FALLO EN EL GATEWAY")
                continue
            
            if gateway == "No encontrado" or not gateway:
                print(f"⚠️ Sin gateway para VRF '{vrf}' en {equipo}")
                continue

            try:
                print(f"🔍 Entrando a total_rutas para VRF: {vrf} con gateway: {gateway}")

                # Buscar el bloque de rutas que sigue al gateway
                pattern = re.finditer(
                    rf'Routing Table: {(vrf)}\n.*?Gateway of last resort is {(gateway)} to.*?\n(.*?)(?=\nRouting Table:|\Z)',
                    text,
                    re.DOTALL
                )
                for match in pattern:
                    rutas_bloque = match.group(1).strip()
                    print(f"📦 Rutas encontradas para {vrf}:\n{rutas_bloque}")
                    osat_sn2 = 0
                    osat_sn4 = 0
                    o_hub_s2 = 0
                    o_hub_s4 = 0
                    osat_total=0
                    O_hub_sn2_total = 0
                    O_hub_sn4_total = 0
                    O_sat_sn2_total = 0
                    O_sat_sn4_total = 0
                    O_sat_total = 0
                    if equipo in (rtcur01, lur_dist01, lur_dist02):
                        osat_sn2 = len(re.findall(pattern_sat_sn2[0], rutas_bloque, re.MULTILINE))
                        osat_sn4 = len(re.findall(pattern_sat_sn4[0], rutas_bloque, re.MULTILINE))
                        o_hub_s2 = len(re.findall(pattern_hub_sn2[0], rutas_bloque, re.MULTILINE))
                        o_hub_s4 = len(re.findall(pattern_hub_sn4[0], rutas_bloque, re.MULTILINE))
                        for pat_sn2, pat_sn4 in zip(pattern_sat_sn2, pattern_sat_sn4):
                            if osat_sn2 == 0:
                                osat_sn2 = len(re.findall(pat_sn2, rutas_bloque, re.MULTILINE))
                            if osat_sn4 == 0:
                                osat_sn4 = len(re.findall(pat_sn4, rutas_bloque, re.MULTILINE))
                    else :
                        osat_total = len(re.findall(pattern_sat_sn2[0], rutas_bloque, re.MULTILINE))
                        o_hub_s2 = len(re.findall(pattern_hub_sn2[0], rutas_bloque, re.MULTILINE))
                        o_hub_s4 = len(re.findall(pattern_hub_sn4[0], rutas_bloque, re.MULTILINE))
                        for pat_sn2 in pattern_sat_sn2:
                            if osat_total == 0:
                                osat_total = len(re.findall(pat_sn2, rutas_bloque, re.MULTILINE))
                # Si no se encontró ningún bloque
                O_hub_sn2_total += o_hub_s2
                O_hub_sn4_total += o_hub_s4
                O_sat_sn2_total += osat_sn2
                O_sat_sn4_total += osat_sn4
                O_sat_total += osat_total
                if equipo in (rtcur01, lur_dist01, lur_dist02):
                    print(f"\n📊 Totales en {equipo} y la VRF {vrf}: HUB SN2 = {O_hub_sn2_total}, HUB SN4 = {O_hub_sn4_total},SAT SN2 = {O_sat_sn2_total},SAT SN4 = {O_sat_sn4_total}")
                else :
                    print(f"\n📊 Totales en {equipo} y la VRF {vrf}: HUB SN2 = {O_hub_sn2_total}, HUB SN4 = {O_hub_sn4_total},SAT TOTALES = {O_sat_total}")
            except Exception as e:
                print(f"Fallo la obtención de rutas: {e}")
            try:
                if equipo == rtcur01:
                    canales_acumulados.update({
                        f"HUB_SN2_RUTAS {vrf}": O_hub_sn2_total,
                        f"HUB_SN4_RUTAS {vrf}": O_hub_sn4_total,
                        f"SAT_SN2_RUTAS {vrf}": O_sat_sn2_total,
                        f"SAT_SN4_RUTAS {vrf}": O_sat_sn4_total,
                    })
                elif equipo in (lur_dist01, lur_dist02):
                    canales_acumulados.update({
                        f"HUB_SEIIc_RUTAS {vrf}": O_hub_sn2_total,
                        f"HUB_DIALOG_SN4_RUTAS {vrf}": O_hub_sn4_total,
                        f"SAT_SEIIc_RUTAS {vrf}": O_sat_sn2_total,
                        f"SAT_DIALOG_SN4_RUTAS {vrf}": O_sat_sn4_total,
                    })    
                elif equipo in (lur_rtcore01, lur_rtcore02):
                    canales_acumulados.update({
                        f"HUB_SEIIc_RUTAS {vrf}": O_hub_sn2_total,
                        f"SAT_SEIIc_RUTAS {vrf}": O_sat_sn2_total,
                    })                 
                else:
                    canales_acumulados.update({
                        f"HUB_SN2_RUTAS {vrf}": O_hub_sn2_total,
                        f"HUB_SN4_RUTAS {vrf}": O_hub_sn4_total,
                        f"RUTAS_SAT_TOTALES {vrf}": osat_total
                    })
            except Exception as e:
                print(f"Fallo la obtención de rutas: {e}")
            except Exception as e:
                    print(f"fallo al enviar datos : {e}")
        to_prtg(urls[0],canales_acumulados)
        net_connect.disconnect()

    except Exception as e:
        print(f"❌ Error en {equipo}: {e}")
while True:
    try:
        hilos = []
        for nombre_equipo, datos in equipos.items():
            hilo = threading.Thread(
                target=procesar_equipo,
                args=(
                    datos["IP"],
                    datos["user"],
                    datos["password"],
                    datos["vrf"],
                    datos["pattern_hub_sn2"],
                    datos["pattern_hub_sn4"],
                    datos["pattern_sat_sn2"],
                    datos["pattern_sat_sn4"],
                    datos["urls"]
                )
            )
            hilos.append(hilo)
            hilo.start()

        # Esperar a que todos los hilos terminen
        for hilo in hilos:
            hilo.join()
        time.sleep(30)
    except Exception as e:
        print("Fallo")
