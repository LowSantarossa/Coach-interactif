import requests
from config import GRANBY_LAT, GRANBY_LON

WMO_CODES = {
    0: "Ciel dégagé ☀️",
    1: "Principalement dégagé 🌤️",
    2: "Partiellement nuageux ⛅",
    3: "Couvert ☁️",
    45: "Brouillard 🌫️",
    48: "Brouillard givrant 🌫️",
    51: "Bruine légère 🌦️",
    53: "Bruine modérée 🌦️",
    55: "Bruine dense 🌧️",
    61: "Pluie faible 🌧️",
    63: "Pluie modérée 🌧️",
    65: "Pluie forte 🌧️",
    66: "Pluie verglaçante légère 🧊",
    67: "Pluie verglaçante forte 🧊",
    71: "Neige faible 🌨️",
    73: "Neige modérée 🌨️",
    75: "Neige forte ❄️",
    77: "Grains de neige ❄️",
    80: "Averses de pluie faibles 🌦️",
    81: "Averses de pluie modérées 🌧️",
    82: "Averses de pluie violentes ⛈️",
    85: "Averses de neige faibles 🌨️",
    86: "Averses de neige fortes ❄️",
    95: "Orage ⛈️",
}

def get_weather_granby() -> dict:
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={GRANBY_LAT}&longitude={GRANBY_LON}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&timezone=America%2FToronto&forecast_days=3"
    )
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        curr = data.get("current", {})
        code = curr.get("weather_code", 0)
        temp = curr.get("temperature_2m", 0)
        feels = curr.get("apparent_temperature", 0)
        wind = curr.get("wind_speed_10m", 0)
        precip = curr.get("precipitation", 0)

        # Logique de recommandation Course extérieure vs Tapis Horizon T202
        if code in [65, 66, 67, 75, 82, 86, 95] or feels < -18 or wind > 45:
            conseil = "Tapis Horizon T202 recommandé (conditions extérieures difficiles)."
        elif precip > 0 or feels < -8 or wind > 30:
            conseil = "Sortie possible avec équipement adapté, ou option Tapis Horizon T202."
        else:
            conseil = "Conditions idéales pour courir dehors à Granby !"

        return {
            "ok": True,
            "temp": temp,
            "feels_like": feels,
            "humidity": curr.get("relative_humidity_2m", 0),
            "wind": wind,
            "precip": precip,
            "description": WMO_CODES.get(code, "Conditions variables"),
            "conseil": conseil,
            "daily": data.get("daily", {})
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
