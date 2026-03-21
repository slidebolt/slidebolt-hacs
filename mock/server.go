package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"

	"github.com/gorilla/websocket"
	"github.com/grandcat/zeroconf"
)

func logJSON(label string, v any) {
	b, _ := json.MarshalIndent(v, "  ", "  ")
	log.Printf("%s:\n  %s", label, string(b))
}

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

// --- Wire types ---

type message struct {
	Type     string         `json:"type"`
	Auth     *bool          `json:"auth,omitempty"`
	Snapshot *snapshot       `json:"snapshot,omitempty"`
	ID       string         `json:"id,omitempty"`
	EntityID string         `json:"entity_id,omitempty"`
	Command  string         `json:"command,omitempty"`
	Params   map[string]any `json:"params,omitempty"`
	Success  *bool          `json:"success,omitempty"`
	Entity   *wireEntity    `json:"entity,omitempty"`
}

type snapshot struct {
	Devices []device `json:"devices"`
}

type device struct {
	ID       string       `json:"id"`
	Name     string       `json:"name"`
	Entities []wireEntity `json:"entities"`
}

type wireEntity struct {
	UniqueID   string         `json:"unique_id"`
	EntityID   string         `json:"entity_id"`
	Platform   string         `json:"platform"`
	Name       string         `json:"name"`
	Available  bool           `json:"available"`
	State      map[string]any `json:"state"`
	Attributes map[string]any `json:"attributes"`
}

// --- Mock entity state ---

type mockEntity struct {
	wireEntity
	onCommand func(cmd string, params map[string]any)
}

var (
	mu       sync.Mutex
	entities map[string]*mockEntity
)

func init() {
	entities = make(map[string]*mockEntity)

	// --- Switches ---
	addSwitch("mock-switch-1", "switch.mock_switch", "Mock Switch", false)

	// --- Cover ---
	addCover("mock-cover-1", "cover.mock_cover", "Mock Cover", 100, "door")

	// --- Lights ---
	// On/off only
	addLight("mock-light-onoff", "light.onoff_bulb", "On/Off Bulb",
		false, nil, nil, nil, nil, nil,
		[]string{"onoff"}, 0)

	// Dimmable
	brightness128 := 128
	addLight("mock-light-dimmer", "light.dimmable_bulb", "Dimmable Bulb",
		true, &brightness128, nil, nil, nil, strPtr("brightness"),
		[]string{"brightness"}, 0)

	// RGB
	addLight("mock-light-rgb", "light.rgb_bulb", "RGB Bulb",
		true, &brightness128, []int{255, 0, 100}, nil, strPtr("rgb"),
		nil,
		[]string{"rgb"}, 0)

	// Color temp
	ct4000 := 4000
	addLight("mock-light-ct", "light.color_temp_bulb", "Color Temp Bulb",
		true, &brightness128, nil, &ct4000, strPtr("color_temp"),
		nil,
		[]string{"color_temp"}, 0)

	// RGB + Color temp
	addLight("mock-light-rgbct", "light.rgb_ct_bulb", "RGB+CT Bulb",
		true, &brightness128, []int{0, 255, 0}, &ct4000, strPtr("rgb"),
		nil,
		[]string{"rgb", "color_temp"}, 0)

	// --- Sensors ---
	addSensor("mock-sensor-temp", "sensor.temperature", "Temperature", 22.5, "°C", "temperature", "measurement")
	addSensor("mock-sensor-humidity", "sensor.humidity", "Humidity", 45.0, "%", "humidity", "measurement")
	addSensor("mock-sensor-battery", "sensor.battery", "Battery", 87.0, "%", "battery", "measurement")

	// --- Binary sensors ---
	addBinarySensor("mock-bsensor-door", "binary_sensor.front_door", "Front Door", false, "door")
	addBinarySensor("mock-bsensor-motion", "binary_sensor.hallway_motion", "Hallway Motion", true, "motion")

	// --- Lock ---
	addLock("mock-lock-1", "lock.front_door", "Front Door Lock", true)

	// --- Fan ---
	addFan("mock-fan-1", "fan.ceiling_fan", "Ceiling Fan", false, 0)

	// --- Climate ---
	addClimate("mock-climate-1", "climate.thermostat", "Thermostat", "heat", 22, 20.5)

	// --- Button ---
	addButton("mock-button-1", "button.restart", "Restart", "restart")

	// --- Number ---
	addNumber("mock-number-1", "number.volume", "Volume", 50, 0, 100, 1, "%", "slider")

	// --- Select ---
	addSelect("mock-select-1", "select.mode", "Mode", "home", []string{"home", "away", "sleep", "party"})

	// --- Text ---
	addText("mock-text-1", "text.display_message", "Display Message", "Hello!", 0, 64, "text")

	// --- Camera (PTZ + motion detection) ---
	addCamera("mock-camera-1", "camera.front_door", "Front Door Camera",
		"rtsp://localhost:1234/front-door",
		"http://localhost:1234/front-door/snapshot.jpg",
		true, false, true)

	// --- Alarm control panel ---
	addAlarmPanel("mock-alarm-1", "alarm_control_panel.home_alarm", "Home Alarm", "disarmed")

	// --- Valve ---
	addValve("mock-valve-1", "valve.water_main", "Water Main", 100, "water")

	// --- Siren ---
	addSiren("mock-siren-1", "siren.alarm", "Alarm Siren", false,
		[]string{"alarm", "chime", "fire"})

	// --- Humidifier ---
	addHumidifier("mock-humid-1", "humidifier.bedroom", "Bedroom Humidifier",
		false, 45, 38, []string{"auto", "low", "medium", "high"}, "auto")

	// --- Media player ---
	addMediaPlayer("mock-media-1", "media_player.living_room", "Living Room Speaker",
		"paused", 0.65, false, "Bohemian Rhapsody", "Queen",
		[]string{"Spotify", "AirPlay", "Bluetooth"}, "Spotify")

	// --- Remote ---
	addRemote("mock-remote-1", "remote.tv", "TV Remote", true,
		[]string{"Watch TV", "Watch Movie", "Listen Music"}, "Watch TV")

	// --- Event (stateless) ---
	addEvent("mock-event-doorbell", "event.doorbell", "Doorbell",
		[]string{"pressed", "double_pressed", "held"}, "doorbell")
}

