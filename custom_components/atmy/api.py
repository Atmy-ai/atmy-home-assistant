"""The Atmy public API for agents (https://api.atmy.ai/v1): read-only, no key."""

from __future__ import annotations

from typing import Any

import aiohttp

from .const import API


class AtmyError(Exception):
    """The API answered with an error; `code` is its error code (unknown_city, no_city_nearby, ...)."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


class AtmyApi:
    def __init__(self, session: aiohttp.ClientSession, language: str = "en") -> None:
        self._session = session
        self._language = language

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        query = {key: value for key, value in params.items() if value is not None} | {"lang": self._language}
        try:
            async with self._session.get(f"{API}/{path}", params=query, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise AtmyError("cannot_connect", str(err)) from err
        if not isinstance(data, dict):
            raise AtmyError("cannot_connect", "unexpected answer")
        if "error" in data:
            raise AtmyError(str(data["error"].get("code", "unknown")), str(data["error"].get("message", "")))
        return data

    async def cities(self, query: str) -> list[dict[str, Any]]:
        return (await self._get("cities", {"q": query})).get("cities", [])

    async def current(self, city: str | None = None, lat: float | None = None, lon: float | None = None) -> dict[str, Any]:
        return await self._get("air-quality/current", {"city": city, "lat": lat, "lon": lon})

    async def forecast(self, city: str, hours: int = 24) -> dict[str, Any]:
        return await self._get("air-quality/forecast", {"city": city, "hours": hours})
