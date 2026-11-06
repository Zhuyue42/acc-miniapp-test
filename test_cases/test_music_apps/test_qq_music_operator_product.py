from appium.webdriver.common.appiumby import AppiumBy
from common.Logger import logger
from common.flows.music_flow import MusicFlow
import time
import pytest
from datetime import datetime
from pathlib import Path
from common.app_product_instruction import ProductInstructionFile

APP_NAME = "qq_music"

@pytest.fixture
def product_instructions(request):
    """按 App 收集活动说明，用例结束（无论成败）写一份 JSON。"""
    file = ProductInstructionFile(app_name="QQ音乐")
    yield file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(__file__).resolve().parent.parent / "test-results" / \
        "product_instructions" / f"{file.app_name}_{timestamp}.json"
    saved = file.write_json(out)
    logger.info(f"活动说明记录已输出: {saved}")

def test_qq_music_free_traffic(app_driver, app_wait, product_instructions,screen_recording):
    logger.info("开始QQ音乐免流服务订购页面进入测试")

    driver = app_driver(APP_NAME)
    wait = app_wait(driver, 10)
    flow = MusicFlow(driver, wait)

    time.sleep(2)  # 等待应用启动

    flow.open_my_page((AppiumBy.ACCESSIBILITY_ID, "我的"),desc="我的页面")

    flow.open_page_more((AppiumBy.ID, "com.tencent.qqmusic:id/hd6"), desc="右上角-更多")

    #qq音乐的移动推广是单独一个标签
    flow.open_operator_tab((AppiumBy.ACCESSIBILITY_ID, "移动用户免流送会员"), desc="移动运营商推广入口")
    #中国移动套餐一：中国移动x绿钻免流包（入口文案）
    flow.open_operator_tab((AppiumBy.ANDROID_UIAUTOMATOR,
             'new UiSelector().resourceId("exposure_1_0").instance(1)'), desc="中国移动xQQ音乐随心听")
    #从文本容器中提取活动说明，文本容器UUID: 366c7161-a926-4b28-8aae-cd24e073f88b
    CMCC_instruction_5GB_text_container_UUID = '366c7161-a926-4b28-8aae-cd24e073f88b'
    CMCC_instruction_5GB_text = flow.extract_container_text(CMCC_instruction_5GB_text_container_UUID, 
                                                            desc="中国移动xQQ音乐随心听活动说明器",
                                                            swipe_start=0.95, swipe_end=0.05)
    logger.info(f"已提取中国移动xQQ音乐随心听活动说明器内容:\n{CMCC_instruction_5GB_text}")
    product_instructions.add_record(
        app_name="QQ音乐",
        operator="中国移动",
        offer_name="xQQ音乐随心听",
        offer_instruction=CMCC_instruction_5GB_text
    )
    flow.go_back_gesture(times=1, settle_time=0.5)

    #中国移动套餐二：中国移动x超级免流包
    flow.open_operator_tab((AppiumBy.ANDROID_UIAUTOMATOR,
                 'new UiSelector().resourceId("exposure_1_1").instance(1)'), desc="中国移动-QQ音乐超级随心听")
    #从文本容器中提取活动说明，文本容器UUID: 210d1775-957a-44ba-86bb-09d59734622f
    CMCC_instruction_5GB_super_text_container_UUID = '210d1775-957a-44ba-86bb-09d59734622f'
    CMCC_instruction_5GB_super_text = flow.extract_container_text(CMCC_instruction_5GB_super_text_container_UUID, 
                                                                  desc="中国移动xQQ音乐超级随心听活动说明器",
                                                                  swipe_start=0.95, swipe_end=0.05)
    logger.info(f"已提取中国移动xQQ音乐超级随心听活动说明器内容:\n{CMCC_instruction_5GB_super_text}")
    product_instructions.add_record(
        operator="移动",
        offer_name="中国移动xQQ音乐超级随心听",
        offer_instruction=CMCC_instruction_5GB_super_text,
    )

    #左滑屏幕手势返回至“更多页面”
    flow.go_back_gesture(times=2, settle_time=0.5)

    #联通和电信推广入口
    flow.open_operator_tab((AppiumBy.ACCESSIBILITY_ID, "免流量听歌送会员"), desc="联通电信运营商推广入口")
    #联通套餐入口定位：new UiSelector().resourceId("exposure_3_0").instance(1)
    flow.open_operator_tab((AppiumBy.ANDROID_UIAUTOMATOR,
                     'new UiSelector().resourceId("exposure_3_0").instance(1)'), desc="中国联通-积分兑换会员")
    product_instructions.add_record(
        operator="联通",
        offer_name="中国联通-积分兑换会员",
        is_test=False,
        exclude_reasons="活动页无说明文本",
    )
    flow.go_back_gesture(times=1, settle_time=0.5)
    logger.info("联通积分兑换会员活动无说明文本可提取。")
    
    #电信套餐入口定位
    flow.open_operator_tab((AppiumBy.ANDROID_UIAUTOMATOR,
                     'new UiSelector().resourceId("exposure_2_1").instance(1)'), desc="中国电信x流量包")
    #UUID9D7C7B62907C9958F0A0270415507128
    CT_text_container_UUID = 'UUID9D7C7B62907C9958F0A0270415507128'
    CT_text = flow.extract_page_scrolled_text(CT_text_container_UUID, desc="中国电信x流量包活动说明")
    logger.info(f"已提取中国电信x流量包活动说明内容:\n{CT_text}")
    #CT_text = flow.extract_page_scrolled_text(...)
    product_instructions.add_record(
        operator="电信",
        offer_name="中国电信x流量包",
        offer_instruction=CT_text,
    )
    flow.go_back_gesture(times=2, settle_time=0.5)

    #返回更多页面
    # flow.go_back(times=1, back_locator=(AppiumBy.ANDROID_UIAUTOMATOR,
    #                                    'new UiSelector().resourceId("com.tencent.qqmusic:id/a5e").instance(2)'), 
    #                                    settle_time=1) #h5页面返回键和原生页面返回键定位不一致
    # flow.go_back(times=1, back_locator=(AppiumBy.ANDROID_UIAUTOMATOR,
    #                                        'new UiSelector().resourceId("com.tencent.qqmusic:id/a5e").instance(1)'), 
    #                                        settle_time=1) #h5页面返回键和原生页面返回键定位不一致
    
    #电信文本容器：UUID9D7C7B62907C9958F0A0270415507128
    #new UiSelector().className("android.view.View").instance(10)
    # flow.open_operator_tab((AppiumBy.ACCESSIBILITY_ID, "返回"), desc="返回上一页")
    # #联通和电信推广入口
    # flow.open_operator_tab((AppiumBy.ACCESSIBILITY_ID, "免流量听歌送会员"), desc="联通电信运营商推广入口")


