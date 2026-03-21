"""Slidebolt alarm control panel platform."""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("alarm_control_panel", async_add_entities)


class SlideboltAlarmControlPanel(SlideboltBaseEntity, AlarmControlPanelEntity):

    @property
    def alarm_state(self) -> str | None:
        return self._state.get("alarm_state")

    @property
    def code_arm_required(self) -> bool:
        return bool(self._state.get("code_arm_required", False))

    @property
    def supported_features(self) -> AlarmControlPanelEntityFeature:
        return AlarmControlPanelEntityFeature(self._state.get("supported_features", 0))

    async def async_alarm_arm_away(self, code=None) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "alarm_arm_away", {"code": code})

    async def async_alarm_arm_home(self, code=None) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "alarm_arm_home", {"code": code})

    async def async_alarm_arm_night(self, code=None) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "alarm_arm_night", {"code": code})

    async def async_alarm_disarm(self, code=None) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "alarm_disarm", {"code": code})

    async def async_alarm_trigger(self, code=None) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "alarm_trigger", {"code": code})
