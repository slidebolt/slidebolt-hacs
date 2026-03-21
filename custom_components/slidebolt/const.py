"""Constants for Slidebolt."""

DOMAIN = "slidebolt"
DEFAULT_PORT = 39444

PLATFORMS = [
    "alarm_control_panel",
    "binary_sensor",
    "button",
    "camera",
    "climate",
    "cover",
    "event",
    "fan",
    "humidifier",
    "light",
    "lock",
    "media_player",
    "number",
    "remote",
    "select",
    "sensor",
    "siren",
    "switch",
    "text",
    "valve",
]

SIGNAL_ENTITY_UPDATED = f"{DOMAIN}_entity_updated"
SIGNAL_ENTITY_ADDED = f"{DOMAIN}_entity_added"
SIGNAL_ENTITY_REMOVED = f"{DOMAIN}_entity_removed"
