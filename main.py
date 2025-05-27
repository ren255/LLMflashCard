
from storage import StorageController

# ===========================================
# main.py での使用例
# ===========================================

def main_example():
    """main.pyでの使用例"""
    
    # StorageController初期化（自動でディレクトリ・DB作成）
    storage_controller = StorageController("./resources")
    
    # パス情報確認
    paths = storage_controller.get_paths_info()
    print("パス設定:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    
    # 画像ストレージ使用
    image_storage = storage_controller.image_storage
    
    # フラッシュカードストレージ使用  
    flashcard_storage = storage_controller.flashcard_storage
    
    # 任意のストレージ取得も可能
    # some_storage = storage_controller.get_storage("image")
    
    # 統計情報表示
    stats = storage_controller.get_storage_stats()
    print(f"\n統計情報:")
    print(f"  画像ファイル数: {stats['image']['total_files']}")
    print(f"  フラッシュカード数: {stats['flashcard']['total_files']}")
    print(f"  総ファイル数: {stats['total_files']}")
    
    # クリーンアップ
    storage_controller.cleanup()


if __name__ == "__main__":
    main_example()