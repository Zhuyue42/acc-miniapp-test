from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from common.Logger import logger
from common.screenshot import take_screenshot
from common.app_config_load import get_apps_by_type
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pytest

@pytest.fixture(params=get_apps_by_type("shopping").items())  # 类型名按你 YAML 实际调整
def app_context(request):
    app_name, config = request.param
    return app_name, config


@pytest.fixture
def setup_driver(app_context):
    _, config = app_context
    options = UiAutomator2Options().load_capabilities(config["capabilities"])
    driver = webdriver.Remote("http://localhost:4723", options=options)
    try:
        yield driver
    finally:
        driver.quit()

def fill_input(driver, wait, locator, text):
    """定位输入框并输入文本，先清空再输入，更稳。

    :param locator: (AppiumBy.XXX, "选择器")
    :param text: 要输入的文本
    """
    element = wait.until(EC.presence_of_element_located(locator))
    element.click()
    element.clear()  # 清空旧内容，避免 append 到已有文字后
    element.send_keys(text)
    logger.info(f"已输入: {text}")

def test_taobao_mobile_topup(setup_driver):
    logger.info("开始淘宝移动充值页面滑动切换测试")

    time.sleep(2)  # 等待应用启动
    driver = setup_driver
    wait = WebDriverWait(driver, 10)

    # 1. 定位横向滚动容器（UiAutomator + instance(0)，比深 XPath 稳）
    container = wait.until(EC.presence_of_element_located(
        (AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().className("android.widget.HorizontalScrollView").instance(0)')
    ))
    logger.info("已定位到 HorizontalScrollView 容器")

    # 2. 向左滑到第二页（下一页）
    driver.execute_script("mobile: swipeGesture", {
        "elementId": container.id,
        "direction": "left",
        "percent": 0.8,
        "speed": 300,
    })
    time.sleep(1)  # 等待滑动动画完成
    take_screenshot(driver, "滑动切换后_第二页")

    # 4. 点击移动送会员标签
    molbile_topup_icon = wait.until(EC.presence_of_element_located(
                    (AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().description("充值中心").clickable(true)')
                ))
    molbile_topup_icon.click()
    logger.info("已点击「充值中心」")
    take_screenshot(driver, "充值中心页面", settle_time=2 )

    # 3. 向右滑回第一页（上一页）
    # driver.execute_script("mobile: swipeGesture", {
    #     "elementId": container.id,
    #     "direction": "right",
    #     "percent": 0.8,
    #     "speed": 300,
    # })
    # time.sleep(1)
    # take_screenshot(driver, "滑动切换后_第一页")

    #点击充流量tab
    flow_topup_icon = wait.until(EC.presence_of_element_located(
                        (AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().resourceId("TabNavTest1").clickable(true)') #Find By	id：TabNavTest1
                    ))
    flow_topup_icon.click()
    logger.info("已点击「充流量」tab")
    take_screenshot(driver, "流量充值页面", settle_time=2 )

    fill_input(
    driver,
    wait,
    (AppiumBy.ANDROID_UIAUTOMATOR,
     'new UiSelector().className("android.widget.EditText")',
    ),
    "18601724406")
    logger.info("更换手机号为上海联通测试号码： 18601724406")
    take_screenshot(driver, "流量充值页面-上海联通测试号码", settle_time=2 )

    fill_input(
        driver,
        wait,
        (AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().className("android.widget.EditText")',
        ),
        "13301986958")
    logger.info("更换手机号为上海电信测试号码： 13301986958")#纯虚构手机号
    take_screenshot(driver, "流量充值页面-上海电信测试号码", settle_time=2 )