CREATE TABLE eligible_puzzles(
    id serial PRIMARY KEY,
    puzzle_players jsonb NOT NULL,
    daily_theme text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster JSON queries
CREATE INDEX puzzle_players_gin_idx ON eligible_puzzles USING gin(puzzle_players);

