import sqlite3
from typing import Any, List, Tuple, Dict
from .interface_utils import DBManagerInterface

class SQLiteManager(DBManagerInterface):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def create_table(self, table_name: str, columns: Dict[str, str]):
        col_defs = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({col_defs});"
        self.cursor.execute(sql)
        self.conn.commit()

    def insert(self, table_name: str, data: Dict[str, Any]):
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            values = tuple(data.values())
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            self.cursor.execute(sql, values)
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"データベース整合性エラー（重複など）: {e}")
            return None
        except Exception as e:
            print(f"メタデータ保存エラー: {e}")
            return None

    def fetch_all(self, table_name: str) -> List[Dict[str, Any]]:
        sql = f"SELECT * FROM {table_name}"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def fetch_where(
        self, table_name: str, condition: str, params: Tuple[Any, ...]
    ) -> List[Dict[str, Any]]:
        sql = f"SELECT * FROM {table_name} WHERE {condition}"
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def update(
        self,
        table_name: str,
        updates: Dict[str, Any],
        condition: str,
        params: Tuple[Any, ...],
    ):
        set_clause = ", ".join([f"{col} = ?" for col in updates])
        values = list(updates.values()) + list(params)
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        self.cursor.execute(sql, values)
        self.conn.commit()

    def delete(self, table_name: str, condition: str, params: Tuple[Any, ...]):
        sql = f"DELETE FROM {table_name} WHERE {condition}"
        self.cursor.execute(sql, params)
        self.conn.commit()

    def close(self):
        self.conn.close()


