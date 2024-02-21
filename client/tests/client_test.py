import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
from client import ClientApp
from PyQt5.QtWidgets import QApplication, QWidget

class TestClient(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
    @patch('client.pika.BlockingConnection')
    def test_init(self, mock_blocking_connection):
        client = ClientApp()
        self.assertIsNotNone(client.connection)
        self.assertIsNotNone(client.channel)
        self.assertIsNone(client.response)
        self.assertIsNone(client.id)

    @patch('client.pika')
    def test_call(self,mock_pika):
        client = ClientApp()
        client.input.setText('10')
        client.call()
        mock_pika.BlockingConnection.assert_called_once()
        mock_pika.BlockingConnection.return_value.channel.assert_called_once()
        mock_pika.BlockingConnection.return_value.channel.return_value.basic_publish.assert_called_once()

    @patch('client.protocol_pb2.Response')
    def test_on_response(self, mock_response):
        client = ClientApp()
        mock_response.return_value = MagicMock(res = 20)
        client.id = '123'
        client.on_response(None, None, MagicMock(correlation_id='123'), b'')
        self.assertEqual(client.response.res, 20)
        self.assertEqual(client.response_label.text(), "Result: 20")

if __name__ == '__main__':
    unittest.main()