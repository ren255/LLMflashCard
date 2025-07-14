"""
SQLite データベース管理パッケージ

クラス:
    DatabaseManager: データベースファイル操作のコンテキストマネージャー
    TableManager: CRUD操作とテーブル管理

使用方法:
    from database import DatabaseManager, TableManager
    
    with DatabaseManager(db_path) as db:
        tm = TableManager(db)
        tm.insert("table", {"col": "value"})

関数一覧:
    DatabaseManager:
        - __enter__/__exit__: コンテキストマネージャープロトコル
        - get_connection(): アクティブ接続取得
        - get_all_table_names(): 全テーブル名リスト取得
        - database_exists(): DBファイル存在確認
        - backup_database(path): データベースファイルバックアップ
    
    TableManager:
        - insert(table, data): レコード挿入、IDを返す
        - select(table, conditions=None): レコード検索
        - update(table, data, conditions): レコード更新、更新件数を返す
        - delete(table, conditions): レコード削除、削除件数を返す
        - bulk_insert(table, data_list): 一括挿入
        - count(table, conditions=None): レコード数取得
        - exists(table, conditions): レコード存在確認
        - get_table_schema(table): テーブル構造取得
        - get_column_names(table): カラム名リスト取得
        - execute_raw(sql, params=None): 生SQL実行
"""

from .database_manager import DatabaseManager, TableManager

__all__ = ["DatabaseManager", "TableManager"]