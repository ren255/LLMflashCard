from __future__ import annotations
from typing import Optional, Dict, List, Any, Tuple
import os
import uuid
import hashlib
from pathlib import Path

from abc import ABC, abstractmethod
from db.sqlite_utils import SQLiteManager

class BaseStorage(ABC):
    """ストレージ管理の基底クラス"""

    def __init__(self, db_path: str, storage_path: str):
        self.db_path = db_path
        self.storage_path = storage_path
        self.file_manager = self._create_file_manager()
        self.metadata_manager = self._create_metadata_manager()

    @abstractmethod
    def _create_file_manager(self) -> BaseFileManager:
        """ファイルマネージャーを作成（サブクラスで実装）"""
        pass

    @abstractmethod
    def _create_metadata_manager(self) -> BaseMetadataManager:
        """メタデータマネージャーを作成（サブクラスで実装）"""
        pass

    def save(self, source_path: str, original_name: str, collection: str = "", **kwargs) -> Tuple[Optional[int], str]:
        """
        ファイルを保存（重複チェック付き）
        Returns: (record_id, saved_path) - record_idはエラー時None
        """
        try:
            # 一時的にハッシュを計算して重複チェック
            temp_hash = self.file_manager.calculate_hash(source_path)
            existing = self.metadata_manager.get_by_hash(temp_hash)

            if existing:
                # 既に存在する場合は既存のIDを返す
                return existing["id"], existing["file_path"]

            # 新規保存
            saved_path, file_hash, metadata = self.file_manager.save_file(
                source_path, original_name
            )

            # 相対パス計算
            relative_path = self.file_manager.get_relative_path(saved_path)

            # メタデータ準備
            save_data = {
                "filename": metadata["filename"],
                "original_name": original_name,
                "file_path": relative_path,
                "hash": file_hash,
                "collection": collection,
                **metadata,
                **kwargs  # 追加のメタデータ
            }

            # メタデータ保存
            record_id = self.metadata_manager.save_metadata(**save_data)

            return record_id, saved_path

        except Exception as e:
            print(f"ファイル保存エラー: {e}")
            return None, ""

    def get(self, record_id: int) -> Optional[Dict]:
        """レコード情報を取得"""
        metadata = self.metadata_manager.get_by_id(record_id)
        if metadata:
            # 完全パスを追加
            full_path = self.file_manager.get_file_path(metadata["filename"])
            metadata["full_path"] = full_path
        return metadata

    def delete(self, record_id: int) -> bool:
        """ファイルを完全削除"""
        try:
            # メタデータ取得
            metadata = self.metadata_manager.get_by_id(record_id)
            if not metadata:
                return False

            # ファイル削除
            full_path = self.file_manager.get_file_path(metadata["filename"])
            thumbnail_path = metadata.get("thumbnail_path", "")
            self.file_manager.delete_file(full_path, thumbnail_path)

            # メタデータ削除
            self.metadata_manager.delete_metadata(record_id)

            return True
        except Exception as e:
            print(f"削除エラー: {e}")
            return False

    def get_all(self) -> List[Dict]:
        """全レコードを取得"""
        records = self.metadata_manager.get_all()
        for record in records:
            record["full_path"] = self.file_manager.get_file_path(
                record["filename"])
        return records

    def get_by_collection(self, collection: str) -> List[Dict]:
        """コレクション別に取得"""
        records = self.metadata_manager.get_by_collection(collection)
        for record in records:
            record["full_path"] = self.file_manager.get_file_path(
                record["filename"])
        return records

    def update_metadata(self, record_id: int, **kwargs):
        """メタデータを更新"""
        self.metadata_manager.update_metadata(record_id, **kwargs)

    def search(self, condition: str, params: tuple) -> List[Dict]:
        """条件検索"""
        records = self.metadata_manager.search(condition, params)
        for record in records:
            record["full_path"] = self.file_manager.get_file_path(
                record["filename"])
        return records

    def get_collections(self) -> List[str]:
        """すべてのコレクション名を取得"""
        records = self.metadata_manager.get_all()
        collections = set()
        for record in records:
            if record.get("collection"):
                collections.add(record["collection"])
        return sorted(list(collections))

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        all_records = self.metadata_manager.get_all()

        total_size = sum(record.get("file_size", 0) for record in all_records)
        collections = self.get_collections()

        return {
            "total_files": len(all_records),
            "total_size": total_size,
            "collections": len(collections),
            "collection_names": collections
        }
class BaseFileManager(ABC):
    """ファイル管理の基底クラス"""

    def __init__(self, base_path: str, file_type: str):
        self.base_path = Path(base_path)
        self.file_type = file_type
        self.files_dir = self.base_path / file_type
        self.thumbnails_dir = self.base_path / "thumbnails" / file_type
        self.temp_dir = self.base_path / "temp" / file_type

        # ディレクトリ作成
        self._create_directories()

    def _create_directories(self):
        """必要なディレクトリを作成"""
        for directory in [self.files_dir, self.thumbnails_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def calculate_hash(self, file_path: str) -> str:
        """ファイルのSHA256ハッシュを計算"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def generate_filename(self, original_name: str) -> str:
        """新しいファイル名を生成（重複防止）"""
        file_extension = Path(original_name).suffix.lower()
        return f"{uuid.uuid4().hex}{file_extension}"

    def get_file_path(self, filename: str) -> str:
        """ファイル名から完全パスを取得"""
        return str(self.files_dir / filename)

    def get_relative_path(self, full_path: str) -> str:
        """完全パスから相対パスを生成"""
        return str(Path(full_path).relative_to(self.base_path))

    def delete_file(self, file_path: str, thumbnail_path: str = ""):
        """ファイルとサムネイルを削除"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except Exception as e:
            print(f"ファイル削除エラー: {e}")

    @abstractmethod
    def save_file(self, source_path: str, original_name: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        ファイルを保存し、メタデータを返す
        Returns: (saved_path, file_hash, metadata)
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


class BaseMetadataManager(ABC):
    """メタデータ管理の基底クラス"""

    def __init__(self, db_path: str, table_name: str, schema: Dict[str, str]):
        self.db = SQLiteManager(db_path)
        self.table_name = table_name
        self.schema = schema
        self._initialize_tables()

    def _initialize_tables(self):
        """テーブル初期化"""
        self.db.create_table(self.table_name, self.schema)

    def save_metadata(self, **kwargs) -> Optional[int]:
        """
        メタデータを保存
        Returns: 保存されたレコードのID、失敗時はNone
        """
        # スキーマに存在するフィールドのみを抽出
        valid_data = {}
        for key, value in kwargs.items():
            if key in self.schema:
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

