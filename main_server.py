import sys
from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
ROUTE_AGENT_SRC = BASE_DIR / "route_agent" / "src"
sys.path.append(str(ROUTE_AGENT_SRC))

# --- FastAPI imports ---
from fastapi import FastAPI
from pydantic import BaseModel
import polyline

# --- Import your route planner ---
from main import plan_route

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

app = FastAPI()

# ----- CORS Setup -----
origins = [
    "http://localhost:54222",  # your Flutter Web local URL
    "http://127.0.0.1:54222",  # alternative localhost URL
    "*"  # ⚠️ for testing only, allow all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: show the paths
config_path = BASE_DIR / "route_agent" / "config" / "config.yaml"
print("Config path being used:", config_path)

# --- Request schema ---
class RouteRequest(BaseModel):
    user_id: str
    source: str
    destination: str

# --- API endpoint ---
@app.post("/get_route")
def get_route(data: RouteRequest):
    print("Route request received")
    print(data)

    best_route = plan_route(
        user_id=data.user_id,
        start=data.source,
        destination=data.destination
    )

    if not best_route:
        return {"status": "error", "message": "No route found"}

    # decode polyline to coordinates
    coords = polyline.decode(best_route["geometry"])

    return {
        "status": "success",
        "route": coords
    }
