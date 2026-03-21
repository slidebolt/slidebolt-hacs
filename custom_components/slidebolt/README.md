# Slidebolt Custom Component

Home Assistant integration that connects to a Slidebolt server and exposes its devices as native HA entities.

## Architecture

Slidebolt runs as a separate server that manages physical devices (covers, lights, etc.). This integration connects to that server over WebSocket, receives entity state updates, and forwards HA commands back.

```
Slidebolt Server  <--WebSocket-->  This Integration  <-->  Home Assistant
(manages devices)                  (bridge)                 (UI, automations)
```

The integration is **client-only** — it connects outbound to the Slidebolt server. The server address is configured through the standard HA config flow UI.

**This integration is a dumb pipe.** All logic lives on the Slidebolt server. The server sends HA-native values and this component relays them without transformation. Platform entities are thin pass-throughs — they read state/attributes from the payload and hand them directly to HA.

## Setup

Two-step setup — the LLAT is configured on the server side, never stored in HA's config entries.

### 1. Configure the Slidebolt server

Create a long-lived access token in HA (Profile → Long-Lived Access Tokens → Create Token) and configure it on the Slidebolt server. The server uses this token to call HA's APIs directly.

### 2. Add the integration in HA

1. Settings → Devices & Services → Add Integration → "Slidebolt"
2. Enter the Slidebolt server host and port
3. Config flow connects to the server and sends a `hello`
4. Server responds whether it has a valid LLAT configured
5. If no LLAT → config flow shows error: "Slidebolt server does not have an access token configured"
6. If LLAT present → config flow accepts, integration starts, entities appear

### What gets stored where

| Item | Stored in | Purpose |
|---|---|---|
| Host + Port | HA config entry | Integration knows where to connect |
| Long-lived access token | Slidebolt server only | Server uses it to call HA APIs |

The LLAT never passes through or is stored by the config flow. The integration only validates that the server has one configured.

## Configuration

All configuration is through the HA UI config flow. No YAML.

- **Host**: Slidebolt server hostname or IP
- **Port**: Slidebolt server port (default: 8080)

Reconfigure anytime through the integration's options.

## Supported Entity Platforms

- **cover** — motorized covers/blinds with position control
- **light** — on/off, brightness, RGB color, color temperature
- **switch** — simple on/off toggles
- **sensor** — read-only values with units and device classes
- **binary_sensor** — on/off state sensors (motion, door, etc.)
- **lock** — lock/unlock control
- **fan** — on/off with speed percentage
- **climate** — thermostat with HVAC modes and target temperature
- **button** — pressable action triggers
- **number** — numeric inputs with min/max/step
- **select** — dropdown selections from predefined options
- **text** — text inputs with validation

## Server Contract

The Slidebolt server is responsible for sending **HA-native values**. This integration does zero conversion. All values must match what Home Assistant expects natively.

### Entity Payload Format

Every entity the server sends must include these top-level fields:

```json
{
  "unique_id": "device-001-cover",
  "entity_id": "cover.front_door",
  "platform": "cover",
  "name": "Front Door",
  "available": true,
  "state": { ... },
  "attributes": { ... }
}
```

- `unique_id` — stable identifier, never changes
- `entity_id` — desired HA entity ID (e.g., `cover.front_door`)
- `platform` — one of the supported platforms
- `state` — platform-specific state dict (see below)
- `attributes` — passed directly to HA as entity attributes

### State Fields by Platform

All values use HA-native units and ranges. No conversion happens in this component.

**cover:**
```json
{"state": "open", "current_position": 100, "supported_features": 15}
```
- `state`: `"open"` | `"closed"` | `"opening"` | `"closing"`
- `current_position`: 0–100 (0 = closed, 100 = open)
- `supported_features`: HA `CoverEntityFeature` bitmask

**light:**
```json
{"is_on": true, "brightness": 255, "color_mode": "rgb", "rgb_color": [255, 0, 0], "color_temp_kelvin": 4000, "supported_color_modes": ["rgb", "color_temp"], "supported_features": 0}
```
- `brightness`: 0–255 (HA native)
- `color_mode`: `"onoff"` | `"brightness"` | `"color_temp"` | `"rgb"` | `"rgbw"` | `"xy"` etc.
- `rgb_color`: `[r, g, b]` each 0–255
- `color_temp_kelvin`: integer in Kelvin
- `supported_color_modes`: list of HA `ColorMode` strings
- `min_color_temp_kelvin`, `max_color_temp_kelvin`: optional bounds

