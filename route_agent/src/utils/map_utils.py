from geopy.distance import geodesic

def haversine_distance(coord1, coord2):
    """Return distance in km"""
    return geodesic(coord1, coord2).km
