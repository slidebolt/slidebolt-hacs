# slidebolt-hacs

Local development repo for the Slidebolt Home Assistant custom integration.

## Layout

- `custom_components/slidebolt/`: Home Assistant integration code
- `deploy.sh`: copies the integration into the running `homeassistant-dev` container
- `icon.png`: project logo asset

## Deploy

```bash
./deploy.sh
```

This copies `custom_components/slidebolt` into:

```text
homeassistant-dev:/config/custom_components/slidebolt
```
