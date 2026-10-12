from common.Logger import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common.appium_actions import (
    wait_for_element,
    click_element,
    input_text,
    swipe_on_element,
    click_gesture_on_element,
    screenshot,
)

class BaseFlow:
    def __init__(self,driver, wait):
        self.driver = driver
        self.wait = wait
        self.logger = logger

    def wait_for_element(self, locator, desc=""):
        return wait_for_element(self.wait, locator, desc)

    def click(self,locator,desc="",screenshot_name=None,settle_time=0.5):
        return click_element(
            self.wait,
            locator,
            desc,
            screenshot_name,
            self.driver,
            settle_time = settle_time)

    def input_text(self, locator, text, desc=""):
        return input_text(self.wait, locator, text, desc=desc)

    def swipe(self, element, direction="left", percent=0.8, speed=300, settle_time=1, desc=""):
        return swipe_on_element(
            self.driver,
            element,
            direction=direction,
            percent=percent,
            speed=speed,
            settle_time=settle_time,
            desc=desc,
        )

    def click_gesture(self, element, desc=""):
        return click_gesture_on_element(self.driver, element, desc=desc)

    def screenshot(self, step_name, settle_time=0.5):
        return screenshot(self.driver, step_name, settle_time=settle_time)

    def switch_operator_tabs(self, operator_locators: dict, settle_time: int = 2):
        """按给定运营商 locator 字典逐个切换 tab 并截图。

        :param operator_locators: 例如 {
            "移动": (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("移动")'),
            "联通": (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("联通")'),
        }
        :param settle_time: 每次切换后的截图等待时间
        :return: 成功切换并截图的次数
        """
        captured = 0

        for operator_name, locator in operator_locators.items():
            try:
                self.click(
                    locator,
                    desc=f"{operator_name} tab",
                    screenshot_name=f"运营商_{operator_name}",
                    settle_time=settle_time,
                )
                captured += 1
            except Exception as e:
                self.logger.error(f"点击运营商tab {operator_name} 失败: {e}")

        return captured

    def switch_operator_tabs_by_gesture(self, operator_locators: dict, settle_time: int = 2):
        """通过 clickGesture 方式切换运营商 tab 并截图。
           用于有些app中最小定位元素clickble属性不为true"""
        captured = 0

        for operator_name, locator in operator_locators.items():
            try:
                element = self.wait_for_element(locator, desc=f"{operator_name} tab")
                self.click_gesture(element, desc=f"{operator_name} tab")
                self.screenshot(f"运营商_{operator_name}", settle_time=settle_time)
                captured += 1
            except Exception as e:
                self.logger.error(f"通过 clickGesture 点击运营商tab {operator_name} 失败: {e}")

        return captured

    def close_login_popup_if_present(self, popup_locator, close_locator,
                                     timeout=3, desc="登录弹窗"):
        """
        检测登录弹窗是否存在，存在则点击关闭按钮，不存在直接继续流程。
        :param popup_locator: 弹窗特征元素的定位器（用于判断弹窗是否出现）
        :param close_locator: 弹窗关闭按钮的定位器
        :param timeout: 探测弹窗的短超时时间（秒），默认 3
        :param desc: 日志描述
        :return: True=检测到并已关闭，False=未出现
        """
        short_wait = WebDriverWait(self.driver, timeout)
        try:
            short_wait.until(EC.presence_of_element_located(popup_locator))
            logger.info(f"检测到{desc}，尝试关闭")
            short_wait.until(EC.element_to_be_clickable(close_locator)).click()
            logger.info(f"已关闭{desc}")
            return True
        except TimeoutException:
            logger.info(f"未检测到{desc}，继续流程")
            return False