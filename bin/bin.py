import random
from config import MAX_FILL, MAX_INCREMENT, MQTT_BASE_TOPIC

class Bin:
    def __init__(self, bin_id: int):
        self.id = bin_id
        self.max_fill = MAX_FILL
        self.max_increment = MAX_INCREMENT
        self.fill = 0 

    def step(self, mqtt_client=None):
        increment = random.randint(0, self.max_increment)
        if increment > 0:
            self.fill = min(self.fill + increment, self.max_fill)
            if mqtt_client:
                self.publish_fill_level(mqtt_client)

    def subscribe_to_collect(self, mqtt_client):
        topic = f"{MQTT_BASE_TOPIC}/bin{self.id}/collect"

        def on_collect(client, userdata, msg):
            self.collect(mqtt_client)

        mqtt_client.message_callback_add(topic, on_collect)
        mqtt_client.subscribe(topic)

    def collect(self, mqtt_client=None):
        self.fill = 0
        if mqtt_client:
            self.publish_fill_level(mqtt_client)

    def get_fill_level(self) -> int:
        return self.fill

    def publish_fill_level(self, mqtt_client):
        topic = f"{MQTT_BASE_TOPIC}/bin{self.id}/fill_level"
        mqtt_client.publish(topic, str(self.fill))

    def __str__(self):
        return f"Bin {self.id}: {self.fill}%"
