from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from common.Logger import logger
from common.screenshot import take_screenshot
from common.app_config_load import get_app_config
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pytest

APP_NAME = "kugoumusic"
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

def test_kugou_mobile_topup_page(setup_driver):
    logger.info("开始酷狗音乐充值页面进入测试")
    
    time.sleep(2)  # 等待应用启动
    driver = setup_driver
    wait = WebDriverWait(driver, 10)

    # 1. 点击「右上角“更多”按钮」,弹出侧边栏
    more_btn = wait.until(EC.presence_of_element_located(
                (AppiumBy.ACCESSIBILITY_ID, "侧边栏")
            ))
    more_btn.click()
    logger.info("已点击「更多」按钮")
    take_screenshot(driver, "酷狗音乐侧边栏")

    # 2. 在侧边栏中纵向滚动到「免流量听歌」并点击，默认推广页面是移动
    free_listen_btn = wait.until(EC.presence_of_element_located(
        (AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiScrollable(new UiSelector().scrollable(true))'
         '.scrollIntoView(new UiSelector().description("听歌免流量按钮"))')
    ))
    free_listen_btn.click()
    logger.info("已点击「听歌免流量按钮」")
    take_screenshot(driver, "运营商推广-默认移动", settle_time=2)

    for i in range(1,5):
        # 顶部滑动页面截图
        ad_slide_view = wait.until(EC.presence_of_element_located(
        (AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.view.View").instance(5)')
        ))
        logger.info(f"已定位到投放滑动页,第 {i}次滑动前")

        driver.execute_script("mobile: swipeGesture", {
        "elementId": ad_slide_view.id,
        "direction": "left",   # left: 下一页 / right: 上一页
        "percent": 0.8,
        "speed": 300,
        })
        time.sleep(1)
        take_screenshot(driver, f"投放滑动页_第{i+1}页", settle_time=0.5)
        logger.info(f"已完成第{i}次滑动操作并截图")

    # 3. 定位到 text("联通") 元素（clickable=false，但真机点击此处可切换）
    mobile_tab = wait.until(EC.presence_of_element_located(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("联通")')
    ))

    # 3.1用 clickGesture 点击元素中心坐标（等价于真实手指点击）
    driver.execute_script("mobile: clickGesture", {
        "elementId": mobile_tab.id,
    })
    logger.info("已点击「联通」tab")
    take_screenshot(driver, "运营商推广-联通", settle_time=2)

    # 4. 定位到 text("电信") 元素（clickable=false，但真机点击此处可切换）
    mobile_tab = wait.until(EC.presence_of_element_located(
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("电信")')
        ))
    
    
    driver.execute_script("mobile: clickGesture", {
            "elementId": mobile_tab.id,
        })
    logger.info("已点击「电信」tab")
    take_screenshot(driver, "运营商推广-电信", settle_time=2)
    