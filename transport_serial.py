import asyncio
import utime
from machine import UART, Pin

class SerialTransport:
    def __init__(self, uart_id=1, baudrate=115200, tx_pin=9, rx_pin=10):
        self.uart_id = uart_id
        self.baudrate = baudrate
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin
        self.uart = None

    async def start(self):
        self.uart = UART(
            self.uart_id, 
            baudrate=self.baudrate, 
            tx=Pin(self.tx_pin), 
            rx=Pin(self.rx_pin),
            rxbuf=1024
        )
        #print(f"UART{self.uart_id} iniciada en pines TX:{self.tx_pin} RX:{self.rx_pin}")

    async def send(self, data):
        if self.uart:
            self.uart.write(data)

    async def recv(self, timeout_ms=2000):
        if not self.uart:
            return None

        # Usamos ticks_ms para compatibilidad universal en MicroPython
        start_tick = utime.ticks_ms()
        
        while utime.ticks_diff(utime.ticks_ms(), start_tick) < timeout_ms:
            if self.uart.any() >= 4:
                header = self.uart.read(2)
                if header == b'\x94\xC3':
                    len_bytes = self.uart.read(2)
                    length = (len_bytes[0] << 8) | len_bytes[1]
                    
                    payload = b''
                    read_start = utime.ticks_ms()
                    while len(payload) < length:
                        if self.uart.any():
                            payload += self.uart.read(length - len(payload))
                        
                        if utime.ticks_diff(utime.ticks_ms(), read_start) > 1000:
                            break
                        await asyncio.sleep_ms(5)
                    
                    return header + len_bytes + payload
            
            await asyncio.sleep_ms(10)
        
        return None

    def close(self):
        if self.uart:
            try:
                self.uart.deinit()
            except:
                pass
            self.uart = None