func strPtr(s string) *string { return &s }

func reg(e *mockEntity) {
	entities[e.EntityID] = e
}

func addSwitch(uid, eid, name string, on bool) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "switch",
			Name: name, Available: true,
			State:      map[string]any{"is_on": on},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "turn_on":
			e.State["is_on"] = true
		case "turn_off":
			e.State["is_on"] = false
		}
	}
	reg(e)
}

func addCover(uid, eid, name string, pos int, class string) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "cover",
			Name: name, Available: true,
			State: map[string]any{
				"current_position":   pos,
				"state":              coverStateStr(pos),
				"supported_features": 15,
			},
			Attributes: map[string]any{"device_class": class},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "open_cover":
			e.State["current_position"] = 100
			e.State["state"] = "open"
		case "close_cover":
			e.State["current_position"] = 0
			e.State["state"] = "closed"
		case "set_cover_position":
			if p, ok := params["position"].(float64); ok {
				pos := int(p)
				e.State["current_position"] = pos
				e.State["state"] = coverStateStr(pos)
			}
		}
	}
	reg(e)
}

func coverStateStr(pos int) string {
	if pos == 0 {
		return "closed"
	}
	return "open"
}

func addLight(uid, eid, name string, on bool, brightness *int, rgb []int, ctKelvin *int, colorMode *string, defaultColorMode *string, supportedModes []string, features int) {
	state := map[string]any{
		"is_on":                 on,
		"supported_color_modes": supportedModes,
		"supported_features":    features,
	}
	if brightness != nil {
		state["brightness"] = *brightness
	}
	if rgb != nil {
		state["rgb_color"] = rgb
	}
	if ctKelvin != nil {
		state["color_temp_kelvin"] = *ctKelvin
		state["min_color_temp_kelvin"] = 2000
		state["max_color_temp_kelvin"] = 6500
	}
	if colorMode != nil {
		state["color_mode"] = *colorMode
	} else if defaultColorMode != nil {
		state["color_mode"] = *defaultColorMode
	} else {
		state["color_mode"] = "onoff"
	}

	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "light",
			Name: name, Available: true,
			State:      state,
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "turn_on":
			e.State["is_on"] = true
			if b, ok := params["brightness"].(float64); ok {
				e.State["brightness"] = int(b)
			}
			if rgb, ok := params["rgb_color"].([]any); ok && len(rgb) == 3 {
				out := make([]int, 3)
				for i, v := range rgb {
					if f, ok := v.(float64); ok {
						out[i] = int(f)
					}
				}
				e.State["rgb_color"] = out
				e.State["color_mode"] = "rgb"
			}
			if ct, ok := params["color_temp_kelvin"].(float64); ok {
				e.State["color_temp_kelvin"] = int(ct)
				e.State["color_mode"] = "color_temp"
			}
		case "turn_off":
			e.State["is_on"] = false
		}
	}
	reg(e)
}

