import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from client.rabbitmq_client.client import ClientApp, RequestTab


class TestRequestTab(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
        self.tab = RequestTab()

    def tearDown(self):
        self.app.quit()

    @patch('client.rabbitmq_client.client.pika.BlockingConnection')
    def test_initUI(self, mock_pika):
        window = ClientApp()
        self.assertIsNotNone(self.tab.label)
        self.assertIsNotNone(self.tab.input)
        self.assertIsNotNone(self.tab.button)
        self.assertIsNotNone(self.tab.response_label)
        self.assertIsNotNone(self.tab.settings_button)
        self.assertIsInstance(window.request_tab, RequestTab)

    @patch('client.rabbitmq_client.client.SettingsDialog.exec_', return_value=True)
    def test_open_settings(self, mock_exec):
        self.tab.open_settings()
        self.assertEqual(self.tab.response_label.text(), "Настройки сохранены")


    @patch('client.rabbitmq_client.client.pika.BlockingConnection')
    def test_call(self, mock_pika):
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_pika.return_value = mock_connection
        self.tab.input.setText("10")
        self.tab.call()
        mock_connection.close()
        mock_channel.close()
if __name__ == '__main__':
    unittest.main()
