from appium.webdriver.common.appiumby import AppiumBy
from common.Logger import logger
from common.flows.shopping_flow import ShoppingFlow
from selenium.webdriver.support import expected_conditions as EC
import time
import pytest

APP_NAME = "taobao"

PHONE_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().className("android.widget.TextView")'
         '.textMatches("1\\d{2}\\s\\d{4}\\s\\d{4}")')

TEST_PHONE_BY_OPERATOR = {
    "移动": "15021294526",
    "联通": "18601724406",
    "电信": "18116073750",
}

def test_taobao_topup(app_driver, app_wait,screen_recording):
    logger.info("开始淘宝流量充值页面测试")

    driver = app_driver(APP_NAME)
    wait = app_wait(driver, 10)
    flow = ShoppingFlow(driver, wait)

    time.sleep(2)  # 等待应用启动

    

    # 1. 定位横向滚动容器
    flow.swipe_container(
        (AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().className("android.widget.HorizontalScrollView").instance(0)'),
        direction="left",
        desc="首页横向容器滑动到第二页",
        screenshot_name="滑动切换后_第二页",)
    logger.info("已定位到页面中部HorizontalScrollView 容器，可滑动。")

    
    # 2. 点击「充值中心」入口
    flow.open_entry(
        (AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().description("充值中心").clickable(true)'),
        entry_name="充值中心",
        screenshot_name="充值中心页面",
        settle_time=2,
    )
    logger.info("充值中心页面已截图。")

    # 3. 点击「充流量」tab
    flow.open_entry(
        (AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().resourceId("TabNavTest1").clickable(true)'),
        entry_name="充流量tab",
        screenshot_name="流量充值页面",
        settle_time=2,
    )

    # ===== 4. 验证默认回填 =====
    default_phone = flow.read_phone_number(PHONE_INPUT)
    assert default_phone, "流量充值页输入框未回填账号绑定号码"
    logger.info(f"流量充值页输入框已回填账号绑定号码: {default_phone}")
    flow.screenshot("流量充值页面-默认填充绑定号码", settle_time=2)

#TODO 2. 完成根据输入号码运营商不同页面元素进行定位

    PHONE_EDIT = (AppiumBy.ANDROID_UIAUTOMATOR,
              'new UiSelector().className("android.widget.EditText")')

    for operator, phone in TEST_PHONE_BY_OPERATOR.items():
        flow.fill_phone_number(PHONE_EDIT, phone, desc=f"{operator}号码输入框")
        flow.screenshot(f"流量充值页面-{operator}", settle_time=2)

        # 验证：页面出现对应运营商标识（TODO 2 的落点）
        flow.wait_for_element(
            (AppiumBy.ANDROID_UIAUTOMATOR,
             f'new UiSelector().textContains("{operator}")'),
            desc=f"{operator}标识",
        )
        logger.info(f"输入 {phone} 后页面正确识别为 {operator}")




