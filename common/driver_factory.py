from appium import webdriver
from appium.options.android import UiAutomator2Options
from common.app_config_load import get_app_config

DEFAULT_REMOTE_URL = "http://localhost:4723"


def create_driver(app_name: str, remote_url: str = DEFAULT_REMOTE_URL):
    """根据应用名创建 Appium driver。"""
    config = get_app_config(app_name)
    options = UiAutomator2Options().load_capabilities(config["capabilities"])
    driver = webdriver.Remote(remote_url, options=options)
    return driver