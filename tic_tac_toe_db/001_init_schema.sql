-- Tic Tac Toe DB Initial Schema
-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Games Table
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    player_x_id INTEGER NOT NULL REFERENCES users(id),
    player_o_id INTEGER REFERENCES users(id),
    winner_id INTEGER REFERENCES users(id),
    status VARCHAR(20) NOT NULL, -- e.g. waiting, in_progress, finished
    board_state VARCHAR(20) NOT NULL, -- e.g. "XOXOX    O"
    moves_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Moves Table
CREATE TABLE moves (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES users(id),
    move_number INTEGER NOT NULL,
    cell_position INTEGER NOT NULL, -- 0 to 8 for 3x3 grid
    symbol CHAR(1) NOT NULL, -- 'X' or 'O'
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Game Results Table (Match History)
CREATE TABLE game_results (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_x_id INTEGER NOT NULL REFERENCES users(id),
    player_o_id INTEGER NOT NULL REFERENCES users(id),
    winner_id INTEGER REFERENCES users(id),
    finished_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Leaderboard Table (aggregated for quick access)
CREATE TABLE leaderboard (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    draws INTEGER NOT NULL DEFAULT 0,
    games_played INTEGER NOT NULL DEFAULT 0,
    last_played TIMESTAMP WITHOUT TIME ZONE
);

-- Indexes for efficient queries
CREATE INDEX idx_games_status ON games(status);
CREATE INDEX idx_moves_game_id ON moves(game_id);
CREATE INDEX idx_leaderboard_wins ON leaderboard(wins DESC);

-- Triggers, Views, or Functions for leaderboard aggregation would be handled in backend app or via routines, not here for MVP.
