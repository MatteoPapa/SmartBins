import time
from bin.bin import Bin
from mqtt.mqtt_client import setup_mqtt_client
from config import SLEEP_TIME, N_BINS

class BinSimulator:
    def __init__(self):
        self.bins = [Bin(bin_id=i) for i in range(N_BINS)]
        self.client = setup_mqtt_client("bin_simulator")
        for b in self.bins:
            b.subscribe_to_collect(self.client)
        self.client.loop_start()
    
    def run(self):
        while True:
            for b in self.bins:
                b.step(self.client)
            time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    sim = BinSimulator()
    sim.run()
