package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/gorilla/websocket"
)

func main() {
	url := "ws://127.0.0.1:39444/ws"
	if len(os.Args) > 1 {
		url = os.Args[1]
	}

	log.Printf("Connecting to %s", url)

	conn, _, err := websocket.DefaultDialer.Dial(url, nil)
	if err != nil {
		log.Fatalf("connect failed: %v", err)
	}
	defer conn.Close()

	// Send hello
	log.Printf("Sending hello...")
	conn.WriteJSON(map[string]string{"type": "hello"})

	// Read hello response
	var hello map[string]any
	conn.ReadJSON(&hello)
	pretty, _ := json.MarshalIndent(hello, "", "  ")
	log.Printf("Hello response:\n%s", pretty)

	auth, _ := hello["auth"].(bool)
	if !auth {
		log.Fatalf("Server does not have auth configured")
	}

	// Read snapshot
	var snapshot map[string]any
	conn.ReadJSON(&snapshot)
	pretty, _ = json.MarshalIndent(snapshot, "", "  ")
	log.Printf("Snapshot:\n%s", pretty)

	// Send a command: turn on the switch
	log.Printf("Sending turn_on command for switch.mock_switch...")
	conn.WriteJSON(map[string]any{
		"type":      "command",
		"id":        "cmd-1",
		"entity_id": "switch.mock_switch",
		"command":   "turn_on",
		"params":    map[string]any{},
	})

	var result1 map[string]any
	conn.ReadJSON(&result1)
	pretty, _ = json.MarshalIndent(result1, "", "  ")
	log.Printf("Command result:\n%s", pretty)

	time.Sleep(500 * time.Millisecond)

	// Send a command: set cover position
	log.Printf("Sending set_cover_position command for cover.mock_cover...")
	conn.WriteJSON(map[string]any{
		"type":      "command",
		"id":        "cmd-2",
		"entity_id": "cover.mock_cover",
		"command":   "set_cover_position",
		"params":    map[string]any{"position": 50},
	})

	var result2 map[string]any
	conn.ReadJSON(&result2)
	pretty, _ = json.MarshalIndent(result2, "", "  ")
	log.Printf("Command result:\n%s", pretty)

	fmt.Println()
	log.Printf("All tests passed!")
}
