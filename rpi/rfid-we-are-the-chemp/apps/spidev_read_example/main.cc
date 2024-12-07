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

using namespace std::literals::chrono_literals;

int main(int argc, char *argv[]) {

	Spidev spi("/dev/spidev0.0");
	spi.mSpi.setBitsPerWord(8);
	spi.mSpi.setSpeed(488000);
	spi.mSpi.setMode(0);

	std::cout << spi.mSpi << std::endl;

	SysGpio resetPin(25, spidevpp::Gpio::Direction::OUTPUT, spidevpp::Gpio::Value::LOW);

	mfrc522::MFRC522 mfrc(spi, resetPin);
	mfrc.PCD_Init();

	std::cout << "Start read loop!" << std::endl;

while (1) {
    // Look for a card
    if (!mfrc.PICC_IsNewCardPresent()) {
        std::this_thread::sleep_for(1000ms);
        continue;
    }

    if (!mfrc.PICC_ReadCardSerial()) {
        continue;
    }

    // Print UID
    char uidString[50]; // Kartın UID'sini tutacak string
    snprintf(uidString, sizeof(uidString), "");
    
    // Kartın UID'sini string olarak formatla
    for (uint8_t i = 0; i < mfrc.uid.size; ++i) {
        snprintf(uidString + strlen(uidString), sizeof(uidString) - strlen(uidString), "%02X", mfrc.uid.uidByte[i]);
    }

    printf("Card UID: %s\n", uidString);

    // c ile mqtt mesajı atılacak
    int rc;
    struct mosquitto * mosq;

    mosquitto_lib_init();

    mosq = mosquitto_new("publisher-test", true, NULL);

    rc = mosquitto_connect(mosq, "192.168.250.93", 1883, 60);
    if (rc != 0) {
        printf("Client could not connect to broker! Error Code: %d\n", rc);
        mosquitto_destroy(mosq);
        return -1;
    }
    printf("We are now connected to the broker!\n");

    // Kart UID'sini MQTT mesajı olarak gönder
    mosquitto_publish(mosq, NULL, "rfid", strlen(uidString), uidString, 0, false);

    mosquitto_disconnect(mosq);
    mosquitto_destroy(mosq);

    mosquitto_lib_cleanup();

    std::this_thread::sleep_for(1000ms);
}



	return 0;
}
