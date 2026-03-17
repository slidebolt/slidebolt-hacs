#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPONENT_DIR="${ROOT_DIR}/custom_components/slidebolt"
CONTAINER_NAME="${HA_DEV_CONTAINER:-homeassistant-dev}"
DEST_DIR="/config/custom_components/slidebolt"
CONFIG_FILE="/config/configuration.yaml"

if [[ ! -d "${COMPONENT_DIR}" ]]; then
  echo "component directory not found: ${COMPONENT_DIR}" >&2
  exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "container not running: ${CONTAINER_NAME}" >&2
  exit 1
fi

echo "Deploying ${COMPONENT_DIR} -> ${CONTAINER_NAME}:${DEST_DIR}"
docker exec "${CONTAINER_NAME}" mkdir -p /config/custom_components
docker exec "${CONTAINER_NAME}" rm -rf "${DEST_DIR}"
docker cp "${COMPONENT_DIR}" "${CONTAINER_NAME}:/config/custom_components/"
docker exec "${CONTAINER_NAME}" /bin/sh -lc "grep -q '^slidebolt:' ${CONFIG_FILE} || printf '\nslidebolt:\n' >> ${CONFIG_FILE}"
echo "Restarting ${CONTAINER_NAME}"
docker restart "${CONTAINER_NAME}" >/dev/null
echo "Deploy complete and ${CONTAINER_NAME} restarted"
