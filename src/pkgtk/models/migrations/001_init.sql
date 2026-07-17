-- Model librarian schema (v1).
CREATE TABLE IF NOT EXISTS models (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    part        TEXT NOT NULL,
    rev         TEXT NOT NULL,
    corner      TEXT NOT NULL,
    model_type  TEXT NOT NULL,
    state       TEXT NOT NULL DEFAULT 'requested',
    note        TEXT DEFAULT '',
    updated     TEXT DEFAULT '',
    UNIQUE(part, rev, corner, model_type)
);
