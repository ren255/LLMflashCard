# utils/__init__.py
"""
utils パッケージの初期化ファイル

Logger機能を簡単にインポートできるようにするため、
便利なエイリアスとラッパー関数を提供します。

使用例:
    from utils import log
    log.info("メッセージ")
    
    from utils import LogLevel, set_global_log_level
    set_global_log_level(LogLevel.DEBUG)
    
    from utils import get_log_stats
    stats = get_log_stats()
"""

from .Logger import (
    get_logger,
    set_global_log_level,
    get_log_stats,
    setup_dev_logging,
    setup_prod_logging,
    LogLevel,
    LoggerManager
)

logger = get_logger("utils.default")
log = logger

# パッケージの公開API
__all__ = [
    'logger',
    'log',
    'get_logger',
    'set_global_log_level',
    'get_log_stats',
    'setup_dev_logging',
    'setup_prod_logging',
    'LogLevel',
    'LoggerManager'
]

# バージョン情報
__version__ = "1.0.0"
__author__ = "ren toda"