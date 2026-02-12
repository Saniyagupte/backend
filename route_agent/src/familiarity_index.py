# familiarity_index.py

import json
from pathlib import Path
import hashlib

class FamiliarityIndex:
    def __init__(self, cache_file=None):
        # --- make path relative to this file ---
        base_dir = Path(__file__).resolve().parent  # src/
        default_cache = base_dir.parent / "data" / "cached_routes.json"
        
        self.cache_file = Path(cache_file) if cache_file else default_cache
        
        # ensure parent directory exists
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # create empty cache if file doesn't exist
        if not self.cache_file.exists():
            self.cache_file.write_text(json.dumps({}))

    def _hash_route(self, coordinates):
        """
        Create a consistent hash for a list of coordinates.
        """
        coord_string = "|".join(f"{lat:.5f},{lng:.5f}" for lat, lng in coordinates)
        return hashlib.md5(coord_string.encode()).hexdigest()

    def get_score(self, user_id, route):
        try:
            coordinates = route.get("decoded_geometry")  # expects decoded polyline
            route_hash = self._hash_route(coordinates)

            with open(self.cache_file, "r") as f:
                cache = json.load(f)

            return cache.get(route_hash, 0) / 5.0  # normalize: 5+ = max familiarity
        except Exception:
            return 0.0

    def update(self, route):
        try:
            coordinates = route.get("decoded_geometry")
            route_hash = self._hash_route(coordinates)

            if self.cache_file.exists():
                with open(self.cache_file, "r") as f:
                    cache = json.load(f)
            else:
                cache = {}

            cache[route_hash] = cache.get(route_hash, 0) + 1

            with open(self.cache_file, "w") as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"Failed to update familiarity cache: {e}")
