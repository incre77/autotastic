import utime
import urandom
import pb
import asyncio

DATA_SCHEMA = [
    ("varint", "portnum", 1),
    ("bytes", "payload", 2),
    ("bool", "want_response", 3),
    ("fixed32", "dest", 4),
    ("fixed32", "source", 5),
    ("fixed32", "request_id", 6),
    ("fixed32", "reply_id", 7),
    ("fixed32", "emoji", 8),
    ("uint32", "bitfield", 9),
]

MESHPACKET_SCHEMA = [
    ("fixed32", "from", 1),
    ("fixed32", "to", 2),
    ("uint32", "channel", 3),
    ("oneof", "payload_variant", [
        (DATA_SCHEMA, "decoded", 4),
        ("bytes", "encrypted", 5),
    ]),
    ("fixed32", "id", 6),
    ("fixed32", "rx_time", 7),
    ("float", "rx_snr", 8),
    ("uint32", "hop_limit", 9),
    ("bool", "want_ack", 10),
    ("int32", "priority", 11),
    ("int32", "rx_rssi", 12),
    ("bool", "via_mqtt", 14),
    ("uint32", "hop_start", 15),
    ("bytes", "public_key", 16),
    ("bool", "pki_encrypted", 17),
    ("uint32", "next_hop", 18),
    ("uint32", "relay_node", 19),
    ("uint32", "tx_after", 20),
]

CHANNEL_SETTINGS_SCHEMA = [
    ("uint32", "channel_num", 1),
    ("string", "name", 3),
]

CHANNEL_SCHEMA = [
    ("int32", "index", 1),
    (CHANNEL_SETTINGS_SCHEMA, "settings", 2),
    ("int32", "role", 3),
]

USER_SCHEMA = [
    ("string", "id", 1),
    ("string", "long_name", 2),
    ("string", "short_name", 3),
    ("int32", "hw_model", 5),
    ("bool", "is_licensed", 6),
    ("int32", "role", 7),
    ("bytes", "public_key", 8),
]

ENVIRONMENTMETRICS_SCHEMA = [
    ("float", "temperature", 1),
    ("float", "relative_humidity", 2),
    ("float", "barometric_pressure", 3),
    ("float", "gas_resistance", 4),
    ("float", "voltage", 5),
    ("float", "current", 6),
    ("uint32", "iaq", 7),
    ("float", "distance", 8),
    ("float", "lux", 9),
    ("float", "white_lux", 10),
    ("float", "ir_lux", 11),
    ("float", "uv_lux", 12),
    ("uint32", "wind_direction", 13),
    ("float", "wind_speed", 14),
    ("float", "weight", 15),
    ("float", "wind_gust", 16),
    ("float", "wind_lull", 17),
    ("float", "radiation", 18),
    ("float", "rainfall_1h", 19),
    ("float", "rainfall_24h", 20),
    ("uint32", "soil_moisture", 21),
    ("float", "soil_temperature", 22)
]

DEVICEMETRICS_SCHEMA = [
    ("uint32", "battery_level", 1),
    ("float", "voltage", 2),
]

TELEMETRY_SCHEMA = [
    ("fixed32", "time", 1),
    ("oneof", "variant", [
        (DEVICEMETRICS_SCHEMA, "device_metrics", 2),
        (ENVIRONMENTMETRICS_SCHEMA, "environment_metrics", 3),
    ]),
]

MYNODEINFO_SCHEMA = [
    ("uint32", "my_node_num", 1),
]

NODEINFO_SCHEMA = [
    ("uint32", "num", 1),
    (USER_SCHEMA, "user", 2),
    ("float", "snr", 4),
    ("fixed32", "last_heard", 5),
    (DEVICEMETRICS_SCHEMA, "device_metrics", 6),
    ("uint32", "hops_away", 9),
]

LORACONFIG_SCHEMA = [
    ("bool", "use_preset", 1),
    ("int32", "modem_preset", 2),
    ("int32", "region", 7),
]

CONFIG_SCHEMA = [
    ("oneof", "variant", [
        (LORACONFIG_SCHEMA, "lora", 6),
    ]),
]

