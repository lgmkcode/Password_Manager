from gpiozero import Button
from signal import pause
import sys
import paho.mqtt.client as paho

BROKER_IP = "192.168.207.93"
BROKER_PORT = 9999
MAX_LENGTH = 4
MQTT_TOPIC = "pin"

# MQTT Bağlantısı
client = paho.Client()
if client.connect(BROKER_IP, BROKER_PORT, 60) != 0:
    print("Couldn't connect to the MQTT broker")
    sys.exit(1)

# Fiziksel Pin Tanımları
button_pins = {16: "1", 26: "2", 6: "3", 5: "4"}
buttons = []
input_sequence = ""

def button_pressed(value):
    global input_sequence
    if len(input_sequence) < MAX_LENGTH:
        input_sequence += value
        if len(input_sequence) == MAX_LENGTH:
            finalize_input()

def finalize_input():
    global input_sequence
    print(f"Final input: {input_sequence}")
    client.publish(MQTT_TOPIC, input_sequence)
    input_sequence = ""

# Butonları tanımlama ve olayları atama
for pin, value in button_pins.items():
    button = Button(pin, pull_up=True, bounce_time=0.15)
    button.when_pressed = lambda v=value: button_pressed(v)
    buttons.append(button)

print("4 haneli sayıyı oluşturmak için butonlara basın...")
pause()
