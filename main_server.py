import sys
from pathlib import Path

# -------- FASTAPI --------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import polyline

# -------- PATH SETUP --------
BASE_DIR = Path(__file__).resolve().parent

VOICE_AGENT = BASE_DIR / "voice_agent"
RELAX_AGENT = BASE_DIR / "relaxation_agent"
ROUTE_AGENT = BASE_DIR / "route_agent" / "src"

sys.path.append(str(VOICE_AGENT.resolve()))
sys.path.append(str(RELAX_AGENT.resolve()))
sys.path.append(str(ROUTE_AGENT.resolve()))

# -------- IMPORT AGENTS --------
from route_agent.src.main import plan_route                # route_agent/src/main.py
# from voice_processor import process_audio  # voice_agent
# from relax_engine import analyze_stress    # relaxation_agent

# -------- APP INIT --------
app = FastAPI(title="NeuroDrive AI Backend")

# -------- CORS (IMPORTANT) --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all for now (mobile testing)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- ROOT TEST --------
@app.get("/")
def home():
    return {"status": "Backend running successfully"}

# =========================================
# 📍 ROUTE REQUEST MODEL
# =========================================
class RouteRequest(BaseModel):
    user_id: str
    source: str
    destination: str

# =========================================
# 🧭 ROUTE ENDPOINT
# =========================================
@app.post("/get_route")
def get_route(data: RouteRequest):

    best_route = plan_route(
        user_id=data.user_id,
        start=data.source,
        destination=data.destination,
    )

    if not best_route:
        return {"status": "error", "message": "No route found"}

    coords = polyline.decode(best_route["geometry"])

    return {
        "status": "success",
        "route": coords,
    }

# # =========================================
# # 🎤 VOICE REQUEST MODEL
# # =========================================
# class VoiceRequest(BaseModel):
#     user_id: str
#     audio_path: str   # path inside backend server

# # =========================================
# # 🧠 VOICE → STRESS → RELAX ENDPOINT
# # =========================================
# @app.post("/process_voice")
# def process_voice(data: VoiceRequest):

#     print("Voice received from:", data.user_id)

#     # ---- STEP 1: Voice to text + features ----
#     voice_out = process_audio(data.audio_path)

#     text = voice_out.get("text", "")
#     features = voice_out.get("features", {})

#     print("Recognized text:", text)

#     # ---- STEP 2: Stress analysis ----
#     relax = analyze_stress(text, features, data.user_id)

#     stress = relax.get("stress_score", 0)
#     emotion = relax.get("emotion", "neutral")
#     coping = relax.get("coping_text", "")
#     voice_style = relax.get("voice_style", "neutral")

#     print("Stress:", stress)
#     print("Coping:", coping)

#     return {
#         "status": "processed",
#         "text": text,
#         "emotion": emotion,
#         "stress": stress,
#         "coping": coping,
#         "voice_style": voice_style
#     }
