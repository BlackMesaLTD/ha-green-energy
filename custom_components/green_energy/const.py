"""Constants for Green Energy integration."""
from typing import Final

DOMAIN: Final = "green_energy"
VERSION: Final = "1.0.0"

# Config entry keys
CONF_PAIRING_CODE: Final = "pairing_code"
CONF_TOKEN: Final = "api_token"
CONF_INSTANCE_ID: Final = "instance_id"
CONF_USER_EMAIL: Final = "user_email"

# Options keys
CONF_SOLAR_ENTITY: Final = "solar_entity"
CONF_BATTERY_ENTITY: Final = "battery_entity"
CONF_GRID_ENTITY: Final = "grid_entity"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# API
DEFAULT_API_URL: Final = "https://green-energy-topaz.vercel.app"
API_TIMEOUT: Final = 30

# Defaults
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds
MIN_SCAN_INTERVAL: Final = 30
MAX_SCAN_INTERVAL: Final = 3600

# Platforms
PLATFORMS: Final = ["sensor", "binary_sensor"]
