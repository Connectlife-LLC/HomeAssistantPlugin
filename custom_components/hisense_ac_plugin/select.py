"""Platform for Hisense AC select integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HisenseACPluginDataUpdateCoordinator
from .models import DeviceInfo as HisenseDeviceInfo

_LOGGER = logging.getLogger(__name__)

# Sleep mode is a binary switch on this device; SELECT_TYPES is intentionally empty.
SELECT_TYPES: dict[str, dict] = {}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hisense AC select platform."""
    coordinator: HisenseACPluginDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    devices = coordinator.data
    if not devices:
        return

    entities = []
    for device_id, device in devices.items():
        if not (isinstance(device, HisenseDeviceInfo) and device.is_devices()):
            continue

        parser = coordinator.api_client.parsers.get(device.device_id)

        for select_type, select_info in SELECT_TYPES.items():
            key = select_info["key"]
            in_status = key in (device.status or {})
            in_parser = parser and key in getattr(parser, "attributes", {})
            if not (in_status or in_parser):
                continue

            # Resolve options from the filtered parser if available
            options: dict[str, str] = select_info["default_options"]
            if parser:
                attr = parser.attributes.get(key)
                if attr and attr.value_map:
                    options = dict(attr.value_map)

            entities.append(HisenseSelect(coordinator, device, select_type, select_info, options))

    if entities:
        _LOGGER.info("Adding %d select entities", len(entities))
        async_add_entities(entities)


class HisenseSelect(CoordinatorEntity, SelectEntity):
    """Hisense AC select entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HisenseACPluginDataUpdateCoordinator,
        device: HisenseDeviceInfo,
        select_type: str,
        select_info: dict[str, Any],
        options: dict[str, str],
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device.puid
        self._select_type = select_type
        self._select_key = select_info["key"]
        self._options_map = options          # raw_value -> label
        self._reverse_map = {v: k for k, v in options.items()}  # label -> raw_value
        self._attr_unique_id = f"{device.device_id}_{select_type}"
        self._attr_name = select_info["name"]
        self._attr_icon = select_info.get("icon")
        self._attr_options = list(options.values())
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.name,
            manufacturer="Hisense",
            model=f"{device.type_name} ({device.feature_name})",
        )

    @property
    def _device(self) -> HisenseDeviceInfo | None:
        return self.coordinator.get_device(self._device_id)

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        dev = self._device
        return bool(dev and dev.is_online and dev.is_onOff)

    @property
    def current_option(self) -> str | None:
        dev = self._device
        if not dev:
            return None
        raw = dev.get_status_value(self._select_key)
        if raw is None:
            return None
        return self._options_map.get(str(raw))

    async def async_select_option(self, option: str) -> None:
        raw = self._reverse_map.get(option)
        if raw is None:
            _LOGGER.warning("Unknown option %s for %s", option, self._select_type)
            return
        await self.coordinator.async_control_device(
            puid=self._device_id,
            properties={self._select_key: raw},
        )
