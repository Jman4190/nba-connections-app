CREATE TABLE public.new_themes(
    theme_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    theme text NOT NULL,
    theme_description text NOT NULL,
    sql_query text NOT NULL,
    used_in_puzzle boolean DEFAULT FALSE
)
TABLESPACE pg_default;

-- Add index for commonly queried columns with a unique name
CREATE INDEX new_themes_used_puzzle_idx ON public.new_themes(used_in_puzzle);
