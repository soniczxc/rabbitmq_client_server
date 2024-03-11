import sys
import configparser
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTabWidget, QDialog
import pika
from proto import protocol_pb2
import uuid

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('/home/vova/PycharmProjects/rabbitmq_client_server/client/rabbitmq_client/client_config.ini')

RABBITMQ_HOST = config.get('RabbitMQ', 'host')
RABBITMQ_PORT = int(config.get('RabbitMQ', 'port'))
QUEUE_REQUEST_NAME = config.get('RabbitMQ', 'queue_request')
TIME_LIMIT = int(config.get('RabbitMQ', 'time_limit'))

LOG_LEVEL = config.get('Logging', 'level')
LOG_FILE = config.get('Logging', 'file')

logging.basicConfig(filename=LOG_FILE, encoding='utf-8', level=LOG_LEVEL.upper(), filemode='w')


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Settings')
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel('RabbitMQ Host:'))
        self.rabbitmq_host_input = QLineEdit(RABBITMQ_HOST)
        layout.addWidget(self.rabbitmq_host_input)

        layout.addWidget(QLabel('RabbitMQ Port:'))
        self.rabbitmq_port_input = QLineEdit(str(RABBITMQ_PORT))
        layout.addWidget(self.rabbitmq_port_input)

        layout.addWidget(QLabel('Queue Request Name:'))
        self.queue_request_name_input = QLineEdit(QUEUE_REQUEST_NAME)
        layout.addWidget(self.queue_request_name_input)

        layout.addWidget(QLabel('Time Limit:'))
        self.time_limit_input = QLineEdit(str(TIME_LIMIT))
        layout.addWidget(self.time_limit_input)

        layout.addWidget(QLabel('Logger Level:'))
        self.logger_level_input = QLineEdit(LOG_LEVEL)
        layout.addWidget(self.logger_level_input)

        layout.addWidget(QLabel('Logger File:'))
        self.logger_file_input = QLineEdit(LOG_FILE)
        layout.addWidget(self.logger_file_input)

        self.save_button = QPushButton('Save Settings')
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_settings(self):
        config['RabbitMQ']['host'] = self.rabbitmq_host_input.text()
        config['RabbitMQ']['port'] = self.rabbitmq_port_input.text()
        config['RabbitMQ']['queue_request'] = self.queue_request_name_input.text()
        config['RabbitMQ']['time_limit'] = self.time_limit_input.text()
        config['Logging']['level'] = self.logger_level_input.text()
        config['Logging']['file'] = self.logger_file_input.text()

        with open('client_config.ini', 'w') as configfile:
            config.write(configfile)
        self.accept()


class RequestTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue=QUEUE_REQUEST_NAME)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self.on_response, auto_ack=True)
        self.response = None
        self.id = str(uuid.uuid4())

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel('Enter a number:')
        layout.addWidget(self.label)

        self.input = QLineEdit()
        layout.addWidget(self.input)

        self.button = QPushButton('Send Request')
        self.button.clicked.connect(self.call)
        layout.addWidget(self.button)

        self.response_label = QLabel('Result:')
        layout.addWidget(self.response_label)

        self.settings_button = QPushButton('Settings')
        self.settings_button.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_button)

        self.setLayout(layout)

    def on_response(self, ch, method, props, body):
        if self.id == props.correlation_id:

            response = protocol_pb2.Response()
            response.ParseFromString(body)

            self.response = response
            self.response_label.setText(f"Result: {self.response.res}")
            logger.info(f"Received response from server: {response.res}")

    def call(self):
        try:
            request = protocol_pb2.Request()
            request.id = self.id
            request.req = int(self.input.text())
            self.response = None

            self.channel.basic_publish(exchange='',
                                       routing_key=QUEUE_REQUEST_NAME,
                                       properties=pika.BasicProperties(reply_to=self.callback_queue,
                                                                       correlation_id=request.id),
                                       body=request.SerializeToString())
            self.connection.process_data_events(time_limit=TIME_LIMIT)
            logger.info(f"Sent request to server: {request.req}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def open_settings(self):
        dialog = SettingsDialog()
        if dialog.exec_():
            self.response_label.setText(f"Настройки сохранены")
            pass


class ClientApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.request_tab = RequestTab()

        layout.addWidget(self.request_tab)
        self.setLayout(layout)
        self.setWindowTitle('Client')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    client_window = ClientApp()
    client_window.show()
    sys.exit(app.exec_())