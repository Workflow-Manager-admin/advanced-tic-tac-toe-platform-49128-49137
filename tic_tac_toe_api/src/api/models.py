"""Models for ORM/database and API schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr

# ---------------------------
# API Schemas for FastAPI
# ---------------------------

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Payload for user registration."""
    username: str = Field(..., description="Desired username")
    email: EmailStr = Field(..., description="User's email")
    password: str = Field(..., description="Desired password")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """Payload for user login."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="User's password")

# PUBLIC_INTERFACE
class UserInfo(BaseModel):
    """User info returned to clients."""
    id: int
    username: str
    email: EmailStr
    created_at: datetime

# PUBLIC_INTERFACE
class TokenResponse(BaseModel):
    """Response with JWT token after authentication."""
    access_token: str
    token_type: str = "bearer"

# PUBLIC_INTERFACE
class GameCreate(BaseModel):
    """Payload for creating a new game."""
    pass

# PUBLIC_INTERFACE
class GameJoin(BaseModel):
    """Payload for joining a game."""
    game_id: int

# PUBLIC_INTERFACE
class GameMoveRequest(BaseModel):
    """Payload for making a move."""
    game_id: int
    cell_position: int = Field(..., ge=0, le=8, description="Position on 3x3 grid (0-8)")

# PUBLIC_INTERFACE
class MoveInfo(BaseModel):
    """Info about an individual move."""
    move_number: int
    cell_position: int
    symbol: str
    player_id: int
    created_at: datetime

# PUBLIC_INTERFACE
class GameStatus(BaseModel):
    """Current state of a specific game."""
    id: int
    player_x_id: int
    player_o_id: Optional[int]
    winner_id: Optional[int]
    status: str
    board_state: str
    moves_count: int
    moves: List[MoveInfo]
    created_at: datetime
    updated_at: datetime

# PUBLIC_INTERFACE
class GameSummary(BaseModel):
    """Short summary of a game for lists/match history."""
    id: int
    opponent_username: str
    is_winner: Optional[bool]
    status: str
    created_at: datetime

# PUBLIC_INTERFACE
class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    user_id: int
    username: str
    wins: int
    losses: int
    draws: int
    games_played: int
    last_played: Optional[datetime]

# ---------------------------
# DB/ORM Models (for SQL results, internal, not exposed!!)
# You can use NamedTuple or custom classes if needed.
# ---------------------------
