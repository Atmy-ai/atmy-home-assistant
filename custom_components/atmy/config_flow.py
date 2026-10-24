"""Set up Atmy in the UI: the city nearest to home, or one found by name."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import api_language
from .api import AtmyApi, AtmyError
from .const import CONF_CITY, CONF_CITY_ID, DOMAIN

CONF_QUERY = "query"
ERRORS = {"unknown_city": "not_found", "no_city_nearby": "no_city_nearby", "cannot_connect": "cannot_connect"}


class AtmyConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._choices: dict[str, dict[str, Any]] = {}

    def _api(self) -> AtmyApi:
        return AtmyApi(async_get_clientsession(self.hass), api_language(self.hass))

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            query = (user_input.get(CONF_QUERY) or "").strip()
            try:
                if not query:
                    # Empty: the city with an Atmy summary nearest to home (within 50 km).
                    city = (await self._api().current(lat=self.hass.config.latitude, lon=self.hass.config.longitude))["city"]
                    return await self._create(city)
                cities = await self._api().cities(query)
            except AtmyError as err:
                errors["base"] = ERRORS.get(err.code, "cannot_connect")
            else:
                if not cities:
                    errors["base"] = "not_found"
                elif len(cities) == 1:
                    return await self._create(cities[0])
                else:
                    self._choices = {city["slug"]: city for city in cities[:50]}
                    return await self.async_step_pick()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Optional(CONF_QUERY, default=""): str}), errors=errors)

    async def async_step_pick(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return await self._create(self._choices[user_input[CONF_CITY]])
        options = {slug: f"{city.get('name')}, {city.get('country')}" for slug, city in self._choices.items()}
        return self.async_show_form(step_id="pick", data_schema=vol.Schema({vol.Required(CONF_CITY): vol.In(options)}))

    async def _create(self, city: dict[str, Any]) -> ConfigFlowResult:
        await self.async_set_unique_id(str(city["id"]))
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=f"{city.get('name')}, {city.get('country')}",
                                       data={CONF_CITY: city["slug"], CONF_CITY_ID: city["id"]})
