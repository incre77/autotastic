# autotastic
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
* En el esp32 tx_pin=9 y rx_pin=10 configurados en el archivo transport_serial.py
* En mi caso particular trabaje con un nfr52840 donde el rx y el tx eran el 6 y el 8

### 2. Configuración Wi-Fi
Si no hay Wi-Fi configurado, el dispositivo entra en modo AP:
* **SSID:** `AUTOTASTIC_192_168_4_1`
* **Acceso:** Navega a `http://192.168.4.1` para configurar el SSID y Password finales.

---

## 💬 Comandos de Control (vía Chat)

Puedes gestionar el dispositivo enviando mensajes desde cualquier nodo de la red:

## 💬 Interacciones desde el Chat 

El dispositivo monitoriza el tráfico de la red, pero por seguridad y organización, **los comandos de administración solo se procesan si se envían a través del Canal 1**.
Asegurate de que tu segundo canal tanto en el nodo a controlar como el nodo controlador tengan el mismo canal con la misma clave para que nadie pueda manipular las reglas que gestionarán tu nodo.

### 1. Comandos de Sistema
| Comando | Acción |
| :--- | :--- |
| `/help` | Muestra la lista de comandos disponibles y ayuda rápida. |
| `/server` | Devuelve la **IP actual** (Local o AP) para acceder a la configuración web. |

<img width="1574" height="756" alt="Captura desde 2026-02-14 19-18-02" src="https://github.com/user-attachments/assets/6940b1c1-a9ca-4d0b-a3ec-f2937bf346e0" />

### 2. Gestión de Reglas Dinámicas
Permiten editar el comportamiento del dispositivo sin necesidad de cables:

| Comando | Parámetros | Descripción |
| :--- | :--- | :--- |
| `/rule_list` | (ninguno) | Lista los nombres de todas las reglas guardadas. |
| `/rule_add` | `NOMBRE CODIGO` | Añade una regla. El código se indenta automáticamente. |
| `/rule_change` | `NOMBRE CODIGO` | Actualiza el código de una regla existente. |
| `/rule_delete` | `NOMBRE` | Borra la regla del sistema. |

![photo_2026-02-14_19-22-23](https://github.com/user-attachments/assets/fd97e36b-5c4c-4ad4-b79d-fe9a0400fa65)


# Vea el contenido de external_code.py que ya dispone de varios ejemplos de reglas.


 Esta parte del archivo external_code.py es mejor no tocarla y mantenera tal cual.

    from sendmail import *
    import machine,time
    async def rules(device,packet,ch,txt):


 Esta regla es un ejemplo de como crear una variable e igualarla a 0 si no existe y sumar 1 si existe, despues envia un mensaje de vuelta al canal con el contenido de la variable

    #RULE:A    
    if ch==2 and 'c1' in txt: global c; c = c + 1 if 'c' in globals() else 1; await device.send_to_channel(ch, f"Contador:{c}.")    

 Esta regla solo se ejecuta si se recibe un texto que contanga la palaga  "gorrion" en el canal 0 (el canal 0 es None. si) y si ocurre se setean unas variables que haran falta en la siguiente regla
> 
    #RULE:B
    if(ch == None and "gorrion" in txt ):
        host = "smtp.tuservidor.net"
        port = 465
        user = "info@tucorreo.es"
        password = "tu password" 

 Esta regla tiene exactamente la misma condición que la anterior y es igual porque un paquete meshtastic tiene una limitacion de 237 bytes de los cuales
 la cabecera ocupa unos 40. Asi que el contenido de cada una de estas reglas debe ser de 195 bytes maximo para poder ser manejadas remotamente desde otro 
 nodo. Si quieres puedes añadir reglas mas grandes pero tendrás que gestinarlas via wifi.

 Debido a falta de memoria cuando se ejecuta un program_mail como es en este caso. Se programa el mail a enviar  y se resetea el controlador para enviar el 
 mail justos despues del arranque. Una vez enviado vuelve a resetear el controlador volviendo a su estado natural de espera de eventos.

    #RULE:C
    if(ch == None and "gorrion" in txt ):
        await program_mail("tucorreo@gmail.com", "notificacion autotastic", f"Se detectó la palabra gorrion en el canal 0.",host,port,user,password)
        
Esta regla se ejecuta si en tercer canal configurado en tu nodo se recibe un mensaje que contenga el texto "led". En ese caso se enviará un pulso al pin 0 durante 3 segundos y despues se apagará    

    #RULE:D
    if(ch==2 and 'led' in txt):
        led = machine.Pin(0, machine.Pin.OUT)
        led.value(1)
        time.sleep(3)
        led.value(0)

En el archivo device.py podreis encontrar mas funciones para enviar mensajes directos o mensajes de telemetria y puede que algo mas.

---

## 📧 Envío de Email (RAM Inteligente)

Para evitar errores de memoria (MemoryError), el módulo `sendmail.py`:
1. Guarda los datos en `pendant_mail.json`.
2. Ejecuta un `machine.reset()`.
3. Al arrancar, `boot.py` detecta el correo, lo envía con la RAM limpia y continúa con el flujo normal.

---

Este software ha sido desarrollado con thonny.
<img width="903" height="685" alt="Captura desde 2026-02-14 19-14-01" src="https://github.com/user-attachments/assets/b8087525-32e9-468a-a3e1-8db3870c5c05" />


## 🛡️ Licencia

Este proyecto está bajo una licencia de **Uso No Comercial**. 

* **No Comercial:** No se permite el uso de este software con fines lucrativos.
* **Atribución:** Si utilizas o modificas este código, debes citar al autor original y vincular a este repositorio.
