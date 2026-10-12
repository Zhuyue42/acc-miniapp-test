from common.flows.base_flow import BaseFlow


class ShoppingFlow(BaseFlow):
    def open_entry(self, locator, entry_name, screenshot_name=None, settle_time=1):
        return self.click(locator, desc=entry_name, screenshot_name=screenshot_name, settle_time=settle_time)

    def swipe_container(self, container_locator, direction="left", desc="页面滑动", screenshot_name=None):
        container = self.wait_for_element(container_locator, desc="滑动容器")
        self.swipe(container, direction=direction, desc=desc)
        if screenshot_name:
            self.screenshot(screenshot_name, settle_time=1)

    def read_phone_number(self, locator, desc="手机号输入框"):
        """读取输入框当前已填入的号码。"""
        element = self.wait_for_element(locator, desc=desc)
        phone = element.text
        self.logger.info(f"{desc} 当前号码: {phone}")
        return phone

    def fill_phone_number(self, locator, phone_number, desc="手机号输入框"):
        return self.input_text(locator, phone_number, desc=desc)