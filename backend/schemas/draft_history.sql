CREATE TABLE draft_history(
    person_id integer,
    player_name text,
    season integer,
    round_number integer,
    round_pick integer,
    overall_pick integer,
    draft_type text,
    team_id integer,
    team_city text,
    team_name text,
    team_abbreviation text,
    organization text,
    organization_type text,
    player_profile_flag boolean,
    PRIMARY KEY (person_id, season, overall_pick)
);

-- Create indexes for better query performance
CREATE INDEX idx_draft_history_season ON draft_history(season);

CREATE INDEX idx_draft_history_team_id ON draft_history(team_id);

CREATE INDEX idx_draft_history_overall_pick ON draft_history(overall_pick);

