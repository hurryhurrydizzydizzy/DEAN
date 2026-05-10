# Decentralized Emergency Alert Network (Lamport Clock)

This project is a small distributed-system simulation with three components:

1. `naming_server.py`: Service registry (register/lookup).
2. `monitoring_server.py`: Receives sensor alerts, computes logical order, and broadcasts emergency updates.
3. `sensor_client.py`: Sends alerts and receives emergency updates.

The system uses Lamport logical clocks to track causal ordering between distributed events.

## Architecture

### System Topology

```
                           ┌──────────────────┐
                           │ NAMING SERVER    │
                           │   (Port 5050)    │
                           └────────┬─────────┘
                                    │
                            (Register/Lookup)
                                    │
                                    ▼
                           ┌──────────────────┐
                           │ MONITORING       │
                           │ SERVER           │
                           │ (Port 6060)      │
                           └────┬─┬─┬─┬───────┘
                                │ │ │ │
                  ┌─────────────┘ │ │ └──────────────┐
                  │               │ │                │
                  ▼               ▼ ▼                ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │  Sensor A   │ │  Sensor B   │ │  Sensor C   │ ...
            │ (no delay)  │ │  (2s delay) │ │  (3s delay) │
            └─────────────┘ └─────────────┘ └─────────────┘
```

### Component Roles

**Naming Server** (Port 5050)
- Service registry for service discovery
- Monitoring Server registers once at startup
- Each sensor looks up address once at startup
- Then sensors connect directly to Monitoring Server

**Monitoring Server** (Port 6060)
- Maintains persistent connections from all sensors
- Receives alert messages from each sensor
- Updates Lamport clock using incoming sensor timestamp
- Tracks and prints event order based on:
  - sensor detection timestamp (`detected_at_ns`) as primary sort key
  - server-observed Lamport time as tie-breaker
- Broadcasts emergency update to all connected sensors

**Sensor Client**
- Discovers Monitoring Server via Naming Server
- Maintains persistent connection to Monitoring Server
- Sends random fire/smoke/heat events
- Uses per-sensor configured delay to simulate network/send delay
- Receives `emergency_update` messages and updates local Lamport clock

### Connection Flow

```
Step 1: Monitoring Server Registers
Monitoring Server → Naming Server (5050)
  Send: {
    "type": "register",
    "name": "monitoring.server.main",
    "host": "127.0.0.1",
    "port": 6060
  }

Step 2: Sensors Lookup Address
Sensor A → Naming Server (5050)
  Send: {"type": "lookup", "name": "monitoring.server.main"}
  Receive: {"host": "127.0.0.1", "port": 6060}

(Sensors B, C, D, E do the same)

Step 3: Sensors Connect to Monitoring Server
All Sensors → Monitoring Server (6060)
  PERSISTENT connection established (stays open)

Step 4: Continuous Alert Loop
Sensor A → Monitoring Server (6060)
  Send: {
    "type": "alert",
    "sensor_id": "SensorA",
    "event": "fire_detected",
    "timestamp": 1,
    "detected_at_ns": 1234567890123456
  }

Step 5: Broadcast Response
Monitoring Server → All Sensors (A, B, C, D, E)
  Send: {
    "type": "emergency_update",
    "status": "confirmed_fire",
    "first_detected_by": "SensorA",
    "lamport_time": 4
  }
```

## Project Files

- `config.py`: Shared configuration and environment variable parsing.
- `lamport.py`: Lamport clock implementation.
- `JSON_MESSAGE_FORMATS.txt`: Example payloads used by services.

## Requirements

- Python 3.9+
- No third-party packages required (standard library only).

## Configuration

All settings are in `config.py` with sensible defaults. For single-machine local runs, just run the scripts as-is.

Sensor delays are pre-configured (SensorB: 2s, SensorC: 3s, SensorD: 4s, SensorE: 5s). Sensors not in `SENSOR_DELAY_BY_ID` send without delay.

## Run Locally (Single Machine)

Open three terminals in project folder.

### Terminal 1: Naming Server
```powershell
python naming_server.py
```

### Terminal 2: Monitoring Server
```powershell
python monitoring_server.py
```

### Terminal 3+: Sensors
```powershell
python sensor_client.py
```

Use different sensor IDs (for example `SensorA`, `SensorB`, `SensorC`, `SensorD`, `SensorE`).

## Run Across Multiple Machines

Example setup:

- Machine A: Naming server
- Machine B: Monitoring server  
- Machine C/D/E: Sensors

All configuration defaults are in `config.py`. For multi-machine deployments, override these env vars:

**On Monitoring Server:**
- `NAMING_SERVER_HOST`: IP/hostname of the naming server machine
- `MONITORING_SERVER_ADVERTISE_HOST`: The monitoring server's reachable IP (auto-detected locally; set explicitly for remote deployments)

**On Sensor Machines:**
- `NAMING_SERVER_HOST`: IP/hostname of the naming server machine

Ensure firewalls allow inbound TCP on ports 5050 (naming) and 6060 (monitoring).

## Troubleshooting

### WinError 10013 on bind
Another process or OS reservation is using your port. Set the port env var (e.g., `NAMING_SERVER_PORT=5051`) before running the server.

### Sensor cannot connect to monitoring server across machines
- Verify `MONITORING_SERVER_ADVERTISE_HOST` points to reachable monitoring host IP.
- Verify naming server has the correct registered host/port.
- Verify firewall rules.

### `name not found` lookup response
Monitoring server likely has not registered yet. Start naming server first, then monitoring server, then sensors.
