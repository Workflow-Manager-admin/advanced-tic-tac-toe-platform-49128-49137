"""FastAPI API endpoints for users, games, moves, leaderboard."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Dict

from src.api.models import (
    UserCreate, UserInfo, TokenResponse,
    GameJoin, GameMoveRequest,
    GameStatus, GameSummary, LeaderboardEntry
)
from src.api.db import Database
from src.api.auth_utils import (
    hash_password, verify_password, create_access_token, decode_access_token
)
from src.api.game_service import (
    create_game, join_game, get_available_games, get_game_status, make_move,
    get_leaderboard, get_match_history
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Utility for dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user_id = payload["user_id"]
    pool = await Database.get_conn()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id, username, email, created_at FROM users WHERE id=$1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(user)

@router.post("/auth/register", response_model=UserInfo, tags=["Auth"])
async def register_user(user: UserCreate):
    """Register a new user."""
    pool = await Database.get_conn()
    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT 1 FROM users WHERE username=$1 OR email=$2", user.username, user.email)
        if exists:
            raise HTTPException(status_code=409, detail="Username or email already in use")
        hashed_pw = hash_password(user.password)
        rec = await conn.fetchrow("""
            INSERT INTO users (username, email, hashed_password)
            VALUES ($1, $2, $3)
            RETURNING id, username, email, created_at
        """, user.username, user.email, hashed_pw)
        return UserInfo(**dict(rec))

@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token."""
    pool = await Database.get_conn()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE username=$1", form_data.username)
        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        token = create_access_token({"user_id": user["id"]})
        return TokenResponse(access_token=token)

@router.post("/games/", response_model=GameStatus, tags=["Games"])
async def create_new_game(current_user=Depends(get_current_user)):
    """Start a new Tic Tac Toe game (as X, waiting for opponent)."""
    gid = await create_game(current_user["id"])
    return await get_game_status(gid, current_user["id"])

@router.post("/games/join", response_model=GameStatus, tags=["Games"])
async def join_existing_game(join_req: GameJoin, current_user=Depends(get_current_user)):
    """Join another player's waiting game (become O)."""
    result = await join_game(current_user["id"], join_req.game_id)
    if not result:
        raise HTTPException(status_code=400, detail="Could not join game (maybe already started or invalid)")
    return result

@router.get("/games/available", response_model=List[Dict], tags=["Games"])
async def available_games():
    """List games waiting for a player_o."""
    return await get_available_games()

@router.get("/games/{game_id}/status", response_model=GameStatus, tags=["Games"])
async def retrieve_game_status(game_id: int, current_user=Depends(get_current_user)):
    """Fetch the status and state of a specified game."""
    status_ = await get_game_status(game_id, current_user["id"])
    if not status_:
        raise HTTPException(status_code=404, detail="Game not found")
    return status_

@router.post("/games/move", response_model=GameStatus, tags=["Games"])
async def play_move(move: GameMoveRequest, current_user=Depends(get_current_user)):
    """Submit a move to the game (place X or O)."""
    game_info = await get_game_status(move.game_id, current_user["id"])
    if not game_info:
        raise HTTPException(status_code=404, detail="Game not found")
    user_symbol = "X" if game_info["player_x_id"] == current_user["id"] else "O"
    result = await make_move(move.game_id, current_user["id"], move.cell_position, user_symbol)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/leaderboard", response_model=List[LeaderboardEntry], tags=["Leaderboard"])
async def fetch_leaderboard():
    """Fetch the current leaderboard."""
    return await get_leaderboard(limit=10)

@router.get("/history", response_model=List[GameSummary], tags=["History"])
async def fetch_match_history(current_user=Depends(get_current_user)):
    """Show your recent match history (finished games)."""
    return await get_match_history(current_user["id"])
