import os
from pathlib import Path
from typing import Dict, Any
from pathlib import Path

from .image_managers import ImageStorage
from .flashcard_managers import FlashcardStorage
from db import SQLiteManager
from db.models import IMAGE_SCHEMA, FLASHCARD_SCHEMA
from utils import log

class StorageController:
    """ストレージ管理の統合クラス - main.pyから呼ばれる"""
    
    FILETYPE_INFO = {
        "image": {
            "schema": IMAGE_SCHEMA,
            "storage_class": ImageStorage,
        },
        "flashcard": {
            "schema": FLASHCARD_SCHEMA,
            "storage_class": FlashcardStorage,
        },
    }

    def __init__(self, base_path: Path):
        """StorageControllerの初期化"""
        self.base_path = base_path
        
        if not (self.base_path.is_absolute() and self.base_path.exists() and self.base_path.is_dir()):
            log.error("invalid path")
            raise OSError("invalid path")
        
        self.db_dir = self.base_path / "db"
        
        # 辞書でパスとストレージインスタンスを管理
        self.db_paths = {}
        self.storage_paths = {}
        self._storage_instances = {}
        
        self._setup()

    def _setup(self):
        """初期セットアップ"""
        # 各ファイルタイプの情報を辞書に保存
        for file_type, info in self.FILETYPE_INFO.items():
            # データベースパス
            self.db_paths[file_type] = Path(self.db_dir / f"{file_type}s.db")
            
            # ストレージパス（各ファイルタイプごとに直接配置）
            self.storage_paths[file_type] = Path(self.base_path / file_type)
            
            # ストレージインスタンスは遅延初期化のためNoneで初期化
            self._storage_instances[file_type] = None
        
        self._setup_directories()
        self._setup_databases()

    def _setup_directories(self):
        """必要なディレクトリを作成"""
        # 基本ディレクトリ
        base_directories = [
            self.db_dir,
            self.base_path / "temp",
            self.base_path / "thumbnails",
        ]
        
        # 各ファイルタイプのディレクトリ
        type_directories = []
        for file_type in self.FILETYPE_INFO.keys():
            type_directories.extend([
                self.base_path / file_type,              # resources/image, resources/flashcard
                self.base_path / "temp" / file_type,     # resources/temp/image, resources/temp/flashcard
                self.base_path / "thumbnails" / file_type, # resources/thumbnails/image, resources/thumbnails/flashcard
            ])
        
        all_directories = base_directories + type_directories
        
        for directory in all_directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        log.info(f"ディレクトリセットアップ完了: {self.base_path}")

    def _setup_databases(self):
        """データベースをセットアップ（テーブル作成）"""
        for file_type, info in self.FILETYPE_INFO.items():
            db_path = self.db_paths[file_type]
            schema = info["schema"]
            table_name = file_type + "_metadata"
            
            if not os.path.exists(db_path):
                log.info(f"{file_type}データベースを作成: {db_path}")
            
            db = SQLiteManager(db_path)
            db.create_table(table_name, schema)
            db.close()
        
        log.info("データベースセットアップ完了")

    def _get_storage_instance(self, file_type: str):
        """ストレージインスタンスを取得（遅延初期化）"""
        if file_type not in self.FILETYPE_INFO:
            log.error(f"未対応のファイルタイプ: {file_type}")
            raise ValueError("Unsupported file type")
        
        if self._storage_instances[file_type] is None:
            info = self.FILETYPE_INFO[file_type]
            storage_class = info["storage_class"]
            
            file_type_paths = {
            "base_path": str(self.base_path),
            "db_path": self.db_paths[file_type],
            "storage_path": self.storage_paths[file_type],
            "thumbnails_path": str(self.base_path / "thumbnails" / file_type),
            "temp_path": str(self.base_path / "temp" / file_type),
            }
            
            self._storage_instances[file_type] = storage_class(
                file_type,
                file_type_paths,
            )
        
        return self._storage_instances[file_type]

    @property
    def image_storage(self) -> ImageStorage:
        """画像ストレージのインスタンスを取得"""
        return self._get_storage_instance("image")

    @property
    def flashcard_storage(self) -> FlashcardStorage:
        """フラッシュカードストレージのインスタンスを取得"""
        return self._get_storage_instance("flashcard")

    def get_storage(self, file_type: str):
        """任意のファイルタイプのストレージを取得"""
        return self._get_storage_instance(file_type)

    def get_paths_info(self) -> Dict[str, Any]:
        """パス情報を取得"""
        paths_info = {
            "base_path": str(self.base_path),
            "db_dir": str(self.db_dir),
            "temp_dir": str(self.base_path / "temp"),
            "thumbnails_dir": str(self.base_path / "thumbnails"),
        }
        
        # 各ファイルタイプのパス情報を追加
        for file_type in self.FILETYPE_INFO.keys():
            paths_info.update({
                f"{file_type}_db_path": self.db_paths[file_type],
                f"{file_type}_storage_path": self.storage_paths[file_type],
                f"{file_type}_temp_path": str(self.base_path / "temp" / file_type),
                f"{file_type}_thumbnails_path": str(self.base_path / "thumbnails" / file_type),
            })
        
        return paths_info

    def get_storage_stats(self) -> Dict[str, Any]:
        """全ストレージの統計情報を取得"""
        stats = {}
        total_files = 0
        total_size = 0
        
        for file_type in self.FILETYPE_INFO.keys():
            storage = self._get_storage_instance(file_type)
            
            if file_type == "flashcard":
                type_stats = storage.get_flashcard_stats()
            else:
                type_stats = storage.get_stats()
            
            stats[file_type] = type_stats
            total_files += type_stats.get("total_files", 0)
            total_size += type_stats.get("total_size", 0)
        
        stats.update({
            "total_files": total_files,
            "total_size": total_size
        })
        
        return stats

    def cleanup(self):
        """リソースのクリーンアップ"""
        for file_type, instance in self._storage_instances.items():
            if instance is not None:
                instance.metadataMgr.db.close()
                log.info(f"{file_type}ストレージをクリーンアップ")
        
        log.info("StorageController クリーンアップ完了")
