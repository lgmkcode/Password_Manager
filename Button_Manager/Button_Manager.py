"""

Raspberry Pi PIN Reading and MQTT Sending System
------------------------------------------------
This program reads a 4-digit PIN code from physical buttons on the Raspberry Pi
and sends this code to an MQTT broker.
Features:
- Uses 4 physical buttons (GPIO pins: 16, 26, 6, 5)
- Each button represents a digit (1, 2, 3, 4 respectively)
- A maximum 4-digit PIN code can be created
- The created PIN code is automatically sent to the MQTT broker
- Bounce time prevents noise in button readings
Usage:
1. When the program starts, it connects to the MQTT broker
2. The user creates a 4-digit PIN code by pressing physical buttons
3. When all 4 digits are completed, the code is automatically sent to the MQTT broker
4. After the PIN code is sent, the system is ready for a new PIN code
Requirements:
- gpiozero library
- paho-mqtt library
- A running MQTT broker (default port: 9999)

"""

from gpiozero import Button
from signal import pause
import sys
import paho.mqtt.client as paho

# Sabit değişkenler
BROKER_IP = "192.168.207.93"
BROKER_PORT = 9999
MAX_LENGTH = 4
MQTT_TOPIC = "pin"
BUTTON_PINS = {16: "1", 26: "2", 6: "3", 5: "4"}

class PinReader:
    def __init__(self):
        self.input_sequence = ""
        self.buttons = []
        self.client = None
    
    def button_pressed(self, value):
        if len(self.input_sequence) < MAX_LENGTH:
            self.input_sequence += value
            if len(self.input_sequence) == MAX_LENGTH:
                self.finalize_input()
    
    def finalize_input(self):
        print(f"Final input: {self.input_sequence}")
        self.client.publish(MQTT_TOPIC, self.input_sequence)
        self.input_sequence = ""
    
    def setup_mqtt(self):
        self.client = paho.Client()
        if self.client.connect(BROKER_IP, BROKER_PORT, 60) != 0:
            print("Couldn't connect to the MQTT broker")
            return False
        return True
    
    def setup_buttons(self):
        for pin, value in BUTTON_PINS.items():
            button = Button(pin, pull_up=True, bounce_time=0.15)
            button.when_pressed = lambda v=value: self.button_pressed(v)
            self.buttons.append(button)

def main():
    # Create PIN reader object
    pin_reader = PinReader()
    
    # Set up MQTT connection
    if not pin_reader.setup_mqtt():
        sys.exit(1)
    
    # Set up buttons
    pin_reader.setup_buttons()
    
    # Inform the user
    print("Press the buttons to create a 4-digit number...")
    
    # Keep the program running
    try:
        pause()
    except KeyboardInterrupt:
        print("\nProgram is terminating...")
        sys.exit(0)
if __name__ == "__main__":
    main()
