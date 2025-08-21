# Hisense Air Conditioner Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![HACS][hacsbadge]][hacs]

**English** | [中文](README_zh.md)

This integration allows you to control Hisense smart home devices through Home Assistant using the ConnectLife cloud
service.

## Features

- 🌡️ **Climate Control**: Full air conditioner control (temperature, mode, fan speed, swing)
- 💧 **Humidity Management**: Dehumidifier and humidifier control
- 🔥 **Water Heating**: Heat pump and water heater management
- 📊 **Real-time Monitoring**: Temperature, humidity, and energy consumption sensors
- 🏠 **Zone Control**: Multi-zone climate management for compatible systems
- ⚡ **Energy Tracking**: Daily energy consumption monitoring
- 🔧 **Fault Detection**: Real-time error code monitoring and alerts

## Supported Devices

| Device Type                   | Models         | Features                                  |
|-------------------------------|----------------|-------------------------------------------|
| **Split Air Conditioners**    | 009-199 series | Full climate control, energy monitoring   |
| **Window Air Conditioners**   | 008-399 series | Climate control, basic sensors            |
| **Portable Air Conditioners** | 006-299 series | Climate control, mobility features        |
| **Dehumidifiers**             | 007 series     | Humidity control, fan speed management    |
| **Heat Pumps**                | 035-699 series | Heating/cooling, water heating            |
| **Ducted Systems**            | Various        | Zone control, advanced climate management |

## Installation

### Prerequisites

- Home Assistant 2023.1.0 or later
- ConnectLife account with registered devices
- Active internet connection for cloud API access

### Method 1: HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to **Integrations**
3. Click the **Explore & Download Repositories** button
4. Search for "Hisense Air Conditioner"
5. Click **Download**
6. Restart Home Assistant

### Method 2: Manual Installation

1. Download the latest release from [GitHub releases][releases]
2. Extract the archive
3. Copy the `custom_components/hisense_ac_plugin` folder to your Home Assistant `custom_components` directory
4. Restart Home Assistant

## Configuration

### Step 1: Network Configuration (Windows Users)

For proper OAuth2 authentication, you need to configure local DNS resolution:

1. Navigate to `C:\Windows\System32\drivers\etc\`
2. Right-click on the `hosts` file and select "Edit"
3. Change `127.0.0.1` with your Home Assistant instance IP and add the following line :
   ```
   127.0.0.1 homeassistant.local
   ```
4. Save the file

**Note**: This step is required for the OAuth2 redirect to work properly during setup.

### Step 2: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Hisense Air Conditioner"
4. Follow the configuration flow

### Step 3: Authentication

1. Enter your ConnectLife account credentials
2. Complete the OAuth2 authorization process
3. Wait for device discovery to complete

**Important**:

- Disable VPN/proxy services during setup
- Ensure your ConnectLife account has devices registered
- The initial sync may take 1-2 minutes

## Usage

### Climate Control

The integration creates climate entities for each air conditioning unit:

```yaml
# Example automation
automation:
  - alias: "Cool down at night"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      service: climate.set_temperature
      target:
        entity_id: climate.living_room_ac
      data:
        temperature: 24
        hvac_mode: cool
```

### Energy Monitoring

Energy consumption sensors are created automatically:

- `sensor.{device_name}_daily_energy`: Daily energy consumption (kWh)
- `sensor.{device_name}_power`: Current power consumption (W)

### Zone Control

For multi-zone systems, individual zone switches are created:

- `switch.{device_name}_zone_1`: Zone 1 control
- `switch.{device_name}_zone_2`: Zone 2 control

## Entity Types

| Platform         | Description                   | Example Entities                   |
|------------------|-------------------------------|------------------------------------|
| **Climate**      | AC units, heat pumps          | `climate.living_room_ac`           |
| **Sensor**       | Temperature, humidity, energy | `sensor.bedroom_temperature`       |
| **Switch**       | Zones, special functions      | `switch.turbo_mode`                |
| **Number**       | Target values, settings       | `number.display_brightness`        |
| **Humidifier**   | Dehumidifier control          | `humidifier.basement_dehumidifier` |
| **Water Heater** | Hot water systems             | `water_heater.main_unit`           |

## Troubleshooting

### Common Issues

#### Authentication Failed

**Symptom**: Login fails or shows "Invalid credentials"

**Solution**:

- Verify your ConnectLife username and password
- Ensure 2FA is disabled temporarily during setup
- Try logging into the ConnectLife app to verify credentials

#### Device Not Found

**Symptom**: No devices appear after setup

**Solution**:

- Verify devices are online in the ConnectLife app
- Check internet connectivity
- Restart the integration from **Settings** → **Devices & Services**

#### OAuth2 Redirect Error

**Symptom**: "Page not found" after login

**Solution**:

- Ensure the hosts file modification was completed correctly
- Restart your browser
- Disable VPN/proxy services

#### Connection Timeout

**Symptom**: Integration shows "Unavailable" status

**Solution**:

- Check Home Assistant logs for specific error messages
- Verify ConnectLife service status
- Restart Home Assistant

### Debug Logging

To enable debug logging, add this to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.hisense_ac_plugin: debug
```

### Getting Help

1. Check the [Troubleshooting Wiki][wiki]
2. Search existing [GitHub Issues][issues]
3. Create a new issue with:
    - Home Assistant version
    - Integration version
    - Device model
    - Error logs (with sensitive data removed)

### Development Setup

```bash
git clone https://github.com/Connectlife-LLC/HomeAssistantPlugin.git
cd HomeAssistantPlugin
# Set up your development environment
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not officially affiliated with Hisense. It uses the ConnectLife cloud API for device communication.
Use at your own risk.

## Support

- ⭐ Star this repository if you find it useful
- 🐛 Report bugs via [GitHub Issues][issues]
- 💡 Request features via [GitHub Discussions][discussions]

---

**Made with ❤️ for the Home Assistant community**

[releases-shield]: https://img.shields.io/github/release/Connectlife-LLC/HomeAssistantPlugin.svg?style=for-the-badge

[releases]: https://github.com/Connectlife-LLC/HomeAssistantPlugin/releases

[commits-shield]: https://img.shields.io/github/commit-activity/y/Connectlife-LLC/HomeAssistantPlugin.svg?style=for-the-badge

[commits]: https://github.com/Connectlife-LLC/HomeAssistantPlugin/commits/main

[license-shield]: https://img.shields.io/github/license/Connectlife-LLC/HomeAssistantPlugin.svg?style=for-the-badge

[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge

[hacs]: https://github.com/hacs/integration

[issues]: https://github.com/Connectlife-LLC/HomeAssistantPlugin/issues

[discussions]: https://github.com/Connectlife-LLC/HomeAssistantPlugin/discussions

[wiki]: https://github.com/Connectlife-LLC/HomeAssistantPlugin/wiki
