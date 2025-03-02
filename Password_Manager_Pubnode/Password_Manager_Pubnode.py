"""
RFID and PIN Based Authentication System
-------------------------------------------

This program manages an RFID and PIN based authentication system running on Raspberry Pi.
It provides secure authentication between various devices using Firebase and MQTT protocol.

System Features:
1. Firebase Integration:
   - Pulls user data from Firebase database
   - Stores data in local JSON files

2. MQTT Communication:
   - Enables data exchange between PC and Raspberry Pi
   - Listens for RFID and PIN data
   - Transmits authentication results
   - Broker IP: 192.168.13.93, Port: 9999

3. LED Indicators:
   - RFID LED (GPIO 17): RFID authentication successful
   - PIN LED (GPIO 22): PIN authentication successful
   - Error LED (GPIO 4): Authentication error

4. Security Verifications:
   - RFID card verification
   - PIN authentication
   - Two-factor authentication (RFID + PIN)

Workflow:
1. Program connects to MQTT broker
2. Pulls user data from Firebase
3. Checks data from RFID reader
4. Verifies PIN entries
5. Shows results with LEDs
6. If authentication is successful, transmits user data to PC

Requirements:
- paho-mqtt library
- firebase-admin library
- gpiozero library
- Firebase service account credentials (JSON)
- Working MQTT broker

Error Management:
- All critical operations are protected with try-except blocks
- Error states are logged to console
- Visual feedback is provided with LEDs

"""

import sys
import json
import time
import paho.mqtt.client as paho
import firebase_admin
from firebase_admin import credentials, db
from gpiozero import LED
from time import sleep

# LED Definitions
led_rfid = LED(17)
led_pin = LED(22)
led_error = LED(4)

# Flag to check if Firebase is initialized
firebase_initialized = False

def initialize_firebase():
    """ Initializes Firebase connection. """
    global firebase_initialized
    if not firebase_initialized:
        cred = credentials.Certificate('muhtas-2990b-firebase-adminsdk-4hyi4-b20232f6db.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://muhtas-2990b-default-rtdb.firebaseio.com/'
        })
        firebase_initialized = True

def pull_data():
    """ Pulls data from Firebase and saves it to a JSON file. """
    initialize_firebase()
    try:
        ref = db.reference('/')
        data = ref.get()
        if data:
            with open('password_rpi.json', 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            print("Data successfully pulled and saved to 'password_rpi.json' file.")
        else:
            print("Warning: Empty data received from Firebase.")
    except Exception as e:
        print(f"Error: An error occurred while pulling Firebase data -> {e}")

def check_rfid(user_id):
    """ Checks the incoming RFID data. """
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
        print(f"Error: An error occurred during RFID verification -> {e}")
    return False

def read_pin_from_tmp():
    """ Reads pin information from tmp_password.json file. """
    try:
        with open("tmp_password.json", "r") as file:
            data = json.load(file)
            key = list(data.keys())[0]
            return str(data[key].get("pin", ""))
    except Exception as e:
        print(f"Error: An error occurred while reading PIN -> {e}")
        return None

def send_data_to_pc(client):
    """ Sends JSON file to PC over MQTT. """
    try:
        with open('tmp_password.json', 'r') as file:
            data = json.load(file)

        data_out = json.dumps(data)
        client.publish("rpi-to-pc-data", data_out, qos=0)
        client.publish("rpi-to-pc-flag", "pull-end-flag", qos=0)
        print("Data successfully sent to PC.")
    except Exception as e:
        print(f"Error: An error occurred during MQTT transmission -> {e}")

def led_blink(led, duration=2):
    """ Turns on and off the specified LED for a certain duration. """
    led.on()
    sleep(duration)
    led.off()

def on_message(client, userdata, msg):
    """ Processes messages coming from MQTT. """
    payload = msg.payload.decode()

    if msg.topic == "pc-to-rpi-flag" and payload == "pull-start-flag":
        pull_data()

    elif msg.topic == "rfid":
        if not check_rfid(payload):
            led_blink(led_error)  # Invalid RFID
            return
        led_blink(led_rfid)  # Valid RFID

    elif msg.topic == "pin":
        correct_pin = read_pin_from_tmp()
        if correct_pin is None or payload != correct_pin:
            led_blink(led_error)  # Wrong PIN
            return
        led_blink(led_pin)  # Correct PIN
        send_data_to_pc(client)

def start_mqtt():
    """ Starts MQTT connection and listens for messages. """
    client = paho.Client()
    client.on_message = on_message

    if client.connect("192.168.13.93", 9999, 60) != 0:
        print("Could not connect to MQTT broker!")
        sys.exit(1)

    client.subscribe("pc-to-rpi-flag", qos=0)
    client.subscribe("rfid", qos=0)
    client.subscribe("pin", qos=0)

    try:
        print("MQTT listener started, waiting for messages...")
        client.loop_forever()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        print("Terminating MQTT connection...")
        client.disconnect()

if __name__ == "__main__":
    start_mqtt()