func addSensor(uid, eid, name string, value float64, unit, class, stateClass string) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "sensor",
			Name: name, Available: true,
			State: map[string]any{
				"native_value":               value,
				"native_unit_of_measurement": unit,
				"device_class":               class,
				"state_class":                stateClass,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {} // read-only
	reg(e)
}

func addBinarySensor(uid, eid, name string, on bool, class string) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "binary_sensor",
			Name: name, Available: true,
			State: map[string]any{
				"is_on":        on,
				"device_class": class,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {} // read-only
	reg(e)
}

func addLock(uid, eid, name string, locked bool) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "lock",
			Name: name, Available: true,
			State: map[string]any{
				"is_locked":    locked,
				"is_locking":   false,
				"is_unlocking": false,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "lock":
			e.State["is_locked"] = true
		case "unlock":
			e.State["is_locked"] = false
		}
	}
	reg(e)
}

func addFan(uid, eid, name string, on bool, pct int) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "fan",
			Name: name, Available: true,
			State: map[string]any{
				"is_on":              on,
				"percentage":         pct,
				"supported_features": 1, // SET_SPEED
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "turn_on":
			e.State["is_on"] = true
			if e.State["percentage"] == 0 {
				e.State["percentage"] = 50
			}
		case "turn_off":
			e.State["is_on"] = false
		case "set_percentage":
			if p, ok := params["percentage"].(float64); ok {
				e.State["percentage"] = int(p)
				e.State["is_on"] = int(p) > 0
			}
		}
	}
	reg(e)
}

func addClimate(uid, eid, name, mode string, target, current float64) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "climate",
			Name: name, Available: true,
			State: map[string]any{
				"hvac_mode":             mode,
				"hvac_modes":            []string{"off", "heat", "cool", "auto"},
				"target_temperature":    target,
				"current_temperature":   current,
				"temperature_unit":      "°C",
				"target_temperature_step": 0.5,
				"min_temp":              5,
				"max_temp":              35,
				"supported_features":    1, // TARGET_TEMPERATURE
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "set_hvac_mode":
			if m, ok := params["hvac_mode"].(string); ok {
				e.State["hvac_mode"] = m
			}
		case "set_temperature":
			if t, ok := params["temperature"].(float64); ok {
				e.State["target_temperature"] = t
			}
		}
	}
	reg(e)
}

func addButton(uid, eid, name, class string) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "button",
			Name: name, Available: true,
			State: map[string]any{
				"device_class": class,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		log.Printf("--- Button pressed: %s", eid)
	}
	reg(e)
}

func addNumber(uid, eid, name string, value, min, max, step float64, unit, mode string) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "number",
			Name: name, Available: true,
			State: map[string]any{
				"native_value":               value,
				"native_min_value":           min,
				"native_max_value":           max,
				"native_step":                step,
				"native_unit_of_measurement": unit,
				"mode":                       mode,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		if cmd == "set_native_value" {
			if v, ok := params["value"].(float64); ok {
				e.State["native_value"] = v
			}
		}
	}
	reg(e)
}

func addSelect(uid, eid, name, current string, options []string) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "select",
			Name: name, Available: true,
			State: map[string]any{
				"current_option": current,
				"options":        options,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		if cmd == "select_option" {
			if o, ok := params["option"].(string); ok {
				e.State["current_option"] = o
			}
		}
	}
	reg(e)
}

func addText(uid, eid, name, value string, minLen, maxLen int, mode string) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "text",
			Name: name, Available: true,
			State: map[string]any{
				"native_value": value,
				"native_min":   minLen,
				"native_max":   maxLen,
				"mode":         mode,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		if cmd == "set_value" {
			if v, ok := params["value"].(string); ok {
				e.State["native_value"] = v
			}
		}
	}
	reg(e)
}

