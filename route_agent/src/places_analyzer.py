import requests
from utils.logger import logger

class PlacesAnalyzer:
    """
    Analyzes nearby Points of Interest (POIs) using the Geoapify Places API
    to estimate a sensory overload score.
    """

    def __init__(self, api_key):
        self.api_key = api_key
        self.geoapify_url = "https://api.geoapify.com/v2/places"

    def get_sensory_score_for_route(self, locations):
        """
        Calculate sensory score across a list of lat,lng locations.
        """
        try:
            scores = [self.get_sensory_score(loc) for loc in locations]
            return sum(scores) / len(scores) if scores else 0.0
        except Exception as e:
            logger.error(f"Error in sensory route score: {e}")
            return 0.5

    def get_sensory_score(self, location):
        """
        Estimate sensory overload score for one location based on POI count.
        """
        try:
            lat, lng = map(float, location.split(","))
            poi_count = self.get_poi_count(lat, lng)
            max_pois = 50
            score = min(poi_count / max_pois, 1.0)
            return score
        except Exception as e:
            logger.error(f"Error in sensory score for {location}: {e}")
            return 0.5

    def get_poi_count(self, lat, lng, radius=1500):
        """
        Use Geoapify to count POIs around a given lat/lng within radius.
        Queries each category separately to avoid 400 errors.
        """
        categories_list = [
            "commercial.supermarket",
            "healthcare",
            "leisure.playground",
            "office.educational_institution"
        ]
        total_pois = 0

        for category in categories_list:
            filter_circle = f"circle:{lng},{lat},{radius}"
            params = {
                "categories": category,
                "filter": filter_circle,
                "limit": 100,
                "apiKey": self.api_key
            }

            try:
                response = requests.get(self.geoapify_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                total_pois += len(data.get("features", []))
            except Exception as e:
                logger.error(f"Geoapify API error for {category}: {e}")
                total_pois += 0

        return total_pois
