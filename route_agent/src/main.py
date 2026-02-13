# main.py
import yaml
from route_fetcher import RouteFetcher
from places_analyzer import PlacesAnalyzer
from weather_fetcher import WeatherFetcher
from road_quality_estimator import RoadQualityEstimator
from complexity_analyzer import ComplexityAnalyzer
from familiarity_index import FamiliarityIndex
from scorer import RouteScorer
from stress_listener import StressListener
from reroute_manager import RerouteManager
from utils.logger import logger
import polyline
from pathlib import Path
import yaml
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="neuro_route_agent")

BASE_DIR = Path(__file__).resolve().parent
config_path = BASE_DIR.parent / "config" / "config.yaml"

# Load config
with open(config_path) as f:
    config = yaml.safe_load(f)

import requests
from utils.logger import logger

def normalize_location(location: str) -> str:
    """
    Converts a place name or coordinates to 'lat,lon' format using Geoapify.
    """
    # If already coordinates
    if "," in location:
        parts = location.split(",")
        if len(parts) == 2:
            try:
                float(parts[0])
                float(parts[1])
                return location
            except ValueError:
                pass

    # Use Geoapify geocoding
    GEOAPIFY_API_KEY = config["api_keys"]["GEOAPIFY_API_KEY"]
    url = f"https://api.geoapify.com/v1/geocode/search?text={location}&apiKey={GEOAPIFY_API_KEY}"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"Geoapify request failed: {e}")
        raise ValueError("Geocoding service unavailable. Try again later.")

    features = data.get("features")
    if not features:
        raise ValueError(f"Could not geocode location: {location}")

    lat = features[0]["properties"]["lat"]
    lon = features[0]["properties"]["lon"]
    return f"{lat},{lon}"



# Initialize components
fetcher = RouteFetcher(config["api_keys"]["openrouteservice"])
places = PlacesAnalyzer(config["api_keys"]["GEOAPIFY_API_KEY"])
weather_fetcher = WeatherFetcher(config["api_keys"]["openweather"])
road_estimator = RoadQualityEstimator()
complexity_analyzer = ComplexityAnalyzer()
familiarity = FamiliarityIndex()
scorer = RouteScorer(config["route"]["weights"])
stress_listener = StressListener()
reroute_manager = RerouteManager()

# --- Helper function to reduce coordinates ---
def sample_coordinates(coords, n=5):
    """
    Reduce coordinates list to n roughly evenly spaced points.
    """
    if len(coords) <= n:
        return coords
    step = len(coords) / n
    sampled = [coords[int(i * step)] for i in range(n)]
    return sampled

# --- Main route planning function ---
from tabulate import tabulate  # add at the top of your file

def plan_route(user_id, start, destination, condition="adhd"):
    """
    condition: 'autism' or 'adhd'
    """
    # --- normalize inputs ---
    try:
        start_coords = normalize_location(start)
        destination_coords = normalize_location(destination)
    except ValueError as e:
        logger.error(str(e))
        return None

    logger.info(f"Using coordinates: {start_coords} -> {destination_coords}")
    logger.info(f"User condition: {condition}")

    # --- fetch routes ---
    routes = fetcher.fetch_all_routes(start_coords, destination_coords)

    if not routes:
        logger.error("No routes found.")
        return None

    best_score = float("inf")
    best_route = None
    best_sensory = float("inf")
    table_data = []

    for idx, route in enumerate(routes, start=1):
        # --- Always calculate common scores ---
        coordinates = polyline.decode(route["geometry"])
        coordinates = sample_coordinates(coordinates, n=5)

        weather_scores = [weather_fetcher.get_weather_impact(lat, lon) for lat, lon in coordinates]
        weather_score = max(weather_scores)

        familiarity_score = familiarity.get_score(user_id, route)
        stress_level = stress_listener.get_stress_level(user_id)
        road_quality_score = 0.7  # placeholder

        # --- Conditional scores based on user condition ---
        if condition == "autism":
            complexity_score = 0  # ignore complexity
            sensory_score = places.get_sensory_score_for_route([f"{lat},{lng}" for lat, lng in coordinates])
        elif condition == "adhd":
            complexity_score = complexity_analyzer.calculate(route)
            sensory_score = 0  # ignore sensory
        else:
            # default fallback
            complexity_score = complexity_analyzer.calculate(route)
            sensory_score = places.get_sensory_score_for_route([f"{lat},{lng}" for lat, lng in coordinates])

        # --- Compute final score using RouteScorer ---
        score = scorer.score(
            complexity=complexity_score,
            sensory=sensory_score,
            road_quality=road_quality_score,
            weather=weather_score,
            familiarity=familiarity_score
        )

        logger.info(
            f"Route {idx} | Score: {score:.2f} | "
            f"Complexity: {complexity_score:.2f} | "
            f"Sensory: {sensory_score:.2f} | "
            f"Weather: {weather_score:.2f}"
        )

        table_data.append([
            idx,
            f"{score:.2f}",
            f"{complexity_score:.2f}",
            f"{sensory_score:.2f}",
            f"{road_quality_score:.2f}",
            f"{weather_score:.2f}",
            f"{familiarity_score:.2f}",
            f"{stress_level:.2f}",
        ])

        if score < best_score or (score == best_score and sensory_score < best_sensory):
            best_score = score
            best_route = route
            best_sensory = sensory_score

    if table_data:
        from tabulate import tabulate
        print("\n=== Route Score Summary ===")
        headers = ["Route #", "Total Score", "Complexity", "Sensory", "Road Quality", "Weather", "Familiarity", "Stress"]
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))

    if best_route:
        familiarity.update(best_route)

    logger.info(f"Best route selected with score {best_score:.2f}")
    return best_route
