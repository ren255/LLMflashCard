# Python Logging システム設計書

## 概要

アプリケーション全体で統一されたロギング機能を提供するシステムの設計。コンソール出力とファイル出力の両方をサポートし、可読性の高いフォーマットを実現する。

## 出力フォーマット仕様

### コンソール出力

```
[INFO]    filename:line  : log message
[WARNING] filename:line  : log message
[ERROR]   filename:line  : log message
```

**フォーマット詳細:**

- `[log_level]`: 色付き、10 文字固定（右パディング）
- `filename:line`: 20 文字固定（右パディング）
- `: ` 区切り文字
- `log message`: 実際のログメッセージ

**色設定:**

- INFO: 青色
- WARNING: 黄色
- ERROR: 赤色
- DEBUG: 緑色
- CRITICAL: マゼンタ色

### ファイル出力

```
2025-01-15 10:30:45 [INFO]   filename:line @function_name : log message
```

**フォーマット詳細:**

- `YYYY-MM-DD HH:MM:SS`: タイムスタンプ
- `[log_level]`: 色なし、10 文字固定（右パディング）
- `filename:line`: 20 文字固定（右パディング）
- `@function_name`: 10 文字固定（右パディング
- `: ` 区切り文字
- `log message`: 実際のログメッセージ

## ログファイル管理

### ファイル配置構造

```
root/
├── log/
│   ├── live/
│   │   ├── 2025-01-15_app.log      # 今日のアプリケーションログ
│   │   ├── 2025-01-15_sql.log      # 今日のSQLログ
│   │   └── 2025-01-15_error.log    # 今日のエラーログ すべての層から
│   ├── daily/
│   │   ├── 2025-01-14/
│   │   │   ├── 2025-01-14_app.log
│   │   │   ├── 2025-01-14_sql.log
│   │   │   └── 2025-01-14_error.log
│   │   ├── 2025-01-13/
│   │   │   └── ...
│   │   └── ...
│   └── archive/
│       └── (1ヶ月前のログ、処理は実装しない)
```

### ファイル命名規則

- **アプリケーションログ**: `YYYY-MM-DD_app.log`
- **SQL ログ**: `YYYY-MM-DD_sql.log`
- **エラーログ**: `YYYY-MM-DD_error.log`

### ローテーション処理

- **日付更新タイミング**: 午前 4 時
- **処理方法**: 書き込み時に日付をチェックし、4 時を過ぎていたら自動的に live から該当日付の daily ディレクトリに移動
- **フォルダ作成**: daily ディレクトリ内に日付フォルダを自動生成
- **即座フラッシュ**: 全ログファイルは即座にフラッシュ（バッファリングなし）
- **同時書き込み**: 複数プロセスからの同時書き込み対応は不要
- archive ディレクトリの処理は実装しない（pass）

## SQLAlchemy 専用ログ設定

### 出力先の分離


### SQLAlchemy Logger 階層
設定ファイルで選択される
```
sqlalchemy.engine     # SQL文の実行ログ
sqlalchemy.pool       # コネクションプールログ
sqlalchemy.dialects   # データベース固有の処理ログ
sqlalchemy.orm        # ORMレベルの処理ログ
```

## カスタム Formatter 設計

### ConsoleFormatter

- 色付きログレベル表示
- ファイル名:行番号の固定幅フォーマット
- 簡潔な出力形式

### FileFormatter

- タイムスタンプ付き
- 関数名情報を含む
- 色情報なし（プレーンテキスト）

## 設定ファイル

### YAML 設定ファイル

```yaml
# logging_config.yaml
logging:
  level: INFO
  console:
    enabled: true
    level: INFO
    format: console
  file:
    enabled: true
    level: DEBUG

sql:
  active: [engine] # , pool, dialects, orm
  console:
    enabled: true
    level: ERROR
  file:
    enabled: true
    level: INFO

rotation:
  flush_immediately: true
  max_size: null # 現状無視
  hour: 4 # 午前4時に日付更新　
  archive_days: 30 # 実装しない（pass）
```
真夜中の開発中に変わるといらつく、またAnkiもresetは4時　個人開発なのでもんだいなし
sql.activeでSQLAlchemy Logger 階層のうち使うものをONにする。

## パフォーマンス考慮事項

### 非同期ログ出力

- 同時書き込み対応は不要（単一プロセス想定）
- 即座フラッシュによる確実な書き込み

### メモリ使用量最適化

- バッファリングなし（即座フラッシュ）
- 適切なファイルクローズ処理

### ファイル I/O 最適化

- 即座フラッシュによる確実な書き込み
- 1 日の最大ファイルサイズ制限は現状無視

## エラーハンドリング
- 設定エラー　- 不正な設定値
- ログ出力エラー
- ファイル書き込み失敗時
などではlogしてすること

## 使用例

### 基本的な使用方法

```python
from app.config.logging_config import setup_logging, get_logger

# 設定ファイルを指定して初期化
setup_logging('config/logging_config.yaml')

# ロガー取得
logger = get_logger('app')

# ログ出力（即座にフラッシュ）
logger.info("処理開始")
logger.warning("警告メッセージ")
logger.error("エラーが発生しました")
```

### ロガー構成

```python
# 2つのメインロガーのみ使用
app_logger = get_logger('app')                    # アプリケーションログ全般
sql_logger = get_logger('sqlalchemy')     # SQLクエリログ（ファイルのみ）
```

### SQLAlchemy 設定例

```python
# YAML設定またはデバッグ時のみコンソール出力
import os
import yaml

# 設定ファイル読み込み
with open('config/logging_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

SQL_DEBUG = os.getenv('SQL_DEBUG', 'false').lower() == 'true'
sql_console_enabled = config['sql']['console']['enabled'] or SQL_DEBUG

# engine設定
engine = create_engine(
    DATABASE_URL,
    echo=sql_console_enabled,          # 設定またはデバッグ時のみコンソール出力
)
```

## 拡張性

### プラグイン対応

- カスタムハンドラーの追加
- 外部ログ収集システムとの連携

### 監視システム連携

- ログレベル別メトリクス収集
- アラート機能との統合

### 構造化ログ対応

- JSON 形式でのログ出力オプション
- ログ解析ツールとの連携# Python Logging システム設計書
