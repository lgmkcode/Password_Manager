import unittest
from unittest.mock import Mock, patch
from gpiozero.pins.mock import MockFactory
from gpiozero import Device
from Button_Manager import PinReader, BUTTON_PINS, MAX_LENGTH, MQTT_TOPIC, BROKER_IP, BROKER_PORT

class TestPinReader(unittest.TestCase):
    def setUp(self):
        # GPIO mock settings
        Device.pin_factory = MockFactory()
        # Create the object to be tested
        self.pin_reader = PinReader()
        # Mock the MQTT client
        self.mock_mqtt = Mock()
        self.pin_reader.client = self.mock_mqtt

    def test_button_pressed_single(self):
        """Test single button press"""
        self.pin_reader.button_pressed("1")
        self.assertEqual(self.pin_reader.input_sequence, "1")
        # MQTT publish function should not be called yet
        self.mock_mqtt.publish.assert_not_called()

    def test_button_pressed_max_length(self):
        """Test input with maximum length"""
        test_sequence = "1234"
        for digit in test_sequence:
            self.pin_reader.button_pressed(digit)
        # Input sequence should be cleared
        self.assertEqual(self.pin_reader.input_sequence, "")
        # MQTT publish should be called with correct parameters
        self.mock_mqtt.publish.assert_called_once_with(MQTT_TOPIC, test_sequence)

    def test_button_pressed_overflow(self):
        """Test input exceeding maximum length"""
        # First 4 digits
        for digit in "1234":
            self.pin_reader.button_pressed(digit)
        # 5th digit
        self.pin_reader.button_pressed("5")
        
        # MQTT publish should be called only once and contain the first 4 digits
        self.mock_mqtt.publish.assert_called_once_with(MQTT_TOPIC, "1234")
        
        # Input sequence should start with the 5th digit
        self.assertEqual(self.pin_reader.input_sequence, "5")

    @patch('paho.mqtt.client.Client')
    def test_setup_mqtt_success(self, mock_mqtt_client):
        """Test successful MQTT connection"""
        # Configure the connect method of the mock MQTT client
        mock_client_instance = Mock()
        mock_client_instance.connect.return_value = 0
        mock_mqtt_client.return_value = mock_client_instance
        # Test MQTT setup
        pin_reader = PinReader()
        result = pin_reader.setup_mqtt()
        # Assertions
        self.assertTrue(result)
        mock_client_instance.connect.assert_called_once_with(BROKER_IP, BROKER_PORT, 60)

    @patch('paho.mqtt.client.Client')
    def test_setup_mqtt_failure(self, mock_mqtt_client):
        """Test failed MQTT connection"""
        # Configure the connect method of the mock MQTT client
        mock_client_instance = Mock()
        mock_client_instance.connect.return_value = 1  # Connection error
        mock_mqtt_client.return_value = mock_client_instance
        # Test MQTT setup
        pin_reader = PinReader()
        result = pin_reader.setup_mqtt()
        # Assertions
        self.assertFalse(result)
        mock_client_instance.connect.assert_called_once_with(BROKER_IP, BROKER_PORT, 60)

    def test_setup_buttons(self):
        """Test button setup"""
        self.pin_reader.setup_buttons()
        # Correct number of buttons should be created
        self.assertEqual(len(self.pin_reader.buttons), len(BUTTON_PINS))
        # when_pressed callback should be set for each button
        for button in self.pin_reader.buttons:
            self.assertIsNotNone(button.when_pressed)

if __name__ == '__main__':
    unittest.main()
