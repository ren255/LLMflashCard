from __future__ import annotations
from typing import Optional, Dict, List, Any, Tuple
import shutil
from pathlib import Path
from PIL import Image

from .base_managers import BaseStorage, BaseMetadataManager
from .file_manager import FileManager
from db.models import IMAGE_SCHEMA

##
# @brief 画像ストレージ管理クラス
# @details メタデータclassとfilemanagerを組み合わせて画像の保存、検索、メタデータ管理を行う


class ImageStorage(BaseStorage):
    """画像ストレージ管理クラス"""

    def __init__(self, file_type: str, paths: Dict[str, str]):
        super().__init__(file_type, paths)

    def _create_file_manager(self) -> FileManager:
        """画像ファイルマネージャーを作成"""
        return FileManager(self.paths)

    def _create_metadata_manager(self) -> ImageMetadataManager:
        """画像メタデータマネージャーを作成"""
        return ImageMetadataManager(self.paths["db_path"], IMAGE_SCHEMA)

    # 画像固有の便利メソッド
    def save(self, source_path: Path, collection: str = "", **kwargs) -> int | None:
        """
        画像を保存（画像固有のパラメータ付き）
        record_idを返す。重複ファイルは保存しない。
        """
        return self.save_file(source_path=source_path, collection=collection, **kwargs)

    # def get_children(self, parent_id: int) -> List[Dict]:
    #     """親画像の子画像を取得"""
    #     children = self.metadataMgr.get_children(parent_id)
    #     for child in children:
    #         child["full_path"] = self.fileMgr.get_file_path(child["filename"])
    #     return children

    def save_split_image(
        self, parent_id: int, maskid: int, region_index: int, **kwargs
    ) -> int | None:
        """
        分割画像を保存
        """
        metadata = self.get(parent_id)
        if not metadata:
            return None

        return self.save(
            source_path=metadata["file_path"],
            original_name=metadata["original_name"],
            collection=metadata["collection"],
            image_type="split",
            parent_image_id=parent_id,
            region_index=region_index,
            **kwargs,
        )

    def get_thumbnail_path(self, record_id: int) -> Optional[str]:
        """サムネイルパスを取得"""
        metadata = self.get(record_id)
        return metadata.get("thumbnail_path") if metadata else None

    def get_image_info(self, record_id: int) -> Optional[Dict]:
        """画像固有の詳細情報を取得"""
        return self.metadataMgr.get_specific_fields(record_id)

    def update_image_type(self, record_id: int, image_type: str):
        """画像タイプを更新"""
        self.update_metadata(record_id, image_type=image_type)

    def link_mask(self, image_id: int, mask_data: str):
        """画像にマスク情報をリンク"""
        self.update_metadata(image_id, mask_image_id=mask_data)

    # def get_by_size_range(self, min_width: int = 0, max_width: int = 999999,
    #                      min_height: int = 0, max_height: int = 999999) -> List[Dict]:
    #     """サイズ範囲で画像を検索"""
    #     records = self.metadataMgr.get_by_size_range(
    #         min_width, max_width, min_height, max_height
    #     )
    #     for record in records:
    #         record["full_path"] = self.fileMgr.get_file_path(record["filename"])
    #     return records

    # def get_by_format(self, format_name: str) -> List[Dict]:
    #     """フォーマットで画像を検索"""
    #     records = self.metadataMgr.get_by_format(format_name)
    #     for record in records:
    #         record["full_path"] = self.fileMgr.get_file_path(record["filename"])
    #     return records

    def get_image_stats(self) -> Dict[str, Any]:
        """画像固有の統計情報を取得"""
        base_stats = self.get_stats()
        all_records = self.get_all()

        formats = {}
        types = {}
        sizes = {"small": 0, "medium": 0, "large": 0}

        for record in all_records:
            # フォーマット統計
            format_name = record.get("format", "unknown")
            formats[format_name] = formats.get(format_name, 0) + 1

            # タイプ統計
            image_type = record.get("image_type", "unknown")
            types[image_type] = types.get(image_type, 0) + 1

            # サイズ統計
            width = record.get("width", 0) or 0
            height = record.get("height", 0) or 0
            max_dimension = max(width, height)

            if max_dimension < 500:
                sizes["small"] += 1
            elif max_dimension < 1500:
                sizes["medium"] += 1
            else:
                sizes["large"] += 1

        return {**base_stats, "formats": formats, "types": types, "sizes": sizes}

    def search_by_content(self, search_term: str) -> List[Dict]:
        """
        ファイル名や元ファイル名で画像を検索

        Args:
            search_term: 検索語

        Returns:
            マッチしたレコードのリスト
        """
        condition = "(original_name LIKE ? OR filename LIKE ?)"
        params = (f"%{search_term}%", f"%{search_term}%")
        return self.search(condition, params)


class ImageMetadataManager(BaseMetadataManager):
    """画像メタデータ管理"""

    def __init__(self, db_path: str, schema: Dict[str, str]):
        super().__init__(db_path, "images", schema)

    def get_specific_fields(self, record_id: int) -> Optional[Dict]:
        """画像固有のフィールドを取得"""
        record = self.get_by_id(record_id)
        if record:
            return {
                "width": record.get("width"),
                "height": record.get("height"),
                "format": record.get("format"),
                "thumbnail_path": record.get("thumbnail_path"),
                "image_type": record.get("image_type"),
                "region_index": record.get("region_index"),
                "parent_image_id": record.get("parent_image_id"),
                "mask_image_id": record.get("mask_image_id"),
            }
        return None

    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """画像のメタデータを取得"""
        try:
            with Image.open(file_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "file_size": file_path.stat().st_size,
                }
        except Exception as e:
            print(f"画像メタデータ取得エラー: {e}")
            return {
                "width": None,
                "height": None,
                "format": None,
                "file_size": file_path.stat().st_size,
            }

    def get_by_type(self, image_type: str) -> List[Dict]:
        """画像タイプで検索"""
        return self.search("image_type = ?", (image_type,))

    def get_children(self, parent_id: int) -> List[Dict]:
        """親画像IDで子画像を検索"""
        return self.search("parent_image_id = ?", (parent_id,))

    def get_by_size_range(
        self,
        min_width: int = 0,
        max_width: int = 999999,
        min_height: int = 0,
        max_height: int = 999999,
    ) -> List[Dict]:
        """サイズ範囲で画像を検索"""
        condition = "width BETWEEN ? AND ? AND height BETWEEN ? AND ?"
        params = (min_width, max_width, min_height, max_height)
        return self.search(condition, params)

    def get_by_format(self, format_name: str) -> List[Dict]:
        """フォーマットで画像を検索"""
        return self.search("format = ?", (format_name,))
