# SmartBins

<img width="1900" height="1013" alt="Schermata del 2025-08-20 10-41-53" src="https://github.com/user-attachments/assets/f2139d56-f0ed-4667-9ec1-ceebabfc5677" />

Simulation-based optimization of waste collection with an IoT network of **smart bins**.  
Bins publish fill levels over MQTT; a **Central Station** applies an **MDP policy** (precomputed via value iteration) to decide when to collect. A lightweight **web dashboard** shows live bin status.

## Architecture

- **Bin Simulator** (`bin_simulator.py`, `bin.py`)  
  Simulates `N_BINS`, each increasing its fill level randomly and publishing:
  - `bins/bin{ID}/fill_level`
  - listens on `bins/bin{ID}/collect` to reset to 0

- **Central Station** (`central_station.py`)  
  - Subscribes to all fill-level updates, discretizes state (10%), anduses **MDP policy** loaded from `mdp/policy.pkl`
  - Publishes `collect` commands and (optionally) logs results to CSV.

- **MQTT Broker** (Mosquitto)  
  - TCP: `1883` (Python clients)  
  - WebSockets: `9001` (dashboard)

- **Web Dashboard** (`/dashboard/index.html`)  
  Simple HTML/JS using MQTT over WebSockets for live visualization.

## Requirements

- Docker & Docker Compose  
- Python 3.9+ (to run simulator, central station, analysis scripts)

## Quick Start (Docker services)

```bash
# 1) Start broker + central station + dashboard
docker compose up -d

# 2) (Optional) Watch logs
docker compose logs -f
```

> If you get “address already in use” on `1883`, you probably have a local Mosquitto running.  
> Stop it (`sudo systemctl stop mosquitto`) **or** edit `docker-compose.yml` to map a different host port, e.g. `1884:1883`, and set `MQTT_PORT=1884` for the Central Station / simulator.

## Run the Simulator (host)

```bash
# In another terminal
python3 bin_simulator.py
```

> Ensure your simulator points to the broker:
> - If running **on host**, set `BROKER_ADDRESS=localhost` in `config.py`.
> - If running **in Docker**, use `BROKER_ADDRESS=mqtt-broker`.

## Central Station (policy choice)

By default, `central_station.py` loads `mdp/policy.pkl`.  
If you added the minimal logging/policy toggle as discussed, you can switch:

```python
# central_station.py (at the bottom)
station = CentralStation(use_mdp=True)   # MDP
# station = CentralStation(use_mdp=False)  # Threshold (80%)
```

Run it:

```bash
python3 central_station.py
```

This writes CSV logs like:
```
results_mdp_YYYYmmdd_HHMMSS.csv
results_threshold_YYYYmmdd_HHMMSS.csv
```

Columns: `t, bin_states, action, step_cost, total_cost`.

## Build / Rebuild the MDP Policy

If you want to recompute the policy:

```bash
python3 mdp/policy_solver.py
# Produces mdp/policy.pkl
```

## Web Dashboard

Open:
```
http://localhost:8080
```
It connects to Mosquitto via WebSockets on `ws://localhost:9001`.


## Troubleshooting

- **Port 1883 busy**: stop local Mosquitto or remap to `1884:1883` and set `MQTT_PORT=1884`.
- **No dashboard updates**: ensure `9001` is exposed and the dashboard is pointing to the right WS URL.
- **Simulator not connecting**: verify `BROKER_ADDRESS`/`MQTT_PORT` in `config.py`.
