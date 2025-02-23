import unittest
from unittest.mock import Mock, patch
from gpiozero.pins.mock import MockFactory
from gpiozero import Device

from Button_Manager import PinReader, BUTTON_PINS, MAX_LENGTH, MQTT_TOPIC, BROKER_IP, BROKER_PORT

class TestPinReader(unittest.TestCase):
    def setUp(self):
        # GPIO mock ayarları
        Device.pin_factory = MockFactory()
        # Test edilecek nesneyi oluştur
        self.pin_reader = PinReader()
        # MQTT client'ı mockla
        self.mock_mqtt = Mock()
        self.pin_reader.client = self.mock_mqtt

    def test_button_pressed_single(self):
        """Tek buton basışını test et"""
        self.pin_reader.button_pressed("1")
        self.assertEqual(self.pin_reader.input_sequence, "1")
        # MQTT publish fonksiyonu henüz çağrılmamalı
        self.mock_mqtt.publish.assert_not_called()

    def test_button_pressed_max_length(self):
        """Maximum uzunlukta girdi testi"""
        test_sequence = "1234"
        for digit in test_sequence:
            self.pin_reader.button_pressed(digit)
        # Input sequence temizlenmeli
        self.assertEqual(self.pin_reader.input_sequence, "")
        # MQTT publish doğru parametrelerle çağrılmalı
        self.mock_mqtt.publish.assert_called_once_with(MQTT_TOPIC, test_sequence)

    def test_button_pressed_overflow(self):
        """Maximum uzunluktan fazla girdi testi"""
        # İlk 4 rakam
        for digit in "1234":
            self.pin_reader.button_pressed(digit)
        # 5. rakam
        self.pin_reader.button_pressed("5")
        
        # MQTT publish sadece bir kez çağrılmalı ve ilk 4 rakamı içermeli
        self.mock_mqtt.publish.assert_called_once_with(MQTT_TOPIC, "1234")
        
        # Input sequence 5. rakamdan başlamalı
        self.assertEqual(self.pin_reader.input_sequence, "5")

    @patch('paho.mqtt.client.Client')
    def test_setup_mqtt_success(self, mock_mqtt_client):
        """Başarılı MQTT bağlantı testi"""
        # Mock MQTT client'ın connect metodunu configure et
        mock_client_instance = Mock()
        mock_client_instance.connect.return_value = 0
        mock_mqtt_client.return_value = mock_client_instance
        # MQTT kurulumunu test et
        pin_reader = PinReader()
        result = pin_reader.setup_mqtt()
        # Assertions
        self.assertTrue(result)
        mock_client_instance.connect.assert_called_once_with(BROKER_IP, BROKER_PORT, 60)

    @patch('paho.mqtt.client.Client')
    def test_setup_mqtt_failure(self, mock_mqtt_client):
        """Başarısız MQTT bağlantı testi"""
        # Mock MQTT client'ın connect metodunu configure et
        mock_client_instance = Mock()
        mock_client_instance.connect.return_value = 1  # Bağlantı hatası
        mock_mqtt_client.return_value = mock_client_instance
        # MQTT kurulumunu test et
        pin_reader = PinReader()
        result = pin_reader.setup_mqtt()
        # Assertions
        self.assertFalse(result)
        mock_client_instance.connect.assert_called_once_with(BROKER_IP, BROKER_PORT, 60)

    def test_setup_buttons(self):
        """Buton kurulum testi"""
        self.pin_reader.setup_buttons()
        # Doğru sayıda buton oluşturulmalı
        self.assertEqual(len(self.pin_reader.buttons), len(BUTTON_PINS))
        # Her buton için when_pressed callback'i ayarlanmalı
        for button in self.pin_reader.buttons:
            self.assertIsNotNone(button.when_pressed)

if __name__ == '__main__':
    unittest.main()
