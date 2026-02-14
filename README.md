# autotastic
Meshtastic MicroPython Controller 🛰️
# Meshtastic MicroPython Controller 🛰️

Framework ligero basado en **MicroPython** para interactuar con dispositivos **Meshtastic** vía Serial (UART). Permite automatizar respuestas, enviar telemetría, gestionar el nodo desde la web y ejecutar reglas personalizadas.



## 🚀 Características principales

* **Protocolo Nativo:** Codificación y decodificación Protobuf para Meshtastic.
* **Motor de Reglas Dinámico:** Sistema para modificar `external_code.py` en tiempo real mediante comandos de chat.
* **Servidor Web:** Interfaz para configurar Wi-Fi y editar el código de reglas desde el navegador.
* **Gestión de Correo:** Envío SMTP con persistencia post-reinicio para optimizar el uso de RAM.
* **Asíncrono:** Basado en `uasyncio` para multitarea sin bloqueos.

---

## 📂 Estructura del Proyecto

| Archivo | Función |
| :--- | :--- |
| **boot.py** | Punto de entrada. Inicializa hardware, listener y servidor web. |
| **device.py** | Núcleo de lógica Meshtastic y esquemas de datos. |
| **transport_serial.py** | Manejo de bajo nivel de la comunicación UART. |
| **pb.py** | Librería Protobuf optimizada para MicroPython. |
| **webserver.py** | Servidor HTTP de configuración y edición remota. |
| **manage_rules.py** | Lógica para procesar comandos `/rule_...`. |
| **external_code.py** | Almacén de reglas dinámicas ejecutables. |
| **sendmail.py** | Cliente SMTP para notificaciones externas. |

---

## 🛠️ Instalación y Configuración

### 1. Conexión Hardware
Conecta tu dispositivo MicroPython al nodo Meshtastic:
* **TX (MicroPython)** -> **RX (Meshtastic)**
* **RX (MicroPython)** -> **TX (Meshtastic)**
* Baudrate: `115200`

### 2. Configuración Wi-Fi
Si no hay Wi-Fi configurado, el dispositivo entra en modo AP:
* **SSID:** `AUTOTASTIC_192_168_4_1`
* **Acceso:** Navega a `http://192.168.4.1` para configurar el SSID y Password finales.

---

## 💬 Comandos de Control (vía Chat)

Puedes gestionar el dispositivo enviando mensajes desde cualquier nodo de la red:

## 💬 Interacciones desde el Chat 

El dispositivo monitoriza el tráfico de la red, pero por seguridad y organización, **los comandos de administración solo se procesan si se envían a través del Canal 1**.

### 1. Comandos de Sistema
| Comando | Acción |
| :--- | :--- |
| `/help` | Muestra la lista de comandos disponibles y ayuda rápida. |
| `/server` | Devuelve la **IP actual** (Local o AP) para acceder a la configuración web. |

### 2. Gestión de Reglas Dinámicas
Permiten editar el comportamiento del dispositivo sin necesidad de cables:

| Comando | Parámetros | Descripción |
| :--- | :--- | :--- |
| `/rule_list` | (ninguno) | Lista los nombres de todas las reglas guardadas. |
| `/rule_add` | `NOMBRE CODIGO` | Añade una regla. El código se indenta automáticamente. |
| `/rule_change` | `NOMBRE CODIGO` | Actualiza el código de una regla existente. |
| `/rule_delete` | `NOMBRE` | Borra la regla del sistema. |

> **Ejemplo:** `/rule_add alerta if 'auxilio' in txt: print('Alerta detectada')`
> Vea el contenido de external_code.py que ya dispone de varios ejemplos de reglas.

---

## 📧 Envío de Email (RAM Inteligente)

Para evitar errores de memoria (MemoryError), el módulo `sendmail.py`:
1. Guarda los datos en `pendant_mail.json`.
2. Ejecuta un `machine.reset()`.
3. Al arrancar, `boot.py` detecta el correo, lo envía con la RAM limpia y continúa con el flujo normal.

---

## 🛡️ Licencia

Este proyecto está bajo una licencia de **Uso No Comercial**. 

* **No Comercial:** No se permite el uso de este software con fines lucrativos.
* **Atribución:** Si utilizas o modificas este código, debes citar al autor original y vincular a este repositorio.
