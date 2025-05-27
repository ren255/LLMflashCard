# Storage Module Testing Guide

## 概要

このドキュメントでは、`storage/`モジュールの包括的なテストを実行する方法について説明します。ストレージモジュールは以下のコンポーネントで構成されています：

- **StorageController**: 統合管理クラス
- **BaseStorage/BaseMetadataManager**: 基底クラス
- **ImageStorage/ImageMetadataManager**: 画像管理
- **FlashcardStorage/FlashcardMetadataManager**: フラッシュカード管理
- **FileManager**: ファイル操作

## テスト戦略

### 1. テスト構造

```ini
tests/
├── test_storage_integration.py    # 統合テスト
├── test_storage_controller.py     # StorageController
├── test_file_manager.py          # FileManager
├── test_image_managers.py        # 画像管理
├── test_flashcard_managers.py    # フラッシュカード管理
├── test_base_managers.py         # 基底クラス
├── fixtures/                     # テストデータ
│   ├── test_images/
│   │   ├── sample.jpg
│   │   ├── sample.png
│   │   └── large_image.jpg
│   ├── test_csvs/
│   │   ├── sample.csv
│   │   ├── utf8.csv
│   │   └── shift_jis.csv
│   └── test_databases/
└── conftest.py                   # pytest設定・フィクスチャ

```

### 2. テスト環境セットアップ

#### 必要なライブラリ

```bash
pip install pytest pytest-cov pytest-mock pillow pandas

```

#### テストデータ準備

- **画像ファイル**: JPEG, PNG, 異なるサイズ
- **CSVファイル**: UTF-8, Shift-JIS, 異なる区切り文字
- **一時ディレクトリ**: テスト専用の隔離された環境

## テストケース詳細

### 1. StorageController テスト

#### 初期化・セットアップ

- [ ] ディレクトリ構造の正しい作成
- [ ] データベースファイルの作成
- [ ] パス設定の検証
- [ ] 権限エラーのハンドリング

#### ストレージインスタンス管理

- [ ] 遅延初期化の動作確認
- [ ] プロパティアクセス（image_storage, flashcard_storage）
- [ ] get_storage()メソッドの動作
- [ ] 無効なファイルタイプの処理

#### 統計・情報取得

- [ ] get_paths_info()の正確性
- [ ] get_storage_stats()の集計処理
- [ ] 空のストレージでの統計

#### クリーンアップ

- [ ] cleanup()メソッドの動作
- [ ] データベース接続の適切な閉じ処理

### 2. FileManager テスト

#### ファイル操作

- [ ] save_file(): 正常保存、権限エラー、存在しないファイル
- [ ] delete_file(): ファイル削除、サムネイル削除
- [ ] move_from_temp(): 一時ファイルの移動
- [ ] save_to_temp(): 一時保存

#### ハッシュ・ファイル名生成

- [ ] calculate_hash(): 同一ファイルの同一ハッシュ
- [ ] generate_filename(): 一意性の確認
- [ ] get_file_path(): パス構築の正確性

#### サムネイル処理

- [ ] create_thumbnail(): 画像形式別対応
- [ ] サイズ調整の確認
- [ ] 非画像ファイルのエラーハンドリング

#### ディレクトリ管理

- [ ] _ensure_directories(): ディレクトリ作成
- [ ] 権限不足時の処理

### 3. ImageStorage テスト

#### 画像保存・取得

- [ ] save(): 正常保存、重複チェック
- [ ] get(): メタデータ取得
- [ ] get_all(): 全画像取得
- [ ] delete(): 画像削除

#### 画像固有機能

- [ ] save_split_image(): 分割画像保存
- [ ] get_thumbnail_path(): サムネイルパス取得
- [ ] get_image_info(): 画像詳細情報
- [ ] link_mask(): マスク情報リンク

#### 検索・フィルタ機能

- [ ] get_by_collection(): コレクション別取得
- [ ] search_by_content(): 内容検索
- [ ] 条件検索（search()メソッド）

#### 統計情報

- [ ] get_image_stats(): フォーマット、サイズ統計
- [ ] 空データでの統計処理

### 4. FlashcardStorage テスト

#### CSV保存・取得

