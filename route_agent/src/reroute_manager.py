from utils.logger import logger

class RerouteManager:
    def should_reroute(self, stress_level, route_score, threshold=0.7):
        if stress_level > threshold:
            logger.info("High stress: rerouting needed")
            return True
        if route_score < 0.5:
            logger.info("Low route score: rerouting needed")
            return True
        return False
