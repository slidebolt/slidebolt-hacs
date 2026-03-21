#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="slidebolt-ha-dev"
HA_IMAGE="ghcr.io/home-assistant/home-assistant:stable"
HA_PORT=38123

log() { echo -e "\033[0;32m[ha-dev]\033[0m $1"; }

destroy() {
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    log "Destroyed"
}

restore_baseline() {
    log "Restoring baseline state..."
    rm -rf "$SCRIPT_DIR/testconfig/.storage" "$SCRIPT_DIR/testconfig/home-assistant_v2.db" \
           "$SCRIPT_DIR/testconfig/home-assistant.log" "$SCRIPT_DIR/testconfig/home-assistant.log.1" \
           "$SCRIPT_DIR/testconfig/.ha_run.lock"
    cp -r "$SCRIPT_DIR/testconfig-baseline-storage" "$SCRIPT_DIR/testconfig/.storage"
    cp "$SCRIPT_DIR/testconfig-baseline.db" "$SCRIPT_DIR/testconfig/home-assistant_v2.db"
}

start() {
    destroy
    restore_baseline

    log "Starting Home Assistant on port $HA_PORT..."

    docker run -d \
        --name "$CONTAINER_NAME" \
        --network=host \
        -v "$SCRIPT_DIR/testconfig:/config" \
        -v "$SCRIPT_DIR/custom_components:/config/custom_components" \
        "$HA_IMAGE" > /dev/null

    log "Container started: http://localhost:8123 (host network)"
}

logs() {
    docker logs "$CONTAINER_NAME" "$@"
}

save_baseline() {
    log "Saving current container state as baseline..."
    docker exec "$CONTAINER_NAME" sh -c "cp -r /config/.storage /tmp/storage-snap && cp /config/home-assistant_v2.db /tmp/snap.db"
    rm -rf "$SCRIPT_DIR/testconfig-baseline-storage"
    docker cp "$CONTAINER_NAME":/tmp/storage-snap "$SCRIPT_DIR/testconfig-baseline-storage"
    docker cp "$CONTAINER_NAME":/tmp/snap.db "$SCRIPT_DIR/testconfig-baseline.db"
    log "Baseline updated."
}

case "${1:-start}" in
    start)         start ;;
    stop)          destroy ;;
    restart)       start ;;
    logs)          shift; logs "$@" ;;
    save-baseline) save_baseline ;;
    *)
        echo "Usage: $0 [start|stop|restart|logs|save-baseline]"
        echo ""
        echo "  start (default)  Restore baseline and start HA on port $HA_PORT"
        echo "  stop             Destroy the container"
        echo "  restart          Destroy and recreate from baseline"
        echo "  logs             Tail container logs (pass extra args to docker logs)"
        echo "  save-baseline    Save current running container state as the new baseline"
        exit 1
        ;;
esac
