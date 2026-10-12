from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from common.Logger import logger
from common.screenshot import take_screenshot
from common.app_config_load import get_app_config
from common.table_record import TableRecord
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
import time
import pytest

APP_NAME = "bilibili"
#logger = logging.getLogger("appium_calculator_test")
@pytest.fixture
def app_context():
    config = get_app_config(APP_NAME)
    return APP_NAME,config

@pytest.fixture
def setup_driver(app_context):
    _, config = app_context
    options = UiAutomator2Options().load_capabilities(config["capabilities"])
    driver = webdriver.Remote("http://localhost:4723", options=options)
    yield driver
    driver.quit()


@pytest.fixture
def table_record(request, app_context):
    """为本用例收集表格字段，结束时写入一份 JSON 记录。"""
    _, config = app_context
    app_types = {"video": "视频类", "music": "音乐类", "shopping": "购物类"}
    record = TableRecord(
        test_name=request.node.nodeid,
        app_type=app_types.get(config.get("type"), config.get("type", "")),
        app_name="B站",
    )

    def save_record():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_test_name = request.node.name.replace("/", "_").replace(":", "_")
        output_path = Path(__file__).resolve().parent.parent / "test-results" / "table_records" / f"{safe_test_name}_{timestamp}.json"
        saved_path = record.write_json(output_path)
        logger.info(f"表格字段记录已输出: {saved_path}")

    request.addfinalizer(save_record)
    return record

# @pytest.fixture
# def setup_driver():
#     options = UiAutomator2Options().load_capabilities({
#         "platformName": "Android",
#         "platformVersion": "12",
#         "deviceName": "emulator-5556",
#         "automationName": "UiAutomator2",
#         "appPackage": "tv.danmaku.bili",
#         "appActivity": "tv.danmaku.bili.MainActivityV2",
#         "noReset": True #不重置应用状态
#     })
#     driver = webdriver.Remote("http://localhost:4723", options=options)
#     yield driver
#     driver.quit()
    #return driver

def _visible_text(driver):
    """提取当前页面可见的 text/content-desc，作为字段录入证据。"""
    try:
        root = ET.fromstring(driver.page_source)
    except (ET.ParseError, TypeError):
        return []
    values = []
    for element in root.iter():
        for attribute in ("text", "content-desc"):
            value = element.attrib.get(attribute, "").strip()
            if value and value not in values:
                values.append(value)
    return values


def capture_operator_tab_switch(driver, wait, operator_rows, settle_time=2):
    """
    捕获运营商切换页面的截图。
    :param driver: Appium WebDriver 实例
    :param wait: WebDriverWait 实例
    :param settle_time: 截图前等待的时间（秒），默认 2,要等待页面渲染
    :return: 截图文件路径
    """
    operators = ["移动", "电信","联通"]
    captured = 0

    for op in operators:
        row = operator_rows[op]
        try:
            # 1. 点击运营商按钮
            tab = wait.until(EC.presence_of_element_located(
                (AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().text("{op}").clickable(true)')
            ))
            tab.click()
            logger.info(f"已点击运营商tab: {op},下方页面切换")
            screenshot_path = take_screenshot(driver, f"运营商_{op}", settle_time=settle_time)
            row.add_evidence(
                step=f"切换至{op}页面",
                screenshot=screenshot_path,
                visible_text=_visible_text(driver),
            )
            captured += 1
        except Exception as e:
            row.add_evidence(step=f"切换至{op}页面失败: {e}")
            logger.error(f"点击运营商tab: {op}失败，引发原因: {e}")
    logger.info(f"共捕获 {captured} 张运营商切换页面截图")
    return captured  

def test_bilibili_free_traffic(table_record, setup_driver):
    logger.info("开始B站免流服务订购页面进入测试")
    
    time.sleep(2)  # 等待应用启动
    driver = setup_driver
    wait = WebDriverWait(driver, 10)


    #1.寻找底部【我的】按钮
    my_tab = wait.until(EC.presence_of_element_located(
        (AppiumBy.ACCESSIBILITY_ID, "我的,5之5,标签")
    ))
    my_tab.click()
    logger.info("已进入「我的」页面")
    take_screenshot(driver, "我的页面")

    # 2. 点击「免流量服务」
    free_btn = wait.until(EC.presence_of_element_located(
        (AppiumBy.ACCESSIBILITY_ID, "免流量服务")
    ))
    free_btn.click()
    logger.info("已点击「免流量服务」")

    # 3. 等待免流量页面加载（X5 内核，内容以 android.view.View 暴露，无需切 WebView）
    #time.sleep(3)  # 先给 WebView 一点加载时间
    take_screenshot(driver, "免流量服务", settle_time=3)  # 截图前等待 3 秒，确保页面加载完成
    # 4. 在原生上下文中定位免流量页面元素
    #    建议先看 Inspector 里该元素的 text / content-desc，用文本定位最稳
    h5_element = wait.until(EC.presence_of_element_located(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("流量")')
    ))
    logger.info("免流量页面元素已找到")
    entry_screenshot = take_screenshot(driver, "运营商推广页面")
    assert h5_element is not None

    # 该用例确认了进入页面的路径和入口文案；其他页面评估字段留待后续用例采集。
    operator_rows = {}
    for operator in ("移动", "电信", "联通"):
        row = table_record.new_row(operator)
        row.set("订购入口设计.入口位置", "我的-免流量服务")
        row.set("订购入口设计.入口文案", "免流量服务")
        row.add_evidence(
            step="进入免流量服务页面",
            screenshot=entry_screenshot,
            visible_text=_visible_text(driver),
        )
        operator_rows[operator] = row

    #4.点击运营商tab切换，捕获截图
    captured_count = capture_operator_tab_switch(driver, wait, operator_rows, settle_time=2)
    assert captured_count == 3, f"预期捕获3张运营商切换页面截图，实际捕获 {captured_count} 张"

