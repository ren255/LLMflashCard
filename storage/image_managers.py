from __future__ import annotations
from typing import Optional, Dict, List, Any, Tuple
import shutil
from pathlib import Path
from PIL import Image

from .base_managers import BaseStorage, BaseFileManager, BaseMetadataManager
from db.models import IMAGE_SCHEMA

class ImageStorage(BaseStorage):
    """画像ストレージ管理クラス"""
    
    def __init__(self, db_path: str, storage_path: str):
        super().__init__(db_path, storage_path)
    
    def _create_file_manager(self) -> ImageFileManager:
        """画像ファイルマネージャーを作成"""
        return ImageFileManager(self.storage_path)
    
    def _create_metadata_manager(self) -> ImageMetadataManager:
        """画像メタデータマネージャーを作成"""
        return ImageMetadataManager(self.db_path, IMAGE_SCHEMA)
    
    # 画像固有の便利メソッド
    def save_image(self, source_path: str, original_name: str, 
                   collection: str = "", image_type: str = "original",
                   **kwargs) -> Tuple[Optional[int], str]:
        """
        画像を保存（画像固有のパラメータ付き）
        
        Args:
            source_path: 元ファイルパス
            original_name: 元ファイル名
            collection: コレクション名
            image_type: 画像タイプ（original, split, mask等）
            **kwargs: その他のメタデータ
        
        Returns:
            (record_id, saved_path)
        """
        return self.save(
            source_path=source_path,
            original_name=original_name,
            collection=collection,
            image_type=image_type,
            **kwargs
        )
    
    def get_by_type(self, image_type: str) -> List[Dict]:
        """画像タイプで検索"""
        records = self.metadata_manager.get_by_type(image_type)
        for record in records:
            record["full_path"] = self.file_manager.get_file_path(record["filename"])
        return records
    
    def get_children(self, parent_id: int) -> List[Dict]:
        """親画像の子画像を取得"""
        children = self.metadata_manager.get_children(parent_id)
        for child in children:
            child["full_path"] = self.file_manager.get_file_path(child["filename"])
        return children
    
    def save_split_image(self, source_path: str, original_name: str,
                        parent_id: int, region_index: int,
                        collection: str = "", **kwargs) -> Tuple[Optional[int], str]:
        """
        分割画像を保存
        
        Args:
            source_path: 分割画像のパス
            original_name: 元ファイル名
            parent_id: 親画像のID
            region_index: 分割領域番号
            collection: コレクション名
            **kwargs: その他のメタデータ
        """
        return self.save_image(
            source_path=source_path,
            original_name=original_name,
            collection=collection,
            image_type="split",
            parent_image_id=parent_id,
            region_index=region_index,
            **kwargs
        )
    
    def save_mask_image(self, source_path: str, original_name: str,
                       parent_id: int, mask_data: str,
                       collection: str = "", **kwargs) -> Tuple[Optional[int], str]:
        """
        マスク画像を保存
        
        Args:
            source_path: マスク画像のパス
            original_name: 元ファイル名
            parent_id: 親画像のID
            mask_data: マスク情報（JSON文字列等）
            collection: コレクション名
            **kwargs: その他のメタデータ
        """
        return self.save_image(
            source_path=source_path,
            original_name=original_name,
            collection=collection,
            image_type="mask",
            parent_image_id=parent_id,
            mask_image_id=mask_data,
            **kwargs
        )
    
    def get_thumbnail_path(self, record_id: int) -> Optional[str]:
        """サムネイルパスを取得"""
        metadata = self.get(record_id)
        return metadata.get("thumbnail_path") if metadata else None
    
    def get_image_info(self, record_id: int) -> Optional[Dict]:
        """画像固有の詳細情報を取得"""
        return self.metadata_manager.get_specific_fields(record_id)
    
    def update_image_type(self, record_id: int, image_type: str):
        """画像タイプを更新"""
        self.update_metadata(record_id, image_type=image_type)
    
    def link_mask(self, image_id: int, mask_data: str):
        """画像にマスク情報をリンク"""
        self.update_metadata(image_id, mask_image_id=mask_data)
    
    def get_by_size_range(self, min_width: int = 0, max_width: int = 999999,
                         min_height: int = 0, max_height: int = 999999) -> List[Dict]:
        """サイズ範囲で画像を検索"""
        records = self.metadata_manager.get_by_size_range(
            min_width, max_width, min_height, max_height
        )
        for record in records:
            record["full_path"] = self.file_manager.get_file_path(record["filename"])
        return records
    
    def get_by_format(self, format_name: str) -> List[Dict]:
        """フォーマットで画像を検索"""
        records = self.metadata_manager.get_by_format(format_name)
        for record in records:
            record["full_path"] = self.file_manager.get_file_path(record["filename"])
        return records
    
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
        
        return {
            **base_stats,
            "formats": formats,
            "types": types,
            "sizes": sizes
        }
    
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

class ImageFileManager(BaseFileManager):
    """画像ファイル専用のマネージャー"""
    
    def __init__(self, base_path: str):
        super().__init__(base_path, "images")
    
    def save_file(self, source_path: str, original_name: str) -> Tuple[str, str, Dict[str, Any]]:
        """画像ファイルを保存"""
        try:
            # ファイルハッシュ計算
            file_hash = self.calculate_hash(source_path)
            
            # 新しいファイル名生成
            new_filename = self.generate_filename(original_name)
            
            # 保存パス
            save_path = self.files_dir / new_filename
            
            # ファイルコピー
            shutil.copy2(source_path, save_path)
            
            # 画像メタデータ取得
            metadata = self.get_metadata(save_path)
            
            # サムネイル作成
            thumbnail_path = self._create_thumbnail(save_path, new_filename)
            
            return str(save_path), file_hash, {
                **metadata,
                "thumbnail_path": thumbnail_path,
                "filename": new_filename
            }
        except Exception as e:
            print(f"画像保存エラー: {e}")
            raise
    
    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """画像のメタデータを取得"""
        try:
            with Image.open(file_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "file_size": file_path.stat().st_size
                }
        except Exception as e:
            print(f"画像メタデータ取得エラー: {e}")
            return {
                "width": None,
                "height": None,
                "format": None,
                "file_size": file_path.stat().st_size
            }
    
    def _create_thumbnail(self, image_path: Path, filename: str) -> str:
        """サムネイル作成"""
        try:
            thumbnail_name = f"thumb_{filename}"
            thumbnail_path = self.thumbnails_dir / thumbnail_name
            
            with Image.open(image_path) as img:
                # RGB変換（RGBA対応）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", optimize=True, quality=85)
            
            return str(thumbnail_path)
        except Exception as e:
            print(f"サムネイル作成エラー: {e}")
            return ""


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
                "mask_image_id": record.get("mask_image_id")
            }
        return None
    
    def get_by_type(self, image_type: str) -> List[Dict]:
        """画像タイプで検索"""
        return self.search("image_type = ?", (image_type,))
    
    def get_children(self, parent_id: int) -> List[Dict]:
        """親画像IDで子画像を検索"""
        return self.search("parent_image_id = ?", (parent_id,))
    
    def get_by_size_range(self, min_width: int = 0, max_width: int = 999999,
                         min_height: int = 0, max_height: int = 999999) -> List[Dict]:
        """サイズ範囲で画像を検索"""
        condition = "width BETWEEN ? AND ? AND height BETWEEN ? AND ?"
        params = (min_width, max_width, min_height, max_height)
        return self.search(condition, params)
    
    def get_by_format(self, format_name: str) -> List[Dict]:
        """フォーマットで画像を検索"""
        return self.search("format = ?", (format_name,))


