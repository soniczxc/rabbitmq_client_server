import unittest
from unittest.mock import MagicMock
from server.reabbitmq_server.server import on_request
from proto import protocol_pb2


class TestServer(unittest.TestCase):
    def test_on_request(self):
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_props = MagicMock()
        mock_props.reply_to = 'reply_queue'
        mock_props.correlation_id = 'correlation_id'

        request = protocol_pb2.Request()
        request.req = 5
        request.id = '123'
        mock_body = request.SerializeToString()

        on_request(mock_channel, mock_method, mock_props, mock_body)

        response = protocol_pb2.Response()
        response.ParseFromString(mock_channel.basic_publish.call_args.kwargs['body'])

        mock_channel.basic_publish.assert_called_once()
        _, kwargs = mock_channel.basic_publish.call_args
        self.assertEqual(kwargs['routing_key'], 'reply_queue')
        self.assertEqual(kwargs['properties'].correlation_id, 'correlation_id')
        self.assertEqual(response.res, 10)
        mock_channel.basic_ack.assert_called_once()


if __name__ == '__main__':
    unittest.main()
