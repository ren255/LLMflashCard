from typing import Dict

IMAGE_SCHEMA = {
    "id"           : "INTEGER PRIMARY KEY AUTOINCREMENT",
    "filename"     : "TEXT NOT NULL",                     # 実際のファイル名
    "original_name": "TEXT",                              # 元のファイル名
    "file_path"    : "TEXT NOT NULL",                     # 相対パス

    "collection"     : "TEXT",    # コレクション名
    "image_type"     : "TEXT",    # 画像の種類（例: original, split, mask）
    "region_index"   : "INTEGER", # 分割領域の番号
    "parent_image_id": "INTEGER", # 元画像のID（分割画像の場合）
    "mask_image_id"  : "TEXT",    # マスク領域の座標や形状（JSON等）

    "file_size"     : "INTEGER",                             # ファイルサイズ(bytes)
    "width"         : "INTEGER",                             # 画像幅
    "height"        : "INTEGER",                             # 画像高さ
    "format"        : "TEXT",                                # JPEG, PNG, etc.
    "hash"          : "TEXT UNIQUE",                         # ファイルハッシュ（重複防止）
    "thumbnail_path": "TEXT",                                # サムネイルパス
    "created_at"    : "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
}

FLASHCARD_SCHEMA = {
    "id"           : "INTEGER PRIMARY KEY AUTOINCREMENT",
    "filename"     : "TEXT NOT NULL",                     # 実際のファイル名
    "original_name": "TEXT",                              # 元のファイル名
    "file_path"    : "TEXT NOT NULL",                     # 相対パス

    "collection": "TEXT",    # コレクション名
    "columns"   : "TEXT",    # JSON形式のカラム構造（ユーザー定義）
    "row_count" : "INTEGER", # レコード数

    "file_size" : "INTEGER",                             # ファイルサイズ(bytes)
    "encoding"  : "TEXT DEFAULT 'utf-8'",                # ファイルエンコーディング
    "delimiter" : "TEXT DEFAULT ','",                    # CSV区切り文字
    "hash"      : "TEXT UNIQUE",                         # ファイルハッシュ（重複防止）
    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
}
