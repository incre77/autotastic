import ujson as json
import os
# Carga de Configuración (global)

def carga_config():
    try:
        with open("app/config.json", 'r') as config_file:
            config = json.loads(config_file.read())
    except OSError:
        print("Config file not found or error reading. Using default config.")
        config = {"wifi": {"ssid": "", "pwd": ""},"fastboot": false, "lastrom":""} # Configuración por defecto
    return config

def guarda_config(config):
    """Guarda el objeto de configuración global en app/config.json."""
    try:
        os.mkdir('app')
    except OSError:
        pass
    try:
        with open('app/config.json', 'w') as f:
            f.write(json.dumps(config))
        print("Configuración guardada.")
    except Exception as e:
        print(f"Error al guardar config: {e}")
    return
    
