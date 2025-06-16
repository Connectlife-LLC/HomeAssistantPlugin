# HomeAssistantPlugin

Hisense Air Conditioner Integration Guide for Home Assistant
Integration Overview
1. Feature Introduction
● Control Hisense AC devices via local API or cloud API.
Supports climate control, sensor data monitoring, zone switching, etc.
Compatible with multi-region/models (note hardware versions and API limitations).
2. Supported Models
Split-type AC
Dehumidifiers
Window AC
Portable AC
Ducted AC
Heat Pumps
Tri-generation Systems
3. Configuration Steps
1. Modify Local Hosts File for IP Mapping
Procedure:
1.	Navigate to C:\Windows\System32\drivers\etc\
2.	Drag hosts file to desktop
3.	Add 127.0.0.1 homeassistant.local, save and return file
2. Add Integration
Go to Settings → Devices & Services → Add Integration → Search: "Hisense Air Conditioner"
3. Submit Credentials
● Enter ConnectLife account credentials
● Note: Disable VPN/proxy tools during authorization
4. Wait for Device Data Sync
4. Feature Details
1. AC Control (Climate Entity)
Parameters:
Power, Mode (Cool/Heat/Fan/Dehumidify/Auto), Target Temp, Fan Speed, Swing (Horizontal/Vertical)
2. Sensor Data
Data Type	Description	Limitations
Indoor Temp	Real-time	Some models unsupported
Humidity	(Humidity-sensor models only)	Some models unsupported
Energy Usage	Daily kWh (resets at 00:00)	Some models unsupported
Errors	Active fault codes	-
3. Switch Controls
Zone Control (AirBase/SKYFi)
● Each zone generates independent switch ("-" prefix zones ignored)
● Master switch syncs with climate entity
● Conflict Note: Some functions (e.g., Turbo/Silent) are mutually exclusive
Function Switches
Data Type	Description	Limitations
Fan Speed	Dehumidifier speed control	Switch-based (official API lacks speed attribute)
4. Numeric Controls (Number Entity)
● Display Temp: Zone temp monitoring (Tri-gen systems)
● Control Temp: Zone temp adjustment (Tri-gen systems)
5. Dehumidifier (Humidity Entity)
Parameters:
Power, Mode (Continuous/Normal/Auto/Dry-Clothes*), Target Humidity, Fan Speed
*Partial models
6. Water Heater Control
Heat Pumps
Modes: Standard/ECO/Dual-Energy/Dual-1/Electric, Target Temp
Tri-gen Systems
Modes: Heat/Cool/Auto/HotWater+Cool/HotWater+Auto/HotWater/HotWater+Heat
5. Troubleshooting
Issue	Possible Cause	Solution
Login unresponsive	Network isolation/firewall	Disable VPN/proxy
Auth failure	Incorrect credentials	Verify username/password
"Page not found" post-login	Missing hosts entry	Repeat Step 1
Device sync failure	Home Assistant error	Reinstall integration
6. Appendices
1. Documentation Updates
● Contribute via Home Assistant GitHub repo
2. References
● Official Home Assistant Integration Docs
Style Notes
● Tables/lists for readability; key warnings in bold/color
● Extensible: May add screenshots, YAML samples, or automation examples


