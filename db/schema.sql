CREATE TABLE files (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    filename      TEXT NOT NULL,
    original_name TEXT,
    file_path     TEXT NOT NULL,
    collection    TEXT,
    file_type     TEXT,    -- image, flashcard, text, etc.
    file_size     INTEGER,
    hash          TEXT UNIQUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE images (
    file_id        INTEGER PRIMARY KEY, -- files.idと1対1
    image_type     TEXT,
    region_index   INTEGER,
    parent_image_id INTEGER,
    mask_image_id  INTEGER,
    width          INTEGER,
    height         INTEGER,
    format         TEXT,
    thumbnail_path TEXT,
    FOREIGN KEY(file_id) REFERENCES files(id)
);


CREATE TABLE flashcards (
    file_id    INTEGER PRIMARY KEY, -- files.idと1対1
    columns    TEXT,                -- JSON
    row_count  INTEGER,
    encoding   TEXT DEFAULT 'utf-8',
    delimiter  TEXT DEFAULT ',',
    FOREIGN KEY(file_id) REFERENCES files(id)
);


CREATE TABLE llm_outputs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    input_ref   INTEGER,     -- files.id（入力ファイルがある場合）
    prompt      TEXT,        -- プロンプト内容
    output      TEXT,        -- LLMの出力
    model_name  TEXT,        -- 使用モデル
    params      TEXT,        -- JSON形式でパラメータ
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(input_ref) REFERENCES files(id)
);
