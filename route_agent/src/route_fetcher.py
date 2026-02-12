import requests
from utils.logger import logger

class RouteFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openrouteservice.org/v2/directions/driving-car"

    def fetch_all_routes(self, start, destination):
        # ORS expects coordinates in [lng, lat] order, so you need to geocode addresses first or supply coords
        # For simplicity, let's assume start and destination are lat,lng strings "lat,lng"

        try:
            start_coords = self._geocode(start)  # returns [lng, lat]
            dest_coords = self._geocode(destination)

            headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }

            body = {
                "coordinates": [start_coords, dest_coords],
                "alternative_routes": {
                    "target_count": 3,       #List of 3 routes required 
                    "share_factor": 0.4,    #Should share atleast 40% path with mainroute
                    "weight_factor": 1.4     #routes up to 40% less optimal than main route
                }
            }

            response = requests.post(self.base_url, json=body, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch route from OpenRouteService: {response.text}")
                return []

            data = response.json()

            if "routes" not in data or len(data["routes"]) == 0:
                logger.warning("No routes found")
                return []

            routes = []
            for route in data["routes"]:
                segment = route["segments"][0]
                route_info = {
                    "start": start,
                    "destination": destination,
                    "distance": segment["distance"] / 1000,   #convert to kilometers 
                    "duration": segment["duration"] / 60,     #Convert to minutes
                    "num_turns": len(segment.get("steps", [])),
                    "geometry": route.get("geometry"),
                }
                routes.append(route_info)

            return routes


        except Exception as e:
            logger.error(f"Error parsing route data: {e}")
            return []


    def _geocode(self, location):
        print(f"Geocoding location input: '{location}'")  # Debug line
        if "," in location:
            parts = location.split(",")
            print(f"Split parts: {parts}")
            if len(parts) != 2:
                raise ValueError(f"Expected 2 parts for lat,lng, got {len(parts)}: {parts}")
            lat_str, lng_str = parts
            return [float(lng_str.strip()), float(lat_str.strip())]  # ORS expects [lng, lat]
        else:
            raise ValueError(f"Geocoding not implemented for location '{location}'")

