"""Optional providers. Demo data and live data use the same refresh interface."""
from datetime import datetime
import re
from .core import AuthenticationRequired

TIMEOUT = (5, 15)


def weather(config):
    import requests
    response = requests.get(
        "https://api.weatherapi.com/v1/forecast.json",
        params={"key": config.weather_key, "q": config.weather_location, "days": 2, "aqi": "no", "alerts": "no"},
        timeout=TIMEOUT, allow_redirects=False,
    )
    response.raise_for_status()
    data = response.json()
    # Use the provider's local hour, not the display computer's timezone.
    local_hour = int(data["location"]["localtime"].split(" ")[1].split(":")[0])
    day, hour, label = (0, 12, "Afternoon") if local_hour < 10 else (0, 18, "Evening") if local_hour < 16 else (1, 12, "Tomorrow")
    forecast = data["forecast"]["forecastday"][day]["hour"][hour]
    current = data["current"]
    return f"{current['temp_c']} °C · {current['condition']['text']}\n{label}: {forecast['temp_c']} °C · {forecast['condition']['text']}"


def instagram(config):
    import requests
    try:
        expiry = datetime.fromisoformat(config.token_expiry.replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.astimezone()
        if expiry <= datetime.now().astimezone():
            raise ValueError("Expired token")
    except (ValueError, TypeError):
        raise AuthenticationRequired() from None
    if not re.fullmatch(r"v[1-9][0-9]*\.[0-9]+", config.graph_version):
        raise ValueError("Configure a Graph API version before using Instagram.")
    if not config.instagram_id.isascii() or not config.instagram_id.isdigit():
        raise ValueError("Configure a numeric Instagram business account ID.")
    response = requests.get(
        f"https://graph.facebook.com/{config.graph_version}/{config.instagram_id}",
        headers={"Authorization": f"Bearer {config.access_token}"},
        params={"fields": "username,followers_count"}, timeout=TIMEOUT, allow_redirects=False,
    )
    if response.status_code in {401, 403}:
        raise AuthenticationRequired()
    if response.status_code >= 400:
        try:
            error = response.json().get("error", {})
        except (ValueError, AttributeError):
            error = {}
        # Graph token/session errors can use HTTP 400, not just 401/403.
        if isinstance(error, dict) and error.get("code") in {102, 190}:
            raise AuthenticationRequired()
    response.raise_for_status()
    data = response.json()
    return f"{int(data['followers_count']):,} followers\n@{data['username']}"


def configured_providers(config, *, demo=False):
    if demo:
        return {
            "Weather": lambda: "16 °C · Light cloud\nEvening: 14 °C · Partly cloudy · Sample data",
            "Instagram": lambda: "1,234 followers\n@example_account · Sample data",
        }
    providers = {}
    if config.weather_key and config.weather_location:
        providers["Weather"] = lambda: weather(config)
    if config.access_token and config.instagram_id:
        providers["Instagram"] = lambda: instagram(config)
    return providers
