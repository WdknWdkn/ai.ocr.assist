import os
import logging
from logging.handlers import RotatingFileHandler
import sys

# ログディレクトリの確認と作成
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# ログファイルのパス
LOG_FILE = os.path.join(LOG_DIR, 'invoice_parser.log')

# ロガーの設定
def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # ハンドラが既に追加されている場合は追加しない
    if logger.handlers:
        return logger
    
    # ログフォーマットの設定
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # ファイルハンドラの設定（ローテーション付き）
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # コンソールハンドラの設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    # ハンドラをロガーに追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
