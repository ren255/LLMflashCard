from __future__ import annotations
from typing import Optional, Dict, List, Any, Tuple
import json
import shutil
from pathlib import Path

from .base_managers import BaseStorage, BaseFileManager, BaseMetadataManager
from db.models import FLASHCARD_SCHEMA

class FlashcardStorage(BaseStorage):
    """フラッシュカードストレージ管理クラス"""

    def __init__(self, db_path: str, storage_path: str):
        super().__init__(db_path, storage_path)

    def _create_file_manager(self) -> CSVFileManager:
        """CSVファイルマネージャーを作成"""
        return CSVFileManager(self.storage_path)

    def _create_metadata_manager(self) -> FlashcardMetadataManager:
        """フラッシュカードメタデータマネージャーを作成"""
        return FlashcardMetadataManager(self.db_path, FLASHCARD_SCHEMA)

    # フラッシュカード固有の便利メソッド
    def save_csv(
        self,
        source_path: str,
        original_name: str,
        collection: str = "",
        columns_mapping: Dict[str, str] | None = None,
        **kwargs,
    ) -> Tuple[Optional[int], str]:
        """
        CSVファイルをフラッシュカード用に保存

        Args:
            source_path: 元CSVファイルパス
            original_name: 元ファイル名
            collection: コレクション名
            columns_mapping: カラムマッピング {"question": "質問", "answer": "回答"}
            **kwargs: その他のメタデータ

        Returns:
            (record_id, saved_path)
        """
        # カラムマッピングをJSONで保存
        if columns_mapping:
            kwargs["columns"] = json.dumps(columns_mapping)

        return self.save(
            source_path=source_path,
            original_name=original_name,
            collection=collection,
            **kwargs,
        )

    def get_columns(self, record_id: int) -> List[str]:
        """CSVのカラム一覧を取得"""
        info = self.metadata_manager.get_specific_fields(record_id)
        if info and info.get("columns"):
            return info["columns"]
        return []

    def update_columns_mapping(self, record_id: int, columns_mapping: Dict[str, str]):
        """カラムマッピングを更新"""
        self.metadata_manager.update_columns(record_id, list(columns_mapping.keys()))
        self.update_metadata(record_id, columns=json.dumps(columns_mapping))

    def get_csv_info(self, record_id: int) -> Optional[Dict]:
        """CSV固有の詳細情報を取得"""
        return self.metadata_manager.get_specific_fields(record_id)

    def get_by_row_count_range(self, min_rows: int, max_rows: int) -> List[Dict]:
        """行数範囲でフラッシュカードを検索"""
        records = self.metadata_manager.get_by_row_count_range(min_rows, max_rows)
        for record in records:
            record["full_path"] = self.file_manager.get_file_path(record["filename"])
        return records

    def get_encoding_info(self, record_id: int) -> Optional[str]:
        """ファイルエンコーディング情報を取得"""
        metadata = self.get(record_id)
        return metadata.get("encoding") if metadata else None

    def update_encoding(self, record_id: int, encoding: str):
        """エンコーディング情報を更新"""
        self.update_metadata(record_id, encoding=encoding)

    def get_delimiter_info(self, record_id: int) -> Optional[str]:
        """区切り文字情報を取得"""
        metadata = self.get(record_id)
        return metadata.get("delimiter") if metadata else None

    def update_delimiter(self, record_id: int, delimiter: str):
        """区切り文字を更新"""
        self.update_metadata(record_id, delimiter=delimiter)

    def get_flashcard_stats(self) -> Dict[str, Any]:
        """フラッシュカード固有の統計情報を取得"""
        base_stats = self.get_stats()
        all_records = self.get_all()

        total_rows = sum(record.get("row_count", 0) for record in all_records)
        encodings = {}
        delimiters = {}

        for record in all_records:
            # エンコーディング統計
            encoding = record.get("encoding", "unknown")
            encodings[encoding] = encodings.get(encoding, 0) + 1

            # 区切り文字統計
            delimiter = record.get("delimiter", ",")
            delimiters[delimiter] = delimiters.get(delimiter, 0) + 1

        return {
            **base_stats,
            "total_flashcards": total_rows,
            "encodings": encodings,
            "delimiters": delimiters,
            "avg_rows_per_file": total_rows / len(all_records) if all_records else 0,
        }

    def search_by_content(self, search_term: str) -> List[Dict]:
        """
        ファイル名や元ファイル名でフラッシュカードを検索

        Args:
            search_term: 検索語

        Returns:
            マッチしたレコードのリスト
        """
        condition = "(original_name LIKE ? OR filename LIKE ?)"
        params = (f"%{search_term}%", f"%{search_term}%")
        return self.search(condition, params)

class CSVFileManager(BaseFileManager):
    """CSVファイル専用のマネージャー"""

    def __init__(self, base_path: str):
        super().__init__(base_path, "csvs")

    def save_file(
        self, source_path: str, original_name: str
    ) -> Tuple[str, str, Dict[str, Any]]:
        """CSVファイルを保存"""
        # ファイルハッシュ計算
        file_hash = self.calculate_hash(source_path)

        # 新しいファイル名生成
        new_filename = self.generate_filename(original_name)

        # 保存パス
        save_path = self.files_dir / new_filename

        # ファイルコピー
        shutil.copy2(source_path, save_path)

        # CSVメタデータ取得
        metadata = self.get_metadata(save_path)

        return str(save_path), file_hash, {**metadata, "filename": new_filename}

    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """CSVのメタデータを取得"""
        import pandas as pd

        try:
            # ファイル読み込み（エンコーディング自動検出）
            df = pd.read_csv(file_path, encoding="utf-8")

            return {
                "file_size": file_path.stat().st_size,
                "row_count": len(df),
                "columns": df.columns.tolist(),
                "encoding": "utf-8",
                "delimiter": ",",
            }
        except UnicodeDecodeError:
            try:
                # Shift-JISで再試行
                df = pd.read_csv(file_path, encoding="shift-jis")
                return {
                    "file_size": file_path.stat().st_size,
                    "row_count": len(df),
                    "columns": df.columns.tolist(),
                    "encoding": "shift-jis",
                    "delimiter": ",",
                }
            except Exception:
                return {
                    "file_size": file_path.stat().st_size,
                    "row_count": None,
                    "columns": None,
                    "encoding": "unknown",
                    "delimiter": ",",
                }
        except Exception:
            return {
                "file_size": file_path.stat().st_size,
                "row_count": None,
                "columns": None,
                "encoding": "utf-8",
                "delimiter": ",",
            }


class FlashcardMetadataManager(BaseMetadataManager):
    """フラッシュカードメタデータ管理"""

    def __init__(self, db_path: str, schema: Dict[str, str]):
        super().__init__(db_path, "flashcards", schema)

    def get_specific_fields(self, record_id: int) -> Optional[Dict]:
        """フラッシュカード固有のフィールドを取得"""
        record = self.get_by_id(record_id)
        if record:
            import json

            return {
                "columns": json.loads(record.get("columns", "[]")),
                "row_count": record.get("row_count"),
                "encoding": record.get("encoding"),
                "delimiter": record.get("delimiter"),
            }
        return None

    def update_columns(self, record_id: int, columns: List[str]):
        """カラム情報を更新"""
        self.update_metadata(record_id, columns=json.dumps(columns))

    def get_by_row_count_range(self, min_rows: int, max_rows: int) -> List[Dict]:
        """行数範囲で検索"""
        return self.search("row_count BETWEEN ? AND ?", (min_rows, max_rows))



