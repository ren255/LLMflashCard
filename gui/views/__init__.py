"""
Views パッケージ

メインウィンドウとアプリケーションの主要画面を定義します。
MVCアーキテクチャのView層を構成します。
"""

from .main_window import MainWindow

from utils import log

log.info("Views パッケージが初期化されました")

# エクスポート対象
__all__ = [
    'MainWindow'
]

# 遅延インポート（必要時にのみロード）
def get_main_window():
    """メインウィンドウクラスを取得"""
    from .main_window import MainWindow
    return MainWindow