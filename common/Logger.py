import logging
import sys
from pathlib import Path
from datetime import datetime

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialied = False
        return cls._instance
    
    def __init__(self):
        if self._initialied:
            return
        
        self.logger = logging.getLogger("acc_test")
        self.logger.setLevel(logging.DEBUG)

        #清空已有handlers防止重复
        self.logger.handlers.clear()

        #格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        #控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        #文件输出
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f'acc_miniapp_test_{today}.log'

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self._initialized = True

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, msg):
        self.logger.error(msg)
    
    def debug(self, msg):
        self.logger.debug(msg)
    
    def exception(self, msg):
        self.logger.exception(msg)

    def section(self, title):
        sep = '=' * 50
        self.info(sep)
        self.info(title.center(40))
        self.info(sep)
       
# 直接导出一个全局实例，不用管任何参数
log = Logger()