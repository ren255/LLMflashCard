from __future__ import annotations
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
import json

from abc import ABC, abstractmethod
from db.sqlite_utils import SQLiteManager

from .file_manager import FileManager
from utils import log
##
# @brief ストレージ管理の基底クラス
# @details このクラスはストレージ管理の基本的な機能を提供し、サブクラスで具体的な実装を行う


class BaseStorage(ABC):

    def __init__(self, file_type: str, paths: Dict[str, str]):
        self.file_type = file_type
        self.paths = paths

        self.fileMgr = self._create_file_manager()
        self.metadataMgr = self._create_metadata_manager()

    @abstractmethod
    def _create_file_manager(self) -> FileManager:
        """ファイルマネージャーを作成（サブクラスで実装）"""
        pass

    @abstractmethod
    def _create_metadata_manager(self) -> BaseMetadataManager:
        """メタデータマネージャーを作成（サブクラスで実装）"""
        pass

    @abstractmethod
    def save(self, source_path: Path,  collection: str = "", **kwargs) -> int | None:
        """
        ファイルを保存（サブクラスで実装）
        Returns: (record_id, saved_path) - record_idはエラー時None
        """
        pass

    def save_file(self, source_path: Path, collection: str = "", **kwargs) -> int | None:
        """
        ファイルを保存（重複チェック付き）
        Returns: (record_id, saved_path) - record_idはエラー時None
        """
        try:
            file_hash = self.fileMgr.calculate_hash(source_path)
            existing = self.metadataMgr.get_by_hash(file_hash)
            if existing:
                log.error(f"重複ファイル検出: {existing['filename']}")
                return None

            saved_path = self.fileMgr.save_file(source_path)
            if not saved_path:
                return None

            metadata = self.metadataMgr.get_metadata(source_path)
            thumbnail_path = self.fileMgr.create_thumbnail(saved_path)
            save_data = {
                "filename": saved_path.name,
                "original_name": Path(source_path).name,
                "file_path": self.paths["base_path"] / saved_path,
                "thumbnail_path": str(thumbnail_path) if thumbnail_path else "",
                "hash": file_hash,
                "collection": collection,
                **metadata,
                **kwargs  # 追加のメタデータ
            }

            record_id = self.metadataMgr.save_metadata(**save_data)
            if record_id is None:
                log.error(f"メタデータ保存失敗")
                return None

            return record_id

        except Exception as e:
            log.error(f"ファイル保存エラー: 'source_path' : from{e}")

    def get(self, record_id: int) -> Optional[Dict]:
        """レコード情報を取得"""
        metadata = self.metadataMgr.get_by_id(record_id)
        if metadata:
            full_path = self.fileMgr.get_file_path(metadata["filename"])
            metadata["full_path"] = full_path
        return metadata

    def delete(self, record_id: int) -> bool:
        """ファイルを完全削除"""
        try:
            # メタデータ取得
            metadata = self.metadataMgr.get_by_id(record_id)
            if not metadata:
                return False

            full_path = self.fileMgr.get_file_path(metadata["filename"])
            thumbnail_path = metadata.get("thumbnail_path", "")
            self.fileMgr.delete_file(full_path, thumbnail_path)
            self.metadataMgr.delete_metadata(record_id)

            return True
        except Exception as e:
            log.info(f"削除エラー: {e}")
            return False

    def get_all(self) -> List[Dict]:
        """全レコードを取得"""
        records = self.metadataMgr.get_all()
        for record in records:
            record["full_path"] = self.fileMgr.get_file_path(
                record["filename"])
        return records

    def get_by_collection(self, collection: str) -> List[Dict]:
        """コレクション別に取得"""
        records = self.metadataMgr.get_by_collection(collection)
        for record in records:
            record["full_path"] = self.fileMgr.get_file_path(
                record["filename"])
        return records

    def update_metadata(self, record_id: int, **kwargs):
        """メタデータを更新"""
        self.metadataMgr.update_metadata(record_id, **kwargs)

    def search(self, condition: str, params: tuple) -> List[Dict]:
        """条件検索"""
        records = self.metadataMgr.search(condition, params)
        for record in records:
            record["full_path"] = self.fileMgr.get_file_path(
                record["filename"])
        return records

    def get_collections(self) -> List[str]:
        """すべてのコレクション名を取得"""
        records = self.metadataMgr.get_all()
        collections = set()
        for record in records:
            if record.get("collection"):
                collections.add(record["collection"])
        return sorted(list(collections))

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        all_records = self.metadataMgr.get_all()

        total_size = sum(record.get("file_size", 0) for record in all_records)
        collections = self.get_collections()

        return {
            "total_files": len(all_records),
            "total_size": total_size,
            "collections": len(collections),
            "collection_names": collections
        }


class BaseMetadataManager(ABC):
    """メタデータ管理の基底クラス"""

    def __init__(self, db_path: str, table_name: str, schema: Dict[str, str]):
        self.db = SQLiteManager(Path(db_path))
        self.table_name = table_name
        self.schema = schema
        self._initialize_tables()

    def _initialize_tables(self):
        """テーブル初期化"""
        self.db.create_table(self.table_name, self.schema)

    def save_metadata(self, **kwargs) -> int | None:
        """
        メタデータを保存
        Returns: 保存されたレコードのID、失敗時はNone
        """
        # スキーマに存在するフィールドのみを抽出
        valid_data = {}
        for key, value in kwargs.items():
            if key in self.schema:
                if type(value) is type(Path()):
                    value = str(value)
                elif type(value) is type([]):
                    value = json.dumps(value)
                valid_data[key] = value

        result = self.db.insert(self.table_name, valid_data)
        return result

    def get_by_id(self, record_id: int) -> Optional[Dict]:
        """IDでレコードを取得"""
        result = self.db.fetch_where(self.table_name, "id = ?", (record_id,))
        return result[0] if result else None

    def get_by_hash(self, file_hash: str) -> Optional[Dict]:
        """ハッシュでレコードを検索（重複チェック）"""
        result = self.db.fetch_where(self.table_name, "hash = ?", (file_hash,))
        return result[0] if result else None

    def get_by_collection(self, collection: str) -> List[Dict]:
        """コレクションでレコードを取得"""
        return self.db.fetch_where(self.table_name, "collection = ?", (collection,))

    def update_metadata(self, record_id: int, **kwargs):
        """メタデータを更新"""
        # スキーマに存在するフィールドのみを抽出
        valid_updates = {}
        for key, value in kwargs.items():
            if key in self.schema and key != "id":  # idは更新しない
                valid_updates[key] = value

        if valid_updates:
            self.db.update(self.table_name, valid_updates,
                           "id = ?", (record_id,))

    def delete_metadata(self, record_id: int):
        """メタデータを削除"""
        self.db.delete(self.table_name, "id = ?", (record_id,))

    def get_all(self) -> List[Dict]:
        """全レコードを取得"""
        return self.db.fetch_all(self.table_name)

    def search(self, condition: str, params: tuple) -> List[Dict]:
        """条件検索"""
        return self.db.fetch_where(self.table_name, condition, params)

    @abstractmethod
    def get_specific_fields(self, record_id: int) -> Optional[Dict]:
        """
        サブクラス固有のフィールド取得
        サブクラスで実装する
        """
        pass

    @abstractmethod
    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        ファイルのメタデータを取得
        サブクラスで実装する
        """
        pass
