import socket, json, os, network, time, machine
from wifi import *
import app.cfg as cfg

def urldecode(s):
    s = s.replace('+', ' ')
    parts = s.split('%')
    if len(parts) == 1: return s
    
    res = parts[0].encode()
    for part in parts[1:]:
        try:
            # Convierte los 2 hex en un byte y añade el resto de la cadena
            res += bytes([int(part[:2], 16)]) + part[2:].encode()
        except:
            res += b'%' + part.encode()
    return res.decode('utf-8')


def load_web_server():
    global localip 
    config = cfg.carga_config()

    # --- Inicio ---
    try:
        localip = config.get("ip", "")
        connected, wlan = do_connect(config.get("ssid", ""), config.get("pass", ""), localip)
        print("ip",wlan.ifconfig()[0])
    except OSError:
        connected = False

    if not connected:
        create_access_point()
        localip = "192.168.4.1"
     

    # --- Servidor ---
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        try:
            request = conn.recv(4096).decode('utf-8')
            if "POST /" in request:
                body = request.split('\r\n\r\n')[1]
                params = {x.split('=')[0]: x.split('=')[1] for x in body.split('&') if '=' in x}
                
                with open('app/config.json', 'w') as f:
                    json.dump({'ssid': urldecode(params.get('ssid','')), 'pass': urldecode(params.get('pass','')), 'ip': urldecode(params.get('ip',''))}, f)
                
                with open('external_code.py', 'w',encoding="utf-8") as f:
                    f.write(urldecode(params.get('code', '')))
                
                conn.send('HTTP/1.1 200 OK\r\n\r\nOK. Reiniciando...')
                time.sleep(1)
                machine.reset()
            else:
                conf = {"ssid": "", "pass": "", "ip": ""}
                try:
                    with open('app/config.json', 'r') as f: conf.update(json.load(f))
                except: pass
                
                code = ""
                try:
                    with open('external_code.py', 'r') as f: code = f.read()
                except: pass

                html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{{font-family:sans-serif;padding:20px;}}input,textarea{{width:100%;margin:5px 0;padding:8px;box-sizing: border-box;}}textarea{{height:500px;}}</style></head>
                <body><h2>Configuración</h2><form method="POST">
                SSID:<input name="ssid" value="{conf['ssid']}">
                Pass:<input type="password" name="pass" value="{conf['pass']}">
                IP:<input name="ip" value="{conf['ip']}" placeholder="192.168.1.100">
                Código:<textarea name="code" spellcheck="false">{code}</textarea>
                <input type="submit" value="Guardar"></form></body></html>"""
                conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n' + html)
        except: pass
        finally: conn.close()

