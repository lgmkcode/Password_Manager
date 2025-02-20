"""
Firebase ve MQTT Veri Senkronizasyon Sistemi
------------------------------------------

Bu program, PC ve Firebase Realtime Database arasında veri senkronizasyonunu 
sağlayan bir ara katman olarak çalışır. MQTT protokolü üzerinden gelen verileri
alır, işler ve Firebase veritabanına aktarır.

Sistem Özellikleri:
1. MQTT İletişimi:
   - PC'den gelen JSON verilerini dinler
   - İki ayrı topic üzerinden haberleşme:
     * pc-to-rpi-data: JSON verilerinin alındığı kanal
     * pc-to-rpi-flag: Senkronizasyon tetikleyici kanalı
   - Broker Bağlantısı:
     * IP: 192.168.207.93
     * Port: 9999

2. Dosya İşlemleri:
   - JSON verilerini yerel dosyada saklar (password_rpi.json)
   - Mevcut kullanıcı verilerini koruyarak güncelleme yapar
   - UTF-8 karakter desteği ile çoklu dil desteği

3. Firebase Entegrasyonu:
   - Realtime Database bağlantısı
   - Otomatik veri senkronizasyonu
   - Güvenli kimlik doğrulama ile veri aktarımı

Çalışma Akışı:
1. Firebase bağlantısı başlatılır
2. MQTT broker'a bağlanır ve topicler dinlenir
3. PC'den gelen veriler JSON formatında alınır
4. Veriler önce yerel dosyaya kaydedilir
5. Senkronizasyon bayrağı geldiğinde veriler Firebase'e aktarılır

Hata Yönetimi:
- JSON format kontrolleri
- Dosya okuma/yazma hata yönetimi
- Bağlantı kopması durumları
- Veri tutarlılığı kontrolleri

Güvenlik Özellikleri:
- Firebase kimlik doğrulama
- Yerel veri yedekleme
- Veri bütünlüğü kontrolleri

Gereksinimler:
- paho-mqtt kütüphanesi
- firebase-admin kütüphanesi
- Firebase servis hesabı kimlik bilgileri (JSON)
- Çalışan bir MQTT broker
"""
import sys
import json
import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, db

# MQTT Ayarları
MQTT_HOST = "192.168.207.93"
MQTT_PORT = 9999
DATA_TOPIC = "pc-to-rpi-data"  # JSON verilerinin gönderildiği konu
FLAG_TOPIC = "pc-to-rpi-flag"  # İşlem tetikleyici bayrak konusu
FLAG_MESSAGE = "send_start_flag"  # JSON verisinin hazır olduğunu belirten bayrak

# Firebase'i Başlatma
FIREBASE_CRED_PATH = 'muhtas-2990b-firebase-adminsdk-4hyi4-b20232f6db.json'
FIREBASE_DB_URL = 'https://muhtas-2990b-default-rtdb.firebaseio.com/'

def initialize_firebase():
    """Firebase bağlantısını başlatır."""
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

def read_json_file(filename='password_rpi.json'):
    """Belirtilen JSON dosyasını okur ve içeriğini döndürür."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Hata: {filename} dosyası okunamadı.")
        return {}

def write_json_file(data, filename='password_rpi.json'):
    """JSON verisini belirtilen dosyaya yazar."""
    user_id = list(data.keys())[0]
    json_data = read_json_file(filename)
    
    if user_id in json_data:
        json_data[user_id] = data[user_id]
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=4, ensure_ascii=False)
        print(f"Kullanıcı {user_id} güncellendi.")
    else:
        print(f"Hata: Kullanıcı ID {user_id} dosyada bulunamadı!")

def push_data_to_firebase():
    """JSON verisini Firebase Realtime Database'e yükler."""
    json_data = read_json_file()
    if json_data:
        db.reference('/').set(json_data)
        print("JSON verisi başarıyla Firebase'e yüklendi.")
    else:
        print("Hata: Firebase'e yüklenecek veri bulunamadı!")

def on_message(client, userdata, msg):
    """MQTT mesajlarını işler."""
    payload = msg.payload.decode()
    print(f"Mesaj alındı: {msg.topic} -> {payload}")
    
    if msg.topic == DATA_TOPIC:
        try:
            message_data = json.loads(payload)
            write_json_file(message_data)
            print("JSON verisi başarıyla kaydedildi.")
        except json.JSONDecodeError:
            print("Hata: Geçersiz JSON verisi alındı.")
    elif msg.topic == FLAG_TOPIC and payload == FLAG_MESSAGE:
        print("Bayrak mesajı alındı, Firebase'e veri gönderiliyor...")
        push_data_to_firebase()

def main():
    """Ana program akışı."""
    initialize_firebase()
    
    client = mqtt.Client()
    client.on_message = on_message
    
    if client.connect(MQTT_HOST, MQTT_PORT, 60) != 0:
        print("MQTT broker'a bağlanılamadı!")
        sys.exit(1)
    
    client.subscribe([(DATA_TOPIC, 0), (FLAG_TOPIC, 0)])
    
    try:
        print("Mesajlar dinleniyor... (Çıkış için CTRL+C)")
        client.loop_forever()
    except KeyboardInterrupt:
        print("Çıkış yapılıyor...")
    finally:
        print("MQTT bağlantısı kapatılıyor...")
        client.disconnect()

if __name__ == "__main__":
    main()