FROMRADIO_SCHEMA = [
    ("uint32", "id", 1),
    ("oneof", "payload_variant", [
        (MESHPACKET_SCHEMA, "packet", 2),
        (MYNODEINFO_SCHEMA, "my_info", 3),
        (NODEINFO_SCHEMA, "node_info", 4),
        (CONFIG_SCHEMA, "config", 5),
        ("uint32", "config_complete_id", 7),
        (CHANNEL_SCHEMA, "channel", 10),
    ]),
]

TORADIO_SCHEMA = [
    (MESHPACKET_SCHEMA, "packet", 1),
    ("uint32", "want_config_id", 3),
    (NODEINFO_SCHEMA, "node_info", 4),
]

PORTNUMS = {
    0: "UNKNOWN_APP",
    1: "TEXT_MESSAGE_APP",
    2: "REMOTE_HARDWARE_APP",
    3: "POSITION_APP",
    4: "NODEINFO_APP",
    5: "ROUTING_APP",
    6: "ADMIN_APP",
    7: "TEXT_MESSAGE_COMPRESSED_APP",
    8: "WAYPOINT_APP",
    9: "AUDIO_APP",
    10: "DETECTION_SENSOR_APP",
    11: "ALERT_APP",
    32: "REPLY_APP",
    33: "IP_TUNNEL_APP",
    34: "PAXCOUNTER_APP",
    64: "SERIAL_APP",
    65: "STORE_FORWARD_APP",
    66: "RANGE_TEST_APP",
    67: "TELEMETRY_APP",
    68: "ZPS_APP",
    69: "SIMULATOR_APP",
    70: "TRACEROUTE_APP",
    71: "NEIGHBORINFO_APP",
    72: "ATAK_PLUGIN",
    73: "MAP_REPORT_APP",
    74: "POWERSTRESS_APP",
    76: "RETICULUM_TUNNEL_APP",
    256: "PRIVATE_APP",
    257: "ATAK_FORWARDER",
    511: "MAX",
}
NAMES_TO_PORTNUMS = {v: k for k, v in PORTNUMS.items()}


class Channel:
    def __init__(self, index, name, role):
        self.index = int(index)
        self.name = name
        self.role = int(role or 0)

class Node:
    def __init__(self, index, short_name, long_name, num, idx):
        self.index = int(index)
        self.short_name = short_name
        self.long_name = long_name
        self.num = num
        self.id = idx
    

