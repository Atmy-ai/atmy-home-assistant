"""Atmy air quality: PM2.5 of a city from public and citizen sensor networks (https://atmy.ai)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AtmyApi
from .const import LANGUAGES
from .coordinator import AtmyCoordinator

PLATFORMS = [Platform.SENSOR]

type AtmyConfigEntry = ConfigEntry[AtmyCoordinator]


def api_language(hass: HomeAssistant) -> str:
    language = hass.config.language or "en"
    return language if language in LANGUAGES else language.split("-")[0] if language.split("-")[0] in LANGUAGES else "en"


async def async_setup_entry(hass: HomeAssistant, entry: AtmyConfigEntry) -> bool:
    coordinator = AtmyCoordinator(hass, entry, AtmyApi(async_get_clientsession(hass), api_language(hass)))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AtmyConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
