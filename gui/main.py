"""
GUIアプリケーションメインエントリーポイント

LLM FlashCardのGUIアプリケーションを起動します。
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils import log
from gui.views.main_window import MainWindow
from gui.controllers.main_controller import MainController


class GUIApplication:
    """GUIアプリケーションクラス"""
    
    def __init__(self):
        """アプリケーションの初期化"""
        self.main_window: MainWindow | None = None
        self.main_controller: MainController | None = None
        
        log.info("GUIアプリケーションを初期化中...")
    
    def initialize(self) -> None:
        """アプリケーションの初期化処理"""
        try:
            # メインコントローラーの作成
            self.main_controller = MainController()
            self.main_controller.initialize()
            
            # メインウィンドウの作成
            self.main_window = MainWindow()
            
            # コントローラーとビューの関連付け
            self.main_controller.set_view(self.main_window)
            self.main_window.set_controller(self.main_controller)
            
            log.info("GUIアプリケーションの初期化完了")
            
        except Exception as e:
            log.error(f"GUIアプリケーションの初期化に失敗: {e}")
            raise
    
    def run(self) -> None:
        """アプリケーションの実行"""
        try:
            if not self.main_window:
                raise RuntimeError("メインウィンドウが初期化されていません")
            
            log.info("GUIアプリケーションを開始します")
            
            # メインループの開始
            self.main_window.mainloop()
            
        except Exception as e:
            log.error(f"GUIアプリケーションの実行中にエラー: {e}")
            raise
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        log.info("GUIアプリケーションのクリーンアップ中...")
        
        if self.main_controller:
            try:
                self.main_controller.cleanup()
            except Exception as e:
                log.error(f"メインコントローラーのクリーンアップエラー: {e}")
        
        log.info("GUIアプリケーションのクリーンアップ完了")


def main() -> None:
    """メイン関数"""
    try:
        # アプリケーションの作成と実行
        app = GUIApplication()
        app.initialize()
        app.run()
        
    except KeyboardInterrupt:
        log.info("ユーザーによってアプリケーションが中断されました")
    except Exception as e:
        log.error(f"アプリケーションでエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()