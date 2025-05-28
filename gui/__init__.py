"""
GUI パッケージ

LLM FlashCardのグラフィカルユーザーインターフェース関連の
すべてのコンポーネントを含みます。

このパッケージはMVCアーキテクチャに基づいて構成されています：
- controllers/: コントローラー層（ビジネスロジックとUI間の仲介）
- views/: ビュー層（メインウィンドウ）
- components/: UIコンポーネント層（再利用可能なUI要素）
- styles/: スタイル定義（テーマ、色など）
- utils/: GUI関連のユーティリティ
"""

from utils import log

from .views.main_window import MainWindow
from .main import GUIApplication
from .controllers import MainController

# バージョン情報
__version__ = "1.0.0"
__author__ = "LLM FlashCard Team"

# パッケージレベルでの初期化
log.info("GUIパッケージが初期化されました")

# 主要なクラスのエクスポート（必要に応じて追加）
__all__ = [
    "MainWindow",
    "MainController",
    "GUIApplication"
]

# 遅延インポート（循環インポートを避けるため）
def get_main_window():
    """メインウィンドウクラスを取得"""
    from gui.views.main_window import MainWindow
    return MainWindow

def get_main_controller():
    """メインコントローラークラスを取得"""
    from gui.controllers.main_controller import MainController
    return MainController

def get_gui_application():
    """GUIアプリケーションクラスを取得"""
    from gui.main import GUIApplication
    return GUIApplication