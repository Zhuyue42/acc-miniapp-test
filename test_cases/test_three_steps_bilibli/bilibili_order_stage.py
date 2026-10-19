"""步骤 B：校验人工选中的套餐，并为一次订购生成一条表格记录。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from common.table_record import TableRecord, TableRecordRow


CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "test_data" / "bilibili_offer_candidates.json"


def load_catalog(path: str | Path = CATALOG_PATH) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_offer_selection(
    operator: str,
    offer_id: str,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """校验步骤 B 的当前订单目标；每家可选 1–3 个，整个批次最多 9 个。

    未运行的运营商可以保持 0 个选择。调用本函数代表要执行该运营商的一笔
    套餐订购，因此该运营商必须至少选 1 个，且本次 offer_id 必须已被选中。
    """
    catalog = catalog or load_catalog()
    operators = catalog.get("operators", {})
    if operator not in operators:
        raise ValueError(f"未知运营商: {operator}；可用运营商: {', '.join(operators)}")

    selected_by_operator: dict[str, list[dict[str, Any]]] = {}
    for name, candidates in operators.items():
        ids = [candidate["id"] for candidate in candidates]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{name} 的候选套餐 ID 有重复")
        selected = [candidate for candidate in candidates if candidate.get("selected") is True]
        if len(selected) > 3:
            raise ValueError(f"{name} 已选择 {len(selected)} 个套餐；每家最多选择 3 个")
        selected_by_operator[name] = selected

    selected_total = sum(len(items) for items in selected_by_operator.values())
    if selected_total > 9:
        raise ValueError(f"当前共选择 {selected_total} 个套餐；三个运营商合计最多 9 个")

    selected_for_operator = selected_by_operator[operator]
    if not selected_for_operator:
        raise ValueError(f"{operator} 尚未选择套餐；步骤 B 只对已选套餐运行")

    match = next((candidate for candidate in selected_for_operator if candidate["id"] == offer_id), None)
    if match is None:
        raise ValueError(f"套餐 {offer_id} 不在 {operator} 已选套餐中")
    return match


def create_offer_record(
    table_record: TableRecord,
    operator: str,
    offer_id: str,
    catalog: dict[str, Any] | None = None,
) -> TableRecordRow:
    """为当前一次人工订购创建且仅创建一条正式表格记录。"""
    catalog = catalog or load_catalog()
    offer = validate_offer_selection(operator, offer_id, catalog)
    existing = next((
        row for row in table_record.rows
        if row.fields.get("运营商") == operator
        and row.metadata.get("offer_id") == offer_id
    ), None)
    if existing is not None:
        return existing
    if len(table_record.rows) >= 9:
        raise ValueError("一个 B 站测试批次最多只能创建 9 条套餐记录")

    row = table_record.new_row(operator, metadata={
        "offer_id": offer["id"],
        "selection_status": "selected",
        "order_status": "awaiting_human_order",
        "marketing_badge": offer.get("badge"),
        "call_to_action": offer.get("call_to_action", []),
        "transcription_source": catalog.get("source"),
    })
    row.set("订购入口设计.入口位置", "我的-免流量服务")
    row.set("订购入口设计.入口文案", "免流量服务")
    row.set("页面信息.业务信息展示.业务名称", offer["name"])
    row.set("页面信息.业务信息展示.资费价格", offer.get("price"))
    row.set("页面信息.业务信息展示.权益内容", offer["description"])
    return row
