"""Polls one city's air quality now and its forecast."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AtmyApi, AtmyError
from .const import CONF_CITY, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AtmyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: AtmyApi) -> None:
        super().__init__(hass, _LOGGER, name=f"{DOMAIN} {entry.title}", update_interval=UPDATE_INTERVAL, config_entry=entry)
        self.api = api
        self.city = entry.data[CONF_CITY]

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            current = await self.api.current(city=self.city)
        except AtmyError as err:
            raise UpdateFailed(f"Atmy: {err}") from err
        try:
            forecast = await self.api.forecast(self.city)
        except AtmyError:
            # The forecast only adds the accumulation index; the air values stand without it.
            forecast = None
        return {"current": current, "forecast": forecast}
