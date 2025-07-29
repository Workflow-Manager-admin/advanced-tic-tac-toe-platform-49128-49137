# Tic Tac Toe Database

This service provides the persistent PostgreSQL database schema for the Advanced Tic Tac Toe platform. It supports:

- User accounts and authentication
- Persistent gameplay state for ongoing games
- Move-by-move storage for history and analytics
- Tracking completed matches for stats and leaderboards
- A leaderboard table for fast queries on user rankings

## Schema Overview

- **users**: Player login and profile info.
- **games**: Active and historical games with board state and metadata.
- **moves**: Each individual Tic Tac Toe move per game.
- **game_results**: Completed match summary (for match history).
- **leaderboard**: Aggregated player statistics.

## Migrations

Apply schema migrations using your preferred database migration tool or directly via psql:

```sh
psql $DATABASE_URL -f 001_init_schema.sql
```

Replace `$DATABASE_URL` with your actual database connection string.
