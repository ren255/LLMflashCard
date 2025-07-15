import logging
import sys
from pathlib import Path

def setup_logging():
    """
    アプリケーション全体で使用するlogging設定
    デフォルトのlogging設定のみを使用
    """
    # ログレベルの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # SQLAlchemyのlogging設定
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.ERROR)
    
    # アプリケーションのrootログ設定
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.INFO)
    
    return app_logger

# デフォルトのloggerを取得
def get_logger(name: str = 'app'):
    """
    指定された名前のloggerを取得
    """
    return logging.getLogger(name)