import requests
import time
from utils.logger import logger

class RoadQualityEstimator:
    """
    Estimates road difficulty using OpenStreetMap data.
    Returns a score where higher = worse road.
    """

    def __init__(self):
        self.overpass_url = "https://overpass.kumi.systems/api/interpreter"
        self._cache = {}

    def estimate_difficulty(self, coords, max_samples=10):
        """
        Returns average road difficulty along a set of coordinates.
        Higher value = worse road.
        """
        if not coords:
            logger.warning("Empty coordinate list passed to RoadQualityEstimator.")
            return 0.3  # fallback neutral difficulty

        coords = self._sample_coords(coords, max_samples)
        difficulties = []

        for lat, lon in coords:
            difficulty = self._query_osm_difficulty(lat, lon)
            difficulties.append(difficulty)
            time.sleep(1.2)  # polite delay to avoid rate limiting

        avg_difficulty = sum(difficulties) / len(difficulties)
        return max(0, min(avg_difficulty, 1))

    def _sample_coords(self, coords, max_points):
        if len(coords) <= max_points:
            return coords
        step = max(1, len(coords) // max_points)
        return coords[::step]

    def _query_osm_difficulty(self, lat, lon):
        """
        Returns road difficulty (higher = worse) for a single point.
        """
        key = f"{lat:.5f},{lon:.5f}"
        if key in self._cache:
            return self._cache[key]

        query = f"""
        [out:json][timeout:25];
        way(around:50,{lat},{lon})[highway];
        out tags;
        """
        try:
            response = requests.get(self.overpass_url, params={"data": query}, timeout=30)
            response.raise_for_status()
            data = response.json()
            elements = data.get("elements", [])
            if not elements:
                quality = 0.6
            else:
                tags = elements[0].get("tags", {})
                highway = tags.get("highway", "")
                surface = tags.get("surface", "asphalt")
                lanes = int(tags.get("lanes", "2")) if tags.get("lanes", "2").isdigit() else 2

                type_score = {
                    "motorway": 1.0, "trunk": 0.9, "primary": 0.8,
                    "secondary": 0.7, "tertiary": 0.6, "residential": 0.5,
                    "unclassified": 0.5, "service": 0.4
                }.get(highway, 0.5)

                surface_score = {
                    "asphalt": 1.0, "concrete": 0.9, "paved": 0.8,
                    "gravel": 0.5, "unpaved": 0.3
                }.get(surface, 0.7)

                lane_score = min(lanes / 4, 1.0)
                quality = 0.5 * type_score + 0.3 * surface_score + 0.2 * lane_score

            # complement: difficulty = 1 - quality
            difficulty = max(0, min(quality, 1))
            self._cache[key] = difficulty
            return difficulty
        except Exception as e:
            logger.error(f"Overpass API request failed or invalid data: {e}")
            return 0.3  # fallback neutral difficulty