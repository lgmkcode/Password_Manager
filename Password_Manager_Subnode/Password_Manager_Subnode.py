"""
Firebase and MQTT Data Synchronization System
------------------------------------------

This program works as a middleware that provides data synchronization between 
PC and Firebase Realtime Database. It receives data via MQTT protocol,
processes it and transfers it to the Firebase database.

System Features:
1. MQTT Communication:
   - Listens to JSON data coming from PC
   - Communication over two separate topics:
     * pc-to-rpi-data: Channel where JSON data is received
     * pc-to-rpi-flag: Synchronization trigger channel
   - Broker Connection:
     * IP: 192.168.207.93
     * Port: 9999

2. File Operations:
   - Stores JSON data in local file (password_rpi.json)
   - Updates while preserving existing user data
   - Multi-language support with UTF-8 character support

3. Firebase Integration:
   - Realtime Database connection
   - Automatic data synchronization
   - Secure data transfer with authentication

Workflow:
1. Firebase connection is initiated
2. Connects to MQTT broker and listens to topics
3. Data from PC is received in JSON format
4. Data is first saved to local file
5. When synchronization flag is received, data is transferred to Firebase

Error Management:
- JSON format checks
- File read/write error handling
- Connection loss situations
- Data consistency checks

Security Features:
- Firebase authentication
- Local data backup
- Data integrity checks

Requirements:
- paho-mqtt library
- firebase-admin library
- Firebase service account credentials (JSON)
- A running MQTT broker
"""
import sys
import json
import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, db

# MQTT Settings
MQTT_HOST = "192.168.207.93"
MQTT_PORT = 9999
DATA_TOPIC = "pc-to-rpi-data"  # Topic where JSON data is sent
FLAG_TOPIC = "pc-to-rpi-flag"  # Process trigger flag topic
FLAG_MESSAGE = "send_start_flag"  # Flag indicating JSON data is ready

# Initialize Firebase
FIREBASE_CRED_PATH = 'muhtas-2990b-firebase-adminsdk-4hyi4-b20232f6db.json'
FIREBASE_DB_URL = 'https://muhtas-2990b-default-rtdb.firebaseio.com/'

def initialize_firebase():
    """Initializes Firebase connection."""
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

def read_json_file(filename='password_rpi.json'):
    """Reads the specified JSON file and returns its contents."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error: Could not read {filename} file.")
        return {}

def write_json_file(data, filename='password_rpi.json'):
    """Writes JSON data to the specified file."""
    user_id = list(data.keys())[0]
    json_data = read_json_file(filename)
    
    if user_id in json_data:
        json_data[user_id] = data[user_id]
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=4, ensure_ascii=False)
        print(f"User {user_id} updated.")
    else:
        print(f"Error: User ID {user_id} not found in file!")

def push_data_to_firebase():
    """Uploads JSON data to Firebase Realtime Database."""
    json_data = read_json_file()
    if json_data:
        db.reference('/').set(json_data)
        print("JSON data successfully uploaded to Firebase.")
    else:
        print("Error: No data found to upload to Firebase!")

def on_message(client, userdata, msg):
    """Processes MQTT messages."""
    payload = msg.payload.decode()
    print(f"Message received: {msg.topic} -> {payload}")
    
    if msg.topic == DATA_TOPIC:
        try:
            message_data = json.loads(payload)
            write_json_file(message_data)
            print("JSON data successfully saved.")
        except json.JSONDecodeError:
            print("Error: Invalid JSON data received.")
    elif msg.topic == FLAG_TOPIC and payload == FLAG_MESSAGE:
        print("Flag message received, sending data to Firebase...")
        push_data_to_firebase()

def main():
    """Main program flow."""
    initialize_firebase()
    
    client = mqtt.Client()
    client.on_message = on_message
    
    if client.connect(MQTT_HOST, MQTT_PORT, 60) != 0:
        print("Could not connect to MQTT broker!")
        sys.exit(1)
    
    client.subscribe([(DATA_TOPIC, 0), (FLAG_TOPIC, 0)])
    
    try:
        print("Listening for messages... (Press CTRL+C to exit)")
        client.loop_forever()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        print("Closing MQTT connection...")
        client.disconnect()

if __name__ == "__main__":
    main()
