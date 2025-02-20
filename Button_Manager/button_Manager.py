"""
Raspberry Pi PIN Okuma ve MQTT İle Gönderme Sistemi
------------------------------------------------

Bu program, Raspberry Pi üzerindeki fiziksel butonlardan 4 haneli bir PIN kodu okur
ve bu kodu MQTT broker'a gönderir. 

Özellikler:
- 4 adet fiziksel buton kullanır (GPIO pinleri: 16, 26, 6, 5)
- Her buton bir rakamı temsil eder (sırasıyla 1, 2, 3, 4)
- Maksimum 4 haneli bir PIN kodu oluşturulabilir
- Oluşturulan PIN kodu otomatik olarak MQTT broker'a gönderilir
- Bounce time ile buton okumalarındaki gürültü engellenir

Kullanım:
1. Program başlatıldığında MQTT broker'a bağlanır
2. Kullanıcı fiziksel butonlara basarak 4 haneli PIN kodunu oluşturur
3. 4 hane tamamlandığında, kod otomatik olarak MQTT broker'a gönderilir
4. PIN kodu gönderildikten sonra sistem yeni bir PIN kodu için hazır hale gelir

Gereksinimler:
- gpiozero kütüphanesi
- paho-mqtt kütüphanesi
- Çalışan bir MQTT broker (varsayılan port: 9999)
"""

from gpiozero import Button
from signal import pause
import sys
import paho.mqtt.client as paho

# Sabit değişkenler
BROKER_IP = "192.168.207.93"
BROKER_PORT = 9999
MAX_LENGTH = 4
MQTT_TOPIC = "pin"
BUTTON_PINS = {16: "1", 26: "2", 6: "3", 5: "4"}

class PinReader:
    def __init__(self):
        self.input_sequence = ""
        self.buttons = []
        self.client = None
    
    def button_pressed(self, value):
        if len(self.input_sequence) < MAX_LENGTH:
            self.input_sequence += value
            if len(self.input_sequence) == MAX_LENGTH:
                self.finalize_input()
    
    def finalize_input(self):
        print(f"Final input: {self.input_sequence}")
        self.client.publish(MQTT_TOPIC, self.input_sequence)
        self.input_sequence = ""
    
    def setup_mqtt(self):
        self.client = paho.Client()
        if self.client.connect(BROKER_IP, BROKER_PORT, 60) != 0:
            print("Couldn't connect to the MQTT broker")
            return False
        return True
    
    def setup_buttons(self):
        for pin, value in BUTTON_PINS.items():
            button = Button(pin, pull_up=True, bounce_time=0.15)
            button.when_pressed = lambda v=value: self.button_pressed(v)
            self.buttons.append(button)

def main():
    # Pin okuyucu nesnesini oluştur
    pin_reader = PinReader()
    
    # MQTT bağlantısını kur
    if not pin_reader.setup_mqtt():
        sys.exit(1)
    
    # Butonları ayarla
    pin_reader.setup_buttons()
    
    # Kullanıcıya bilgi ver
    print("4 haneli sayıyı oluşturmak için butonlara basın...")
    
    # Programı çalışır halde tut
    try:
        pause()
    except KeyboardInterrupt:
        print("\nProgram sonlandırılıyor...")
        sys.exit(0)

if __name__ == "__main__":
    main()
