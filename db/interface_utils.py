from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Dict


##
# @brief データベース管理のインターフェース
class DBManagerInterface(ABC):
    @abstractmethod
    def create_table(self, table_name: str, columns: Dict[str, str]):
        """
        テーブルを作成する。
        columnsは {"列名": "型"} の形式で指定する。
        例: {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "age": "INTEGER"}
        """
        pass

    @abstractmethod
    def insert(self, table_name: str, data: Dict[str, Any]) -> int | None:
        """
        レコードを挿入する。
        dataは {"列名": 値} の形式で指定する。
        """
        pass

    @abstractmethod
    def fetch_all(self, table_name: str) -> List[Dict[str, Any]]:
        """
        テーブル内の全レコードを取得する。
        戻り値は各レコードを辞書で表したリスト。
        """
        pass

    @abstractmethod
    def fetch_where(
        self, table_name: str, condition: str, params: Tuple[Any, ...]
    ) -> List[Dict[str, Any]]:
        """
        条件に一致するレコードを取得する。
        condition: "age > ?" のようなSQL条件式
        params: (20,) のようなプレースホルダに対応する値のタプル
        """
        pass

    @abstractmethod
    def update(
        self,
        table_name: str,
        updates: Dict[str, Any],
        condition: str,
        params: Tuple[Any, ...],
    ):
        """
        レコードを更新する。
        updates: {"name": "John"} のような更新内容
        condition: "id = ?" のような条件文
        params: 条件に対応する値のタプル
        """
        pass

    @abstractmethod
    def delete(self, table_name: str, condition: str, params: Tuple[Any, ...]):
        """
        条件に一致するレコードを削除する。
        """
        pass

    @abstractmethod
    def close(self):
        """
        データベース接続を閉じる。
        """
        pass
