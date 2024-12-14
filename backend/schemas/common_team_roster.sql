-- Table for players
CREATE TABLE common_team_roster(
    team_id integer,
    team_name text,
    season text,
    leagueid text,
    player text,
    player_slug text, -- Added
    num text, -- Changed to text to handle 'R' values
    position text,
    height text,
    weight text,
    birth_date text,
    age integer,
    exp text, -- Changed to text to handle 'R' values
    school text,
    player_id integer,
    how_acquired text, -- Added
    nickname text, -- Added
    PRIMARY KEY (team_id, player_id, season)
);

-- Create indexes for better query performance
CREATE INDEX idx_common_team_roster_team_id ON common_team_roster(team_id);

CREATE INDEX idx_common_team_roster_player_id ON common_team_roster(player_id);

CREATE INDEX idx_common_team_roster_season ON common_team_roster(season);

