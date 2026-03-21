"""Base entity and factory for Slidebolt."""

from __future__ import annotations

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import SIGNAL_ENTITY_UPDATED


class SlideboltBaseEntity(Entity):
    """Base entity that reads all state directly from the server payload."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, bridge, unique_id: str) -> None:
        self.bridge = bridge
        self._attr_unique_id = unique_id
        p = bridge.payload(unique_id)
        entity_id = p.get("entity_id")
        if entity_id and "." in entity_id:
            self._attr_suggested_object_id = entity_id.split(".", 1)[1]

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_ENTITY_UPDATED, self._handle_update
            )
        )

    def _handle_update(self, changed_unique_id: str) -> None:
        if changed_unique_id == self._attr_unique_id:
            self.schedule_update_ha_state()

    @property
    def _payload(self) -> dict:
        return self.bridge.payload(self._attr_unique_id)

    @property
    def _state(self) -> dict:
        return self._payload.get("state", {})

    @property
    def available(self) -> bool:
        return bool(self._payload.get("available", True))

    @property
    def name(self) -> str | None:
        return self._payload.get("name")


def create_platform_entity(platform: str, bridge, unique_id: str) -> SlideboltBaseEntity | None:
    """Create a platform-specific entity instance."""
    from .alarm_control_panel import SlideboltAlarmControlPanel
    from .binary_sensor import SlideboltBinarySensor
    from .button import SlideboltButton
    from .camera import SlideboltCamera
    from .climate import SlideboltClimate
    from .cover import SlideboltCover
    from .event import SlideboltEvent
    from .fan import SlideboltFan
    from .humidifier import SlideboltHumidifier
    from .light import SlideboltLight
    from .lock import SlideboltLock
    from .media_player import SlideboltMediaPlayer
    from .number import SlideboltNumber
    from .remote import SlideboltRemote
    from .select import SlideboltSelect
    from .sensor import SlideboltSensor
    from .siren import SlideboltSiren
    from .switch import SlideboltSwitch
    from .text import SlideboltText
    from .valve import SlideboltValve

    classes = {
        "alarm_control_panel": SlideboltAlarmControlPanel,
        "binary_sensor": SlideboltBinarySensor,
        "button": SlideboltButton,
        "camera": SlideboltCamera,
        "climate": SlideboltClimate,
        "cover": SlideboltCover,
        "event": SlideboltEvent,
        "fan": SlideboltFan,
        "humidifier": SlideboltHumidifier,
        "light": SlideboltLight,
        "lock": SlideboltLock,
        "media_player": SlideboltMediaPlayer,
        "number": SlideboltNumber,
        "remote": SlideboltRemote,
        "select": SlideboltSelect,
        "sensor": SlideboltSensor,
        "siren": SlideboltSiren,
        "switch": SlideboltSwitch,
        "text": SlideboltText,
        "valve": SlideboltValve,
    }

    cls = classes.get(platform)
    if cls:
        return cls(bridge, unique_id)
    return None
