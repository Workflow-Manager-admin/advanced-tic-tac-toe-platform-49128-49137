from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as main_router
from src.api.db import Database

app = FastAPI(
    title="Advanced Tic Tac Toe Platform API",
    description="Backend API for advanced Tic Tac Toe game. Handles authentication, game logic, game management, leaderboards, and player history.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Auth", "description": "User authentication and management"},
        {"name": "Games", "description": "Start/join/play Tic Tac Toe games"},
        {"name": "Leaderboard", "description": "Player rankings"},
        {"name": "History", "description": "Match/move history"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await Database.connect()

@app.on_event("shutdown")
async def on_shutdown():
    await Database.close()

@app.get("/", tags=["Health"])
def health_check():
    """API health check."""
    return {"message": "Healthy"}

# Mount main API routes:
app.include_router(main_router)