func addCamera(uid, eid, name, stream, snapshotURL string, motionEnabled, streaming, recording bool) {
	// CameraEntityFeature: ON_OFF=1, STREAM=2
	features := 1 | 2
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "camera",
			Name: name, Available: true,
			State: map[string]any{
				"is_streaming":             streaming,
				"is_recording":             recording,
				"motion_detection_enabled": motionEnabled,
				"stream_source":            stream,
				"snapshot_url":             snapshotURL,
				"supported_features":       features,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "turn_on":
			e.State["is_streaming"] = true
		case "turn_off":
			e.State["is_streaming"] = false
		case "enable_motion_detection":
			e.State["motion_detection_enabled"] = true
		case "disable_motion_detection":
			e.State["motion_detection_enabled"] = false
		case "ptz":
			log.Printf("--- PTZ command: %v", params)
		}
	}
	reg(e)
}

func addAlarmPanel(uid, eid, name, state string) {
	// AlarmControlPanelEntityFeature: ARM_HOME=1, ARM_AWAY=2, ARM_NIGHT=4, TRIGGER=8
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "alarm_control_panel",
			Name: name, Available: true,
			State: map[string]any{
				"alarm_state":        state,
				"code_arm_required":  false,
				"supported_features": 1 | 2 | 4 | 8,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "alarm_arm_away":
			e.State["alarm_state"] = "armed_away"
		case "alarm_arm_home":
			e.State["alarm_state"] = "armed_home"
		case "alarm_arm_night":
			e.State["alarm_state"] = "armed_night"
		case "alarm_disarm":
			e.State["alarm_state"] = "disarmed"
		case "alarm_trigger":
			e.State["alarm_state"] = "triggered"
		}
	}
	reg(e)
}

func addValve(uid, eid, name string, pos int, class string) {
	// ValveEntityFeature: OPEN=1, CLOSE=2, SET_POSITION=4
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "valve",
			Name: name, Available: true,
			State: map[string]any{
				"current_valve_position": pos,
				"state":                 valveStateStr(pos),
				"reports_position":      true,
				"supported_features":    1 | 2 | 4,
			},
			Attributes: map[string]any{"device_class": class},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "open_valve":
			e.State["current_valve_position"] = 100
			e.State["state"] = "open"
		case "close_valve":
			e.State["current_valve_position"] = 0
			e.State["state"] = "closed"
		case "set_valve_position":
			if p, ok := params["position"].(float64); ok {
				pos := int(p)
				e.State["current_valve_position"] = pos
				e.State["state"] = valveStateStr(pos)
			}
		}
	}
	reg(e)
}

func valveStateStr(pos int) string {
	if pos == 0 {
		return "closed"
	}
	return "open"
}

func addSiren(uid, eid, name string, on bool, tones []string) {
	// SirenEntityFeature: TURN_ON=1, TURN_OFF=2, TONES=4, VOLUME_SET=8
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "siren",
			Name: name, Available: true,
			State: map[string]any{
				"is_on":              on,
				"available_tones":    tones,
				"supported_features": 1 | 2 | 4 | 8,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "turn_on":
			e.State["is_on"] = true
		case "turn_off":
			e.State["is_on"] = false
		}
	}
	reg(e)
}

func addHumidifier(uid, eid, name string, on bool, target, current int, modes []string, mode string) {
	// HumidifierEntityFeature: MODES=1
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "humidifier",
			Name: name, Available: true,
			State: map[string]any{
				"is_on":              on,
				"target_humidity":    target,
				"current_humidity":   current,
				"min_humidity":       20,
				"max_humidity":       80,
				"mode":              mode,
				"available_modes":   modes,
				"supported_features": 1,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "turn_on":
			e.State["is_on"] = true
		case "turn_off":
			e.State["is_on"] = false
		case "set_humidity":
			if h, ok := params["humidity"].(float64); ok {
				e.State["target_humidity"] = int(h)
			}
		case "set_mode":
			if m, ok := params["mode"].(string); ok {
				e.State["mode"] = m
			}
		}
	}
	reg(e)
}

