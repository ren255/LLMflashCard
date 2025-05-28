"""
GUIコントローラーパッケージ

MVCアーキテクチャのController層を提供します。
ビジネスロジックとUI間の仲介役を担います。
"""

from .main_controller import (
    MainController,
    BaseController
)

__all__ = [
    'MainController',
    'BaseController'
]