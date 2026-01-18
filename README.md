# Green Energy Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/your-org/ha-green-energy.svg)](https://github.com/your-org/ha-green-energy/releases)

A Home Assistant integration that syncs your energy data with the Green Energy cloud service for optimization recommendations and savings tracking.

## Features

- **Automatic Data Sync**: Monitors your solar, battery, and grid sensors and uploads readings to the cloud
- **Optimization Recommendations**: Receive real-time advice on when to charge/discharge batteries
- **Savings Tracking**: Track your estimated savings from following optimization recommendations
- **Tariff Rate Display**: See your current electricity tariff rate

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click "Integrations"
3. Click the menu (three dots) and select "Custom repositories"
4. Add `https://github.com/your-org/ha-green-energy` as an Integration
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/your-org/ha-green-energy/releases)
2. Extract the `green_energy` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Prerequisites

1. Create an account at [Green Energy](https://your-app.com)
2. Configure your Octopus Energy account (optional but recommended for tariff data)

### Setup

1. Go to Settings → Devices & Services → Add Integration
2. Search for "Green Energy"
3. Generate a pairing code from your [Green Energy dashboard](https://your-app.com/settings/integrations)
4. Enter the pairing code
5. Select which energy sensors to monitor:
   - **Solar Power Sensor**: Your solar panel power output sensor
   - **Battery State Sensor**: Your battery state of charge or power sensor
   - **Grid Power Sensor**: Your grid import/export power sensor
6. Set your preferred sync interval (default: 60 seconds)

## Entities

The integration creates the following entities:

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.green_energy_sync_status` | Current sync status (synced/syncing/error) |
| `sensor.green_energy_last_sync` | Timestamp of last successful sync |
| `sensor.green_energy_readings_today` | Number of readings uploaded today |
| `sensor.green_energy_recommendation` | Current optimization recommendation |
| `sensor.green_energy_savings_today` | Estimated savings today (GBP) |
| `sensor.green_energy_tariff_rate` | Current tariff rate (p/kWh) |

### Binary Sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.green_energy_connected` | Cloud connection status |

## Automations

Use the recommendation sensor in automations:

```yaml
automation:
  - alias: "Battery Charge on Low Rates"
    trigger:
      - platform: state
        entity_id: sensor.green_energy_recommendation
        to: "charge_battery"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.battery_charging
```

## Troubleshooting

### Invalid Pairing Code
- Pairing codes expire after 10 minutes
- Generate a new code from the web dashboard

### Cannot Connect
- Check your internet connection
- Verify the Green Energy service is online

### No Recommendations
- Ensure you have configured monitored sensors
- Wait for the first sync cycle to complete

## Support

- [Report an Issue](https://github.com/your-org/ha-green-energy/issues)
- [Documentation](https://your-app.com/docs/home-assistant)

## License

MIT License - see [LICENSE](LICENSE) for details.
