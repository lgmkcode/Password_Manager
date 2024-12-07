import sys
import paho.mqtt.client as paho
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Constants
MQTT_HOST = "192.168.250.93"
MQTT_PORT = 9999
DATA_TOPIC = "pc-to-rpi-data"  # Topic for JSON datasets
FLAG_TOPIC = "pc-to-rpi-flag"  # Topic for the flag
FLAG_MESSAGE = "send_start_flag"         # Flag indicating JSON data is ready

def initialize_firebase():
    # Initialize Firebase with service account credentials
    cred = credentials.Certificate('muhtas-2990b-firebase-adminsdk-4hyi4-b20232f6db.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://muhtas-2990b-default-rtdb.firebaseio.com/'
    })

def read_json_file():
    # Read JSON file
    with open('password_rpi.json', 'r', encoding='utf-8') as json_file:
        return json.load(json_file)

def write_json_file(data):
    # Write to JSON file
    #with open('password_rpi.json', 'w') as json_file:
    #    json.dump(data, json_file, indent=4)

    user_id = list(data.keys())[0]

    with open('password_rpi.json', "r", encoding="utf-8") as file:
        json_data = json.load(file)

    # Kullanıcı verisini güncelleme
    if user_id in json_data:
        json_data[user_id] = data[user_id]
    else:
         print(f"ID {user_id} dosyada bulunamadı!")

    # Güncellenmiş veriyi dosyaya yazma
    with open('password_rpi.json', "w", encoding="utf-8") as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)

    print(f"Kullanıcı {user_id} güncellendi.")

def push_data():
    # Push JSON data to Firebase Realtime Database
    json_data = read_json_file()
    ref = db.reference('/')  # Root reference
    ref.set(json_data)
    print("JSON data successfully pushed to Firebase.")

def message_handling(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Received message on topic '{msg.topic}': {payload}")
    
    # Determine the message type based on the topic
    if msg.topic == DATA_TOPIC:
        try:
            # Parse and save the JSON dataset
            message_data = json.loads(payload)
            write_json_file(message_data)
            print("JSON dataset written to file.")
        except json.JSONDecodeError:
            print("Received invalid JSON data. Ignoring message.")
    elif msg.topic == FLAG_TOPIC:
        # Handle the flag message
        if payload == FLAG_MESSAGE:
            print("Flag message received. Executing push_data().")
            push_data()
        else:
            print("Unknown flag message received.")

# Initialize Firebase
initialize_firebase()

# Set up MQTT client
client = paho.Client()
client.on_message = message_handling

# Connect to MQTT broker
if client.connect(MQTT_HOST, MQTT_PORT, 60) != 0:
    print("Couldn't connect to the MQTT broker")
    sys.exit(1)

# Subscribe to both topics
client.subscribe(DATA_TOPIC)
client.subscribe(FLAG_TOPIC)

# MQTT event loop
try:
    print("Listening for messages. Press CTRL+C to exit...")
    client.loop_forever()
except KeyboardInterrupt:
    print("Exiting program...")
finally:
    print("Disconnecting from the MQTT broker...")
    client.disconnect()
