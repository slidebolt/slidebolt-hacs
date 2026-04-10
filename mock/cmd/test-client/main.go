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

	log.Printf("Sending hello...")
	conn.WriteJSON(map[string]string{"type": "hello"})

	_, msg, err := conn.ReadMessage()
	if err != nil {
		log.Fatalf("read failed: %v", err)
	}
	log.Printf("Received: %s", msg)

	var parsed map[string]any
	if err := json.Unmarshal(msg, &parsed); err == nil {
		fmt.Printf("Parsed: %#v\n", parsed)
	}

	log.Printf("Sending ping...")
	conn.WriteJSON(map[string]string{"type": "ping"})

	_, msg, err = conn.ReadMessage()
	if err != nil {
		log.Fatalf("read failed: %v", err)
	}
	log.Printf("Received: %s", msg)

	log.Printf("Waiting for events for 10 seconds...")
	deadline := time.Now().Add(10 * time.Second)
	for time.Now().Before(deadline) {
		conn.SetReadDeadline(time.Now().Add(1 * time.Second))
		_, msg, err := conn.ReadMessage()
		if err != nil {
			if ne, ok := err.(interface{ Timeout() bool }); ok && ne.Timeout() {
				continue
			}
			log.Printf("read done: %v", err)
			break
		}
		log.Printf("Event: %s", msg)
	}
}