- [ ] save(): 正常保存、エンコーディング対応
- [ ] get(): メタデータ取得
- [ ] get_all(): 全フラッシュカード取得
- [ ] delete(): ファイル削除

#### CSV固有機能

- [ ] get_columns(): カラム情報取得
- [ ] get_csv_info(): CSV詳細情報
- [ ] get_encoding_info(): エンコーディング情報
- [ ] update_encoding(): エンコーディング更新
- [ ] get_delimiter_info(): 区切り文字情報

#### 検索・統計

- [ ] search_by_content(): 内容検索
- [ ] get_flashcard_stats(): CSV統計
- [ ] エンコーディング・区切り文字の統計

### 5. MetadataManager テスト

#### データベース操作

- [ ] save_metadata(): メタデータ保存
- [ ] get_by_id(): ID検索
- [ ] get_by_hash(): ハッシュ検索
- [ ] update_metadata(): 更新処理
- [ ] delete_metadata(): 削除処理

#### 検索機能

- [ ] get_by_collection(): コレクション検索
- [ ] search(): 条件検索
- [ ] get_all(): 全件取得

#### スキーマ検証

- [ ] 無効なフィールドの除外
- [ ] 必須フィールドの検証
- [ ] データ型の適切な処理


# 現在のfile構造
```
LLMflashCard
├── .git
├── .pytest_cache
├── .venv
├── .VSCodeCounter
├── db
│   ├── __pycache__
│   ├── __init__.py
│   ├── interface_utils.py
│   ├── models.py
│   └── sqlite_utils.py
├── gui
│   └── __init__.py
├── image_processing
│   └── __init__.py
├── llm
│   └── __init__.py
├── logic
│   └── __init__.py
├── resources
│   ├── db
│   │   ├── flashcards.db
│   │   ├── images.db
│   │   ├── my_database.db
│   │   ├── test.db
│   │   └── test.sqlite
│   ├── flashcard
│   ├── image
│   │   └── 477f563689e745089dad3e4798091bc0.png
│   ├── temp
│   │   ├── flashcard
│   │   └── image
│   ├── tempSave
│   ├── thumbnails
│   │   ├── flashcard
│   │   └── image
│   │       └── thumb_477f563689e745089dad3e4798091bc0.png
│   └── upload
├── storage
│   ├── __pycache__
│   ├── __init__.py
│   ├── base_managers.py
│   ├── file_manager.py
│   ├── flashcard_managers.py
│   ├── image_managers.py
│   └── storage_controller.py
├── test
│   ├── fixtures
│   │   ├── test_csvs
│   │   │   ├── basic_flashcards_utf8.csv
│   │   │   ├── japanese_flashcards_cp932.csv
│   │   │   ├── japanese_flashcards_sjis.csv
│   │   │   ├── japanese_flashcards_utf8.csv
│   │   │   ├── large_flashcards.csv
│   │   │   ├── many_columns.csv
│   │   │   ├── minimal_2columns.csv
│   │   │   ├── special_chars_comma.csv
│   │   │   ├── special_chars_semicolon.csv
│   │   │   ├── special_chars_tab.tsv
│   │   │   ├── unicode_special.csv
│   │   │   └── with_nulls.csv
│   │   ├── test_databases
│   │   └── test_images
│   │       ├── corrupted.jpg
│   │       ├── empty.png
│   │       ├── large_banner.png
│   │       ├── large_photo.jpg
│   │       ├── medium_landscape.jpg
│   │       ├── medium_portrait.png
│   │       ├── medium_square.jpg
│   │       ├── pattern_checker.png
│   │       ├── pattern_gradient.jpg
│   │       ├── small_blue.png
│   │       ├── small_green.webp
│   │       ├── small_red.jpg
│   │       ├── tall_poster.png
│   │       └── wide_banner.jpg
│   ├── make_testdata.py
│   ├── pytest.ini
│   ├── StorageTest.md
│   └── test_db.py
├── tests
│   ├── __pycache__
│   ├── calss.dio
│   ├── db.try.py
│   ├── LLMflashCard_tree.txt
│   ├── path.py
│   └── tree.py
├── .gitignore
├── main.py
├── my_database.db
└── requirements.txt
```