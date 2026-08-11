# file: number.py
"""Platform for Hisense AC number integration."""
from __future__ import annotations

import logging
import re
from typing import Any, Callable

from homeassistant.components.number import NumberEntity, NumberDeviceClass, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.core import Event
from homeassistant.helpers.dispatcher import callback

from .const import DOMAIN, StatusKey, MIN_TEMP_WATER, MAX_TEMP_WATER
from .coordinator import HisenseACPluginDataUpdateCoordinator
from .api import HisenseApiClient
from .models import DeviceInfo as HisenseDeviceInfo

_LOGGER = logging.getLogger(__name__)

# Define number types
NUMBER_TYPES = {
    "t_zone1water_settemp1": {
        "key": "t_zone1water_settemp1",
        "name": "1温区设置值",
        "icon": "mdi:thermometer",
        "device_class": NumberDeviceClass.TEMPERATURE,
        "mode": NumberMode.AUTO,
        "unit": "°C",
        "min_value": 16,
        "max_value": 32,
        "step": 0.5,
        "description": "Set 1温区设置值"
    },
    "t_zone2water_settemp2": {
        "key": "t_zone2water_settemp2",
        "name": "2温区设置值",
        "icon": "mdi:thermometer",
        "device_class": NumberDeviceClass.TEMPERATURE,
        "mode": NumberMode.AUTO,
        "unit": "°C",
        "min_value": 16,
        "max_value": 32,
        "step": 0.5,
        "description": "Set 2温区设置值"
    }
}


def _extract_numeric_range(value_range: str) -> tuple[float, float] | None:
    """Extract the first numeric range from value_range like '0~100,16~30'."""
    if not value_range:
        return None

    for item in value_range.split(","):
        item = item.strip()
        if "~" not in item:
            continue
        try:
            min_str, max_str = [part.strip() for part in item.split("~", 1)]
            return float(min_str), float(max_str)
        except (TypeError, ValueError):
            continue

    return None


def _build_zone_damper_number_types(parser) -> list[tuple[str, dict[str, Any]]]:
    """Build number entity definitions for zone damper control (0-100%)."""
    entities: list[tuple[str, dict[str, Any]]] = []
    if not parser:
        return entities

    attrs = getattr(parser, "attributes", {}) or {}

    def is_zone_damper_key(key_lower: str) -> bool:
        if "zone" not in key_lower:
            return False
        if key_lower.endswith("_power") or key_lower.endswith("_switch"):
            return False
        keywords = ("opencontrol", "damper", "aperture", "opening", "position", "percent")
        return any(token in key_lower for token in keywords)

    for key, attr in attrs.items():
        key_lower = key.lower()
        if not is_zone_damper_key(key_lower):
            continue
        if getattr(attr, "read_write", "RW") == "R":
            continue
        if getattr(attr, "attr_type", "") != "Number":
            continue

        value_range = getattr(attr, "value_range", "") or ""
        numeric_range = _extract_numeric_range(value_range)
        if not numeric_range:
            continue

        min_val, max_val = numeric_range
        if min_val != 0 or max_val != 100:
            continue

        zone_match = re.search(r"zone_?(\d+)", key_lower)
        zone_name = f"Zone {zone_match.group(1)}" if zone_match else key.replace("t_", "").replace("_", " ").title()
        number_type = f"zone_{zone_match.group(1)}_damper" if zone_match else f"{key}_damper"

        step = getattr(attr, "step", 1) or 1
        if step == 1:
            step = 5

        number_info = {
            "key": key,
            "name": f"{zone_name} Damper",
            "icon": "mdi:percent",
            "device_class": None,
            "mode": NumberMode.SLIDER,
            "unit": "%",
            "min_value": 0,
            "max_value": 100,
            "step": float(step),
            "description": f"Set {zone_name} damper opening",
        }
        entities.append((number_type, number_info))

    return entities