class MeshtDevice:
    def __init__(self, transport):
        self.transport = transport
        self.channels = []
        self.nodes = []

    def _send_framed(self, data):
        """Añade la cabecera 0x94 0xC3 requerida por Meshtastic."""
        length = len(data)
        header = bytes([0x94, 0xC3, (length >> 8) & 0xFF, length & 0xFF])
        return header + data

    async def start(self):
        """Inicia transporte y solicita la lista de canales."""
        await self.transport.start()

    async def recv(self):
        """Recibe, desenmarca y decodifica paquetes de la radio."""
        raw = await self.transport.recv()
        if not raw or len(raw) < 4:
            return None

        # Verificar cabecera 0x94 0xC3
        if raw[0] == 0x94 and raw[1] == 0xC3:
            length = (raw[2] << 8) | raw[3]
            data = raw[4:4+length]
        else:
            data = raw

        try:
            fr = pb.decode(data, FROMRADIO_SCHEMA)
            if fr:
                self._maybe_store_channel(fr)
                self._maybe_store_my_node(fr)
                self._maybe_store_node(fr)
                
            return fr
        except:
            return None
        
    def _maybe_store_node(self, from_radio):
        ni = from_radio.get("node_info")
        if not ni: return
        
        num = ni.get("num", 0)
        user = ni.get("user", {})
        # Cambiamos 0 por strings por defecto
        idx= user.get("id", "???")
        sn = user.get("short_name", "???")
        ln = user.get("long_name", "Desconocido")
        
        self.nodes = [n for n in self.nodes if n.num != num]
        new_node = Node(len(self.nodes), sn, ln, num,idx)
        self.nodes.append(new_node)
        
        #print(f"✅ Nodo: {ln} ({sn}) registrado.")
        
    def _maybe_store_channel(self, from_radio):
        """Extrae y guarda la información de canales recibida."""
        ch = from_radio.get("channel")
        if not ch: return
        
        idx = ch.get("index", 0)
        settings = ch.get("settings", {})
        name = settings.get("name", f"CH_{idx}")
        role = ch.get("role", 0)

        # Actualizar lista local (evitar duplicados)
        self.channels = [c for c in self.channels if c.index != idx]
        if role != 0: # 0 = Canal deshabilitado
            self.channels.append(Channel(idx, name, role))
            self.channels.sort(key=lambda x: x.index)
            #print(f"✅ Canal detectado: {name} (Index: {idx})")
    
    def _maybe_store_my_node(self, from_radio):
        mi = from_radio.get("my_info")
        if not mi: return
        self.my_node_num = mi.get("my_node_num", 0)
        print(f"Numero de nodo:{self.my_node_num}")
        #self.my_node_id = f"{my_node_num & 0xFFFFFFFF:08x}"
        
    def close(self):
        self.transport.close()
        

    async def send_telemetry(self,
                            temperature=None,
                            relative_humidity=None,
                            barometric_pressure=None,
                            gas_resistance=None,
                            voltage=None,
                            current=None,
                            iaq=None,
                            distance=None,
                            lux=None,
                            white_lux=None,
                            ir_lux=None,
                            uv_lux=None,
                            wind_direction=None,
                            wind_speed=None,
                            weight=None,
                            wind_gust=None,
                            wind_lull=None,
                            radiation=None,
                            rainfall_1h=None,
                            rainfall_24h=None,
                            soil_moisture=None,
                            soil_temperature=None):

        telemetry_data = {}

        if temperature is not None:
            telemetry_data["temperature"] = float(temperature)
        if relative_humidity is not None:
            telemetry_data["relative_humidity"] = float(relative_humidity)
        if barometric_pressure is not None:
            telemetry_data["barometric_pressure"] = float(barometric_pressure)
        if gas_resistance is not None:
            telemetry_data["gas_resistance"] = float(gas_resistance)
        if voltage is not None:
            telemetry_data["voltage"] = float(voltage)
        if current is not None:
            telemetry_data["current"] = float(current)
        if iaq is not None:
            telemetry_data["iaq"] = int(iaq)
        if distance is not None:
            telemetry_data["distance"] = float(distance)
        if lux is not None:
            telemetry_data["lux"] = float(lux)
        if white_lux is not None:
            telemetry_data["white_lux"] = float(white_lux)
        if ir_lux is not None:
            telemetry_data["ir_lux"] = float(ir_lux)
        if uv_lux is not None:
            telemetry_data["uv_lux"] = float(uv_lux)
        if wind_direction is not None:
            telemetry_data["wind_direction"] = int(wind_direction)
        if wind_speed is not None:
            telemetry_data["wind_speed"] = float(wind_speed)
        if weight is not None:
            telemetry_data["weight"] = float(weight)
        if wind_gust is not None:
            telemetry_data["wind_gust"] = float(wind_gust)
        if wind_lull is not None:
            telemetry_data["wind_lull"] = float(wind_lull)
        if radiation is not None:
            telemetry_data["radiation"] = float(radiation)
        if rainfall_1h is not None:
            telemetry_data["rainfall_1h"] = float(rainfall_1h)
        if rainfall_24h is not None:
            telemetry_data["rainfall_24h"] = float(rainfall_24h)
        if soil_moisture is not None:
            telemetry_data["soil_moisture"] = int(soil_moisture)
        if soil_temperature is not None:
            telemetry_data["soil_temperature"] = float(soil_temperature)

        telemetry_wrapper = {
            "time": int(utime.time()),
            "environment_metrics": telemetry_data
        }

        encoded_payload = pb.encode(telemetry_wrapper, TELEMETRY_SCHEMA)

        data = {
            "portnum": NAMES_TO_PORTNUMS["TELEMETRY_APP"],
            "payload": encoded_payload,
            "want_response": False,
        }
        meshpacket = {
            "id": urandom.getrandbits(31),
            "to": 0xFFFFFFFF,
            "channel": 0,
            "decoded": data,
        }

        payload = pb.encode({"packet": meshpacket}, TORADIO_SCHEMA)
        framed_payload = self._send_framed(payload)

        await self.transport.send(framed_payload)
        return meshpacket
        
    async def request_config(self):
        """Solicita la configuración y canales al nodo."""
        request_id = urandom.getrandbits(28) + 1
        #request_id = 1
        payload = pb.encode({"want_config_id": request_id}, TORADIO_SCHEMA)
        framed_payload = self._send_framed(payload)
        print(f"\nPidiendo info (Request id: {request_id})...")
        await self.transport.send(framed_payload)
        return request_id

    def get_channel_info(self, name):
        # self.channels contiene objetos de la clase Channel
        for ch in self.channels:
            if ch.name == name:
                return {
                    "index": ch.index,
                    "name": ch.name,
                    "role": ch.role,
                    "role_name": "PRIMARY" if ch.role == 1 else "SECONDARY"
                }
        return None
        
    async def send_ack_old(self, p_interna, my_node_num):
        mesh_packet = {
            "id": urandom.getrandbits(31),
            "from": my_node_num,
            "to": p_interna["from"],
            "channel": p_interna.get("channel", 0),
            "priority": 70, # Prioridad de ACK
            "decoded": {
                "portnum": 32,
                "payload": b"",
                "reply_id": p_interna["id"],
                "dest": p_interna["from"],    # Añadimos destino explícito
                "source": my_node_num    # Añadimos origen explícito
            }
        }

        to_radio = {"packet": mesh_packet}
        payload = pb.encode(to_radio, TORADIO_SCHEMA)
        await self.transport.send(self._send_framed(payload))
                
    async def send_to_channel(self,num,texto):
        DEST_BROADCAST = 0xFFFFFFFF
        randomid = urandom.getrandbits(31)
        mensaje_packet = {
            "from": self.my_node_num,      # Campo 1
            "to": DEST_BROADCAST,     # Campo 2
            "channel": num,             # Campo 3
            "decoded": {              # Campo 4 (dentro de payload_variant)
                "portnum": 1, 
                "payload": texto.encode('utf-8')
            },
            "id": randomid, # Campo 6
            #"hop_limit": 3,                # Campo 9
            "want_ack": True,              # Campo 10
            "priority": 120,               # Campo 11
        }

        to_radio = {"packet": mensaje_packet}
        #print(f"📤 Enviando al canal {num}: {texto} con el id:{self.my_node_num} con el id {randomid}")
        
        try:
            payload = pb.encode(to_radio, TORADIO_SCHEMA)
            print(payload)
            await self.transport.send(self._send_framed(payload))
        except Exception as e:
            print(f"❌ Error al codificar: {e}")
            
            print(f"📤 Enviando al canal 1: {texto} (ID: {mensaje_packet['id']})")
            
            # Codificación y envío
            payload = pb.encode(to_radio, TORADIO_SCHEMA)
            await device.transport.send(self._send_framed(payload))

    

    async def send_to_node(self, node_num, text):
        """Envía un mensaje privado a un nodo específico usando su ID (num)."""
        randomid = urandom.getrandbits(31)
        mensaje_packet = {
            "from": self.my_node_num,
            "to": node_num,           # ID del nodo destino (ej: 34567890)
            #"channel": int(channel_index),
            "decoded": {
                "portnum": 1,         # TEXT_MESSAGE_APP
                "payload": text.encode('utf-8'),
                "want_response": True # Recomendado para DMs
            },
            "id": randomid,
            #"hop_limit": 3,
            "want_ack": True,         # Para saber si llegó
            "priority": 120,
        }

        to_radio = {"packet": mensaje_packet}
        
        print(f"Enviando DM a {node_num}: {text} con el id {randomid}")
        
        payload = pb.encode(to_radio, TORADIO_SCHEMA)
        await self.transport.send(self._send_framed(payload))
        return mensaje_packet["id"]
            
            
    async def send_ack(device, p_recibido):
        id_original = p_recibido.get("id")
        canal = p_recibido.get("channel", 1) # Usamos 1 según tu ejemplo
        rtt = p_recibido.get("from")

        mensaje_packet = {
            "channel": canal,
            "from": rtt,
            "to": rtt,
            "decoded": {
                "request_id": id_original, # Campo 6 del DATA_SCHEMA
                "portnum": 5,              # ADMIN_APP
                "payload": b"\x18\x00"
            },
            "id": urandom.getrandbits(31),
            "priority": 120
        }

        to_radio = {"packet": mensaje_packet}
        
        print(f"📦 Enviando paquete espejo (Port 5, ReqID: {id_original})")
        
        try:
            payload = pb.encode(to_radio, TORADIO_SCHEMA)
            await device.transport.send(device._send_framed(payload))
        except Exception as e:
            print(f"❌ Error: {e}")
