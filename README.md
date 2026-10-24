# Atmy Air Quality for Home Assistant

PM2.5 of your city from [Atmy](https://atmy.ai): public and citizen sensor networks (Sensor.Community, AirGradient, Nebo and others) after the Atmy Data Hub's quality check, refreshed every 15 minutes. No account and no key.

## Sensors

| Entity | What it shows |
|---|---|
| PM2.5 | The city's mean PM2.5 now, µg/m³ (attributes: min, max, median) |
| US AQI | The US EPA air quality index (2024 scale) from that PM2.5 |
| Air quality | Good, moderate, unhealthy for sensitive groups, unhealthy, very unhealthy, hazardous |
| PM2.5 yesterday | The last completed day on the Atmy Data Hub |
| Pollution accumulation | 0–100: how strongly the weather keeps particles near the ground now (attributes: the next 24 hours, the maximum of the next 12) |
| Sensors, Updated | Diagnostics: sensors in the mean and their networks, the time of the values |

## Install

**HACS:** HACS → ⋮ → Custom repositories → add `https://github.com/Atmy-ai/atmy-home-assistant`, category *Integration* → install *Atmy Air Quality* → restart Home Assistant.

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Atmy-ai&repository=atmy-home-assistant&category=integration)

**Manually:** copy `custom_components/atmy` into `config/custom_components/` and restart Home Assistant.

Then Settings → Devices & services → Add integration → **Atmy**. Leave the city empty to use the city nearest to your home (within 50 km), or type a city name in any language. Add the integration again for more cities.

## Data

Documentation: https://atmy.ai/developers/home-assistant/ · Issues: https://github.com/Atmy-ai/atmy-home-assistant/issues


Values are approximate: low-cost optical sensors, not official monitoring. Methodology: https://atmy.ai/air-quality/methodology/ · API: https://atmy.ai/air-quality/api/ · Data terms: https://atmy.ai/legal/data/
