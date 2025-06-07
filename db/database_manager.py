import sqlite3
from pathlib import Path
from typing import Any, Self
import shutil


class DatabaseManager:
    """データベースファイル全体の管理を行うContext Manager"""
    
    def __init__(self, db_path: Path = Path("resources/db.db")):
        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None
    
    def __enter__(self) -> Self:
        """Context Manager開始、接続確立"""
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context Manager終了、接続解放"""
        if self._connection:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
            self._connection.close()
            self._connection = None
    
    def get_connection(self) -> sqlite3.Connection:
        """アクティブ接続取得"""
        if self._connection is None:
            raise RuntimeError("Connection not established. Use within context manager.")
        return self._connection
    
    def get_all_table_names(self) -> list[str]:
        """全テーブル名取得"""
        conn = self.get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]
    
    def database_exists(self) -> bool:
        """データベースファイル存在確認"""
        return self.db_path.exists()
    
    def backup_database(self, backup_path: Path) -> None:
        """データベースバックアップ"""
        if not self.database_exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        shutil.copy2(self.db_path, backup_path)


class TableManager:
    """すべてのテーブル操作を管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def insert(self, table_name: str, data: dict[str, Any]) -> int:
        """レコード挿入、IDを返す"""
        conn = self.db_manager.get_connection()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor = conn.execute(sql, list(data.values()))
        lastrowid = cursor.lastrowid
        if lastrowid is None:
            return 0
        return lastrowid
    def select(self, table_name: str, conditions: dict[str, Any] | None = None) -> list[dict]:
        """レコード検索"""
        conn = self.db_manager.get_connection()
        sql = f"SELECT * FROM {table_name}"
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                where_clauses.append(f"{key} = ?")
                params.append(value)
            sql += " WHERE " + " AND ".join(where_clauses)
        
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def update(self, table_name: str, data: dict[str, Any], conditions: dict[str, Any]) -> int:
        """レコード更新、更新件数を返す"""
        conn = self.db_manager.get_connection()
        set_clauses = []
        params = []
        
        for key, value in data.items():
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        where_clauses = []
        for key, value in conditions.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)
        
        sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
        cursor = conn.execute(sql, params)
        return cursor.rowcount
    
    def delete(self, table_name: str, conditions: dict[str, Any]) -> int:
        """レコード削除、削除件数を返す"""
        conn = self.db_manager.get_connection()
        where_clauses = []
        params = []
        
        for key, value in conditions.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)
        
        sql = f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)}"
        cursor = conn.execute(sql, params)
        return cursor.rowcount
    
    def bulk_insert(self, table_name: str, data_list: list[dict[str, Any]]) -> None:
        """一括挿入"""
        if not data_list:
            return
        
        conn = self.db_manager.get_connection()
        columns = ', '.join(data_list[0].keys())
        placeholders = ', '.join(['?' for _ in data_list[0]])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        values_list = [list(data.values()) for data in data_list]
        conn.executemany(sql, values_list)
    
    def count(self, table_name: str, conditions: dict[str, Any] | None = None) -> int:
        """レコード数取得"""
        conn = self.db_manager.get_connection()
        sql = f"SELECT COUNT(*) FROM {table_name}"
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                where_clauses.append(f"{key} = ?")
                params.append(value)
            sql += " WHERE " + " AND ".join(where_clauses)
        
        cursor = conn.execute(sql, params)
        return cursor.fetchone()[0]
    
    def exists(self, table_name: str, conditions: dict[str, Any]) -> bool:
        """レコード存在確認"""
        return self.count(table_name, conditions) > 0
    
    def get_table_schema(self, table_name: str) -> list[dict]:
        """テーブルスキーマ取得"""
        conn = self.db_manager.get_connection()
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_column_names(self, table_name: str) -> list[str]:
        """カラム名一覧取得"""
        schema = self.get_table_schema(table_name)
        return [column['name'] for column in schema]
    
    def execute_raw(self, sql: str, params: tuple[Any, ...] | dict[str, Any] | None = None) -> list[dict]:
        """生SQL実行（複数テーブル操作含む）"""
        conn = self.db_manager.get_connection()
        if params is None:
            params = () # Changed to empty tuple
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

# 使用例
if __name__ == "__main__":
    db_path = Path("resources/db.db")
    
    with DatabaseManager(db_path) as db_manager:
        table_manager = TableManager(db_manager)
        
        # テーブル一覧取得
        tables = db_manager.get_all_table_names()
        print(f"Tables: {tables}")
        
        # レコード挿入例
        user_id = table_manager.insert("users", {"name": "Alice", "age": 30})
        
        # レコード検索例
        # users = table_manager.select("users", {"age": 30})
        
        # 複数テーブルのJOIN操作例
        # result = table_manager.execute_raw(
        #     "SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id"
        # )
