from appium.webdriver.common.appiumby import AppiumBy
from common.Logger import logger
from common.flows.video_flow import VideoFlow
import time
import pytest

APP_NAME = "iqiyi"

def test_iqiyi_free_traffic(app_driver, app_wait):
    logger.info("开始爱奇艺免流服务订购页面进入测试")

    driver = app_driver(APP_NAME)
    wait = app_wait(driver, 10)
    flow = VideoFlow(driver, wait)

    time.sleep(2)  # 等待应用启动

    #1.寻找底部【我的】按钮并进入
    flow.open_my_page((AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().resourceId("com.qiyi.video:id/unused_res_a")'
         '.childSelector(new UiSelector().text("我的"))'), desc="我的页面")

    # 2. 如果弹出了登录弹窗，点击关闭
    #flow.close_login_popup_if_present((AppiumBy.ACCESSIBILITY_ID, "关闭"))
# 2. 点击「免流量服务」
    flow.open_free_traffic_service((AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().resourceId("com.qiyi.video:id/unused_res_a")'
         '.childSelector(new UiSelector().text("免流量服务"))'))
    
    # 3. 等待免流量页面加载（X5 内核，内容以 android.view.View 暴露，无需切 WebView）
    h5_element = flow.wait_h5_content(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("流量")'),
        desc="免流量页面元素"
    )
    assert h5_element is not None

    # 验证 WebView 内核类型（调试时可用）
    # webview = driver.find_element(AppiumBy.CLASS_NAME, "android.webkit.WebView")
    # logger.info(f"WebView 实际类名: {webview.get_attribute('className')}")
    # 输出包含 android.webkit.WebView

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