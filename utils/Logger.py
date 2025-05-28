# utils/logger.py
"""
LLMflashCard プロジェクト用ロガーシステム

このモジュールは、プロジェクト全体で使用する統一されたロギング機能を提供します。
各モジュール用のロガーを簡単に作成でき、ファイル出力とコンソール出力の両方をサポートします。
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any
import sys
from datetime import datetime
import inspect
import time

class ColorLevelFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[41m", # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        levelname = record.levelname
        color = self.COLORS.get(levelname, "")
        record.levelname = f"{color}{levelname}{self.RESET}"
        return super().format(record)

class logFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        t = time.strftime("%H:%M:%S", ct)
        ms = int(record.msecs)
        return f"{t}:{ms:03d}"
    
    def format(self, record):
        # funcName:lineno を左詰め20桁
        func_line = f"{record.funcName}:{record.lineno}"
        func_line = f"{func_line:<20}"
        record.func_line = func_line

        # levelname を左詰め8桁
        level = f"[{record.levelname}]"
        record.level = f"{level:<10}"

        return super().format(record)

class LoggerManager:
    """ロガー管理クラス - プロジェクト全体のロギングを統括"""
    
    _instance = None
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            LoggerManager._initialized = True
    
    def _setup_logging(self):
        """ロギングシステムの初期設定"""
        # ログディレクトリの作成
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self.formatter = logFormatter(
            '%(asctime)s : %(level)s %(func_line)s : %(message)s'
        )
        
        self.console_formatter = ColorLevelFormatter(
            '[%(levelname)s] %(message)s'
        )
    
    
    def get_logger(self, name: str, level: int = logging.INFO, 
                   file_output: bool = True, console_output: bool = True) -> logging.Logger:
        """
        指定された名前のロガーを取得または作成
        
        Args:
            name: ロガー名（通常は__name__を使用）
            level: ログレベル
            file_output: ファイル出力の有効/無効
            console_output: コンソール出力の有効/無効
            
        Returns:
            設定済みのロガーインスタンス
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 既存のハンドラーをクリア（重複防止）
        logger.handlers.clear()
        
        # ファイルハンドラーの追加
        if file_output:
            self._add_file_handler(logger, name)
        
        # コンソールハンドラーの追加
        if console_output:
            self._add_console_handler(logger)
        
        # プロパゲーションを無効化（重複ログ防止）
        logger.propagate = False
        
        self._loggers[name] = logger
        return logger
    
    def _add_file_handler(self, logger: logging.Logger, name: str):
        """ファイルハンドラーを追加"""
        # モジュール名からファイル名を生成
        safe_name = name.replace('.', '_').replace('/', '_')
        log_file = self.log_dir / f"{safe_name}.log"
        
        # RotatingFileHandlerで自動ローテーション
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(self.formatter)
        logger.addHandler(file_handler)
    
    def _add_console_handler(self, logger: logging.Logger):
        """コンソールハンドラーを追加"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.console_formatter)
        logger.addHandler(console_handler)
    
    def set_global_level(self, level: int):
        """全ロガーのレベルを一括変更"""
        for logger in self._loggers.values():
            logger.setLevel(level)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """ログ統計情報を取得
        total_loggers
        logger_names
        log_directory
        log_files
        """
        stats = {
            'total_loggers': len(self._loggers),
            'logger_names': list(self._loggers.keys()),
            'log_directory': str(self.log_dir),
            'log_files': []
        }
        
        # ログファイル一覧
        if self.log_dir.exists():
            for log_file in self.log_dir.glob("*.log*"):
                stats['log_files'].append({
                    'name': log_file.name,
                    'size': log_file.stat().st_size,
                    'modified': datetime.fromtimestamp(log_file.stat().st_mtime)
                })
        
        return stats


# グローバルインスタンス
_logger_manager = LoggerManager()


def get_logger(name: str | None = None, level: int = logging.INFO, 
               file_output: bool = True, console_output: bool = True) -> logging.Logger:
    """
    ロガーを取得する便利関数
    
    Usage:
        # モジュール内で使用
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        # カスタム設定
        logger = get_logger("custom_logger", level=logging.DEBUG, console_output=False)
    
    Args:
        name: ロガー名（Noneの場合は呼び出し元モジュール名を自動取得）
        level: ログレベル
        file_output: ファイル出力の有効/無効
        console_output: コンソール出力の有効/無効
        
    Returns:
        設定済みのロガーインスタンス
    """
    # nameがNoneの場合は呼び出し元のモジュール名を自動取得
    resolved_name: str
    if name is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            resolved_name = frame.f_back.f_globals.get('__name__', 'unknown')
        else:
            resolved_name = 'unknown'
    else:
        resolved_name = name
    
    return _logger_manager.get_logger(resolved_name, level, file_output, console_output)


def set_global_log_level(level: int):
    """全ロガーのレベルを一括変更する便利関数"""
    _logger_manager.set_global_level(level)


def get_log_stats():
    """ログ統計情報を取得する便利関数"""
    return _logger_manager.get_log_stats()


# 開発用のクイック設定関数
def setup_dev_logging():
    """開発環境用のロギング設定"""
    set_global_log_level(logging.DEBUG)
    
    # 開発用ルートロガー
    root_logger = get_logger("dev", level=logging.DEBUG)
    root_logger.info("Development logging initialized")
    return root_logger


def setup_prod_logging():
    """本番環境用のロギング設定"""
    set_global_log_level(logging.WARNING)
    
    # 本番用ルートロガー
    root_logger = get_logger("prod", level=logging.WARNING, console_output=False)
    root_logger.info("Production logging initialized")
    return root_logger



# ログレベル定数（便利用）
class LogLevel:
    """
    DEBUG
    INFO
    WARNING
    ERROR
    CRITICAL
    """
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


if __name__ == "__main__":
    # テスト用コード
    print("Logger system test...")
    
    # 基本的な使用例
    logger1 = get_logger("test.module1")
    logger2 = get_logger("test.module2", level=LogLevel.DEBUG)
    
    logger1.info("This is an info message from module1")
    logger1.warning("This is a warning from module1")
    logger1.error("This is an error from module1")
    
    logger1.critical("This is a critical message from module1")
    logger1.debug("This is a debug message from module1")
    
    logger2.debug("This is a debug message from module2")
    logger2.info("This is an info message from module2")
    
    # 統計情報の表示
    stats = get_log_stats()
    print(f"\nLog Statistics: {stats}")
    
    print("Logger system test completed!")