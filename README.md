# B 站运营商套餐候选记录

`test_data/bilibili_offer_candidates.json` 是根据用户提供的移动、电信、联通营销页截图整理的候选清单。候选是否实际可订购尚未确认，`selected` 初始均为 `false`。

步骤 A `test_cases/test_bilibili_free_traffic.py` 只采集入口和各运营商营销页面截图、可见文本及候选套餐 ID，不做套餐选择校验，也不为所有候选生成正式表格行。

人工确认后，在 `test_data/bilibili_offer_candidates.json` 中把选中的候选项 `selected` 设为 `true`。每家运营商可选 0–3 个；未选择的运营商允许保持 0 个。步骤 B 的 [bilibili_order_stage.py](test_cases/bilibili_order_stage.py) 仅校验本次指定的运营商和套餐，并为一个套餐创建一条正式订单记录。整个批次最多 9 条，不足 9 条时按实际选中的套餐数输出。

步骤 A 运行后，页面证据和候选 ID 写入 `test-results/table_records/` 下的 JSON。步骤 B 创建的每条订单记录映射到测试记录表字段；后续人工操作、短信匹配、跳转页采集和人工复核结果应更新同一套餐记录。
