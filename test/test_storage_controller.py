"""
StorageController のテストケース
統合管理クラスの初期化、ストレージインスタンス管理、統計情報取得をテスト
"""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from storage.storage_controller import StorageController
from storage.image_managers import ImageStorage
from storage.flashcard_managers import FlashcardStorage


class TestStorageControllerInit:
    """StorageController初期化のテスト"""

    def test_init_creates_directory_structure(self, temp_dir):
        """ディレクトリ構造が正しく作成されることを確認"""
        controller = StorageController(str(temp_dir))
        
        # 基本ディレクトリの存在確認
        assert (temp_dir / "db").exists()
        assert (temp_dir / "image").exists()
        assert (temp_dir / "flashcard").exists()
        assert (temp_dir / "temp").exists()
        assert (temp_dir / "temp" / "image").exists()
        assert (temp_dir / "temp" / "flashcard").exists()
        assert (temp_dir / "thumbnails").exists()
        assert (temp_dir / "thumbnails" / "image").exists()
        assert (temp_dir / "thumbnails" / "flashcard").exists()
        
        controller.cleanup()

    def test_init_creates_databases(self, temp_dir):
        """データベースファイルが正しく作成されることを確認"""
        controller = StorageController(str(temp_dir))
        
        # データベースファイルの存在確認
        assert (temp_dir / "db" / "images.db").exists()
        assert (temp_dir / "db" / "flashcards.db").exists()
        
        # データベースの内容確認
        conn = sqlite3.connect(temp_dir / "db" / "images.db")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'")
        assert cursor.fetchone() is not None
        conn.close()
        
        conn = sqlite3.connect(temp_dir / "db" / "flashcards.db")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flashcards'")
        assert cursor.fetchone() is not None
        conn.close()
        
        controller.cleanup()

    def test_init_with_existing_directory(self, temp_dir):
        """既存ディレクトリでの初期化が正常に動作することを確認"""
        # 事前にディレクトリを作成
        (temp_dir / "image").mkdir(parents=True, exist_ok=True)
        (temp_dir / "db").mkdir(parents=True, exist_ok=True)
        
        controller = StorageController(str(temp_dir))
        assert controller.base_path == Path(temp_dir)
        controller.cleanup()

    def test_init_path_attributes(self, temp_dir):
        """パス属性が正しく設定されることを確認"""
        controller = StorageController(str(temp_dir))
        
        assert controller.base_path == Path(temp_dir)
        assert controller.db_dir == Path(temp_dir) / "db"
        assert "image" in controller.db_paths
        assert "flashcard" in controller.db_paths
        assert controller.db_paths["image"] == Path(temp_dir) / "db" / "images.db"
        assert controller.db_paths["flashcard"] == Path(temp_dir) / "db" / "flashcards.db"
        
        controller.cleanup()

    @patch('storage.storage_controller.Path.mkdir')
    def test_init_permission_error_handling(self, mock_mkdir, temp_dir):
        """権限エラー時の適切なハンドリング"""
        mock_mkdir.side_effect = PermissionError("Permission denied")
        
        with pytest.raises(PermissionError):
            StorageController(str(temp_dir))


