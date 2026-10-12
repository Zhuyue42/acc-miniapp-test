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

APP_NAME = "qqmusic"
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

def test_promotion_page(setup_driver):
    logger.info("开始QQ音乐运营商推广订购页面进入测试")
        
    time.sleep(2)  # 等待应用启动
    driver = setup_driver
    wait = WebDriverWait(driver, 10)

    #1.寻找底部【我的】按钮
    my_tab = wait.until(EC.presence_of_element_located(
            (AppiumBy.ACCESSIBILITY_ID, "我的")
        ))
    my_tab.click()
    logger.info("已进入「我的」页面")
    take_screenshot(driver, "我的页面")

    # 2. 点击「右上角“更多”按钮」
    more_btn = wait.until(EC.presence_of_element_located(
            (AppiumBy.ID, "com.tencent.qqmusic:id/hd6")
        ))
    more_btn.click()
    logger.info("已点击「更多」按钮")
    take_screenshot(driver, "更多页面")

    # 4. 点击移动送会员标签
    CMCC_flow_tab = wait.until(EC.presence_of_element_located(
                (AppiumBy.ACCESSIBILITY_ID, "移动用户免流送会员")
            ))
    CMCC_flow_tab.click()
    logger.info("已点击「移动用户免流送会员」")
    take_screenshot(driver, "移动用户推广页面", settle_time=2 )
    #返回上一页
    driver.back()

    # 5. 点击免流听歌送会员
    time.sleep(1) #等待页面返回成功
    free_flow_tab = wait.until(EC.presence_of_element_located(
                (AppiumBy.ACCESSIBILITY_ID, "免流量听歌送会员")
            ))
    free_flow_tab.click()
    logger.info("已点击「免流量听歌送会员」")
    
    take_screenshot(driver, "免流量听歌推广页面", settle_time=2)