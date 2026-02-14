import usocket as socket
import ssl
import ubinascii
import gc
import json, machine,os,time
from wifi import *


def program_mail(recipient, subject, body, host, port, user, password):
    try:
        # Empaquetamos absolutamente todo
        datos = {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "host": host,
            "port": port,
            "user": user,
            "password": password
        }
        with open('pendant_mail.json', 'w', encoding='utf-8') as f:
            json.dump(datos, f)
            
        print("Datos guardados. Reiniciando para liberar RAM...")
        machine.reset()
    except Exception as e:
        print("Error al guardar pendiente:", e)
        
def check_pendant_mail():
    path = 'pendant_mail.json'
    if path in os.listdir():
        print("📬 Detectado correo pendiente. Procesando...")
        try:
            with open(path, 'r') as f:
                d = json.load(f)
            
            wifi_connect()
            gc.collect()
            # Ejecutamos con los datos guardados
            send_email(
                d['recipient'], d['subject'], d['body'],
                d['host'], d['port'], d['user'], d['password']
            )
            print("✅ Envío post-reinicio exitoso.")
            
        except Exception as e:
            print("❌ Error crítico en envío pendiente:", e)
        finally:
            # Borramos el archivo para no entrar en bucle de reinicios
            os.remove(path)
            #time.sleep(2)
            machine.reset()
            

def send_email(recipient, subject, body, host, port, user, password):
    # 1. Limpieza agresiva antes de empezar
    gc.collect()
    
    addr = socket.getaddrinfo(host, port)[0][-1]
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect(addr)
    
    # 2. SSL con server_hostname ayuda a mbedtls a negociar mejor
    # Si sigue fallando, intenta sin server_hostname
    sock = ssl.wrap_socket(sock, server_hostname=host)
    gc.collect() 

    def send_cmd(cmd):
        sock.write(cmd + "\r\n")
        # No guardamos la respuesta en una variable si no la vamos a usar
        # Leemos y descartamos para ahorrar RAM
        while True:
            line = sock.readline()
            if not line or len(line) < 4 or line[3:4] != b"-":
                break
        gc.collect()

    # --- Flujo ---
    # En lugar de funciones que retornan bytes, enviamos y limpiamos
    while True: # Banner inicial
        l = sock.readline()
        if not l or l[3:4] != b"-": break

    send_cmd("EHLO localhost")
    send_cmd("AUTH LOGIN")
    
    # Enviamos las credenciales directamente sin variables intermedias pesadas
    send_cmd(ubinascii.b2a_base64(user.encode()).decode().strip())
    send_cmd(ubinascii.b2a_base64(password.encode()).decode().strip())

    send_cmd("MAIL FROM:<" + user + ">")
    send_cmd("RCPT TO:<" + recipient + ">")
    send_cmd("DATA")
    
    # Construcción del mensaje directamente al socket para evitar strings gigantes en RAM
    sock.write("From: " + user + "\r\n")
    sock.write("To: " + recipient + "\r\n")
    sock.write("Subject: " + subject + "\r\n\r\n")
    sock.write(body + "\r\n.\r\n")
    
    while True: # Esperar respuesta del DATA
        l = sock.readline()
        if not l or l[3:4] != b"-": break

    send_cmd("QUIT")
    sock.close()
    gc.collect()
    print("Enviado")