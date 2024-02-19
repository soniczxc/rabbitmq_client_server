import pika
from proto import protocol_pb2
import configparser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('server_config.ini')

RABBITMQ_HOST = config.get('RabbitMQ', 'host')
RABBITMQ_PORT = int(config.get('RabbitMQ', 'port'))
QUEUE_REQUEST_NAME = config.get('RabbitMQ', 'queue_request')


LOG_LEVEL = config.get('Logging', 'level')
LOG_FILE = config.get('Logging', 'file')

logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
channel = connection.channel()
channel.queue_declare(queue=QUEUE_REQUEST_NAME)

def on_request(ch, method, props, body):
    request = protocol_pb2.Request()
    request.ParseFromString(body)
    logger.info(f"Received request from client: {request.req}")
    response = protocol_pb2.Response()
    response.id = request.id
    response.res = request.req * 2
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=response.SerializeToString())
    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info(f"Sent response to client: {response.res}")

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=QUEUE_REQUEST_NAME, on_message_callback=on_request)

print(" [x] Awaiting RPC requests")
channel.start_consuming()
