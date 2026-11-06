"""extract_page_scrolled_text 冒烟测试：只跑到电信活动页，验证提取能力。

单独运行：pytest test_cases/test_music_apps/test_extract_page_scrolled_smoke.py -v -s
"""
from appium.webdriver.common.appiumby import AppiumBy
from common.Logger import logger
from common.flows.music_flow import MusicFlow
import time

APP_NAME = "kugou_music"

# 电信活动说明容器（随页面滚动型）
CT_TEXT_CONTAINER_UUID = 'UUID9D7C7B62907C9958F0A0270415507128'


def test_extract_page_scrolled_text_smoke(app_driver, app_wait):
    logger.info("冒烟：extract_page_scrolled_text（移动活动说明）")

    driver = app_driver(APP_NAME)
    wait = app_wait(driver, 10)
    flow = MusicFlow(driver, wait)

    time.sleep(2)  # 等待应用启动

    # 最短导航路径：直达电信活动页
    # flow.open_my_page((AppiumBy.ACCESSIBILITY_ID, "我的"), desc="我的页面")
    # flow.open_page_more((AppiumBy.ID, "com.tencent.qqmusic:id/hd6"), desc="右上角-更多")
    # flow.open_operator_tab((AppiumBy.ACCESSIBILITY_ID, "免流量听歌送会员"),
    #                        desc="联通电信运营商推广入口")
    # flow.open_operator_tab((AppiumBy.ANDROID_UIAUTOMATOR,
    #                         'new UiSelector().resourceId("exposure_2_1").instance(1)'),
    #                        desc="中国电信x流量包")

    # 被测函数
    # text = flow.extract_page_scrolled_text(CT_TEXT_CONTAINER_UUID,
    #                                        desc="中国电信x流量包活动说明")
    # CMCC_instruction_5GB_super_text_container_UUID = 'UUID9D7C7B62907C9958F0A0270415507128'
    # CMCC_instruction_5GB_super_text = flow.extract_container_text(CMCC_instruction_5GB_super_text_container_UUID, 
    #                                                               desc="中国电信网易云音乐会员权益2GB通用流量包活动说明器",
    #                                                               swipe_start=0.88, swipe_end=0.12)
    # logger.info(f"已提取中国电信网易云音乐会员权益2GB通用流量包活动说明器内容:\n{CMCC_instruction_5GB_super_text}")
    CMCC_text_container_UUID = 'page-content'
    CMCC_text = flow.extract_page_scrolled_text(CMCC_text_container_UUID, desc="中国移动-酷狗随心听会员包活动说明")
    logger.info(f"中国移动-酷狗随心听会员包活动说明:\n{CMCC_text}")
    # 冒烟断言：非空 + 有编号条目 + 文本量达到基本规模
    assert CMCC_text, "提取结果为空"
    lines = [ln for ln in CMCC_text.split("\n") if ln.strip()]
    assert len(lines) >= 3, f"提取条目过少，疑似只采到首屏: {len(lines)} 条"
    assert any(ln.strip()[0].isdigit() for ln in lines), "未见编号条目，疑似锚定错容器"
    assert len(CMCC_text) > 200, f"文本过短，疑似未滚动收集: {len(CMCC_text)} 字"
    logger.info(f"冒烟通过：{len(lines)} 条 / {len(CMCC_text)} 字，前 100 字:\n{CMCC_text[:100]}")