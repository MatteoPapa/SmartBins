import paho.mqtt.client as mqtt
from config import BROKER_ADDRESS, MQTT_PORT

def setup_mqtt_client(client_id: str) -> mqtt.Client:
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    client.connect(BROKER_ADDRESS, MQTT_PORT)
    return client
