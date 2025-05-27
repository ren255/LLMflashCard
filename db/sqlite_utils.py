import sqlite3
from typing import Any, List, Tuple, Dict
from .interface_utils import DBManagerInterface
from utils import log
from pathlib import Path

class SQLiteManager(DBManagerInterface):
    def __init__(self, db_path: Path):
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            log.info(f"SQLite database connection established: {self.db_path}")
        except Exception as e:
            log.error(f"Failed to connect to SQLite database {self.db_path}: {e}")
            raise

    def create_table(self, table_name: str, columns: Dict[str, str]):
        try:
            col_defs = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({col_defs});"
            self.cursor.execute(sql)
            self.conn.commit()
            log.info(f"Table '{table_name}' created or verified successfully")
        except Exception as e:
            log.error(f"Failed to create table '{table_name}': {e}")
            raise

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
            log.warning(f"Database integrity error for table '{table_name}' (duplicate or constraint violation): {e}")
            return None
        except Exception as e:
            log.error(f"Failed to insert data into table '{table_name}': {e}")
            log.debug(f"Data to insert:")
            for key, value in data.items():
                log.debug(f"    Data: {key} = {value}")
            log.debug("")
            
            return None

    def fetch_all(self, table_name: str) -> List[Dict[str, Any]]:
        try:
            sql = f"SELECT * FROM {table_name}"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            log.error(f"Failed to fetch all data from table '{table_name}': {e}")
            return []

    def fetch_where(
        self, table_name: str, condition: str, params: Tuple[Any, ...]
    ) -> List[Dict[str, Any]]:
        try:
            sql = f"SELECT * FROM {table_name} WHERE {condition}"
            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            log.error(f"Failed to fetch data from table '{table_name}' with condition '{condition}': {e}")
            return []

    def update(
        self,
        table_name: str,
        updates: Dict[str, Any],
        condition: str,
        params: Tuple[Any, ...],
    ):
        try:
            set_clause = ", ".join([f"{col} = ?" for col in updates])
            values = list(updates.values()) + list(params)
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
            self.cursor.execute(sql, values)
            self.conn.commit()
        except Exception as e:
            log.error(f"Failed to update table '{table_name}' with condition '{condition}': {e}")
            raise

    def delete(self, table_name: str, condition: str, params: Tuple[Any, ...]):
        try:
            sql = f"DELETE FROM {table_name} WHERE {condition}"
            self.cursor.execute(sql, params)
            self.conn.commit()
        except Exception as e:
            log.error(f"Failed to delete from table '{table_name}' with condition '{condition}': {e}")
            raise

    def close(self):
        try:
            if self.conn:
                self.conn.close()
                log.info(f"SQLite database connection closed: {self.db_path}")
        except Exception as e:
            log.error(f"Error closing SQLite database connection: {e}")