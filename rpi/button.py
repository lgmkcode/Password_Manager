from gpiozero import Button
from signal import pause

import sys
import paho.mqtt.client as paho

client = paho.Client()

if client.connect("192.168.250.93", 9999, 60) != 0:
    print("Couldn't connect to the mqtt broker")
    sys.exit(1)

# Fiziksel Pinler
button1 = Button(6, pull_up=True, bounce_time=0.15)  # Pin 31
button2 = Button(5, pull_up=True, bounce_time=0.15)  # Pin 29

# Giriş dizisi
input_sequence = ""

# Maksimum uzunluk
max_length = 6

def button1_pressed():
    global input_sequence
    if len(input_sequence) < max_length:
        input_sequence += "1"
        if len(input_sequence) == max_length:
            finalize_input()

def button2_pressed():
    global input_sequence
    if len(input_sequence) < max_length:
        input_sequence += "2"
        if len(input_sequence) == max_length:
            finalize_input()

def finalize_input():
    global input_sequence
    print(f"Final input: {input_sequence}")
    client.publish("pin", input_sequence)

# Olay işlevlerini atama
button1.when_pressed = button1_pressed
button2.when_pressed = button2_pressed

print("6 haneli sayıyı oluşturmak için butonlara basın...")
pause()
