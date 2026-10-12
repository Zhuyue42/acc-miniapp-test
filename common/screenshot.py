import os
import time
from pathlib import Path

def take_screenshot(driver, step_name, base_dir="screenshots",settle_time=0.5):
    """
    截图并按 app 名称 + 步骤名 + 时间戳保存。

    :param driver:    Appium WebDriver 实例
    :param step_name: 步骤名（如 "我的页面"、"免流量服务"）
    :param base_dir:  截图根目录
    :param settle_time: 截图前等待的时间（秒），默认 0.5 秒
    """
    # 等待页面稳定
    time.sleep(settle_time)
    # 1. 获取 app 名称（包名），失败则用默认值
    app_name = "unknown"
    try:
        app_name = driver.current_package          # 如 tv.danmaku.bili
    except Exception:
        try:
            app_name = driver.capabilities.get("appPackage", "unknown")
        except Exception:
            pass

    # 2. 按「日期 / app 名」建文件夹
    date_dir = time.strftime("%Y-%m-%d")
    folder = Path(base_dir) / date_dir / app_name
    folder.mkdir(parents=True, exist_ok=True)

    # 3. 生成带时间戳的文件名
    timestamp = time.strftime("%H%M%S")
    filename = f"{step_name}_{timestamp}.png"
    filepath = folder / filename

    # 4. 截图保存
    driver.get_screenshot_as_file(str(filepath))
    return str(filepath)