def _build_zone_damper_from_status(device: HisenseDeviceInfo) -> list[tuple[str, dict[str, Any]]]:
    """Fallback builder: infer zone damper keys from live status values."""
    entities: list[tuple[str, dict[str, Any]]] = []
    status = device.status or {}

    def is_zone_damper_key(key_lower: str) -> bool:
        if "zone" not in key_lower:
            return False
        if key_lower.endswith("_power") or key_lower.endswith("_switch"):
            return False
        keywords = ("opencontrol", "damper", "aperture", "opening", "position", "percent")
        return any(token in key_lower for token in keywords)

    for key, value in status.items():
        key_lower = str(key).lower()
        if not is_zone_damper_key(key_lower):
            continue
        if "temp" in key_lower or "humidity" in key_lower:
            continue
        if key_lower.endswith("_power"):
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue

        if numeric_value < 0 or numeric_value > 100:
            continue

        zone_match = re.search(r"zone_?(\d+)", key_lower)
        zone_name = f"Zone {zone_match.group(1)}" if zone_match else key.replace("t_", "").replace("_", " ").title()
        number_type = f"zone_{zone_match.group(1)}_damper" if zone_match else f"{key}_damper"

        number_info = {
            "key": key,
            "name": f"{zone_name} Damper",
            "icon": "mdi:percent",
            "device_class": None,
            "mode": NumberMode.SLIDER,
            "unit": "%",
            "min_value": 0,
            "max_value": 100,
            "step": 5.0,
            "description": f"Set {zone_name} damper opening",
        }
        entities.append((number_type, number_info))

    return entities

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Hisense AC number platform."""
    coordinator: HisenseACPluginDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    try:
        # Get devices from coordinator
        devices = coordinator.data
        _LOGGER.debug("Setting up numbers with coordinator data: %s", devices)

        if not devices:
            _LOGGER.warning("No devices found in coordinator data")
            return

        entities = []
        for device_id, device in devices.items():
            _LOGGER.debug("Processing device for numbers: %s", device.to_dict())

            if isinstance(device, HisenseDeviceInfo) and device.is_devices():
                parser = coordinator.api_client.parsers.get(device.device_id)
                created_keys: set[str] = set()
                created_zone_indices: set[str] = set()

                # Add numbers for each supported feature
                for number_type, number_info in NUMBER_TYPES.items():
                    # Check if the device supports this attribute
                    if device.has_attribute(number_info["key"], parser):
                        if device.status.get("f_zone2_select") == "0" and number_type == "t_zone2water_settemp2":
                            continue
                        _LOGGER.info(
                            "Adding %s number for device: %s",
                            number_info["name"],
                            device.name
                        )
                        entity = HisenseNumber(
                            coordinator,
                            device,
                            number_type,
                            number_info
                        )
                        entities.append(entity)

                # Add dynamic zone damper controls, e.g. t_zone1_damper: 0-100 step 5
                for number_type, number_info in _build_zone_damper_number_types(parser):
                    zone_match = re.search(r"zone_(\d+)_damper", number_type)
                    zone_idx = zone_match.group(1) if zone_match else None
                    if zone_idx and zone_idx in created_zone_indices:
                        continue
                    if device.has_attribute(number_info["key"], parser):
                        entity = HisenseNumber(
                            coordinator,
                            device,
                            number_type,
                            number_info,
                        )
                        entities.append(entity)
                        created_keys.add(number_info["key"])
                        if zone_idx:
                            created_zone_indices.add(zone_idx)

                # Fallback: create zone damper entities from status if parser metadata is missing.
                for number_type, number_info in _build_zone_damper_from_status(device):
                    zone_match = re.search(r"zone_(\d+)_damper", number_type)
                    zone_idx = zone_match.group(1) if zone_match else None
                    if zone_idx and zone_idx in created_zone_indices:
                        continue
                    if number_info["key"] in created_keys:
                        continue
                    entity = HisenseNumber(
                        coordinator,
                        device,
                        number_type,
                        number_info,
                    )
                    entities.append(entity)
                    if zone_idx:
                        created_zone_indices.add(zone_idx)
            else:
                _LOGGER.warning(
                    "Skipping unsupported device: %s-%s (%s)",
                    getattr(device, 'type_code', None),
                    getattr(device, 'feature_code', None),
                    getattr(device, 'name', None)
                )

        if not entities:
            _LOGGER.warning("No supported numbers found")
            return

        _LOGGER.info("Adding %d number entities", len(entities))
        async_add_entities(entities)

    except Exception as err:
        _LOGGER.error("Failed to set up number platform: %s", err)
        raise

class HisenseNumber(CoordinatorEntity, NumberEntity):
    """Representation of a Hisense AC number."""

    _attr_has_entity_name = True
    _temperatureRange = [
        # [ModeType.COOL] 制冷
        [16, 30, 5, 27, None, None],
        # [ModeType.HEAT] 加热
        [16, 30, 25, 65, None, None],
        # [ModeType.AUTO] 自动
        [16, 30, 5, 65, None, None],
        # [ModeType.COOL_DHW] 制冷 + 制热水
        [16, 30, 5, 27, 35, 55],
        # [ModeType.HEAT_DHW] 加热 + 制热水
        [16, 30, 25, 65, 35, 55],
        # [ModeType.AUTO_DHW] 自动 + 制热水
        [16, 30, 5, 65, 35, 55],
        # [ModeType.ONLY_DHW] 制热水
        [None, None, None, None, 35, 55],
    ]
    _WATER_TEMP_KEYS = {"t_zone1water_settemp1", "t_zone2water_settemp2"}

    def _zone_index(self) -> str | None:
        """Extract zone index from number_type or property key."""
        for source in (self._number_type, self._number_key):
            match = re.search(r"zone_?(\d+)", source.lower())
            if match:
                return match.group(1)
        return None

    def _is_zone_damper(self) -> bool:
        key_lower = self._number_key.lower()
        if "zone" not in key_lower:
            return False
        if self._number_key in self._WATER_TEMP_KEYS:
            return False
        return self._attr_native_unit_of_measurement == "%"

    def __init__(
        self,
        coordinator: HisenseACPluginDataUpdateCoordinator,
        device: HisenseDeviceInfo,
        number_type: str,
        number_info: dict,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.current_mode = None
        self._device_id = device.puid
        self._number_type = number_type
        self._number_info = number_info
        self._number_key = number_info["key"]
        key_lower = self._number_key.lower()
        if "zone" in key_lower and self._number_type.endswith("_damper"):
            zone_idx = self._zone_index()
            if zone_idx:
                # Canonical unique_id for zone dampers to avoid duplicated entities
                # caused by historical language/key naming changes.
                self._attr_unique_id = f"{device.device_id}_zone_{zone_idx}_damper"
            else:
                self._attr_unique_id = f"{device.device_id}_{self._number_key}"
        elif "zone" in key_lower:
            # Keep a stable unique_id based on raw key to avoid duplicate entities after upgrades.
            self._attr_unique_id = f"{device.device_id}_{self._number_key}"
        else:
            self._attr_unique_id = f"{device.device_id}_{number_type}"
        self._attr_name = number_info["name"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.name,
            manufacturer="Hisense",
            model=f"{device.type_name} ({device.feature_name})",
        )
        self._attr_icon = number_info["icon"]
        self._attr_device_class = number_info.get("device_class")
        self._attr_mode = number_info.get("mode")
        self._attr_native_unit_of_measurement = number_info.get("unit")
        self._attr_native_min_value = float(number_info.get("min_value"))
        self._attr_native_max_value = float(number_info.get("max_value"))
        self._attr_native_step = float(number_info.get("step"))
        self._attr_entity_registry_enabled_default = True
        key_lower = self._number_key.lower()
        if "zone" in key_lower:
            # Keep zone controls in the config section to avoid cluttering primary controls order.
            self._attr_entity_category = EntityCategory.CONFIG
        if self._is_zone_damper():
            self._attr_suggested_display_precision = 0

        # 初始化时更新一次温度范围
        self._cached_device = None
        self._last_t_zone1_temp = None
        self._last_mode = None
        self._update_temperature_range()

    @property
    def name(self) -> str:
        """动态获取翻译后的名称"""
        hass = self.hass
        translation_key = self._number_type  # 使用开关类型作为键
        current_lang = hass.config.language
        translations = hass.data.get(f"{DOMAIN}.translations", {}).get(current_lang, {})
        translated_name = translations.get(translation_key)
        if translated_name:
            return translated_name

        zone_match = re.search(r"zone_(\d+)_damper", translation_key)
        if zone_match:
            zone_idx = zone_match.group(1)
            if current_lang == "zh-Hans":
                return f"分区{zone_idx}风门开度"
            return f"Zone {zone_idx} Damper"

        translated_name = self._number_info["name"]

        if self._is_zone_damper():
            raw_value = None
            if self._device:
                raw_value = self._device.get_status_value(self._number_key)
            if raw_value is not None:
                try:
                    percent = int(float(raw_value))
                    return f"{translated_name} ({percent}%)"
                except (TypeError, ValueError):
                    return translated_name

        return translated_name

    @property
    def _device(self):
        """Get current device data from coordinator."""
        return self.coordinator.get_device(self._device_id)

    def _get_mode_index(self, mode: str) -> int | None:
        """获取模式的索引"""
        mode_map = {
            "1": 0,
            "0": 1,
            "15": 2,
            "5": 3,
            "16": 4,
            "6": 5,
            "3": 6,
        }
        return mode_map.get(mode)

    def _update_temperature_range(self):
        """Update the temperature range based on the current mode and feature_code."""
        # Only water-temperature entities should use mode-based temperature limits.
        if self._number_key not in self._WATER_TEMP_KEYS:
            return

        device = self.coordinator.get_device(self._device_id)
        if not device:
            return

        current_mode = device.get_status_value("t_work_mode")
        t1_temp = device.get_status_value("t_zone1water_settemp1")

        # 如果模式和温区1温度未变，则无需更新
        if current_mode == self._last_mode and t1_temp == self._last_t_zone1_temp:
            return

        self._last_mode = current_mode
        self._last_t_zone1_temp = t1_temp

        mode_index = self._get_mode_index(current_mode)
        if mode_index is None:
            _LOGGER.warning("No temperature range found for mode %s", current_mode)
            return

        temperatures = self._temperatureRange[mode_index]
        if self._number_type == "t_zone2water_settemp2":
            min_val = float(temperatures[2]) if temperatures[2] is not None else MIN_TEMP_WATER
            max_val = float(t1_temp) if t1_temp is not None else MAX_TEMP_WATER
        else:
            min_val = float(temperatures[2]) if temperatures[2] is not None else MIN_TEMP_WATER
            max_val = float(temperatures[3]) if temperatures[3] is not None else MAX_TEMP_WATER

        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Zone damper controls should remain available when device is online.
        if self._number_key not in self._WATER_TEMP_KEYS:
            return bool(self._device and self._device.is_online)

        # 基础可用性检查（设备在线）
        if not self._device or not self._device.is_online:
            return False
        # 新增：设备关机状态下不可用
        power_status = self._device.get_status_value("t_power")
        if power_status != "1":
            _LOGGER.debug("设备已关机，实体不可用")
            return False
        current_mode = self._device.get_status_value("t_work_mode")
        # 判断自动模式
        if current_mode in ["15", "3", "16"]:
            _LOGGER.debug("设备处于自动模式，温度控制不可用")
            return False

        # 判断温区2在制冷或制冷+生活热水模式下是否禁用
        if self._number_type == "t_zone2water_settemp2":
            if current_mode in ["1", "5"]:  # 对应制冷和制冷+生活热水模式
                _LOGGER.debug("当前模式 %s 禁用温区2控制", current_mode)
                return False

        return True

    @property
    def native_value(self) -> float | None:
        """Return the number value."""
        device = self.coordinator.get_device(self._device_id)
        if not device or not device.is_online:
            return None

        value = device.get_status_value(self._number_key)
        if value is None:
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await super().async_added_to_hass()

        # 监听设备数据更新
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    def _handle_coordinator_update(self) -> None:
        """Handle data update from coordinator."""
        self._update_temperature_range()
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new target value."""
        try:
            # Ensure the value is within the valid range
            if value < self._attr_native_min_value or value > self._attr_native_max_value:
                _LOGGER.error("Value out of range: %s", value)
                return

            payload_value = str(value)

            # Some ducted zone controllers reject float strings (e.g. "0.0").
            # For zone damper keys, send integer strings like "0"/"100".
            key_lower = self._number_key.lower()
            if "zone" in key_lower and (
                key_lower.startswith("aus_zone")
                or key_lower.startswith("t_zone")
                or "opencontrol" in key_lower
            ):
                payload_value = str(int(round(value)))

            await self.coordinator.async_control_device(
                puid=self._device_id,
                properties={self._number_key: payload_value},
            )
        except Exception as err:
            _LOGGER.error("Failed to set %s: %s", self._attr_name, err)
