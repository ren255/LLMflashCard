-- ファイル管理テーブル
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

-- 画像固有情報テーブル
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
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- フラッシュカード固有情報テーブル
CREATE TABLE flashcards (
    file_id    INTEGER PRIMARY KEY, -- files.idと1対1
    encoding   TEXT DEFAULT 'utf-8',
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- LLM出力管理テーブル
CREATE TABLE LLM_outputs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    files_num   INTEGER,     -- LLM_filesで関連するfileの数
    prompt      TEXT,        -- プロンプト内容
    output      TEXT,        -- LLMの出力
    model_name  TEXT,        -- 使用モデル
    params      TEXT,        -- JSON形式でパラメータ
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM出力とファイルの関連テーブル（多対多）
CREATE TABLE LLM_files (
    LLM_output_id    INTEGER,  -- LLM_outputs.idへの参照
    file_id          INTEGER,  -- files.idへの参照
    PRIMARY KEY (LLM_output_id, file_id),
    FOREIGN KEY(LLM_output_id) REFERENCES LLM_outputs(id) ON DELETE CASCADE,
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- インデックスの追加（パフォーマンス向上）
CREATE INDEX idx_files_hash ON files(hash);
CREATE INDEX idx_files_file_type ON files(file_type);
CREATE INDEX idx_files_collection ON files(collection);
CREATE INDEX idx_LLM_outputs_created_at ON LLM_outputs(created_at);
CREATE INDEX idx_LLM_files_file_id ON LLM_files(file_id);