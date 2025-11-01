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

dist01="172.25.5.4"
dist02="172.25.5.5"
dmvpn1="172.24.4.194"
dmvpn2="172.24.4.195"
user="brayan.herrera"
password="Ice2307#"
urls=["http://172.20.1.161:5056/BF8645B8-B4FE-45E7-853F-C1F0FDFBE629?value=0"
          ,"http://172.20.1.161:5057/F074AF82-8F04-4B4D-AF37-746275DD0C1B?value=0"
          ,"http://172.20.1.161:5058/0F75321D-3DBC-4331-ABDA-E2E0535C97CF?value=0"
          ,"http://172.20.1.161:5059/A7184501-1031-4D74-B898-67ACCF4099E9?value=0"]
headers = {"Content-Type": "application/json"}
    # Lista de dispositivos Cisco
equipos = [
        dist01,
        dist02,
        dmvpn1,
        dmvpn2
        # Agrega más equipos aquí
    ]
    #FUNCION DE CONEXION

def conect(host,user,password):
        # Datos del equipo
        cisco_device = {
        'device_type': 'cisco_ios',
        'host': host,
        'username': user,
        'password': password,
        #    'secret': 'tu_enable_secret',
        }

        # Conexión
        net_connect = ConnectHandler(**cisco_device)
        net_connect.enable()
        return net_connect

#FUNCIONES DE ANALISIS

def vrfs(archive):
        vrf = defaultdict(list)
        pattern = re.finditer(r'Routing Table:\s*([^\n]+)', archive)
        for match in pattern:
            vrf_id = match.group(1).strip()
            vrf["VRFs"].append(vrf_id)  # Agrega solo el ID, no el diccionario completo

        # Convertir a DataFrame
        vrf_df = pd.DataFrame(vrf)
        print(f"Las VRFs encontradas en la tabla de enrutamiento son:\n{vrf_df}")
        return vrf_df

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
            #"total_routes": total_routes,
            #"bgp_count": bgp_count,
            #"bgp_routes": bgp_routes
        }

def total_rutas(text, vrf_name, gateway_value):
        print(f"🔍 Entrando a total_rutas para VRF: {vrf_name} con gateway: {gateway_value}")

        # Buscar el bloque de rutas que sigue al gateway
        pattern = re.finditer(
            rf'Routing Table: {(vrf_name)}\n.*?Gateway of last resort is {(gateway_value)} to.*?\n(.*?)(?=\nRouting Table:|\Z)',
            text,
            re.DOTALL
        )

        for match in pattern:
            rutas_bloque = match.group(1).strip()
            print(f"📦 Rutas encontradas para {vrf_name}:\n{rutas_bloque}")

            # Contar rutas que comienzan con B, O o R (permitiendo variantes como B*, O IA, R>)
            b_count = len(re.findall(r'^\s*B\S*', rutas_bloque, re.MULTILINE))
            o_count = len(re.findall(r'^\s*O\S*', rutas_bloque, re.MULTILINE))
            r_count = len(re.findall(r'^\s*R\S*', rutas_bloque, re.MULTILINE))

            return {
                "O_count": o_count,
                "B_count": b_count,
                "R_count": r_count
            }

        # Si no se encontró ningún bloque
        print(f"⚠️ No se encontró bloque de rutas para VRF '{vrf_name}' con gateway '{gateway_value}'")
        return {
            "O_count": 0,
            "B_count": 0,
            "R_count": 0
        }

    #FUNCION DE ENVIO A PRTG 

def to_prtg(url_prtg,OSPF,RIP,BGP):    
        # Construir payload con canales separados
        payload_prtg = {
            "prtg": {
            "result": [
            {
                "channel": "OSPF",
                "value": OSPF,
                "unit": "Rutas"
            },
            {
                "channel": "RIP",
                "value": RIP,
                "unit": "Rutas"
            },
            {
                "channel": "BGP",
                "value": BGP,
                "unit": "Rutas"
            }
                        ]
                    }
                }
        try:
            requests.post(
                    url_prtg,
                    headers=headers,
                    data=json.dumps(payload_prtg),
                    timeout=10
                    )
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al enviar datos a PRTG: {e}")

def procesar_equipo(equipo,url,user,password):
    try:
        net_connect = conect(equipo,user, password)
        output = net_connect.send_command("show vrf")
        vrf_list = [line.split()[0] for line in output.splitlines() if line and not line.startswith(('Name', '---'))]
        print(f"\n=== VRFs en {equipo} ===")
        print(output)

        text = "VRF's y sus rutas:\n"
        for vrf in vrf_list:
            try:
                route_output = net_connect.send_command(f"show ip route vrf {vrf}")
                text += f"\nRutas de VRF {vrf}\n{route_output}\n"
            except:
                print(f"⚠️ {equipo}: No tiene contenido o no es VLAN: {vrf}")

        vrf_df = vrfs(text)
        O_total = R_total = B_total = 0

        for _, vlan in vrf_df.iterrows():
            vrf_raw = vlan["VRFs"]
            vrf_name = vrf_raw.replace("VRFs ", "").strip()
            print(f"\n🔍 {equipo} → VRF: {vrf_name}")

            try:
                routes = gateway_ip(text, vrf_name)
                gateway = routes.get("gateway", "No encontrado")
                print(f"Gateway: {gateway}")
            except:
                print("FALLO EN EL GATEWAY")
                continue

            if gateway == "No encontrado" or not gateway:
                print(f"⚠️ Sin gateway para VRF '{vrf_name}' en {equipo}")
                continue

            try:
                resultado = total_rutas(text, vrf_name, gateway)
                if resultado:
                    O_total += resultado.get("O_count", 0)
                    B_total += resultado.get("B_count", 0)
                    R_total += resultado.get("R_count", 0)
                    print(f"Rutas OSPF: {resultado.get('O_count', 0)}")
                    print(f"Rutas BGP: {resultado.get('B_count', 0)}")
                    print(f"Rutas RIP: {resultado.get('R_count', 0)}")
                else:
                    print(f"⚠️ Sin rutas para VRF '{vrf_name}' en {equipo}")
            except:
                print("Fallo la obtención de rutas")
        to_prtg(url,O_total,R_total,B_total)
        print(f"\n📊 Totales en {equipo}: OSPF={O_total}, BGP={B_total}, RIP={R_total}")
        net_connect.disconnect()

    except Exception as e:
        print(f"❌ Error en {equipo}: {e}")

while True:
    try:
        hilos = []
        for equipo,url in zip(equipos,urls):
            hilo = threading.Thread(target=procesar_equipo, args=(equipo,url,user,password))
            hilos.append(hilo)
            hilo.start()

        for hilo in hilos:
            hilo.join()

        time.sleep(30)
    except Exception as e:
        print("Fallo")

