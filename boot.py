import os

if 'pendant_mail.json' in os.listdir():
    from sendmail import *
    check_pendant_mail()
    
import asyncio
import random
import utime
from transport_serial import SerialTransport
from device import MeshtDevice
from external_code import *
from webserver import *
from manage_rules import *
import gc, os

dev = False



# --- FUNCIONES DE UTILIDAD ---
async def channel_list(device):
    print("\nLISTA DE CANALES:\n-----------------")
    if not device.channels:
        print("No hay canales registrados aún.")
    for c in device.channels:
        print(f"Canal {c.index}: {c.name} (Role: {c.role})")

async def node_list(device):
    print("\nLISTA DE NODOS:\n-----------------")
    if not device.nodes:
        print("No hay nodos registrados aún.")
    for n in device.nodes:
        print(f"Node {n.index}: {n.short_name} {n.long_name} (ID:{n.id} Num: {n.num})")

# --- TAREAS ASÍNCRONAS ---

async def background_listener(device):
    """Bucle infinito que procesa paquetes entrantes sin bloquear el programa."""
    print("Escucha activa en segundo plano...")
    while True:
        packet = await device.recv()
        if packet:
            # Si quieres ver el crudo para depurar, descomenta la siguiente línea:
            if dev: print(f"DEBUG: {packet}")
            
            p = packet.get("packet")
            if p and "decoded" in p:
                decoded = p["decoded"]
                payload = decoded.get("payload")#.lower()
                # Manejo de Mensajes de Texto (Port 1)
                if decoded.get("portnum") == 1:
                    await device.send_ack(p)
                    if p.get("channel") == 1: #canal de comandos
                        print("MENSAJE RECIBIDO EN EL CANAL PARA COMANDOS")
                        if b"/help" in payload:
                            await device.send_to_channel(1,f"/help\n/server\n/reset\n/rule_list\n/rule_show X\n/rule_del X\n/rule_add X content\n/rule_change X content")
                            
                        if b"/server" in payload:
                            await device.send_to_channel(1,f"Web server running.\nAfter changes node will restart in normal mode.")
                            load_web_server()
                            
                        if b"/rule" in payload:
                            resp = procesar_comando(payload.decode('utf-8', 'ignore'))
                            await device.send_to_channel(1,resp)
                    else:
                        gc.collect()
                        try:
                            await rules(device,p,p.get("channel"),payload.decode('utf-8', 'ignore'))
                        except Exception as e:
                            await device.send_to_channel(p.get("channel"),f"Error executing this rule")
                            await asyncio.sleep(5)
                            await device.send_to_channel(p.get("channel"),f"{e}")
                            
                        '''
                        try:
                            texto = decoded.get("payload").decode()
                            emisor = p_interna.get("from")
                            print(f"\n📩 MENSAJE RECIBIDO de {emisor}: {texto}")
                            # Auto-responder con ACK
                            await device.send_ack(p_interna)
                        except Exception as e:
                            print(f"Error decodificando texto: {e}")
                        '''
        
        await asyncio.sleep_ms(10)

async def send_random_telemetry(device):
    """Ejemplo de envío de telemetría sin reiniciar UART."""
    print("📤 Enviando telemetría...")
    await device.send_telemetry(
        temperature=round(random.uniform(20.0, 30.0), 1),
        voltage=round(random.uniform(3.7, 4.2), 2),
        relative_humidity=round(random.uniform(30.0, 60.0), 1)
    )

# --- FLUJO PRINCIPAL ---

async def main():
    # 1. Configuración de transporte
    transport = SerialTransport(uart_id=1, baudrate=115200, tx_pin=9, rx_pin=10)
    device = MeshtDevice(transport)
    
    # 2. Inicio de comunicación (UNA SOLA VEZ)
    await device.start()
    
    # 3. Lanzar el listener en segundo plano
    asyncio.create_task(background_listener(device))
    
    # 4. Sincronización inicial (Despertar al nodo)
    print("Sincronizando configuración...")
    await device.request_config()
    
    # Esperamos un poco a que lleguen los primeros paquetes de config/nodos
    await asyncio.sleep(2)
    
    # 5. Mostrar estado inicial
    await channel_list(device)
    await node_list(device)
    
    # --- EJEMPLO DE BUCLE DE OPERACIÓN ---
    print("\nSistema listo. Presiona Ctrl+C para salir.")
    
    try:
        count = 0
        while True:
            await asyncio.sleep(10)
            continue
            count += 1
            # Cada 30 segundos enviamos un latido al canal 0
            if count % 3 == 0: 
                await device.send_to_channel(1, f"Keep-alive #{count}")
            
            # Cada 60 segundos enviamos telemetría
            if count % 6 == 0:
                await send_random_telemetry(device)
                
            await asyncio.sleep(10) 
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        device.close()

if __name__ == "__main__":
    asyncio.run(main())

