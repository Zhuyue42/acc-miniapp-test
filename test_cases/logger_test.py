import logging
import pytest
import sys
from common.Logger import logger


class TestLoggingConfiguration:
    def test_logger_has_handlers(self):
        """验证日志单例已正确配置输出通道"""
        handlers = logger.logger.handlers
        handler_types = {type(h) for h in handlers}

        assert len(handlers) >= 2, "应至少有 console + file 两个 handler"
        assert logging.StreamHandler in handler_types, "缺少终端输出 handler"
        assert logging.FileHandler in handler_types, "缺少文件输出 handler"

    def test_logger_propagate_disabled(self):
        """验证已切断向 root 的传播，避免与 pytest 重复输出"""
        assert logger.logger.propagate is False, "应设置 propagate = False"

    def test_console_level_is_info(self):
        """验证终端只输出 INFO 及以上级别"""
        console = next(
            h for h in logger.logger.handlers if isinstance(h, logging.StreamHandler)
        )
        
        assert console.level == logging.INFO, "终端 handler 级别应为 INFO"

    def test_file_level_is_debug(self):
        """验证文件输出包含 DEBUG 级别"""
        file_handler = next(
            h for h in logger.logger.handlers if isinstance(h, logging.FileHandler)
        )
        assert file_handler.level == logging.DEBUG, "文件 handler 级别应为 DEBUG"

    def test_all_log_levels_output(self, capsys):
        console = next(
        h for h in logger.logger.handlers if isinstance(h, logging.StreamHandler)
    )
        console.stream = sys.stdout
        """验证各日志级别都能正常输出到终端（DEBUG 除外）"""
        logger.debug("这条 DEBUG 不会出现在终端")
        logger.info("你好世界 - INFO级别")
        logger.warning("测试步骤 - WARNING级别")
        logger.error("出错了 - ERROR级别")
        logger.critical("严重故障 - CRITICAL级别")

        captured = capsys.readouterr().out

        # DEBUG 因 console_handler 级别为 INFO，不应出现在终端
        assert "DEBUG" not in captured, "DEBUG 不应出现在终端"
        assert "INFO级别" in captured
        assert "WARNING级别" in captured
        assert "ERROR级别" in captured
        assert "CRITICAL级别" in captured