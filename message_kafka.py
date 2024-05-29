from confluent_kafka import Producer
import socket

def send_message():
    conf = {'bootstrap.servers': "171.244.60.109:29092",
            'client.id': socket.gethostname()}
    producer = Producer(conf)
    producer.produce(topic = 'AI-notifications', key="notification", value="successful create article")
    producer.flush() 

send_message()