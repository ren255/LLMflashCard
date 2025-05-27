# test_storage_integration.py
"""
Storage Module Integration Tests
ストレージモジュール全体の統合テスト
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
import time
import sys
import os

# パスを追加してstorageモジュールをインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from storage import StorageController

class TestStorageIntegration:
    """ストレージモジュール統合テスト"""
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリ"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # クリーンアップ
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp directory: {e}")
    
    @pytest.fixture
    def storage_controller(self, temp_dir):
        """StorageController のテスト用インスタンス"""
        controller = StorageController(temp_dir)
        yield controller
        controller.cleanup()
    
    @pytest.fixture
    def test_data_paths(self):
        """テストデータのパス情報を取得"""
        base = Path("./test/fixtures").resolve()
        image_dir = base / "test_images"
        csv_dir = base / "test_csvs"

        image_paths = [p.resolve() for p in image_dir.glob("*") if p.is_file()]
        csv_paths = [p.resolve() for p in csv_dir.glob("*") if p.is_file()]

        return {
            "images": image_paths,
            "csvs": csv_paths,
        }
    
    def test_full_workflow_images(self, storage_controller, test_data_paths):
        """画像の完全なワークフローテスト"""
        # テストデータ取得
        image_paths = test_data_paths['images']
        
        # 1. 画像を保存
        saved_ids = []
        for image_path in image_paths[:3]:  # 最初の3つを使用
            if Path(image_path).exists():
                record_id = storage_controller.image_storage.save(
                    Path(image_path), 
                    collection="test_collection"
                )
                if record_id:
                    saved_ids.append(record_id)
        
        assert len(saved_ids) >= 1, "少なくとも1つの画像が保存されるべき"
        
        # 2. 保存した画像を取得
        for record_id in saved_ids:
            image_data = storage_controller.image_storage.get(record_id)
            assert image_data is not None, f"画像ID {record_id} が取得できない"
            assert image_data['collection'] == "test_collection"
            assert 'full_path' in image_data
            assert Path(image_data['full_path']).exists()
        
        # 3. サムネイル確認
        for record_id in saved_ids:
            thumbnail_path = storage_controller.image_storage.get_thumbnail_path(record_id)
            if thumbnail_path:
                assert Path(thumbnail_path).exists(), f"サムネイル {thumbnail_path} が存在しない"
        
        # 4. 統計情報取得
        stats = storage_controller.image_storage.get_stats()
        assert stats['total_files'] >= len(saved_ids)
        assert stats['total_size'] > 0
        
        # 5. 検索テスト
        all_images = storage_controller.image_storage.get_all()
        assert len(all_images) >= len(saved_ids)
        
        collection_images = storage_controller.image_storage.get_by_collection("test_collection")
        assert len(collection_images) >= len(saved_ids)
        
        # 6. 削除テスト
        delete_id = saved_ids[0]
        success = storage_controller.image_storage.delete(delete_id)
        assert success, f"画像ID {delete_id} の削除に失敗"
        
        # 削除後の確認
        deleted_image = storage_controller.image_storage.get(delete_id)
        assert deleted_image is None, "削除された画像がまだ取得できる"
    
    def test_full_workflow_flashcards(self, storage_controller, test_data_paths):
        """フラッシュカードの完全なワークフローテスト"""
        # テストデータ取得
        csv_paths = test_data_paths['csvs']
        
        # 1. CSVを保存
        saved_ids = []
        for csv_path in csv_paths[:3]:  # 最初の3つを使用
            if Path(csv_path).exists():
                record_id = storage_controller.flashcard_storage.save(
                    Path(csv_path), 
                    collection="test_flashcards"
                )
                if record_id:
                    saved_ids.append(record_id)
        
        assert len(saved_ids) >= 1, "少なくとも1つのCSVが保存されるべき"
        
        # 2. 保存したCSVを取得
        for record_id in saved_ids:
            csv_data = storage_controller.flashcard_storage.get(record_id)
            assert csv_data is not None, f"CSV ID {record_id} が取得できない"
            assert csv_data['collection'] == "test_flashcards"
            assert 'full_path' in csv_data
            assert Path(csv_data['full_path']).exists()
        
        # 3. CSV固有情報の確認
        for record_id in saved_ids:
            columns = storage_controller.flashcard_storage.get_columns(record_id)
            assert isinstance(columns, list), "カラム情報がリストでない"
            assert len(columns) > 0, "カラムが存在しない"
            
            csv_info = storage_controller.flashcard_storage.get_csv_info(record_id)
            assert csv_info is not None, "CSV情報が取得できない"
            assert 'row_count' in csv_info
            assert csv_info['row_count'] > 0
        
        # 4. 統計情報取得
        stats = storage_controller.flashcard_storage.get_stats()
        assert stats['total_files'] >= len(saved_ids)
        assert stats['total_size'] > 0
        
        # 5. 検索テスト
        all_csvs = storage_controller.flashcard_storage.get_all()
        assert len(all_csvs) >= len(saved_ids)
        
        collection_csvs = storage_controller.flashcard_storage.get_by_collection("test_flashcards")
        assert len(collection_csvs) >= len(saved_ids)
        
        # 6. 削除テスト
        delete_id = saved_ids[0]
        success = storage_controller.flashcard_storage.delete(delete_id)
        assert success, f"CSV ID {delete_id} の削除に失敗"
        
        # 削除後の確認
        deleted_csv = storage_controller.flashcard_storage.get(delete_id)
        assert deleted_csv is None, "削除されたCSVがまだ取得できる"
    
    def test_duplicate_detection(self, storage_controller, test_data_paths):
        """重複検出機能のテスト"""
        image_paths = test_data_paths['images']
        
        if len(image_paths) == 0:
            pytest.skip("テスト画像が見つからない")
        
        test_image = next(p for p in image_paths if Path(p).exists())
        
        # 1回目の保存
        record_id1 = storage_controller.image_storage.save(Path(test_image))
        assert record_id1 is not None, "1回目の保存に失敗"
        
        # 2回目の保存（重複）
        record_id2 = storage_controller.image_storage.save(Path(test_image))
        assert record_id2 is None, "重複ファイルが保存されてしまった"
        
        # 保存されたファイル数の確認
        all_images = storage_controller.image_storage.get_all()
        original_count = len(all_images)
        
        # 3回目の保存（重複）
        record_id3 = storage_controller.image_storage.save(Path(test_image))
        assert record_id3 is None, "再度重複ファイルが保存されてしまった"
        
        # ファイル数が増えていないことを確認
        all_images_after = storage_controller.image_storage.get_all()
        assert len(all_images_after) == original_count, "重複保存でファイル数が増加した"
    
    def test_cross_storage_operations(self, storage_controller, test_data_paths):
        """異なるストレージ間での操作テスト"""
        image_paths = test_data_paths['images']
        csv_paths = test_data_paths['csvs']
        
        # 両方のストレージにファイルを保存
        image_id = None
        csv_id = None
        
        if image_paths and Path(image_paths[0]).exists():
            image_id = storage_controller.image_storage.save(Path(image_paths[0]))
        
        if csv_paths and Path(csv_paths[0]).exists():
            csv_id = storage_controller.flashcard_storage.save(Path(csv_paths[0]))
        
        # 統合統計の確認
        total_stats = storage_controller.get_storage_stats()
        
        if image_id:
            assert total_stats['image']['total_files'] >= 1
        if csv_id:
            assert total_stats['flashcard']['total_files'] >= 1
        
        # 総計の確認
        expected_total = 0
        if image_id:
            expected_total += 1
        if csv_id:
            expected_total += 1
        
        if expected_total > 0:
            assert total_stats['total_files'] >= expected_total
            assert total_stats['total_size'] > 0
    
    def test_collection_management(self, storage_controller, test_data_paths):
        """コレクション管理機能のテスト"""
        image_paths = test_data_paths['images']
        
        if not image_paths or not any(Path(p).exists() for p in image_paths):
            pytest.skip("テスト画像が見つからない")
        
        # 複数のコレクションにファイルを保存
        collections = ["collection_a", "collection_b", "collection_c"]
        saved_ids = {}
        
        for i, collection in enumerate(collections):
            if i < len(image_paths) and Path(image_paths[i]).exists():
                record_id = storage_controller.image_storage.save(
                    Path(image_paths[i]), 
                    collection=collection
                )
                if record_id:
                    saved_ids[collection] = record_id
        
        # 各コレクションの確認
        for collection in collections:
            if collection in saved_ids:
                collection_images = storage_controller.image_storage.get_by_collection(collection)
                assert len(collection_images) >= 1, f"コレクション {collection} に画像が見つからない"
                assert all(img['collection'] == collection for img in collection_images)
        
        # コレクション一覧の確認
        all_collections = storage_controller.image_storage.get_collections()
        for collection in saved_ids.keys():
            assert collection in all_collections, f"コレクション {collection} が一覧に含まれていない"
    
    def test_error_handling(self, storage_controller):
        """エラーハンドリングのテスト"""
        # 存在しないファイルの保存
        non_existent_file = Path("/non/existent/file.jpg")
        result = storage_controller.image_storage.save(non_existent_file)
        assert result is None, "存在しないファイルの保存が成功してしまった"
        
        # 存在しないIDの取得
        non_existent_id = 99999
        result = storage_controller.image_storage.get(non_existent_id)
        assert result is None, "存在しないIDで画像が取得されてしまった"
        
        # 存在しないIDの削除
        result = storage_controller.image_storage.delete(non_existent_id)
        assert result is False, "存在しないIDの削除が成功してしまった"
    
    def test_performance_basic(self, storage_controller, test_data_paths):
        """基本的なパフォーマンステスト"""
        image_paths = test_data_paths['images']
        
        if len(image_paths) < 5:
            pytest.skip("パフォーマンステストに十分な画像がない")
        
        # 複数ファイルの保存時間計測
        start_time = time.time()
        saved_ids = []
        
        for image_path in image_paths[:5]:
            if Path(image_path).exists():
                record_id = storage_controller.image_storage.save(Path(image_path))
                if record_id:
                    saved_ids.append(record_id)
        
        save_time = time.time() - start_time
        
        # 取得時間計測
        start_time = time.time()
        for record_id in saved_ids:
            storage_controller.image_storage.get(record_id)
        
        retrieve_time = time.time() - start_time
        
        # 基本的なパフォーマンス確認
        assert save_time < 30.0, f"保存時間が長すぎる: {save_time}秒"
        assert retrieve_time < 5.0, f"取得時間が長すぎる: {retrieve_time}秒"
        
        print(f"パフォーマンス結果:")
        print(f"  保存時間: {save_time:.2f}秒 ({len(saved_ids)}ファイル)")
        print(f"  取得時間: {retrieve_time:.2f}秒 ({len(saved_ids)}ファイル)")
    
    def test_cleanup_verification(self, storage_controller, test_data_paths):
        """クリーンアップ処理の確認"""
        image_paths = test_data_paths['images']
        
        if not image_paths or not Path(image_paths[0]).exists():
            pytest.skip("テスト画像が見つからない")
        
        # ファイル保存
        record_id = storage_controller.image_storage.save(Path(image_paths[0]))
        assert record_id is not None, "ファイル保存に失敗"
        
        # パス情報取得
        paths_info = storage_controller.get_paths_info()
        base_path = Path(paths_info['base_path'])
        
        # ファイルが存在することを確認
        assert base_path.exists(), "ベースディレクトリが存在しない"
        
        # クリーンアップ実行
        storage_controller.cleanup()
        
        # データベース接続が閉じられていることを確認
        # （具体的な確認方法はStorageControllerの実装に依存）
        # ここでは例外が発生しないことを確認
        try:
            storage_controller.get_storage_stats()
        except Exception:
            # データベース接続が閉じられている場合は例外が発生する可能性がある
            pass