"""Constants of the Atmy integration."""

from datetime import timedelta

DOMAIN = "atmy"
API = "https://api.atmy.ai/v1"
# The city values are recomputed every 15 minutes.
UPDATE_INTERVAL = timedelta(minutes=15)
CONF_CITY = "city"
CONF_CITY_ID = "city_id"
ATTRIBUTION = "Atmy (atmy.ai): public and citizen sensor networks; approximate values, not official monitoring."
# Languages of city and country names on Atmy.
LANGUAGES = {"en", "ru", "de", "fr", "es", "it", "pt-BR", "pl", "cs", "hu", "ro", "bg", "sr", "id", "hi", "ja", "zh",
             "uz", "kk", "ky", "tg", "az", "ka", "hy", "tr"}
LEVELS = ["good", "moderate", "sensitive", "unhealthy", "very_unhealthy", "hazardous"]
