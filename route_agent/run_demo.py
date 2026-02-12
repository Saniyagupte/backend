import sys
import os
import polyline

# Add the 'src' directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

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

from main import plan_route

if __name__ == "__main__":
    user_id = "user123"
    start = "18.50170815128427,73.8092765250197"        # home
    destination = "18.489838882873816,73.85283698022204" # college

    route = plan_route(user_id, start, destination)
    print("Planned Route:")
    coordinates = polyline.decode(route["geometry"])
    coordinates = sample_coordinates(coordinates, n=5)
    print(coordinates)