func addMediaPlayer(uid, eid, name, state string, volume float64, muted bool, title, artist string, sources []string, source string) {
	// MediaPlayerEntityFeature: PAUSE=1, VOLUME_SET=4, VOLUME_MUTE=8,
	// PREVIOUS_TRACK=16, NEXT_TRACK=32, TURN_ON=128, TURN_OFF=256,
	// PLAY=16384, STOP=32768, SELECT_SOURCE=2048
	features := 1 | 4 | 8 | 16 | 32 | 128 | 256 | 2048 | 16384 | 32768
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "media_player",
			Name: name, Available: true,
			State: map[string]any{
				"state":              state,
				"volume_level":       volume,
				"is_volume_muted":    muted,
				"media_title":        title,
				"media_artist":       artist,
				"source":             source,
				"source_list":        sources,
				"supported_features": features,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "turn_on":
			e.State["state"] = "idle"
		case "turn_off":
			e.State["state"] = "off"
		case "media_play":
			e.State["state"] = "playing"
		case "media_pause":
			e.State["state"] = "paused"
		case "media_stop":
			e.State["state"] = "idle"
		case "set_volume_level":
			if v, ok := params["volume_level"].(float64); ok {
				e.State["volume_level"] = v
			}
		case "mute_volume":
			if m, ok := params["is_volume_muted"].(bool); ok {
				e.State["is_volume_muted"] = m
			}
		case "select_source":
			if s, ok := params["source"].(string); ok {
				e.State["source"] = s
			}
		}
	}
	reg(e)
}

func addRemote(uid, eid, name string, on bool, activities []string, current string) {
	// RemoteEntityFeature: ACTIVITY=4
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "remote",
			Name: name, Available: true,
			State: map[string]any{
				"is_on":            on,
				"activity_list":    activities,
				"current_activity": current,
				"supported_features": 4,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		switch cmd {
		case "turn_on":
			e.State["is_on"] = true
		case "turn_off":
			e.State["is_on"] = false
		case "send_command":
			log.Printf("--- Remote send_command: %v", params)
		}
	}
	reg(e)
}

func addEvent(uid, eid, name string, eventTypes []string, class string) {
	e := &mockEntity{
		wireEntity: wireEntity{
			UniqueID: uid, EntityID: eid, Platform: "event",
			Name: name, Available: true,
			State: map[string]any{
				"event_types":  eventTypes,
				"device_class": class,
			},
			Attributes: map[string]any{},
		},
	}
	e.onCommand = func(cmd string, params map[string]any) {
		log.Printf("--- Event command (unexpected): %s %v", cmd, params)
	}
	reg(e)
}

// --- Snapshot + command handling ---

func buildSnapshot() snapshot {
	mu.Lock()
	defer mu.Unlock()

	var ents []wireEntity
	for _, e := range entities {
		ents = append(ents, e.wireEntity)
	}
	return snapshot{
		Devices: []device{
			{ID: "mock-device-1", Name: "Mock Device", Entities: ents},
		},
	}
}

func handleCommand(msg message) wireEntity {
	mu.Lock()
	defer mu.Unlock()

	e, ok := entities[msg.EntityID]
	if !ok {
		log.Printf("!!! Unknown entity: %s", msg.EntityID)
		return wireEntity{}
	}
	e.onCommand(msg.Command, msg.Params)
	return e.wireEntity
}

// --- WebSocket handler ---

func handleWS(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("upgrade error: %v", err)
		return
	}
	defer conn.Close()

	log.Printf(">>> Client connected: %s", r.RemoteAddr)

	var hello message
	if err := conn.ReadJSON(&hello); err != nil {
		log.Printf("<<< read error: %v", err)
		return
	}
	logJSON("<<< Received", hello)

	if hello.Type != "hello" {
		log.Printf("!!! Expected hello, got: %s", hello.Type)
		return
	}

	authOK := true
	resp := message{Type: "hello", Auth: &authOK}
	logJSON(">>> Sending hello response", resp)
	if err := conn.WriteJSON(resp); err != nil {
		log.Printf("!!! write error: %v", err)
		return
	}
	log.Printf("--- Hello handshake complete")

	snap := buildSnapshot()
	snapMsg := message{Type: "snapshot", Snapshot: &snap}
	logJSON(">>> Sending snapshot", snapMsg)
	if err := conn.WriteJSON(snapMsg); err != nil {
		log.Printf("!!! write error: %v", err)
		return
	}
	total := 0
	for _, d := range snap.Devices {
		total += len(d.Entities)
	}
	log.Printf("--- Snapshot sent (%d entities)", total)

	log.Printf("--- Entering message loop, waiting for commands...")
	for {
		var msg message
		if err := conn.ReadJSON(&msg); err != nil {
			log.Printf("<<< Client disconnected: %v", err)
			return
		}
		logJSON("<<< Received", msg)

		switch msg.Type {
		case "command":
			ent := handleCommand(msg)
			success := true
			result := message{
				Type:     "command_result",
				ID:       msg.ID,
				EntityID: msg.EntityID,
				Success:  &success,
			}
			logJSON(">>> Sending command_result", result)
			if err := conn.WriteJSON(result); err != nil {
				log.Printf("!!! write error: %v", err)
				return
			}

			update := message{Type: "entity_updated", Entity: &ent}
			logJSON(">>> Sending entity_updated", update)
			if err := conn.WriteJSON(update); err != nil {
				log.Printf("!!! write error: %v", err)
				return
			}

		default:
			log.Printf("??? Unknown message type: %s", msg.Type)
		}
	}
}

