import requests
from geopy.geocoders import Nominatim
from utils.logger import logger

class WeatherFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def get_weather_impact(self, lat, lon):
        """
        Returns a weather impact score between 0 (no impact) and 1 (high impact)
        based on OpenWeatherMap weather codes.
        """
        try:
            params = {"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"}
            resp = requests.get(self.base_url, params=params)
            resp.raise_for_status()  # Raise error for bad HTTP responses
            data = resp.json()
            weather_id = data["weather"][0]["id"]

            # Clear sky
            if weather_id == 800:
                return 0.1
            # Few clouds / scattered clouds
            elif weather_id in [801, 802]:
                return 0.3
            # Broken clouds / overcast
            elif weather_id in [803, 804]:
                return 0.4
            # Drizzle
            elif 300 <= weather_id < 400:
                return 0.5
            # Rain
            elif 500 <= weather_id < 600:
                return 0.6
            # Snow
            elif 600 <= weather_id < 700:
                return 0.7
            # Thunderstorm
            elif 200 <= weather_id < 300:
                return 0.9
            # Extreme weather (tornado, hurricane, etc.)
            elif 900 <= weather_id < 1000:
                return 1.0
            else:
                return 0.5  # Default for unknown codes

        except requests.exceptions.RequestException as e:
            logger.error(f"Weather fetch HTTP error: {e}")
            return 0.5
        except KeyError as e:
            logger.error(f"Weather fetch data error: {e}")
            return 0.5
        except Exception as e:
            logger.error(f"Unexpected weather fetch error: {e}")
            return 0.5
