import os
from pathlib import Path
from typing import Optional

from .image_managers import ImageStorage
from .flashcard_managers import FlashcardStorage
from db.sqlite_utils import SQLiteManager
from db.models import IMAGE_SCHEMA, FLASHCARD_SCHEMA


class StorageManager:
    """ストレージ管理の統合クラス - main.pyから呼ばれる"""
    
    def __init__(self, base_path: str = "./resources"):
        """
        StorageManagerの初期化
        
        Args:
            base_path: ベースディレクトリパス（デフォルト: ./resources）
        """
        self.base_path = Path(base_path)
        
        # パス設定
        self.db_dir = self.base_path / "db"
        self.storage_dir = self.base_path / "storage"
        self.img_dir = self.base_path / "img"  # 画像専用ディレクトリ
        
        # データベースファイルパス
        self.image_db_path = str(self.db_dir / "images.db")
        self.flashcard_db_path = str(self.db_dir / "flashcards.db")
        
        # ストレージインスタンス（遅延初期化）
        self._image_storage: Optional[ImageStorage] = None
        self._flashcard_storage: Optional[FlashcardStorage] = None
        
        # 初期化実行
        self._setup_directories()
        self._setup_databases()
    
    def _setup_directories(self):
        """必要なディレクトリを作成"""
        directories = [
            self.db_dir,
            self.storage_dir,
            self.img_dir,
            self.storage_dir / "images",
            self.storage_dir / "csvs", 
            self.storage_dir / "thumbnails" / "images",
            self.storage_dir / "temp" / "images",
            self.storage_dir / "temp" / "csvs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        print(f"ディレクトリセットアップ完了: {self.base_path}")
    
    def _setup_databases(self):
        """データベースをセットアップ（テーブル作成）"""
        # 画像データベース
        if not os.path.exists(self.image_db_path):
            print(f"画像データベースを作成: {self.image_db_path}")
        
        image_db = SQLiteManager(self.image_db_path)
        image_db.create_table("images", IMAGE_SCHEMA)
        image_db.close()
        
        # フラッシュカードデータベース
        if not os.path.exists(self.flashcard_db_path):
            print(f"フラッシュカードデータベースを作成: {self.flashcard_db_path}")
        
        flashcard_db = SQLiteManager(self.flashcard_db_path)
        flashcard_db.create_table("flashcards", FLASHCARD_SCHEMA)
        flashcard_db.close()
        
        print("データベースセットアップ完了")
    
    @property
    def image_storage(self) -> ImageStorage:
        """画像ストレージのインスタンスを取得（遅延初期化）"""
        if self._image_storage is None:
            self._image_storage = ImageStorage(
                db_path=self.image_db_path,
                storage_path=str(self.img_dir)  # 画像は resources/img に保存
            )
        return self._image_storage
    
    @property
    def flashcard_storage(self) -> FlashcardStorage:
        """フラッシュカードストレージのインスタンスを取得（遅延初期化）"""
        if self._flashcard_storage is None:
            self._flashcard_storage = FlashcardStorage(
                db_path=self.flashcard_db_path,
                storage_path=str(self.storage_dir)  # CSVは resources/storage に保存
            )
        return self._flashcard_storage
    
    def get_paths_info(self) -> dict:
        """パス情報を取得"""
        return {
            "base_path": str(self.base_path),
            "db_dir": str(self.db_dir),
            "storage_dir": str(self.storage_dir),
            "img_dir": str(self.img_dir),
            "image_db": self.image_db_path,
            "flashcard_db": self.flashcard_db_path
        }
    
    def get_storage_stats(self) -> dict:
        """全ストレージの統計情報を取得"""
        image_stats = self.image_storage.get_stats()
        flashcard_stats = self.flashcard_storage.get_flashcard_stats()
        
        return {
            "images": image_stats,
            "flashcards": flashcard_stats,
            "total_files": image_stats["total_files"] + flashcard_stats["total_files"],
            "total_size": image_stats["total_size"] + flashcard_stats["total_size"]
        }
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        if self._image_storage:
            self._image_storage.metadata_manager.db.close()
        if self._flashcard_storage:
            self._flashcard_storage.metadata_manager.db.close()
        
        print("StorageManager クリーンアップ完了")


# ===========================================
# main.py での使用例
# ===========================================

def main_example():
    """main.pyでの使用例"""
    
    # StorageManager初期化（自動でディレクトリ・DB作成）
    storage_manager = StorageManager("./resources")
    
    # パス情報確認
    paths = storage_manager.get_paths_info()
    print("パス設定:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    
    # 画像ストレージ使用
    image_storage = storage_manager.image_storage
    
    # フラッシュカードストレージ使用  
    flashcard_storage = storage_manager.flashcard_storage
    
    # 統計情報表示
    stats = storage_manager.get_storage_stats()
    print(f"\n統計情報:")
    print(f"  画像ファイル数: {stats['images']['total_files']}")
    print(f"  フラッシュカード数: {stats['flashcards']['total_files']}")
    print(f"  総ファイル数: {stats['total_files']}")
    
    # クリーンアップ
    storage_manager.cleanup()


if __name__ == "__main__":
    main_example()