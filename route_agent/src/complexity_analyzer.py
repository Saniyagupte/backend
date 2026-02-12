from utils.logger import logger

class ComplexityAnalyzer:
    def calculate(self, route):
        try:
            turns_score = min(1.0, route["num_turns"] / 30)
            traffic_score = route.get("traffic_density", 0.5)
            time_per_km = route["duration"] / max(route["distance"], 0.1)
            time_score = min(1.0, time_per_km / 2.0)
            complexity = 0.4*turns_score + 0.4*traffic_score + 0.2*time_score
            return max(0, min(complexity,1))
        except Exception as e:
            logger.error(f"Error calculating complexity: {e}")
            return 0.5
