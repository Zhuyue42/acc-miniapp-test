from appium.webdriver.common.appiumby import AppiumBy
from common.Logger import logger
from common.flows.video_flow import VideoFlow
import time
import pytest

APP_NAME = "bilibili"

def test_bilibili_free_traffic(app_driver, app_wait):
    logger.info("开始B站免流服务订购页面进入测试")

    driver = app_driver(APP_NAME)
    wait = app_wait(driver, 10)
    flow = VideoFlow(driver, wait)

    time.sleep(2)  # 等待应用启动
    


    #1.寻找底部【我的】按钮并进入
    flow.open_my_page((AppiumBy.ACCESSIBILITY_ID, "我的"), desc="我的页面")

    # 2. 点击「免流量服务」
    flow.open_free_traffic_service((AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().className("android.view.ViewGroup")'
         '.childSelector(new UiSelector().text("免流量服务"))'))

    # 3. 等待免流量页面加载（X5 内核，内容以 android.view.View 暴露，无需切 WebView）
    h5_element = flow.wait_h5_content(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("流量")'),
        desc="免流量页面元素"
    )
    assert h5_element is not None

    # 4. 切换运营商 tab
    operator_locators = {
        "移动": (AppiumBy.ANDROID_UIAUTOMATOR,
                 'new UiSelector().className("android.widget.ListView")'
                 '.childSelector(new UiSelector().text("移动"))'),
        "电信": (AppiumBy.ANDROID_UIAUTOMATOR,
                 'new UiSelector().className("android.widget.ListView")'
                 '.childSelector(new UiSelector().text("电信"))'),
        "联通": (AppiumBy.ANDROID_UIAUTOMATOR,
                 'new UiSelector().className("android.widget.ListView")'
                 '.childSelector(new UiSelector().text("联通"))'),
    }
    captured_count = flow.switch_operator_tabs(operator_locators)

    assert captured_count == 3, f"预期捕获3张运营商切换页面截图，实际捕获 {captured_count} 张"
