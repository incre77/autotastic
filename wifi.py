import network, time
import app.cfg as cfg

def create_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(False) # Reset de estado
    ap.active(True)
    ap.config(essid="AUTOTASTIC_192_168_4_1", password="")
    print(f"Modo AP: 192.168.4.1")

def do_connect(ssid, pwd, static_ip=""):
    global localip
    sta_if = network.WLAN(network.STA_IF)
    
    # Limpieza profunda para evitar 'Internal State Error'
    if sta_if.active():
        sta_if.active(False)
    time.sleep_ms(100)
    sta_if.active(True)

    if static_ip and len(static_ip) > 7:
        try:
            gw = ".".join(static_ip.split('.')[:-1]) + ".1"
            sta_if.ifconfig((static_ip, '255.255.255.0', gw, '8.8.8.8'))
        except: pass

    if not ssid: return False, sta_if

    print(f"Conectando a {ssid}...")
    sta_if.connect(ssid, pwd)
    
    for t in range(40):
        if sta_if.isconnected():
            localip = sta_if.ifconfig()[0]
            return True, sta_if
        time.sleep_ms(200)
    
    return False, sta_if

def wifi_connect():
    config = cfg.carga_config()
    do_connect(config.get("ssid", ""), config.get("pass", ""), config.get("ip", ""))