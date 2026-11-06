from appium.webdriver.common.appiumby import AppiumBy
from common.Logger import logger
from common.flows.music_flow import MusicFlow
import time
import pytest
from datetime import datetime
from pathlib import Path
from common.app_product_instruction import ProductInstructionFile

APP_NAME = "kugou_music"

@pytest.fixture
def product_instructions(request):
    """按 App 收集活动说明，用例结束（无论成败）写一份 JSON。"""
    file = ProductInstructionFile(app_name="酷狗音乐")
    yield file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(__file__).resolve().parent.parent / "test-results" / \
        "product_instructions" / f"{file.app_name}_{timestamp}.json"
    saved = file.write_json(out)
    logger.info(f"活动说明记录已输出: {saved}")

def test_kugou_music_free_traffic(app_driver, app_wait, product_instructions):
    logger.info("开始酷狗音乐免流服务订购页面进入测试")

    driver = app_driver(APP_NAME)
    wait = app_wait(driver, 10)
    flow = MusicFlow(driver, wait)

    time.sleep(2)  # 等待应用启动

    t0 = time.time()
    flow.open_my_page((AppiumBy.ACCESSIBILITY_ID, "我的"),desc="我的页面")
    logger.info(f"open_my_page 耗时 {time.time() - t0:.1f}s")
    
    flow.open_page_more((AppiumBy.ACCESSIBILITY_ID, "侧边栏"), desc="侧边栏")

    # 右侧侧边栏列表需上滑一屏才出现「免流量听歌」入口
    flow.swipe_screen(direction="up", distance_ratio=0.4,
                      x_ratio=0.8, desc="右侧边栏上滑找免流量听歌入口")

    flow.open_operator_tab((AppiumBy.ACCESSIBILITY_ID, "听歌免流量按钮"), desc="免流量听歌入口")
    
    flow.click_gesture_locator((AppiumBy.ANDROID_UIAUTOMATOR, 
                            'new UiSelector().text("移动")'), 
                            desc="移动营销页面入口")
    
    #移动套餐一：0.01购超级VIP
    flow.click_gesture_locator((AppiumBy.ANDROID_UIAUTOMATOR, 
                        'new UiSelector().text("0.01元购超级VIP")'), 
                        desc="移动套餐一：0.01购超级VIP")
    #活动说明是背景图的一部分，人工实测滑2屏后出现
    image_paths = flow.capture_image_section(
        desc="移动套餐一活动说明图",
        skip_screens=2,swipe_start=0.88, swipe_end=0.12)
    logger.info(f"活动说明截图 {len(image_paths)} 张，首张: {image_paths[0]}")

    flow.go_back_gesture(times=1, settle_time=0.5)
    #移动套餐二：0.01购豪华VIP
    flow.click_gesture_locator((AppiumBy.ANDROID_UIAUTOMATOR, 
                            'new UiSelector().text("次月0.01元领豪华VIP")'), 
                            desc="移动套餐二：0.01购豪华VIP")
    CMCC_text_container_UUID = 'page-content'
    CMCC_text = flow.extract_page_scrolled_text(CMCC_text_container_UUID, desc="中国移动-酷狗随心听会员包活动说明")
    logger.info(f"中国移动-酷狗随心听会员包活动说明:\n{CMCC_text}")
    flow.go_back_gesture(times=1, settle_time=0.5)

    flow.click_gesture_locator((AppiumBy.ANDROID_UIAUTOMATOR, 
                                'new UiSelector().text("联通")'), 
                                desc="移动营销页面入口")

    