class TestStorageControllerInstances:
    """ストレージインスタンス管理のテスト"""

    def test_lazy_initialization(self, temp_dir):
        """遅延初期化が正しく動作することを確認"""
        controller = StorageController(str(temp_dir))
        
        # 初期状態では None
        assert controller._storage_instances["image"] is None
        assert controller._storage_instances["flashcard"] is None
        
        # アクセス時に初期化される
        image_storage = controller.image_storage
        assert isinstance(image_storage, ImageStorage)
        assert controller._storage_instances["image"] is image_storage
        
        flashcard_storage = controller.flashcard_storage
        assert isinstance(flashcard_storage, FlashcardStorage)
        assert controller._storage_instances["flashcard"] is flashcard_storage
        
        controller.cleanup()

    def test_singleton_behavior(self, temp_dir):
        """同一インスタンスが返されることを確認"""
        controller = StorageController(str(temp_dir))
        
        storage1 = controller.image_storage
        storage2 = controller.image_storage
        assert storage1 is storage2
        
        storage3 = controller.flashcard_storage
        storage4 = controller.flashcard_storage
        assert storage3 is storage4
        
        controller.cleanup()

    def test_get_storage_valid_types(self, temp_dir):
        """get_storage()メソッドの正常動作"""
        controller = StorageController(str(temp_dir))
        
        image_storage = controller.get_storage("image")
        assert isinstance(image_storage, ImageStorage)
        
        flashcard_storage = controller.get_storage("flashcard")
        assert isinstance(flashcard_storage, FlashcardStorage)
        
        controller.cleanup()

    def test_get_storage_invalid_type(self, temp_dir):
        """無効なファイルタイプでのエラーハンドリング"""
        controller = StorageController(str(temp_dir))
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            controller.get_storage("invalid_type")
        
        controller.cleanup()

    def test_property_access(self, temp_dir):
        """プロパティアクセスの動作確認"""
        controller = StorageController(str(temp_dir))
        
        # image_storage プロパティ
        image_storage = controller.image_storage
        assert isinstance(image_storage, ImageStorage)
        
        # flashcard_storage プロパティ
        flashcard_storage = controller.flashcard_storage
        assert isinstance(flashcard_storage, FlashcardStorage)
        
        controller.cleanup()


class TestStorageControllerInfo:
    """情報取得メソッドのテスト"""

    def test_get_paths_info(self, temp_dir):
        """パス情報の取得"""
        controller = StorageController(str(temp_dir))
        paths_info = controller.get_paths_info()
        
        # 基本パス
        assert "base_path" in paths_info
        assert "db_dir" in paths_info
        assert "temp_dir" in paths_info
        assert "thumbnails_dir" in paths_info
        
        # ファイルタイプ別パス
        assert "image_db_path" in paths_info
        assert "image_storage_path" in paths_info
        assert "flashcard_db_path" in paths_info
        assert "flashcard_storage_path" in paths_info
        
        # パスの正確性
        assert str(temp_dir) in str(paths_info["base_path"])
        assert str(temp_dir / "db") in str(paths_info["db_dir"])
        
        controller.cleanup()

    def test_get_storage_stats_empty(self, temp_dir):
        """空のストレージでの統計情報取得"""
        controller = StorageController(str(temp_dir))
        stats = controller.get_storage_stats()
        
        assert "image" in stats
        assert "flashcard" in stats
        assert "total_files" in stats
        assert "total_size" in stats
        
        # 初期状態では0
        assert stats["total_files"] == 0
        assert stats["total_size"] == 0
        assert stats["image"]["total_files"] == 0
        assert stats["flashcard"]["total_files"] == 0
        
        controller.cleanup()

    def test_get_storage_stats_with_data(self, temp_dir, sample_image_file, sample_csv_file):
        """データがある状態での統計情報取得"""
        controller = StorageController(str(temp_dir))
        
        # データを追加
        image_id = controller.image_storage.save(sample_image_file, "test_collection")
        csv_id = controller.flashcard_storage.save(sample_csv_file, "test_collection")
        
        assert image_id is not None
        assert csv_id is not None
        
        stats = controller.get_storage_stats()
        
        # 統計が更新されている
        assert stats["total_files"] == 2
        assert stats["total_size"] > 0
        assert stats["image"]["total_files"] == 1
        assert stats["flashcard"]["total_files"] == 1
        
        controller.cleanup()


class TestStorageControllerCleanup:
    """クリーンアップ機能のテスト"""

    def test_cleanup_closes_connections(self, temp_dir):
        """クリーンアップでデータベース接続が閉じられることを確認"""
        controller = StorageController(str(temp_dir))
        
        # ストレージインスタンスを初期化
        _ = controller.image_storage
        _ = controller.flashcard_storage
        
        # クリーンアップ実行
        controller.cleanup()
        
        # 再度アクセス時に新しいインスタンスが作成される
        new_image_storage = controller.image_storage
        assert new_image_storage is not None

    def test_cleanup_multiple_calls(self, temp_dir):
        """複数回のクリーンアップ呼び出しでエラーが発生しないことを確認"""
        controller = StorageController(str(temp_dir))
        
        controller.cleanup()
        controller.cleanup()  # 2回目の呼び出し
        # エラーが発生しないことを確認

    @patch('storage.base_managers.BaseMetadataManager.close')
    def test_cleanup_calls_storage_cleanup(self, mock_close, temp_dir):
        """ストレージのクリーンアップが呼ばれることを確認"""
        controller = StorageController(str(temp_dir))
        
        # ストレージインスタンスを初期化
        _ = controller.image_storage
        _ = controller.flashcard_storage
        
        controller.cleanup()
        
        # 各ストレージのクリーンアップが呼ばれることを確認
        assert mock_close.call_count >= 2