func main() {
	port := "0" // random port by default
	if p := os.Getenv("PORT"); p != "" {
		port = p
	}

	if token := os.Getenv("HA_TOKEN"); token != "" {
		haURL := os.Getenv("HA_URL")
		if haURL == "" {
			haURL = "http://localhost:38123"
		}
		haURL = strings.TrimRight(haURL, "/")

		req, _ := http.NewRequest("GET", haURL+"/api/", nil)
		req.Header.Set("Authorization", "Bearer "+token)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Printf("WARNING: Could not reach HA at %s: %v", haURL, err)
		} else {
			resp.Body.Close()
			if resp.StatusCode == 200 {
				log.Printf("Verified LLAT against HA at %s", haURL)
			} else {
				log.Printf("WARNING: HA returned %d for LLAT check", resp.StatusCode)
			}
		}
	}

	log.Printf("Loaded %d mock entities", len(entities))
	http.HandleFunc("/ws", handleWS)

	// Listen on the requested port (0 = random)
	ln, err := net.Listen("tcp", ":"+port)
	if err != nil {
		fmt.Fprintf(os.Stderr, "listen error: %v\n", err)
		os.Exit(1)
	}
	actualPort := ln.Addr().(*net.TCPAddr).Port
	log.Printf("Mock Slidebolt server listening on :%d", actualPort)

	// Advertise via mDNS. Bind only to the primary outbound interface so we
	// share the same multicast group that HA's python-zeroconf listens on,
	// avoiding conflicts with avahi-daemon on the other interfaces.
	iface := outboundInterface()
	mdnsServer, err := zeroconf.Register(
		"Slidebolt Mock",
		"_slidebolt._tcp",
		"local.",
		actualPort,
		[]string{"version=0.0.1"},
		iface,
	)
	if err != nil {
		log.Printf("WARNING: mDNS registration failed: %v", err)
	} else {
		log.Printf("mDNS: advertising _slidebolt._tcp on port %d (iface %v)", actualPort, iface)
		defer mdnsServer.Shutdown()
	}

	// Handle shutdown
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigCh
		log.Printf("Shutting down...")
		if mdnsServer != nil {
			mdnsServer.Shutdown()
		}
		os.Exit(0)
	}()

	if err := http.Serve(ln, nil); err != nil {
		fmt.Fprintf(os.Stderr, "server error: %v\n", err)
		os.Exit(1)
	}
}

// outboundInterface returns the network interface used for the default route,
// so mDNS is only advertised on the same interface HA's zeroconf listens on.
func outboundInterface() []net.Interface {
	conn, err := net.Dial("udp", "1.1.1.1:53")
	if err != nil {
		return nil // fall back to all interfaces
	}
	defer conn.Close()
	localIP := conn.LocalAddr().(*net.UDPAddr).IP

	ifaces, err := net.Interfaces()
	if err != nil {
		return nil
	}
	for _, iface := range ifaces {
		addrs, _ := iface.Addrs()
		for _, addr := range addrs {
			var ip net.IP
			switch v := addr.(type) {
			case *net.IPNet:
				ip = v.IP
			case *net.IPAddr:
				ip = v.IP
			}
			if ip != nil && ip.Equal(localIP) {
				return []net.Interface{iface}
			}
		}
	}
	return nil
}
