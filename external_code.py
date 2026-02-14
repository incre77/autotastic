from sendmail import *
import machine,time
async def rules(device,packet,ch,txt):
    #RULE:A
    if ch==2 and 'c1' in txt: global c; c = c + 1 if 'c' in globals() else 1; await device.send_to_channel(ch, f"Contador:{c}.")
    #RULE:B

    if(ch == None and "gorrion" in txt ):
        host = "smtp.tuserver.net"
        port = 465
        user = "info@tucorreo.es"
        password = "9845720938572903" 

    #RULE:C

    if(ch == None and "gorrion" in txt ):
        await program_mail("destinatario@gmail.com", "notificacion autotastic", f"Se detectó la palabra gorrion en el canal 0.",host,port,user,password)

    #RULE:D
    if(ch==2 and 'led' in txt):
        led = machine.Pin(0, machine.Pin.OUT)
        led.value(1)
        time.sleep(3)
        led.value(0)


    #RULE:E
    xx=123