class TestStorageControllerEdgeCases:
    """エッジケースのテスト"""

    def test_invalid_base_path(self):
        """無効なベースパスでの初期化"""
        with pytest.raises((OSError, PermissionError)):
            StorageController("/invalid/path/that/does/not/exist/and/cannot/be/created")

    def test_relative_path_handling(self, temp_dir):
        """相対パスでの初期化"""
        # 一時的に作業ディレクトリを変更
        original_cwd = Path.cwd()
        try:
            temp_dir.chmod(0o755)
            temp_dir.parent.as_posix()
            
            controller = StorageController(".")
            assert controller.base_path.is_absolute()
            controller.cleanup()
        finally:
            # 作業ディレクトリを元に戻す
            pass

    def test_unicode_path_handling(self, temp_dir):
        """Unicode文字を含むパスでの処理"""
        unicode_dir = temp_dir / "テスト_フォルダ"
        unicode_dir.mkdir(exist_ok=True)
        
        controller = StorageController(str(unicode_dir))
        assert controller.base_path == unicode_dir
        controller.cleanup()

    def test_concurrent_access_simulation(self, temp_dir):
        """同時アクセスのシミュレーション"""
        controller1 = StorageController(str(temp_dir))
        controller2 = StorageController(str(temp_dir))
        
        # 両方のcontrollerでストレージにアクセス
        storage1 = controller1.image_storage
        storage2 = controller2.image_storage
        
        assert storage1 is not None
        assert storage2 is not None
        
        controller1.cleanup()
        controller2.cleanup()


class TestStorageControllerIntegration:
    """統合テスト"""

    @pytest.mark.integration
    def test_full_workflow(self, temp_dir, sample_image_file, sample_csv_file):
        """完全なワークフローのテスト"""
        controller = StorageController(str(temp_dir))
        
        # 1. ファイル保存
        image_id = controller.image_storage.save(sample_image_file, "images")
        csv_id = controller.flashcard_storage.save(sample_csv_file, "flashcards")
        
        assert image_id is not None
        assert csv_id is not None
        
        # 2. データ取得
        image_data = controller.image_storage.get(image_id)
        csv_data = controller.flashcard_storage.get(csv_id)
        
        assert image_data is not None
        assert csv_data is not None
        assert image_data["collection"] == "images"
        assert csv_data["collection"] == "flashcards"
        
        # 3. 統計情報確認
        stats = controller.get_storage_stats()
        assert stats["total_files"] == 2
        assert stats["image"]["total_files"] == 1
        assert stats["flashcard"]["total_files"] == 1
        
        # 4. 削除
        assert controller.image_storage.delete(image_id)
        assert controller.flashcard_storage.delete(csv_id)
        
        # 5. 削除後の確認
        assert controller.image_storage.get(image_id) is None
        assert controller.flashcard_storage.get(csv_id) is None
        
        controller.cleanup()

    @pytest.mark.integration
    def test_error_recovery(self, temp_dir, corrupted_files):
        """エラーからの回復テスト"""
        controller = StorageController(str(temp_dir))
        
        # 破損ファイルでの保存試行
        image_result = controller.image_storage.save(corrupted_files["bad_image"], "test")
        csv_result = controller.flashcard_storage.save(corrupted_files["bad_csv"], "test")
        
        # エラーでもシステムが継続動作すること
        stats = controller.get_storage_stats()
        assert isinstance(stats, dict)
        
        controller.cleanup()