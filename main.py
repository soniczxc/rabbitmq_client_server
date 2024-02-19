import pika
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
import protocol_pb2
import uuid

class Client(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self.on_response, auto_ack=True)

        self.response = None
        self.corr_id = None

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

        self.setLayout(layout)
        self.setWindowTitle('Client')
        self.show()

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            response = protocol_pb2.Response()
            response.ParseFromString(body)
            self.response = response
            self.response_label.setText(f"Response: {self.response.res}")

    def call(self):
        try:
            request = protocol_pb2.Request()
            request.id = str(uuid.uuid4())
            request.req = int(self.input.text())
            self.response = None
            self.corr_id = request.id

            self.channel.basic_publish(exchange='',
                                       routing_key='rpc_queue',
                                       properties=pika.BasicProperties(reply_to=self.callback_queue,
                                                                       correlation_id=request.id),
                                       body=request.SerializeToString())
            self.connection.process_data_events(time_limit=None)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    client_window = Client()

    sys.exit(app.exec_())
