import logging
import sys
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "route_agent.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("route_agent")
