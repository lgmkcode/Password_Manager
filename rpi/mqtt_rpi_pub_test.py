import sys
import paho.mqtt.client as paho
import json
import firebase_admin
from firebase_admin import credentials, db


# Firebase'i global olarak başlat
firebase_initialized = False
def initialize_firebase():
    global firebase_initialized
    if not firebase_initialized:
        cred = credentials.Certificate('muhtas-2990b-firebase-adminsdk-4hyi4-b20232f6db.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://muhtas-2990b-default-rtdb.firebaseio.com/'
        })
        firebase_initialized = True


def check_rfid(client,msg):
    user_id = msg.payload.decode()
    print("1. User id: ", user_id)
    with open("password_rpi.json", "r") as f:
        data = json.load(f)
    print("2")

    selected_user_data = data.get(user_id)
    if selected_user_data:
        print("3. selected_user_data: ", selected_user_data)

        output_data = { user_id: selected_user_data}
        with open("tmp_password.json", "w") as new_file:
            json.dump(output_data, new_file, indent=4)

        print("4")
        return True

    return False

# MQTT Callback when a message is received
def on_message(client, userdata, msg):
    #print(f"Message received on {msg.topic}: {msg.payload.decode()}")

    if msg.topic == "pc-to-rpi-flag" and msg.payload.decode() == "pull-start-flag":
        pull_data()

    if msg.topic == "rfid":

        if check_rfid(client, msg) != True:
            print("No data push. Buzzer will be open")
            return


        send_data_to_pc(client, msg)


# Function to pull data from Firebase
def pull_data():

    initialize_firebase()

    # 2. Firebase Realtime Database'den verileri çek
    ref = db.reference('/')  # Kök referansı alabilirsin veya alt bir referans kullanabilirsin
    data = ref.get()  # Veriyi al

    # 3. Veriyi JSON dosyasına kaydet
    with open('password_rpi.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    print("Veri başarıyla çekildi ve 'password_rpi.json' dosyasına kaydedildi.")


# Function to send pulled data to the PC
def send_data_to_pc(client, msg):
    with open('tmp_password.json', 'r') as file:
        data = json.load(file)

    data_out = json.dumps(data)

    client.publish("rpi-to-pc-data", data_out, 0)
    client.publish("rpi-to-pc-flag", "pull-end-flag", 0)



client = paho.Client()
client.on_message = on_message

if client.connect("192.168.250.93", 9999, 60) != 0:
    print("Couldn't connect to the mqtt broker")
    sys.exit(1)

client.subscribe("pc-to-rpi-flag", 0)
client.subscribe("rfid", 0)

try:
    print("Listening for messages. Press CTRL+C to exit...")
    client.loop_forever()
except KeyboardInterrupt:
    print("Exiting program...")
finally:
    print("Disconnecting from the MQTT broker...")
    client.disconnect()

