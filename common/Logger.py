"""
项目日志模块（单例）

职责：统一记录测试用例的运行结果、步骤、断言等信息，
     负责「终端输出」+「按日期归档的文件输出」两路。

与 pytest 的集成：
- 通过 `propagate = False` 切断日志向 root logger 的传播，
  避免与 pytest 的 log_cli / log_file 重复输出。
- 因此 pytest.ini 中已关闭 log_cli 与 log_file，
  日志输出完全由本模块接管。
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

# 项目根目录（本文件位于 common/ 下）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOGGER_NAME = "acc_test"


class Logger:
    """日志单例封装，提供统一格式的终端与文件输出。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, name: str = LOGGER_NAME, level: int = logging.DEBUG):
        if self._initialized:
            return

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 关键：切断向 root 的传播，避免 pytest 重复输出
        self.logger.propagate = False
        # 清空已有 handler，防止重复初始化时叠加
        self.logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # 终端输出：INFO 及以上
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件输出：DEBUG 及以上，按日期归档
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / f"acc_miniapp_test_{datetime.now():%Y-%m-%d}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self._initialized = True

    # ---- 便捷方法（统一缩进，透传参数） ----
    def debug(self, message, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.exception(message, *args, **kwargs)

    def section(self, title: str):
        """输出醒目的分节标题，便于在日志中定位。"""
        sep = "=" * 50
        self.logger.info(sep)
        self.logger.info(title.center(50))
        self.logger.info(sep)


# 导出全局单例
logger = Logger()