**switch:**
```json
{"is_on": true}
```

**sensor:**
```json
{"native_value": 23.5, "native_unit_of_measurement": "°C", "device_class": "temperature", "state_class": "measurement"}
```

**binary_sensor:**
```json
{"is_on": true, "device_class": "door"}
```

**lock:**
```json
{"is_locked": true, "is_locking": false, "is_unlocking": false}
```

**fan:**
```json
{"is_on": true, "percentage": 50, "supported_features": 1}
```
- `percentage`: 0–100
- `supported_features`: HA `FanEntityFeature` bitmask

**climate:**
```json
{"hvac_mode": "heat", "target_temperature": 22, "current_temperature": 20, "temperature_unit": "°C", "hvac_modes": ["off", "heat", "cool", "auto"], "supported_features": 1, "min_temp": 5, "max_temp": 35, "target_temperature_step": 1}
```
- `hvac_mode`: HA `HVACMode` string (`"off"`, `"heat"`, `"cool"`, `"auto"`, etc.)
- `temperature_unit`: `"°C"` or `"°F"` (HA `UnitOfTemperature` values)
- `supported_features`: HA `ClimateEntityFeature` bitmask

**button:**
```json
{"device_class": "restart"}
```
(No state — buttons are stateless)

**number:**
```json
{"native_value": 50, "native_min_value": 0, "native_max_value": 100, "native_step": 1, "native_unit_of_measurement": "%", "mode": "slider"}
```

**select:**
```json
{"current_option": "option_a", "options": ["option_a", "option_b", "option_c"]}
```

**text:**
```json
{"native_value": "hello", "native_min": 0, "native_max": 255, "pattern": null, "mode": "text"}
```

### Command Format (HA → Server)

When the user interacts with an entity in HA, the integration sends the command to the server exactly as HA provides it — no parameter remapping.

```json
{
  "type": "command",
  "id": "cmd-1",
  "entity_id": "cover.front_door",
  "command": "set_cover_position",
  "params": {
    "position": 50
  }
}
```

Command names and params match the HA service call method names and kwargs directly (e.g., `async_turn_on` becomes `"turn_on"`, `kwargs["brightness"]` becomes `{"brightness": 255}`).

## WebSocket Protocol

The integration maintains a persistent WebSocket connection to the Slidebolt server.

### Connection & Auth Handshake

1. Integration connects to `ws://{host}:{port}/ws`
2. Integration sends `{"type": "hello"}`
3. Server responds with `{"type": "hello", "auth": true}` or `{"type": "hello", "auth": false}`
   - `auth: false` → server has no LLAT configured, integration disconnects with error
   - `auth: true` → server is ready, proceed
4. Server sends `snapshot` with all current entity states

The config flow uses this same handshake to validate the server before accepting. During normal operation, the integration reconnects and repeats this handshake automatically.

Note: the integration never sends the LLAT. The server already has it and uses it independently to call HA's REST/WebSocket APIs.

### Inbound Messages (Server → HA)

| Type | Purpose |
|---|---|
| `hello` | Handshake response (includes `auth` status) |
| `snapshot` | Full entity state dump (sent on connect) |
| `entity_added` | New entity appeared |
| `entity_updated` | Entity state changed |
| `entity_removed` | Entity removed |

### Outbound Messages (HA → Server)

| Type | Purpose |
|---|---|
| `hello` | Handshake request |
| `command` | Control command for an entity |

## File Structure

```
custom_components/slidebolt/
├── __init__.py          # Integration setup, config entry lifecycle
├── config_flow.py       # UI config flow (host/port input, connection test)
├── const.py             # Constants (domain, platforms, signals)
├── bridge.py            # WebSocket client, entity state management
├── entity_base.py       # Base class shared by all platform entities
├── manifest.json        # HA integration manifest
├── strings.json         # UI strings for config flow
├── cover.py             # Cover platform
├── light.py             # Light platform
├── switch.py            # Switch platform
├── sensor.py            # Sensor platform
├── binary_sensor.py     # Binary sensor platform
├── lock.py              # Lock platform
├── fan.py               # Fan platform
├── climate.py           # Climate platform
├── button.py            # Button platform
├── number.py            # Number platform
├── select.py            # Select platform
└── text.py              # Text platform
```

## Dev Testing

```bash
# Start a clean HA instance with the component loaded
./test-ha.sh

# Stop it
./test-ha.sh stop

# View logs
./test-ha.sh logs -f
```
