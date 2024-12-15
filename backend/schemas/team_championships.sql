CREATE TABLE IF NOT EXISTS team_championships(
    id serial PRIMARY KEY,
    team_id integer NOT NULL,
    team_name text NOT NULL,
    year_awarded integer NOT NULL,
    opposite_team text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (team_id, year_awarded)
);

CREATE INDEX IF NOT EXISTS idx_team_championships_team_id ON team_championships(team_id);

CREATE INDEX IF NOT EXISTS idx_team_championships_year_awarded ON team_championships(year_awarded);

-- Trigger to update the updated_at column
CREATE OR REPLACE FUNCTION update_modified_column()
    RETURNS TRIGGER
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER update_team_championships_modtime
    BEFORE UPDATE ON team_championships
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

