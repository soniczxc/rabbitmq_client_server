import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
from client.rabbitmq_client.client import ClientApp, SettingsDialog
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel

class TestClient(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])

    @patch('client.open')
    def test_save_settings(self, mock_open):
        dialog = SettingsDialog()
        dialog.rabbitmq_host_input.setText('new_host')
        dialog.rabbitmq_port_input.setText('5678')
        dialog.queue_request_name_input.setText('new_queue')
        dialog.time_limit_input.setText('30')
        dialog.logger_level_input.setText('DEBUG')
        dialog.logger_file_input.setText('new_log_file.txt')

        dialog.save_settings()

        mock_open.assert_called_once_with('client_config.ini', 'w')
        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(
            "[RabbitMQ]\nhost = new_host\nport = 5678\nqueue_request = new_queue\ntime_limit = 30\n\n[Logging]\nlevel = DEBUG\nfile = new_log_file.txt\n"
        )

    @patch('client.pika.BlockingConnection')
    def test_init(self, mock_blocking_connection):
        client = ClientApp()
        self.assertIsNotNone(client.connection)
        self.assertIsNotNone(client.channel)
        self.assertIsNone(client.response)
        self.assertIsNone(client.id)

    @patch('client.pika')
    def test_call(self, mock_pika):
        client = ClientApp()
        client.input = QLineEdit()
        client.input.setText('10')
        client.button = QPushButton()
        client.call()
        mock_pika.BlockingConnection.assert_called_once()
        mock_pika.BlockingConnection.return_value.channel.assert_called_once()
        mock_pika.BlockingConnection.return_value.channel.return_value.basic_publish.assert_called_once()

    @patch('client.protocol_pb2.Response')
    def test_on_response(self, mock_response):
        client = ClientApp()
        mock_response.return_value = MagicMock(res=20)
        client.id = '123'
        client.response_label = QLabel()
        client.on_response(None, None, MagicMock(correlation_id='123'), b'')
        self.assertEqual(client.response.res, 20)
        self.assertEqual(client.response_label.text(), "Result: 20")

    def test_open_settings(self):
        client = ClientApp()
        client.response_label = QLabel()
        client.open_settings()
        self.assertEqual(client.response_label.text(), "Настройки сохранены")

if __name__ == '__main__':
    unittest.main()
