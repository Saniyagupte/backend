
import requests
from urllib.parse import urlencode
from utils.logger import logger

class RouteScorer:
    def __init__(self, weights: dict):
        self.weights = weights

    def score(self, complexity, sensory, road_quality, weather, familiarity):
        score = (
            self.weights["complexity"] * ( complexity) +
            self.weights["sensory"] * (sensory) +
            self.weights["road_quality"] *(1- road_quality) +
            self.weights["weather"] * ( weather) +
            self.weights["familiarity"] * ( 1- familiarity) 
        )
        return score
