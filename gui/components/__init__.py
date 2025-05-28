"""
Components パッケージ

再利用可能なUIコンポーネントを定義します。
MVCアーキテクチャのView層の一部として、
共通のUI要素を提供します。
"""

from utils import log

from .common.base_window import BaseWindow, BaseMainWindow
from .common.custom_widgets import (
    StatusBar,
    SearchWidget,
    ProgressDialog,
    ImagePreviewWidget,
    FlashcardPreviewWidget,
)

log.info("Components パッケージが初期化されました")

# エクスポート対象
__all__ = [
    # Common components
    "BaseWindow",
    "BaseMainWindow", 
    "StatusBar",
    "SearchWidget",
    "ProgressDialog",
    "ImagePreviewWidget",
    "FlashcardPreviewWidget",
]