import threading
from bin.bin_simulator import BinSimulator
from mqtt.central_station import CentralStation

if __name__ == "__main__":
    sim_thread = threading.Thread(target=lambda: BinSimulator().run())
    sim_thread.start()

    CentralStation().run()
