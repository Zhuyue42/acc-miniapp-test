import time
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

    def click_gesture_locator(self, locator, desc="", settle_time=1):
        """按定位器等待元素并用 clickGesture 点击（适合 clickable=false 的自绘控件）。"""
        element = self.wait_for_element(locator, desc=desc)
        self.click_gesture(element, desc=desc)
        time.sleep(settle_time)
        return element

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

    def go_back(self, times=1, back_locator=None, settle_time=1):
        """返回上一页，可返回多次。

        :param times: 返回次数
        :param back_locator: 页面内返回按钮定位器；None 则用系统返回键。
            H5/WebView 页面务必传页面内按钮，系统返回键可能直接关掉整个 WebView。
        """
        for i in range(times):
            if back_locator:
                self.click(back_locator, desc=f"返回按钮(第{i + 1}次)")
            else:
                self.driver.back()
                self.logger.info(f"已按系统返回键(第{i + 1}次)")
                time.sleep(settle_time)
        return self

    def go_back_until(self, anchor_locator, max_back=5, back_locator=None,
                      settle_time=1, desc="目标页"):
        """反复返回直到 anchor 元素出现，用于跨多级页面回到已知页面。

        :param anchor_locator: 目标页的特征元素定位器
        :param max_back: 最大返回次数，超过抛 TimeoutException
        :return: True=已回到目标页；异常=未回到
        """
        for i in range(max_back + 1):
            try:
                self.wait_for_element(anchor_locator, desc=f"{desc}(第{i}次返回后)")
                self.logger.info(f"已回到{desc}")
                return True
            except TimeoutException:
                if i == max_back:
                    break
                if back_locator:
                    self.click(back_locator, desc=f"返回按钮(第{i + 1}次)")
                else:
                    self.driver.back()
                    self.logger.info(f"已按系统返回键(第{i + 1}次)")
                time.sleep(settle_time)
        raise TimeoutException(f"返回 {max_back} 次后仍未回到{desc}")

    def swipe_back(self, y_ratio=0.5, duration=400):
        """从屏幕最左缘右滑，触发系统侧滑返回手势。

        起点必须贴紧 x=0，否则触发的是应用内滑动而非系统返回。
        """
        size = self.driver.get_window_size()
        self.driver.swipe(0, int(size["height"] * y_ratio),
                          int(size["width"] * 0.6), int(size["height"] * y_ratio),
                          duration)
        self.logger.info("已通过左缘侧滑返回一级")
    
    def go_back_gesture(self, times=1, settle_time=1, y_ratio=0.5, duration=400):
        """左缘侧滑返回，指定返回层数。

        :param times: 侧滑返回次数（每滑一次约退一级）
        :param settle_time: 每次侧滑后的等待时间（秒），等页面切换动画完成
        :param y_ratio: 手势起点纵向位置（屏幕高度比例），避开导航栏/状态栏
        :param duration: 手势时长（毫秒），太短可能不被识别为系统返回手势
        """
        size = self.driver.get_window_size()
        y = int(size["height"] * y_ratio)
        for i in range(times):
            self.driver.swipe(0, y, int(size["width"] * 0.6), y, duration)
            self.logger.info(f"已通过左缘侧滑返回(第{i + 1}/{times}次)")
            time.sleep(settle_time)
        return self
    
    #qq音乐由于新页面叠加在旧页面上导致终止定位元素失效
    def go_back_until_gesture(self, anchor_locator, max_back=5,
                              settle_time=1, desc="目标页", probe_timeout=3):
        """反复左缘侧滑，直到 anchor 元素出现（回到目标页）。

        不依赖返回键定位，适合 H5/原生混合页面逐级回退。
        :param probe_timeout: 每轮探测 anchor 的短超时（秒）
        """
        short_wait = WebDriverWait(self.driver, probe_timeout)
        for i in range(max_back + 1):
            try:
                short_wait.until(EC.presence_of_element_located(anchor_locator))
                self.logger.info(f"已回到{desc}（侧滑 {i} 次）")
                return True
            except TimeoutException:
                if i == max_back:
                    break
                self.swipe_back()
                time.sleep(settle_time)
        raise TimeoutException(f"侧滑 {max_back} 次后仍未回到{desc}")

    #向上滑动手势
    def swipe_screen(self, direction="up", distance_ratio=0.5, duration=500,
                     settle_time=1, x_ratio=0.5, desc="屏幕滑动"):
        """按坐标在屏幕上滑动，不依赖元素定位。

        :param direction: up=内容上移（看下方内容）/ down=内容下移
        :param distance_ratio: 滑动距离占屏幕高度比例
        :param x_ratio: 手势纵向线的横向位置（屏幕宽度比例），
                        侧边栏等局部列表要把 x 落在其面板范围内
        """
        size = self.driver.get_window_size()
        cx = int(size["width"] * x_ratio)
        cy = size["height"] // 2
        delta = int(size["height"] * distance_ratio / 2)
        if direction == "up":
            self.driver.swipe(cx, cy + delta, cx, cy - delta, duration)
        else:
            self.driver.swipe(cx, cy - delta, cx, cy + delta, duration)
        time.sleep(settle_time)
        self.logger.info(f"已完成屏幕滑动: {desc or direction}")
        return self


    def capture_image_section(self, desc="图片说明区",
                              skip_screens=0, max_scrolls=15,
                              swipe_start=0.85, swipe_end=0.30,
                              settle=1.0, screenshot_prefix=None,
                              locator=None):
        """滚动到说明区后连续截图直到页面底部。

        两种定位说明区的方式（二选一）：
        1. 传 locator：滚动到该元素出现后开始截图（说明区有可定位锚点时）；
        2. 传 skip_screens：先盲滑 N 屏再开始截图（说明是背景图的一部分、
           无锚点可定位时，N 由人工实测得出）。
        """
        size = self.driver.get_window_size()
        cx = size["width"] // 2

        def scroll_once():
            self.driver.swipe(cx, int(size["height"] * swipe_start),
                              cx, int(size["height"] * swipe_end), 500)
            time.sleep(settle)

        # 阶段 1：到达说明区
        if locator is not None:
            short_wait = WebDriverWait(self.driver, 3)
            deadline = time.time() + 30
            while time.time() < deadline:
                try:
                    short_wait.until(EC.presence_of_element_located(locator))
                    break
                except TimeoutException:
                    scroll_once()
            else:
                raise TimeoutException(f"滚动后仍未出现: {desc}")
        else:
            for i in range(skip_screens):
                scroll_once()
                self.logger.info(f"{desc}: 跳过第 {i + 1}/{skip_screens} 屏")

        # 阶段 2：连续截图直到页面底部（内容不再变化）
        prefix = screenshot_prefix or desc
        paths = []
        prev_source = None
        for i in range(max_scrolls):
            path = self.screenshot(f"{prefix}_第{i + 1}屏", settle_time=0.5)
            paths.append(path)
            source = self.driver.page_source
            if source == prev_source:
                self.logger.info(f"{desc} 已到底，共截图 {len(paths)} 张")
                break
            prev_source = source
            scroll_once()
        else:
            self.logger.warning(f"{desc} 达到最大滚动次数 {max_scrolls}")
        return paths