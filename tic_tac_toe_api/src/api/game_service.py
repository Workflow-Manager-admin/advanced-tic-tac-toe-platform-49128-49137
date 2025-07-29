"""Tic Tac Toe core game logic and DB operations."""
from typing import Optional, List

from src.api.db import Database
from src.api.models import MoveInfo, GameStatus, GameSummary, LeaderboardEntry

def initial_board() -> str:
    return " " * 9

def board_to_list(board: str) -> List[str]:
    """Convert board_state string to list."""
    return list(board)

def list_to_board(lst: List[str]) -> str:
    """Convert list of chars to board string."""
    return "".join(lst)

def check_winner(board: str) -> Optional[str]:
    """Determine if there is a winner."""
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    board_lst = board_to_list(board)
    for (a, b, c) in wins:
        if board_lst[a] == board_lst[b] == board_lst[c] != " ":
            return board_lst[a]
    return None

def board_full(board: str) -> bool:
    return all(c in "XO" for c in board)

# PUBLIC_INTERFACE
async def create_game(player_x_id: int) -> int:
    """Create a new game record, return game_id."""
    from datetime import datetime  # moved import inside to avoid linter complaint
    pool = await Database.get_conn()
    now = datetime.utcnow()
    async with pool.acquire() as conn:
        rec = await conn.fetchrow("""
            INSERT INTO games (player_x_id, status, board_state, moves_count, created_at, updated_at)
            VALUES ($1, 'waiting', $2, 0, $3, $3)
            RETURNING id
        """, player_x_id, initial_board(), now)
        return rec["id"]

# PUBLIC_INTERFACE
async def join_game(player_id: int, game_id: int) -> Optional[dict]:
    """Join an existing game as player_o. Returns current status or None if not allowed."""
    pool = await Database.get_conn()
    async with pool.acquire() as conn:
        game = await conn.fetchrow("SELECT * FROM games WHERE id=$1", game_id)
        if not game or game["status"] != "waiting" or game["player_x_id"] == player_id:
            return None  # cannot join
        await conn.execute(
            "UPDATE games SET player_o_id=$1, status='in_progress', updated_at=NOW() WHERE id=$2",
            player_id, game_id)
        return await get_game_status(game_id, player_id)  # send new state

# PUBLIC_INTERFACE
async def get_available_games() -> List[dict]:
    """Fetch games waiting for a player_o."""
    pool = await Database.get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, player_x_id, created_at FROM games WHERE status='waiting'")
        return [{"id": r["id"], "player_x_id": r["player_x_id"], "created_at": r["created_at"]} for r in rows]

# PUBLIC_INTERFACE
async def get_game_status(game_id: int, req_user: int) -> dict:
    """Return GameStatus for specified game (with moves list)."""
    pool = await Database.get_conn()
    async with pool.acquire() as conn:
        game = await conn.fetchrow("SELECT * FROM games WHERE id=$1", game_id)
        if not game:
            return None
        # Moves
        moves = await conn.fetch("SELECT move_number, cell_position, symbol, player_id, created_at FROM moves WHERE game_id=$1 ORDER BY move_number", game_id)
        move_objs = [
            MoveInfo(
                move_number=m["move_number"], cell_position=m["cell_position"],
                symbol=m["symbol"], player_id=m["player_id"], created_at=m["created_at"])
            for m in moves
        ]
        return GameStatus(
            id=game["id"], player_x_id=game["player_x_id"], player_o_id=game["player_o_id"],
            winner_id=game["winner_id"], status=game["status"], board_state=game["board_state"],
            moves_count=game["moves_count"], moves=move_objs, created_at=game["created_at"], updated_at=game["updated_at"]
        ).model_dump()

