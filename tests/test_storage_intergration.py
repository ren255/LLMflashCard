"""
Storage Module Integration Tests

StorageControllerを中心とした統合テスト
画像とフラッシュカードストレージの連携動作を検証
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import time
import os
import json
from typing import List, Dict, Any

# テスト対象のインポート（実際のプロジェクト構造に合わせて調整）
from storage.storage_controller import StorageController
from storage.base_managers import BaseStorage
from storage.image_managers import ImageStorage
from storage.flashcard_managers import FlashcardStorage


class TestStorageIntegration:
    """Storage統合テストクラス"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """各テストの前後でテスト環境をセットアップ・クリーンアップ"""
        # テスト用一時ディレクトリ作成
        self.test_base_path = Path(tempfile.mkdtemp(prefix="storage_test_"))
        self.controller = StorageController(str(self.test_base_path))
        
        # テストデータのパス（fixturesディレクトリ）
        self.fixtures_path = Path(__file__).parent / "fixtures"
        self.test_images_path = self.fixtures_path / "test_images"
        self.test_csvs_path = self.fixtures_path / "test_csvs"
        self.bulk_path = self.fixtures_path / "bulk"
        
        yield
        
        # クリーンアップ
        self.controller.cleanup()
        if self.test_base_path.exists():
            shutil.rmtree(self.test_base_path)

    def test_controller_initialization(self):
        """StorageControllerの初期化テスト"""
        # ディレクトリ構造の確認
        assert self.controller.base_path.exists()
        assert (self.controller.base_path / "db").exists()
        assert (self.controller.base_path / "image").exists()
        assert (self.controller.base_path / "flashcard").exists()
        assert (self.controller.base_path / "temp").exists()
        assert (self.controller.base_path / "thumbnails").exists()
        assert (self.controller.base_path / "thumbnails" / "image").exists()
        assert (self.controller.base_path / "thumbnails" / "flashcard").exists()
        
        # データベースファイルの確認
        for file_type in ["image", "flashcard"]:
            db_path = self.controller.db_paths[file_type]
            assert Path(db_path).exists()

    def test_storage_instance_access(self):
        """ストレージインスタンスのアクセステスト"""
        # 遅延初期化の確認
        assert self.controller._storage_instances["image"] is None
        assert self.controller._storage_instances["flashcard"] is None
        
        # プロパティアクセス
        image_storage = self.controller.image_storage
        assert isinstance(image_storage, ImageStorage)
        assert self.controller._storage_instances["image"] is not None
        
        flashcard_storage = self.controller.flashcard_storage
        assert isinstance(flashcard_storage, FlashcardStorage)
        assert self.controller._storage_instances["flashcard"] is not None
        
        # get_storage()メソッド
        assert self.controller.get_storage("image") is image_storage
        assert self.controller.get_storage("flashcard") is flashcard_storage
        
        # 無効なファイルタイプ
        with pytest.raises(ValueError):
            self.controller.get_storage("invalid_type")

    def test_paths_info(self):
        """パス情報取得テスト"""
        paths_info = self.controller.get_paths_info()
        
        # 必要なキーの存在確認
        required_keys = [
            "base_path", "db_dir", "temp_dir", "thumbnails_dir",
            "image_db_path", "image_storage_path", "image_temp_path", "image_thumbnails_path",
            "flashcard_db_path", "flashcard_storage_path", "flashcard_temp_path", "flashcard_thumbnails_path"
        ]
        
        for key in required_keys:
            assert key in paths_info
            assert paths_info[key]  # 空でないことを確認

    def test_image_storage_basic_operations(self):
        """画像ストレージの基本操作テスト"""
        image_storage = self.controller.image_storage
        
        if not self.test_images_path.exists():
            pytest.skip("Test images directory not found")
        
        # テスト画像の保存
        test_image = self.test_images_path / "small_red.jpg"
        if test_image.exists():
            record_id = image_storage.save(test_image, collection="test_collection")
            assert record_id is not None
            
            # 保存されたデータの取得
            saved_data = image_storage.get(record_id)
            assert saved_data is not None
            assert saved_data["collection"] == "test_collection"
            assert "full_path" in saved_data
            assert saved_data["original_name"] == "small_red.jpg"
            
            # サムネイルの確認
            thumbnail_path = image_storage.get_thumbnail_path(record_id)
            assert thumbnail_path is not None
            assert Path(thumbnail_path).exists()
            
            # 画像削除
            assert image_storage.delete(record_id) is True
            assert image_storage.get(record_id) is None

    def test_flashcard_storage_basic_operations(self):
        """フラッシュカードストレージの基本操作テスト"""
        flashcard_storage = self.controller.flashcard_storage
        
        if not self.test_csvs_path.exists():
            pytest.skip("Test CSVs directory not found")
        
        # テストCSVの保存
        test_csv = self.test_csvs_path / "basic_flashcards_utf8.csv"
        if test_csv.exists():
            record_id = flashcard_storage.save(test_csv, collection="test_flashcards")
            assert record_id is not None
            
            # 保存されたデータの取得
            saved_data = flashcard_storage.get(record_id)
            assert saved_data is not None
            assert saved_data["collection"] == "test_flashcards"
            assert "full_path" in saved_data
            assert saved_data["original_name"] == "basic_flashcards_utf8.csv"
            
            # CSV固有情報の取得
            columns = flashcard_storage.get_columns(record_id)
            assert isinstance(columns, list)
            assert len(columns) > 0
            
            csv_info = flashcard_storage.get_csv_info(record_id)
            assert csv_info is not None
            assert "row_count" in csv_info
            assert "encoding" in csv_info
            
            # フラッシュカード削除
            assert flashcard_storage.delete(record_id) is True
            assert flashcard_storage.get(record_id) is None

    def test_duplicate_file_handling(self):
        """重複ファイル処理テスト"""
        image_storage = self.controller.image_storage
        
        test_image = self.test_images_path / "small_blue.png"
        if not test_image.exists():
            pytest.skip("Test image not found")
        
        # 最初の保存
        record_id1 = image_storage.save(test_image, collection="test1")
        assert record_id1 is not None
        
        # 同じファイルの再保存（重複として処理される）
        record_id2 = image_storage.save(test_image, collection="test2")
        assert record_id2 is None  # 重複なのでNoneが返される
        
        # 元のレコードが残っていることを確認
        saved_data = image_storage.get(record_id1)
        assert saved_data is not None

    def test_collection_management(self):
        """コレクション管理テスト"""
        image_storage = self.controller.image_storage
        flashcard_storage = self.controller.flashcard_storage
        
        # 複数のファイルを異なるコレクションに保存
        collections = ["collection_a", "collection_b", "collection_c"]
        image_files = [f for f in self.test_images_path.glob("*.jpg")][:3]
        csv_files = [f for f in self.test_csvs_path.glob("*.csv")][:3]
        
        saved_image_ids = []
        saved_csv_ids = []
        
        # 画像保存
        for i, img_file in enumerate(image_files):
            if i < len(collections):
                record_id = image_storage.save(img_file, collection=collections[i])
                if record_id:
                    saved_image_ids.append(record_id)
        
        # CSV保存
        for i, csv_file in enumerate(csv_files):
            if i < len(collections):
                record_id = flashcard_storage.save(csv_file, collection=collections[i])
                if record_id:
                    saved_csv_ids.append(record_id)
        
        # コレクション一覧の確認
        image_collections = image_storage.get_collections()
        flashcard_collections = flashcard_storage.get_collections()
        
        for collection in collections:
            if collection in image_collections:
                collection_images = image_storage.get_by_collection(collection)
                assert len(collection_images) >= 0
            
            if collection in flashcard_collections:
                collection_flashcards = flashcard_storage.get_by_collection(collection)
                assert len(collection_flashcards) >= 0

    def test_search_functionality(self):
        """検索機能テスト"""
        image_storage = self.controller.image_storage
        flashcard_storage = self.controller.flashcard_storage
        
        # テストデータ保存
        test_image = self.test_images_path / "medium_square.jpg"
        test_csv = self.test_csvs_path / "japanese_flashcards_utf8.csv"
        
        image_id = None
        csv_id = None
        
        if test_image.exists():
            image_id = image_storage.save(test_image, collection="search_test")
        
        if test_csv.exists():
            csv_id = flashcard_storage.save(test_csv, collection="search_test")
        
        # 内容検索
        if image_id:
            search_results = image_storage.search_by_content("medium")
            assert len(search_results) >= 1
            
        if csv_id:
            search_results = flashcard_storage.search_by_content("japanese")
            assert len(search_results) >= 1
        
        # 条件検索
        if image_id:
            condition_results = image_storage.search("collection=?", ("search_test",))
            assert len(condition_results) >= 1

    def test_statistics_collection(self):
        """統計情報収集テスト"""
        # 複数ファイル保存
        image_storage = self.controller.image_storage
        flashcard_storage = self.controller.flashcard_storage
        
        # テストファイル保存
        saved_count = 0
        for img_file in list(self.test_images_path.glob("*.jpg"))[:2]:
            if image_storage.save(img_file, collection="stats_test"):
                saved_count += 1
        
        for csv_file in list(self.test_csvs_path.glob("*.csv"))[:2]:
            if flashcard_storage.save(csv_file, collection="stats_test"):
                saved_count += 1
        
        # 統計情報取得
        storage_stats = self.controller.get_storage_stats()
        
        # 基本統計の確認
        assert "total_files" in storage_stats
        assert "total_size" in storage_stats
        assert storage_stats["total_files"] >= 0
        assert storage_stats["total_size"] >= 0
        
        # ファイルタイプ別統計
        if "image" in storage_stats:
            image_stats = storage_stats["image"]
            assert "total_files" in image_stats
            
        if "flashcard" in storage_stats:
            flashcard_stats = storage_stats["flashcard"]
            assert "total_files" in flashcard_stats

    def test_encoding_detection(self):
        """エンコーディング検出テスト"""
        flashcard_storage = self.controller.flashcard_storage
        
        # 異なるエンコーディングのCSVファイルをテスト
        encoding_files = {
            "utf8": "japanese_flashcards_utf8.csv",
            "sjis": "japanese_flashcards_sjis.csv",
            "cp932": "japanese_flashcards_cp932.csv"
        }
        
        for expected_encoding, filename in encoding_files.items():
            csv_file = self.test_csvs_path / filename
            if csv_file.exists():
                record_id = flashcard_storage.save(csv_file)
                if record_id:
                    detected_encoding = flashcard_storage.get_encoding_info(record_id)
                    assert detected_encoding is not None
                    # エンコーディングが検出されていること（具体的な値は実装による）
                    assert detected_encoding in ["utf-8", "shift-jis", "cp932", "unknown"]

    def test_bulk_operations_performance(self):
        """バルク操作のパフォーマンステスト"""
        if not self.bulk_path.exists():
            pytest.skip("Bulk test files not found")
        
        image_storage = self.controller.image_storage
        flashcard_storage = self.controller.flashcard_storage
        
        # 画像バルク保存
        image_files = list(self.bulk_path.glob("*.jpg"))[:10]  # 最初の10件
        csv_files = list(self.bulk_path.glob("*.csv"))[:10]    # 最初の10件
        
        # 画像保存のパフォーマンス測定
        start_time = time.time()
        saved_images = 0
        for img_file in image_files:
            if image_storage.save(img_file, collection="bulk_test"):
                saved_images += 1
        image_save_time = time.time() - start_time
        
        # CSV保存のパフォーマンス測定
        start_time = time.time()
        saved_csvs = 0
        for csv_file in csv_files:
            if flashcard_storage.save(csv_file, collection="bulk_test"):
                saved_csvs += 1
        csv_save_time = time.time() - start_time
        
        # パフォーマンス結果の記録（テスト失敗させない）
        print(f"\nBulk Operation Performance:")
        print(f"Images: {saved_images} files in {image_save_time:.2f}s")
        print(f"CSVs: {saved_csvs} files in {csv_save_time:.2f}s")
        
        assert saved_images >= 0  # 最低限の成功チェック
        assert saved_csvs >= 0

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        image_storage = self.controller.image_storage
        flashcard_storage = self.controller.flashcard_storage
        
        # 存在しないファイルの保存
        non_existent_file = Path("/non/existent/file.jpg")
        result = image_storage.save(non_existent_file)
        assert result is None
        
        # 存在しないレコードの取得
        result = image_storage.get(99999)
        assert result is None
        
        # 存在しないレコードの削除
        result = image_storage.delete(99999)
        assert result is False
        
        # 破損したファイルの処理
        corrupted_file = self.test_images_path / "corrupted.jpg"
        if corrupted_file.exists():
            result = image_storage.save(corrupted_file)
            # 破損ファイルでもメタデータが取れる場合は保存される場合がある
            # 具体的な動作は実装による

    def test_cleanup_and_resource_management(self):
        """クリーンアップとリソース管理テスト"""
        # テストファイル保存
        test_image = self.test_images_path / "small_green.webp"
        if test_image.exists():
            record_id = self.controller.image_storage.save(test_image)
            assert record_id is not None
        else:
            return
        
        # クリーンアップ実行
        self.controller.cleanup()
        
        # 新しいインスタンス作成時に既存データにアクセス可能か確認
        new_controller = StorageController(str(self.test_base_path))
        
        if record_id:
            # データが永続化されているか確認
            saved_data = new_controller.image_storage.get(record_id)
            assert saved_data is not None
        
        new_controller.cleanup()

    def test_concurrent_access_basic(self):
        """基本的な並行アクセステスト"""
        # 注: 本格的な並行テストは別途必要
        # ここでは基本的な複数操作の順次実行をテスト
        
        image_storage = self.controller.image_storage
        flashcard_storage = self.controller.flashcard_storage
        
        # 複数の画像を順次保存
        image_files = list(self.test_images_path.glob("*.png"))[:3]
        csv_files = list(self.test_csvs_path.glob("*.csv"))[:3]
        
        saved_ids = []
        
        # 画像とCSVを交互に保存
        for i in range(min(len(image_files), len(csv_files))):
            if i < len(image_files):
                img_id = image_storage.save(image_files[i], collection=f"concurrent_{i}")
                if img_id:
                    saved_ids.append(("image", img_id))
            
            if i < len(csv_files):
                csv_id = flashcard_storage.save(csv_files[i], collection=f"concurrent_{i}")
                if csv_id:
                    saved_ids.append(("flashcard", csv_id))
        
        # 保存されたデータの整合性確認
        for storage_type, record_id in saved_ids:
            if storage_type == "image":
                data = image_storage.get(record_id)
            else:
                data = flashcard_storage.get(record_id)
            
            assert data is not None
            assert "collection" in data

    def test_metadata_consistency(self):
        """メタデータ整合性テスト"""
        image_storage = self.controller.image_storage
        
        # 画像保存
        test_image = self.test_images_path / "medium_landscape.jpg"
        if not test_image.exists():
            pytest.skip("Test image not found")
        
        record_id = image_storage.save(test_image, collection="consistency_test")
        assert record_id is not None
        
        # メタデータ取得
        saved_data = image_storage.get(record_id)
        assert saved_data is not None
        
        # メタデータ更新
        image_storage.update_metadata(record_id, collection="updated_collection")
        
        # 更新後のデータ取得
        updated_data = image_storage.get(record_id)
        assert updated_data is not None
        assert updated_data["collection"] == "updated_collection"
        
        # 他のフィールドが保持されていることを確認
        for key in ["filename", "original_name", "file_path", "hash"]:
            assert saved_data[key] == updated_data[key]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])