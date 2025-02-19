#include "spidev_impl.h"
#include "sys_gpio_impl.h"
#include <mfrc522/mfrc522.h>
#include <spidevpp/gpio.h>
#include <stdio.h>
#include <cstring>
#include <mosquitto.h>
#include <iostream>
#include <thread>
#include <chrono>

// Sabitler
constexpr auto MQTT_BROKER_ADDRESS = "192.168.207.93";
constexpr int MQTT_BROKER_PORT = 1883;
constexpr int MQTT_KEEP_ALIVE = 60;
constexpr auto MQTT_TOPIC = "rfid";
constexpr auto SPI_DEVICE = "/dev/spidev0.0";
constexpr int RESET_PIN = 25;
constexpr int SPI_SPEED = 488000;
constexpr int SPI_BITS_PER_WORD = 8;
constexpr auto CARD_POLLING_INTERVAL = std::chrono::milliseconds(1000);

using namespace std::literals::chrono_literals;

// MQTT ile kart UID'sini gönderen fonksiyon
bool sendCardUidViaMqtt(const char* uidString) {
    struct mosquitto* mosq = nullptr;
    bool success = true;
    
    // MQTT kütüphanesini başlat
    mosquitto_lib_init();
    
    // Yeni bir MQTT istemcisi oluştur
    mosq = mosquitto_new("rfid-reader-client", true, nullptr);
    if (!mosq) {
        std::cerr << "MQTT istemcisi oluşturulamadı!" << std::endl;
        mosquitto_lib_cleanup();
        return false;
    }
    
    // Broker'a bağlan
    int rc = mosquitto_connect(mosq, MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "MQTT broker'a bağlanılamadı! Hata Kodu: " << rc << std::endl;
        success = false;
    } else {
        std::cout << "MQTT broker'a başarıyla bağlandı" << std::endl;
        
        // Kart UID'sini MQTT mesajı olarak gönder
        rc = mosquitto_publish(mosq, nullptr, MQTT_TOPIC, strlen(uidString), uidString, 0, false);
        if (rc != MOSQ_ERR_SUCCESS) {
            std::cerr << "MQTT mesajı gönderilemedi! Hata Kodu: " << rc << std::endl;
            success = false;
        }
    }
    
    // Bağlantıyı kapat ve kaynakları temizle
    mosquitto_disconnect(mosq);
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();
    
    return success;
}

// Kart UID'sini hexadecimal string formatına dönüştüren fonksiyon
std::string formatCardUid(const mfrc522::MFRC522::Uid& uid) {
    char uidString[50] = {0};
    
    for (uint8_t i = 0; i < uid.size; ++i) {
        char hexByte[3];
        snprintf(hexByte, sizeof(hexByte), "%02X", uid.uidByte[i]);
        strcat(uidString, hexByte);
    }
    
    return std::string(uidString);
}

int main(int argc, char *argv[]) {
    // SPI arayüzünü yapılandır
    Spidev spi(SPI_DEVICE);
    spi.mSpi.setBitsPerWord(SPI_BITS_PER_WORD);
    spi.mSpi.setSpeed(SPI_SPEED);
    spi.mSpi.setMode(0);
    std::cout << "SPI Yapılandırması: " << spi.mSpi << std::endl;
    
    // RFID okuyucuyu başlat
    SysGpio resetPin(RESET_PIN, spidevpp::Gpio::Direction::OUTPUT, spidevpp::Gpio::Value::LOW);
    mfrc522::MFRC522 mfrc(spi, resetPin);
    mfrc.PCD_Init();
    
    std::cout << "RFID Kart okuma döngüsü başlatıldı!" << std::endl;
    
    // Ana döngü
    while (true) {
        // Yeni kart kontrolü
        if (!mfrc.PICC_IsNewCardPresent()) {
            std::this_thread::sleep_for(CARD_POLLING_INTERVAL);
            continue;
        }
        
        // Kart seri numarasını oku
        if (!mfrc.PICC_ReadCardSerial()) {
            continue;
        }
        
        // Kart UID'sini formatla
        std::string uidString = formatCardUid(mfrc.uid);
        std::cout << "Kart UID: " << uidString << std::endl;
        
        // MQTT ile gönder
        if (sendCardUidViaMqtt(uidString.c_str())) {
            std::cout << "UID başarıyla MQTT üzerinden gönderildi" << std::endl;
        } else {
            std::cerr << "UID gönderilirken hata oluştu" << std::endl;
        }
        
        // Bir sonraki okuma işlemi için bekle
        std::this_thread::sleep_for(CARD_POLLING_INTERVAL);
    }
    
    return 0;
}
