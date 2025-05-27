
from pathlib import Path

from storage import StorageController
from utils import LogLevel, set_global_log_level, log
set_global_log_level(LogLevel.DEBUG)

log.debug("debug: main.pyの実行開始")

# ===========================================
# main.py での使用例
# ===========================================

def main_example():
    """main.pyでの使用例"""
    
    # StorageController初期化（自動でディレクトリ・DB作成）
    storage_controller = StorageController("./resources")
    
    # パス情報確認
    paths = storage_controller.get_paths_info()
    log.info("パス設定:")
    for key, path in paths.items():
        log.info(f"  {key}: {path}")
    
    # 画像ストレージ使用
    image_storage = storage_controller.image_storage
    
    # フラッシュカードストレージ使用  
    flashcard_storage = storage_controller.flashcard_storage
    
    # 任意のストレージ取得も可能
    # some_storage = storage_controller.get_storage("image")
    
    # 統計情報表示
    stats = storage_controller.get_storage_stats()
    log.info(f"  統計情報:")
    log.info(f"  画像ファイル数: {stats['image']['total_files']}")
    log.info(f"  フラッシュカード数: {stats['flashcard']['total_files']}")
    log.info(f"  総ファイル数: {stats['total_files']}")
    
    log.info("------------------------------------------------------------------------")
    
    # 画像ファイルの保存例
    
    sorce_image_path = "C:\\Users\\renpe\\MyDocuments\\screenshot\\スクリーンショット 2025-05-26 221300.png"
    sorce_image_path = Path(sorce_image_path)
    
    saved_image_path = image_storage.save_file(sorce_image_path)
    if saved_image_path:
        log.info(f"画像ファイル保存成功: {saved_image_path}")
    else:
        log.error("画像ファイル保存失敗")
    
    # クリーンアップ
    storage_controller.cleanup()


if __name__ == "__main__":
    main_example()