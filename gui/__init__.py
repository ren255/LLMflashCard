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
from .controllers import MainController

# バージョン情報
__version__ = "1.0.0"
__author__ = "ren toda"

# パッケージレベルでの初期化
log.info("GUIパッケージが初期化されました")

__all__ = [
    "MainWindow",
    "MainController",
]
