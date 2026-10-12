from appium.webdriver.common.appiumby import AppiumBy
from common.Logger import logger
from common.flows.video_flow import VideoFlow
from common.screenshot import take_screenshot
import time
import pytest

APP_NAME = "tencentqqlive"

def test_tencentqqlive_free_traffic(app_driver, app_wait):
    logger.info("开始腾讯视频免流服务订购页面进入测试")

    driver = app_driver(APP_NAME)
    wait = app_wait(driver, 10)
    flow = VideoFlow(driver, wait)

    time.sleep(2)  # 等待应用启动
    


    #1.寻找底部【我的】按钮并进入
    flow.open_my_page((AppiumBy.ACCESSIBILITY_ID, "个人中心"), desc="腾讯视频-个人中心")

    # 2. 点击「免流量服务」
    flow.open_free_traffic_service((AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().className("android.view.View")'
         '.childSelector(new UiSelector().text("免流量领会员'
         '"))'))

    # 3. 等待免流量页面加载（X5 内核，内容以 android.view.View 暴露，无需切 WebView）
    h5_element = flow.wait_h5_content(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("流量")'),
        desc="免流量页面元素"
    )
    assert h5_element is not None

    #页面需要先竖直滑动一下
     # 3.1 页面为整体封装，无可定位子元素，用坐标手势向上滑动一屏的 30%
    bounds_width = 1200
    bounds_height = 2315 
    start_y = int(bounds_height * 0.7)   # 起点：屏幕下方 70% 处
    end_y = int(bounds_height * 0.2)     # 终点：屏幕上滑到 20% 处

    driver.execute_script("mobile: swipeGesture", {
        "left": 0, "top": 0,
        "width": bounds_width, "height": bounds_height,
        "direction": "up",
        "percent": 0.75,
        "speed": 500,
    })
    time.sleep(1)  # 等待滑动动画结束、内容渲染
    logger.info("已向上滑动页面")
    take_screenshot(driver, "滑动后页面")

    # 验证 WebView 内核类型（调试时可用）
    # webview = driver.find_element(AppiumBy.CLASS_NAME, "android.webkit.WebView")
    # logger.info(f"WebView 实际类名: {webview.get_attribute('className')}")
    # 4. 切换运营商 tab（横条 bounds=[0,1524][1200,1664]，宽1200均分三段，纵坐标中点1594）
    tab_x = {"移动": 200, "联通": 600, "电信": 1000}  # 1200 宽的 1/6、3/6、5/6 处
    tab_y = 500                                      # (1524+1664)/2
    
    captured_count = 0
    for op, x in tab_x.items():
        driver.execute_script("mobile: clickGesture", {"x": x, "y": tab_y})
        logger.info(f"已点击「{op}」tab (坐标: {x}, {tab_y})")
        take_screenshot(driver, f"运营商推广-{op}", settle_time=2)
        captured_count += 1
    
    assert captured_count == 3, f"预期捕获3张运营商切换页面截图，实际捕获 {captured_count} 张"