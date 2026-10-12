"""记录流程脚本采集到的测试表格字段，并输出可填表的 JSON。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


# 测试记录表第 3 行叶子表头对应的列；完整路径用于区分重名字段。
TABLE_FIELD_COLUMNS = {
    "APP类型": "A",
    "APP名称": "B",
    "运营商": "C",
    "订购入口设计.入口层级": "D",
    "订购入口设计.入口位置": "E",
    "订购入口设计.入口形式": "F",
    "订购入口设计.入口文案": "G",
    "页面信息.业务信息展示.业务名称": "H",
    "页面信息.业务信息展示.资费价格": "I",
    "页面信息.业务信息展示.是否页面展示权益明细": "J",
    "页面信息.业务信息展示.权益内容": "K",
    "页面信息.业务信息展示.生效规则": "L",
    "页面信息.业务信息展示.合约期": "M",
    "页面信息.业务信息展示.退订提示": "N",
}


class TableRecordRow:
    """一行待填入测试记录表的数据。字段键使用完整分组路径避免重名。"""

    def __init__(self, initial_fields: dict[str, Any] | None = None,
                 metadata: dict[str, Any] | None = None):
        self.fields: dict[str, Any] = dict(initial_fields or {})
        self.metadata: dict[str, Any] = dict(metadata or {})
        self.evidence: list[dict[str, Any]] = []

    def set(self, field_path: str, value: Any) -> None:
        if not field_path or not isinstance(field_path, str):
            raise ValueError("field_path 必须是非空字符串")
        if field_path not in TABLE_FIELD_COLUMNS:
            raise ValueError(f"未登记的测试记录表字段: {field_path}")
        self.fields[field_path] = value

    def add_evidence(self, *, step: str, screenshot: str | None = None,
                     visible_text: list[str] | None = None) -> None:
        item: dict[str, Any] = {"step": step}
        if screenshot:
            item["screenshot"] = screenshot
        if visible_text:
            item["visible_text"] = visible_text
        self.evidence.append(item)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": self.fields,
            "metadata": self.metadata,
            "evidence": self.evidence,
        }


class TableRecord:
    """单个 pytest 用例产生的一组表格行（例如每个运营商一行）。"""

    def __init__(self, test_name: str, app_type: str, app_name: str):
        self.test_name = test_name
        self.app_type = app_type
        self.app_name = app_name
        self.created_at = datetime.now().astimezone().isoformat(timespec="seconds")
        self.entry_evidence: dict[str, Any] | None = None
        self.marketing_pages: list[dict[str, Any]] = []
        self.rows: list[TableRecordRow] = []

    def add_entry_evidence(self, screenshot: str | None,
                           visible_text: list[str]) -> None:
        self.entry_evidence = {
            "screenshot": screenshot,
            "visible_text": visible_text,
        }

    def add_marketing_page(self, operator: str, screenshot: str | None,
                           visible_text: list[str], offer_ids: list[str]) -> None:
        """保存步骤 A 的页面证据；营销候选本身不创建正式套餐记录。"""
        self.marketing_pages.append({
            "operator": operator,
            "screenshot": screenshot,
            "visible_text": visible_text,
            "offer_candidate_ids": offer_ids,
        })

    def new_row(self, operator: str,
                metadata: dict[str, Any] | None = None) -> TableRecordRow:
        row = TableRecordRow({
            "APP类型": self.app_type,
            "APP名称": self.app_name,
            "运营商": operator,
        }, metadata=metadata)
        self.rows.append(row)
        return row

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "source_test": self.test_name,
            "created_at": self.created_at,
            "field_columns": TABLE_FIELD_COLUMNS,
            "entry_evidence": self.entry_evidence,
            "marketing_pages": self.marketing_pages,
            "records": [row.to_dict() for row in self.rows],
        }

    def write_json(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path
