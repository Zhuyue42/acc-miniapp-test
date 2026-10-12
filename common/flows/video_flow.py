from common.flows.base_flow import BaseFlow

class VideoFlow(BaseFlow):
    def open_my_page(self, locator, desc="我的页面"):
        return self.click(locator, desc=desc, screenshot_name=desc, settle_time=1)

    def open_free_traffic_service(self, locator, desc="免流量服务"):
        return self.click(locator, desc=desc, screenshot_name=desc, settle_time=3)

    def wait_h5_content(self, locator, desc="H5内容"):
        element = self.wait_for_element(locator, desc=desc)
        self.screenshot("运营商推广页面", settle_time=2)
        return element