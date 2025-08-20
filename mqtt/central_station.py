import paho.mqtt.client as mqtt
from config import BROKER_ADDRESS, MQTT_PORT, MQTT_BASE_TOPIC, N_BINS
import pickle
import csv, time

# --- Cost constants ---
COLLECTION_COST = 1.0
OVERFLOW_PENALTY = 10.0
OVERFLOW_THRESHOLD = 95

class CentralStation:
    def __init__(self, policy_type="threshold"):
        self.client = mqtt.Client(client_id=f"central_station_{policy_type}", protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.bin_states = {f"bin{i}": 0 for i in range(N_BINS)}
        self.policy_type = policy_type
        self.policy = None
        if self.policy_type == "mdp":
            with open("mdp/policy.pkl", "rb") as f:
                self.policy = pickle.load(f)

        # stats
        self.total_cost = 0.0
        self.collections = 0
        self.overflows = 0

        # CSV logging setup
        self.start_time = time.time()
        self.csvfile = open(f"results_{self.policy_type}.csv", "w", newline="")
        self.writer = csv.writer(self.csvfile)
        self.writer.writerow(["t", "bin_states", "action", "step_cost", "total_cost"])

    def on_connect(self, client, userdata, flags, rc):
        print("CentralStation connected to the broker.")
        self.client.subscribe(f"{MQTT_BASE_TOPIC}/+/fill_level")

    def on_message(self, client, userdata, msg):
        topic_parts = msg.topic.split("/")
        bin_id = topic_parts[1]
        level = int(msg.payload.decode())
        self.bin_states[bin_id] = level  

        # --- decide action ---
        if self.policy_type == "mdp":
            discretized_state = tuple(
                round(self.bin_states[f"bin{i}"] / 10) * 10 for i in range(N_BINS)
            )
            action = self.policy.get(discretized_state, "wait")
        else:  # threshold policy
            # collect the first bin above 80%
            over = [b for b,l in self.bin_states.items() if l > 80]
            action = f"collect_{over[0].replace('bin','')}" if over else "wait"

        step_cost = 0.0
        collected_bin = None

        # collect action
        if action.startswith("collect"):
            bin_index = int(action.split("_")[1])
            collected_bin = f"bin{bin_index}"
            self.send_collect_command(collected_bin)
            self.bin_states[collected_bin] = 0
            self.collections += 1
            step_cost += COLLECTION_COST

        # overflow penalties
        for b, l in self.bin_states.items():
            if l > OVERFLOW_THRESHOLD:
                step_cost += OVERFLOW_PENALTY
                self.overflows += 1

        # update totals
        self.total_cost += step_cost

        # log row
        elapsed = round(time.time() - self.start_time, 2)
        self.writer.writerow([elapsed, dict(self.bin_states), action, step_cost, self.total_cost])

        self.display_status(action, step_cost)

    def display_status(self, action, step_cost):
        print("New SmartBins Status:")
        for bin_id, level in self.bin_states.items():
            print(f"  {bin_id}: {level}%")
        print(f"Action: {action}, step_cost={step_cost}, total_cost={self.total_cost}")
        print("-" * 30)

    def send_collect_command(self, bin_id):
        topic = f"{MQTT_BASE_TOPIC}/{bin_id}/collect"
        self.client.publish(topic, "collect")
        print(f"Sent collect command to {bin_id}")

    def run(self, duration=900):
        self.client.connect(BROKER_ADDRESS, MQTT_PORT)
        self.client.loop_start()
        time.sleep(duration)  # run for N seconds
        self.client.loop_stop()
        self.client.disconnect()
        self.csvfile.close()
        print(f"Finished {self.policy_type} run: collections={self.collections}, overflows={self.overflows}, total_cost={self.total_cost}")

if __name__ == "__main__":
    # switch between "mdp" and "threshold"
    station = CentralStation(policy_type="threshold")
    station.run(duration=900)   # run for 15 minutes
