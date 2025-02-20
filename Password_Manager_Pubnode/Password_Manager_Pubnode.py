"""
RFID ve PIN Tabanlı Kimlik Doğrulama Sistemi
-------------------------------------------

Bu program, Raspberry Pi üzerinde çalışan RFID ve PIN tabanlı bir kimlik doğrulama
sistemini yönetir. Firebase ve MQTT protokolü kullanılarak çeşitli cihazlar arasında
güvenli bir kimlik doğrulama sağlar.

Sistem Özellikleri:
1. Firebase Entegrasyonu:
   - Kullanıcı verilerini Firebase veritabanından çeker
   - Verileri yerel JSON dosyalarında saklar

2. MQTT İletişimi:
   - PC ile Raspberry Pi arasında veri alışverişi sağlar
   - RFID ve PIN verilerini dinler
   - Doğrulama sonuçlarını iletir
   - Broker IP: 192.168.13.93, Port: 9999

3. LED Göstergeler:
   - RFID LED (GPIO 17): RFID doğrulaması başarılı
   - PIN LED (GPIO 22): PIN doğrulaması başarılı
   - Hata LED (GPIO 4): Doğrulama hatası

4. Güvenlik Doğrulamaları:
   - RFID kart kontrolü
   - PIN doğrulaması
   - İki faktörlü kimlik doğrulama (RFID + PIN)

Çalışma Akışı:
1. Program MQTT broker'a bağlanır
2. Firebase'den kullanıcı verilerini çeker
3. RFID okuyucudan gelen verileri kontrol eder
4. PIN girişlerini doğrular
5. Sonuçları LED'ler ile gösterir
6. Doğrulama başarılı ise kullanıcı verilerini PC'ye iletir

Gereksinimler:
- paho-mqtt kütüphanesi
- firebase-admin kütüphanesi
- gpiozero kütüphanesi
- Firebase servis hesabı kimlik bilgileri (JSON)
- Çalışan bir MQTT broker

Hata Yönetimi:
- Tüm kritik işlemler try-except blokları ile korunur
- Hata durumları konsola loglanır
- LED'ler ile görsel geri bildirim sağlanır

"""

import sys
import json
import time
import paho.mqtt.client as paho
import firebase_admin
from firebase_admin import credentials, db
from gpiozero import LED
from time import sleep

# LED Tanımları
led_rfid = LED(17)
led_pin = LED(22)
led_error = LED(4)

# Firebase'in başlatıldığını kontrol eden flag
firebase_initialized = False

def initialize_firebase():
    """ Firebase bağlantısını başlatır. """
    global firebase_initialized
    if not firebase_initialized:
        cred = credentials.Certificate('muhtas-2990b-firebase-adminsdk-4hyi4-b20232f6db.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://muhtas-2990b-default-rtdb.firebaseio.com/'
        })
        firebase_initialized = True

def pull_data():
    """ Firebase'den veriyi çeker ve JSON dosyasına kaydeder. """
    initialize_firebase()
    try:
        ref = db.reference('/')
        data = ref.get()
        if data:
            with open('password_rpi.json', 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            print("Veri başarıyla çekildi ve 'password_rpi.json' dosyasına kaydedildi.")
        else:
            print("Uyarı: Firebase'den boş veri alındı.")
    except Exception as e:
        print(f"Hata: Firebase verisi çekilirken bir hata oluştu -> {e}")

def check_rfid(user_id):
    """ Gelen RFID verisini kontrol eder. """
    try:
        with open("password_rpi.json", "r") as f:
            data = json.load(f)

        selected_user_data = data.get(user_id)
        if selected_user_data:
            output_data = {user_id: selected_user_data}
            with open("tmp_password.json", "w") as new_file:
                json.dump(output_data, new_file, indent=4)
            return True
    except Exception as e:
        print(f"Hata: RFID kontrolü sırasında bir hata oluştu -> {e}")
    return False

def read_pin_from_tmp():
    """ tmp_password.json dosyasından pin bilgisini okur. """
    try:
        with open("tmp_password.json", "r") as file:
            data = json.load(file)
            key = list(data.keys())[0]
            return str(data[key].get("pin", ""))
    except Exception as e:
        print(f"Hata: PIN okuma sırasında bir hata oluştu -> {e}")
        return None

def send_data_to_pc(client):
    """ JSON dosyasını PC'ye MQTT üzerinden gönderir. """
    try:
        with open('tmp_password.json', 'r') as file:
            data = json.load(file)

        data_out = json.dumps(data)
        client.publish("rpi-to-pc-data", data_out, qos=0)
        client.publish("rpi-to-pc-flag", "pull-end-flag", qos=0)
        print("Veri başarıyla PC'ye gönderildi.")
    except Exception as e:
        print(f"Hata: MQTT gönderimi sırasında bir hata oluştu -> {e}")

def led_blink(led, duration=2):
    """ Belirtilen LED'i belirli bir süre yakıp söndürür. """
    led.on()
    sleep(duration)
    led.off()

def on_message(client, userdata, msg):
    """ MQTT'den gelen mesajları işler. """
    payload = msg.payload.decode()

    if msg.topic == "pc-to-rpi-flag" and payload == "pull-start-flag":
        pull_data()

    elif msg.topic == "rfid":
        if not check_rfid(payload):
            led_blink(led_error)  # Hatalı RFID
            return
        led_blink(led_rfid)  # Geçerli RFID

    elif msg.topic == "pin":
        correct_pin = read_pin_from_tmp()
        if correct_pin is None or payload != correct_pin:
            led_blink(led_error)  # Yanlış PIN
            return
        led_blink(led_pin)  # Doğru PIN
        send_data_to_pc(client)

def start_mqtt():
    """ MQTT bağlantısını başlatır ve mesajları dinler. """
    client = paho.Client()
    client.on_message = on_message

    if client.connect("192.168.13.93", 9999, 60) != 0:
        print("MQTT broker'a bağlanılamadı!")
        sys.exit(1)

    client.subscribe("pc-to-rpi-flag", qos=0)
    client.subscribe("rfid", qos=0)
    client.subscribe("pin", qos=0)

    try:
        print("MQTT dinleyici başlatıldı, mesaj bekleniyor...")
        client.loop_forever()
    except KeyboardInterrupt:
        print("Çıkış yapılıyor...")
    finally:
        print("MQTT bağlantısı sonlandırılıyor...")
        client.disconnect()

if __name__ == "__main__":
    start_mqtt()
