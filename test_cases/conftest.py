import pytest
from selenium.webdriver.support.ui import WebDriverWait
from common.Logger import logger
from common.driver_factory import create_driver
from common.adb_screen_record import ScreenRecorder





@pytest.fixture(autouse=True)
def log_test_module(request):
    """在每个测试模块开始时记录日志"""
    module_name = request.node.fspath.purebasename #文件名不含拓展名
    test_function_name = request.node.name #每个测试函数名称
    logger.info(f"=== 开始执行测试模块: {module_name} / 测试函数: {test_function_name} ===")
    yield
    logger.info(f"=== 测试模块执行完毕: {module_name} / 测试函数: {test_function_name}===")

@pytest.fixture
def app_driver():
    """按需创建并回收 driver。"""
    drivers = []

    def _create(app_name: str):
        driver = create_driver(app_name)
        drivers.append(driver)
        return driver

    yield _create

    for driver in drivers:
        driver.quit()


@pytest.fixture
def app_wait():
    """基于 driver 创建 WebDriverWait。"""
    def _create(driver, timeout=10):
        return WebDriverWait(driver, timeout)
    return _create

@pytest.fixture
def screen_recording(request):
    """录屏 fixture：yield 录制器对象，用例结束后自动保存视频。"""
    recorder = ScreenRecorder(name=request.node.name)
    recorder.start()
    yield recorder
    recorder.stop()