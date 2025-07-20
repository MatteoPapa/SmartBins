import threading
from bin.bin_simulator import BinSimulator
from mqtt.central_station import CentralStation

if __name__ == "__main__":
    # Avvia simulatore cassonetti in un thread separato
    sim_thread = threading.Thread(target=lambda: BinSimulator().run())
    sim_thread.start()

    # Avvia la stazione centrale (bloccante)
    CentralStation().run()
