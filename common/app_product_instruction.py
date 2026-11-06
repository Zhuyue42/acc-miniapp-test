from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

# 单条活动说明记录的模板；新增字段只改这里
PRODUCT_INSTRUCTION = {
    "app_name":"",
    "operator":"",
    "offer_name":"",
    "offer_instruction":"",
    "is_test":False,
    "exclude_reasons":""
}

class ProductInstructionRecord:
    """一条活动说明记录，字段以模板为准，防止拼写错误。"""

    def __init__(self, **kwargs: Any):
        unknown = set(kwargs) - set(PRODUCT_INSTRUCTION)
        if unknown:
            raise ValueError(f"未登记的记录字段: {', '.join(unknown)}")
        self.data: dict[str, Any] = {**deepcopy(PRODUCT_INSTRUCTION), **kwargs}

    def set(self, field: str, value: Any) -> None:
        if field not in PRODUCT_INSTRUCTION:
            raise ValueError(f"未登记的记录字段: {field}")
        self.data[field] = value

    def to_dict(self) -> dict[str, Any]:
        return dict(self.data)


class ProductInstructionFile:
    """一个 App 一份文件：收集多条记录，结束时写 JSON。"""

    def __init__(self, app_name: str):
        self.app_name = app_name
        self.created_at = datetime.now().astimezone().isoformat(timespec="seconds")
        self.records: list[ProductInstructionRecord] = []

    def add_record(self, **kwargs: Any) -> ProductInstructionRecord:
        kwargs.setdefault("app_name", self.app_name)
        record = ProductInstructionRecord(**kwargs)
        self.records.append(record)
        return record

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "app_name": self.app_name,
            "created_at": self.created_at,
            "record_count": len(self.records),
            "records": [r.to_dict() for r in self.records],
        }

    def write_json(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path