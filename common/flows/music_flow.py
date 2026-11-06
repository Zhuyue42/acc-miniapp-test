from common.flows.base_flow import BaseFlow
import xml.etree.ElementTree as ET
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
import re
import time


class MusicFlow(BaseFlow):
    def open_my_page(self, locator, desc="我的页面"):
        return self.click(locator, desc=desc, screenshot_name=desc, settle_time=1)

    def open_page_more(self, locator, desc="右上角-更多"):
        return self.click(locator, desc=desc, screenshot_name=desc, settle_time=1)
    
    def open_operator_tab(self, locator, desc="运营商推广标签"):
            return self.click(locator, desc=desc, screenshot_name=desc, settle_time=1)
    
    def open_free_traffic_service(self, locator, desc="免流量服务"):
        return self.click(locator, desc=desc, screenshot_name=desc, settle_time=2)


    def _find_node_by_resource_id(self, resource_id):
        """在整页 XML 中按 resource-id 查找节点，找不到返回 None。"""
        root = ET.fromstring(self.driver.page_source)
        return next((n for n in root.iter()
                     if n.attrib.get("resource-id") == resource_id), None)

    def scroll_page_until_visible(self, resource_id, desc="目标容器",
                                  timeout=20, settle=0.8):
        """在外层页面反复上滑（内容下移），直到 resource-id 节点出现。
        用于把视口外的 X5 懒渲染区域滚进屏幕。返回该节点，超时抛异常。"""
        size = self.driver.get_window_size()
        cx = size["width"] // 2
        deadline = time.time() + timeout
        while True:
            node = self._find_node_by_resource_id(resource_id)
            if node is not None:
                self.logger.info(f"{desc} 已滚入视口")
                return node
            if time.time() >= deadline:
                raise TimeoutException(f"滚动 {timeout}s 后仍未出现容器: {resource_id}")
            # 屏幕中部上滑：内容向下翻一页的 60%
            self.driver.swipe(cx, int(size["height"] * 0.8),
                              cx, int(size["height"] * 0.2), 500)
            time.sleep(settle)
    def _container_bounds(self, resource_id):
        """在整页 XML 中按 resource-id 找容器，返回 [l,t,r,b]，找不到返回 None。"""
        node = self._find_node_by_resource_id(resource_id)
        if node is None:
            return None
        nums = re.findall(r"-?\d+", node.attrib.get("bounds", ""))
        return list(map(int, nums)) if len(nums) == 4 else None
    def scroll_page_until_container_fully_visible(self, resource_id, desc,
                                                  timeout=30, settle=0.8,
                                                  max_scrolls=20,
                                                  swipe_start=0.92, swipe_end=0.08):
        """外层页面上滑，直到容器完整进入视口（而非刚露头就停）。
        若连续多轮 bounds 不再变化，说明外层已滚到底，接受现状。

        :param swipe_start/swipe_end: 外层滑动的起止纵向比例，跨度越大单轮滚动越远
        """
        size = self.driver.get_window_size()
        cx = size["width"] // 2
        deadline = time.time() + timeout
        last_bounds, stagnant = None, 0
        while time.time() < deadline:
            bounds = self._container_bounds(resource_id)
            if bounds is not None:
                l, t, r, b = bounds
                if t >= 0 and b <= size["height"]:
                    self.logger.info(f"{desc} 已完整进入视口: {bounds}")
                    return bounds
                if bounds == last_bounds:
                    stagnant += 1
                    if stagnant >= 2:
                        self.logger.warning(f"外层已滚到底，容器保持: {bounds}")
                        return bounds
                else:
                    stagnant = 0
            last_bounds = bounds
            self.driver.swipe(cx, int(size["height"] * swipe_start),
                              cx, int(size["height"] * swipe_end), 400)
            time.sleep(settle)
        raise TimeoutException(f"滚动 {timeout}s 后容器仍未完整进入视口: {resource_id}")
    
    def extract_container_text(self, resource_id, desc="活动说明容器",
                               max_scrolls=30,
                               swipe_start=0.92, swipe_end=0.08):
        l, t, r, b = self.scroll_page_until_container_fully_visible(
            resource_id, desc=desc, swipe_start=swipe_start, swipe_end=swipe_end)
        cx = (l + r) // 2
        texts: list[str] = []

        def collect() -> bool:
            cur = self._find_node_by_resource_id(resource_id)
            if cur is None:
                return False
            added = False
            for n in cur.iter():
                txt = n.attrib.get("text", "").strip()
                if txt and txt not in texts:
                    texts.append(txt)
                    added = True
            return added

        collect()
        no_new_rounds = 0
        for _ in range(max_scrolls):
            # 内层滑幅加大：容器高度的 95% → 5%，接近整屏翻动
            self.driver.swipe(cx, int(t + (b - t) * 0.95),
                              cx, int(t + (b - t) * 0.05), 300)
            time.sleep(1.0)  # 给 X5 节点重渲染留时间
            if collect():
                no_new_rounds = 0
            else:
                no_new_rounds += 1
                if no_new_rounds >= 2:
                    break  # 连续两轮无新增才认定到底，防渲染延迟误判

        parts: list[str] = []
        for txt in texts:
            if parts and re.match(r"^\d+、", txt):
                parts.append("\n")
            parts.append(txt)
        full_text = "".join(parts)
        self.logger.info(f"已提取{desc}，共 {len(texts)} 段文本")
        return full_text

    def extract_page_scrolled_text(self, resource_id, desc="活动说明容器",
                                   settle=1.0, max_scrolls=30,
                                   no_new_stop=3,
                                   find_timeout=30):
        """收集随页面滚动的容器完整文本。

        活动说明通常是营销页最后一个模块，分两阶段：
        1. 外层页面上滑，直到容器出现（复用 scroll_page_until_visible）；
        2. 继续上滑并逐轮收集容器子树文本，直到连续 no_new_stop 轮无新增
           或容器整体滚出屏幕。
        """
        size = self.driver.get_window_size()
        cx = size["width"] // 2
        texts: list[str] = []

        def collect() -> bool:
            cur = self._find_node_by_resource_id(resource_id)
            if cur is None:
                return False
            added = False
            for n in cur.iter():
                txt = n.attrib.get("text", "").strip()
                if txt and txt not in texts:
                    texts.append(txt)
                    added = True
            return added

        # 阶段 1：先滑到容器出现（活动说明在页面底部，不滑根本不在视口）
        self.scroll_page_until_visible(resource_id, desc=desc,
                                       timeout=find_timeout)

        # 阶段 2：容器已出现，继续滑动并收集
        collect()
        no_new = 0
        last_bounds = None
        for _ in range(max_scrolls):
            # 外层页面上滑约 65% 屏高，保留重叠区防跨过节点
            self.driver.swipe(cx, int(size["height"] * 0.85),
                              cx, int(size["height"] * 0.20), 500)
            time.sleep(settle)
            if collect():
                no_new = 0
            else:
                no_new += 1

            bounds = self._container_bounds(resource_id)
            if bounds is None:
                # 容器已滚出屏幕，说明其内容已全部经过视口
                self.logger.info(f"{desc} 已滚出屏幕，结束收集")
                break
            if bounds == last_bounds and no_new >= 1:
                no_new += 1  # 外层滚不动（页面到底）且无新文本，加速退出
            last_bounds = bounds
            if no_new >= no_new_stop:
                break

        parts: list[str] = []
        for txt in texts:
            if parts and re.match(r"^\d+、", txt):
                parts.append("\n")
            parts.append(txt)
        full_text = "".join(parts)
        self.logger.info(f"已提取{desc}，共 {len(texts)} 段文本")
        return full_text
    def wait_h5_content(self, locator, desc="H5内容"):
        element = self.wait_for_element(locator, desc=desc)
        self.screenshot("运营商推广页面", settle_time=2)
        return element