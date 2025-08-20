import paho.mqtt.client as mqtt
from config import BROKER_ADDRESS, MQTT_PORT, MQTT_BASE_TOPIC, N_BINS
import pickle 

class CentralStation:
    def __init__(self):
        self.client = mqtt.Client(client_id="central_station", protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.bin_states = {f"bin{i}": 0 for i in range(N_BINS)}

        # Load policy
        with open("mdp/policy.pkl", "rb") as f:
            self.policy = pickle.load(f)

    def on_connect(self, client, userdata, flags, rc):
        print("CentralStation connected to the broker.")
        self.client.subscribe(f"{MQTT_BASE_TOPIC}/+/fill_level")

    def on_message(self, client, userdata, msg):
        topic_parts = msg.topic.split("/")
        bin_id = topic_parts[1]
        level = int(msg.payload.decode())
        self.bin_states[bin_id] = level  
        
        # Discretize for the policy lookup
        discretized_state = tuple(
            round(self.bin_states[f"bin{i}"] / 10) * 10 for i in range(N_BINS)
        )
        action = self.policy.get(discretized_state, "wait")

        if action.startswith("collect"):
            bin_index = int(action.split("_")[1])
            bin_to_collect = f"bin{bin_index}"
            self.send_collect_command(bin_to_collect)
            self.bin_states[bin_to_collect] = 0  # assume immediate effect

        self.display_status()

    def display_status(self):
        print("New SmartBins Status:")
        for bin_id, level in self.bin_states.items():
            print(f"  {bin_id}: {level}%")
        print("-" * 30)
    
    def send_collect_command(self, bin_id):
        topic = f"{MQTT_BASE_TOPIC}/{bin_id}/collect"
        self.client.publish(topic, "collect")
        print(f"Sent collect command to {bin_id}")

    def run(self):
        self.client.connect(BROKER_ADDRESS, MQTT_PORT)
        self.client.loop_forever()

if __name__ == "__main__":
    station = CentralStation()
    station.run()
