"""Atmy sensors: PM2.5 now, US AQI, level, yesterday's PM2.5, the pollution accumulation index, the weather Atmy keeps for the city, sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import (CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, PERCENTAGE, EntityCategory, UnitOfPressure, UnitOfSpeed,
                                 UnitOfTemperature)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AtmyConfigEntry
from .const import ATTRIBUTION, CONF_CITY_ID, DOMAIN, LEVELS
from .coordinator import AtmyCoordinator

# US EPA PM2.5 breakpoints (2024 revision): concentration low/high to index low/high.
EPA_2024 = [(0.0, 9.0, 0, 50), (9.1, 35.4, 51, 100), (35.5, 55.4, 101, 150), (55.5, 125.4, 151, 200),
            (125.5, 225.4, 201, 300), (225.5, 325.4, 301, 500)]


def us_aqi(pm25: float | None) -> int | None:
    if pm25 is None:
        return None
    value = int(max(0.0, float(pm25)) * 10) / 10  # truncated to one decimal, as the EPA does
    for c_low, c_high, i_low, i_high in EPA_2024:
        if value <= c_high:
            return round((i_high - i_low) / (c_high - c_low) * (value - c_low) + i_low)
    return 500


def _now(data: dict[str, Any]) -> dict[str, Any]:
    now = data["current"].get("now") or {}
    # A stale city (no fresh readings) has no value now rather than an old one.
    return now if now.get("status") == "current" else {}


def _weather(data: dict[str, Any]) -> dict[str, Any]:
    # Weather from Atmy's own server: the city's latest reading (the API never asks a provider for it).
    return data["current"].get("weather") or {}


def _hours(data: dict[str, Any]) -> list[dict[str, Any]]:
    return (data.get("forecast") or {}).get("hours") or []


def _accumulation_now(data: dict[str, Any]) -> int | None:
    hours = _hours(data)
    return hours[0].get("accumulation_risk") if hours else None


def _accumulation_attributes(data: dict[str, Any]) -> dict[str, Any]:
    hours = _hours(data)[:24]
    risks = [row.get("accumulation_risk") for row in hours[:12] if row.get("accumulation_risk") is not None]
    return {"max_next_12_hours": max(risks) if risks else None,
            "forecast": [{"time": row.get("time"), "risk": row.get("accumulation_risk")} for row in hours]}


def _updated_at(data: dict[str, Any]) -> datetime | None:
    value = _now(data).get("updated_at")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc) if value else None
    except ValueError:
        return None


@dataclass(frozen=True, kw_only=True)
class AtmySensorDescription(SensorEntityDescription):
    value: Callable[[dict[str, Any]], Any]
    attributes: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSORS: tuple[AtmySensorDescription, ...] = (
    AtmySensorDescription(key="pm25", translation_key="pm25", device_class=SensorDeviceClass.PM25,
                          native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, state_class=SensorStateClass.MEASUREMENT,
                          suggested_display_precision=1, value=lambda d: _now(d).get("pm25"),
                          attributes=lambda d: {"min": _now(d).get("min"), "max": _now(d).get("max"), "median": _now(d).get("median"),
                                                "updated_at": _now(d).get("updated_at")}),
    AtmySensorDescription(key="aqi", translation_key="aqi", device_class=SensorDeviceClass.AQI, state_class=SensorStateClass.MEASUREMENT,
                          value=lambda d: us_aqi(_now(d).get("pm25"))),
    AtmySensorDescription(key="level", translation_key="level", device_class=SensorDeviceClass.ENUM, options=LEVELS,
                          value=lambda d: ((_now(d).get("category") or {}).get("level"))),
    AtmySensorDescription(key="pm25_yesterday", translation_key="pm25_yesterday", device_class=SensorDeviceClass.PM25,
                          native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, suggested_display_precision=1,
                          value=lambda d: (d["current"].get("completed_day") or {}).get("pm25"),
                          attributes=lambda d: {"date": (d["current"].get("completed_day") or {}).get("date"),
                                                "sensors": (d["current"].get("completed_day") or {}).get("sensors")}),
    AtmySensorDescription(key="accumulation_risk", translation_key="accumulation_risk", native_unit_of_measurement="%",
                          state_class=SensorStateClass.MEASUREMENT, icon="mdi:weather-fog", value=_accumulation_now,
                          attributes=_accumulation_attributes),
    AtmySensorDescription(key="temperature", translation_key="temperature", device_class=SensorDeviceClass.TEMPERATURE,
                          native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
                          value=lambda d: _weather(d).get("temperature_c"),
                          attributes=lambda d: {"feels_like": _weather(d).get("feels_like_c"), "condition": _weather(d).get("condition"),
                                                "observed_at": _weather(d).get("observed_at")}),
    AtmySensorDescription(key="humidity", translation_key="humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE,
                          state_class=SensorStateClass.MEASUREMENT, value=lambda d: _weather(d).get("humidity_percent")),
    AtmySensorDescription(key="pressure", translation_key="pressure", device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
                          native_unit_of_measurement=UnitOfPressure.HPA, state_class=SensorStateClass.MEASUREMENT, value=lambda d: _weather(d).get("pressure_hpa")),
    AtmySensorDescription(key="wind_speed", translation_key="wind_speed", device_class=SensorDeviceClass.WIND_SPEED,
                          native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
                          value=lambda d: _weather(d).get("wind_m_s"), attributes=lambda d: {"direction": _weather(d).get("wind_direction_deg")}),
    AtmySensorDescription(key="wind_gust", translation_key="wind_gust", device_class=SensorDeviceClass.WIND_SPEED,
                          native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
                          value=lambda d: _weather(d).get("wind_gust_m_s")),
    AtmySensorDescription(key="sensors", translation_key="sensors", state_class=SensorStateClass.MEASUREMENT, icon="mdi:access-point-network",
                          entity_category=EntityCategory.DIAGNOSTIC, value=lambda d: _now(d).get("sensors"),
                          attributes=lambda d: {"networks": (d["current"].get("sources") or {}).get("networks")}),
    AtmySensorDescription(key="updated", translation_key="updated", device_class=SensorDeviceClass.TIMESTAMP,
                          entity_category=EntityCategory.DIAGNOSTIC, value=_updated_at),
)


async def async_setup_entry(hass: HomeAssistant, entry: AtmyConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(AtmySensor(entry.runtime_data, description) for description in SENSORS)


class AtmySensor(CoordinatorEntity[AtmyCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    entity_description: AtmySensorDescription

    def __init__(self, coordinator: AtmyCoordinator, description: AtmySensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        city = coordinator.data["current"].get("city") or {}
        self._attr_unique_id = f"{entry.data[CONF_CITY_ID]}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, str(entry.data[CONF_CITY_ID]))}, name=entry.title, manufacturer="Atmy",
                                            model="City air quality", entry_type=DeviceEntryType.SERVICE,
                                            configuration_url=city.get("page") or "https://atmy.ai")

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self.entity_description.attributes(self.coordinator.data) if self.entity_description.attributes else None