# PUBLIC_INTERFACE
async def make_move(game_id: int, player_id: int, cell_pos: int, symbol: str) -> dict:
    """Validates, applies move, updates DB and returns game status after move, or error."""
    pool = await Database.get_conn()
    async with pool.acquire() as conn:
        rec = await conn.fetchrow("SELECT * FROM games WHERE id=$1", game_id)
        if not rec or rec["status"] not in ("in_progress",):
            return {"error": "Game not in progress or not found"}
        board = list(rec["board_state"])
        if not (0 <= cell_pos <= 8) or board[cell_pos] != " ":
            return {"error": "Invalid move"}
        # Check who's turn
        n_moves = rec["moves_count"]
        turn_symbol = "X" if n_moves % 2 == 0 else "O"
        correct_player = ((turn_symbol == "X" and rec["player_x_id"] == player_id) or 
                          (turn_symbol == "O" and rec["player_o_id"] == player_id))
        if not correct_player:
            return {"error": "Not your turn"}
        # Make the move
        board[cell_pos] = symbol
        new_board = "".join(board)
        winner = check_winner(new_board)
        is_draw = board_full(new_board) and not winner
        # Record move
        await conn.execute("""
            INSERT INTO moves (game_id, player_id, move_number, cell_position, symbol)
            VALUES ($1, $2, $3, $4, $5)
        """, game_id, player_id, n_moves+1, cell_pos, symbol)
        # Update game record
        new_status = "finished" if winner or is_draw else "in_progress"
        winner_id = rec["player_x_id"] if winner == "X" else (rec["player_o_id"] if winner == "O" else None)
        await conn.execute("""
            UPDATE games SET board_state=$1, moves_count=moves_count+1, winner_id=$2, status=$3, updated_at=NOW()
            WHERE id=$4
        """, new_board, winner_id, new_status, game_id)
        # If finished, create game result & update leaderboard
        if new_status == "finished":
            await conn.execute(
                """INSERT INTO game_results (game_id, player_x_id, player_o_id, winner_id)
                   VALUES ($1, $2, $3, $4)""",
                    game_id, rec["player_x_id"], rec["player_o_id"], winner_id)
            # Leaderboard aggregation is handled in backend as simple as possible (for MVP)
            for uid in (rec["player_x_id"], rec["player_o_id"]):
                # Insert or update leaderboard for both players
                # MVP: Increase wins/losses/draws/games_played counters
                if uid is None: continue
                user_won = (uid == winner_id) if winner_id else None
                exists = await conn.fetchval("SELECT 1 FROM leaderboard WHERE user_id=$1", uid)
                if user_won is True:
                    if exists:
                        await conn.execute("UPDATE leaderboard SET wins = wins+1, games_played=games_played+1, last_played=NOW() WHERE user_id=$1", uid)
                    else:
                        await conn.execute("INSERT INTO leaderboard (user_id, wins, games_played, last_played) VALUES ($1, 1, 1, NOW())", uid)
                elif user_won is False:
                    if exists:
                        await conn.execute("UPDATE leaderboard SET losses = losses+1, games_played=games_played+1, last_played=NOW() WHERE user_id=$1", uid)
                    else:
                        await conn.execute("INSERT INTO leaderboard (user_id, losses, games_played, last_played) VALUES ($1, 1, 1, NOW())", uid)
                else:
                    # Draw
                    if exists:
                        await conn.execute("UPDATE leaderboard SET draws = draws+1, games_played=games_played+1, last_played=NOW() WHERE user_id=$1", uid)
                    else:
                        await conn.execute("INSERT INTO leaderboard (user_id, draws, games_played, last_played) VALUES ($1, 1, 1, NOW())", uid)
        # Return updated status:
        return await get_game_status(game_id, player_id)

# PUBLIC_INTERFACE
async def get_leaderboard(limit=10) -> List[LeaderboardEntry]:
    """Fetch leaderboard with top N players by wins."""
    pool = await Database.get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT l.user_id, u.username, l.wins, l.losses, l.draws, l.games_played, l.last_played
            FROM leaderboard l
            JOIN users u ON u.id = l.user_id
            ORDER BY l.wins DESC, l.games_played DESC
            LIMIT $1
        """, limit)
        return [LeaderboardEntry(**dict(r)) for r in rows]

# PUBLIC_INTERFACE
async def get_match_history(user_id: int) -> List[GameSummary]:
    """Show recent finished games for player, as opponent and outcome."""
    pool = await Database.get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT gr.game_id as id,
                   CASE WHEN gr.player_x_id=$1 THEN uo.username ELSE ux.username END as opponent_username,
                   CASE WHEN gr.winner_id=$1 THEN TRUE WHEN gr.winner_id IS NULL THEN NULL ELSE FALSE END as is_winner,
                   g.status,
                   g.created_at
            FROM game_results gr
            JOIN games g ON g.id = gr.game_id
            JOIN users ux ON ux.id = gr.player_x_id
            JOIN users uo ON uo.id = gr.player_o_id
            WHERE gr.player_x_id=$1 OR gr.player_o_id=$1
            ORDER BY g.updated_at DESC LIMIT 20
            """, user_id
        )
        return [GameSummary(**dict(r)) for r in rows]
