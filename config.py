import os
import socket

def _env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


# Naming server settings.
NAMING_SERVER_HOST = os.getenv("NAMING_SERVER_HOST", os.getenv("NAMESERVER_HOST", "localhost"))
NAMING_SERVER_PORT = _env_int("NAMING_SERVER_PORT", _env_int("NAMESERVER_PORT", 5050))
NAMING_SERVER_BIND_HOST = os.getenv("NAMING_SERVER_BIND_HOST", "0.0.0.0")

# Monitoring server settings.
MONITORING_SERVER_BIND_HOST = os.getenv("MONITORING_SERVER_BIND_HOST", "0.0.0.0")
MONITORING_SERVER_PORT = _env_int("MONITORING_SERVER_PORT", 6060)
MONITORING_SERVER_ADVERTISE_HOST = os.getenv(
    "MONITORING_SERVER_ADVERTISE_HOST",
    socket.gethostbyname(socket.gethostname()),
)

# Sensor test settings.
SENSOR_DELAY_BY_ID = {
    "SensorB": 2,
    "SensorC": 3,
    "SensorD": 4,
    "SensorE": 5,
}
