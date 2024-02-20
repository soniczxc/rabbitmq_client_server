import unittest
from unittest.mock import patch, MagicMock
from server import on_request

class TestServer(unittest.TestCase):

    @patch('server.pika')
    @patch('server.protocol_pb2.Response')
    @patch('server.protocol_pb2.Request')
    def test_on_request(self, mock_request, mock_response, mock_pika):
        mock_method = MagicMock()
        mock_props = MagicMock(reply_to='reply_queue', correlation_id='correlation_id')
        mock_body = b'some_request_body'
        mock_channel = MagicMock()

        mock_request_instance = mock_request.return_value
        mock_request_instance.id = 'request_id'
        mock_request_instance.req = 10
        mock_request_instance.SerializeToString.return_value = b'serialized_request'

        mock_response_instance = mock_response.return_value
        mock_response_instance.SerializeToString.return_value = b'serialized_response'

        on_request(mock_channel, mock_method, mock_props, mock_body)

        mock_request.assert_called_once()
        mock_request_instance.ParseFromString.assert_called_once_with(mock_body)
        mock_response.assert_called_once()
        mock_response_instance.id = 'request_id'
        mock_response_instance.res = 20
        mock_response_instance.SerializeToString.assert_called_once()
        mock_pika.BasicProperties.assert_called_once_with(correlation_id='correlation_id')
        mock_channel.basic_publish.assert_called_once_with(
            exchange='',
            routing_key='reply_queue',
            properties=mock_pika.BasicProperties(),
            body=b'serialized_response'
        )


if __name__ == '__main__':
    unittest.main()