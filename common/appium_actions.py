import time
from selenium.webdriver.support import expected_conditions as EC
from common.Logger import logger
from common.screenshot import take_screenshot

def wait_for_element(wait, locator, desc=""):
    element = wait.until(EC.presence_of_element_located(locator))
    if desc:
        logger.info(f"已定位元素: {desc}")
    return element


def click_element(wait, locator, desc="", screenshot_name=None, driver=None, settle_time=0.5):
    element = wait_for_element(wait, locator, desc)
    element.click()
    logger.info(f"已点击: {desc or locator}")

    if driver and screenshot_name:
        take_screenshot(driver, screenshot_name, settle_time=settle_time)

    return element


def input_text(wait, locator, text, desc=""):
    element = wait_for_element(wait, locator, desc)
    element.click()
    element.clear()
    element.send_keys(text)
    logger.info(f"已输入文本: {text}")
    return element


def swipe_on_element(driver, element, direction="left", percent=0.8, speed=300, settle_time=1, desc=""):
    driver.execute_script("mobile: swipeGesture", {
        "elementId": element.id,
        "direction": direction,
        "percent": percent,
        "speed": speed,
    })
    time.sleep(settle_time)
    logger.info(f"已完成滑动: {desc or direction}")


def click_gesture_on_element(driver, element, desc=""):
    driver.execute_script("mobile: clickGesture", {
        "elementId": element.id,
    })
    logger.info(f"已通过 clickGesture 点击: {desc or element}")


def screenshot(driver, step_name, settle_time=0.5):
    path = take_screenshot(driver, step_name, settle_time=settle_time)
    logger.info(f"已截图: {step_name} -> {path}")
    return path