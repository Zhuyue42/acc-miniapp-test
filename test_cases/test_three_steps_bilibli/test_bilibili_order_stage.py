from pathlib import Path
from common.table_record import TableRecord
from test_cases.test_three_steps_bilibli.bilibili_order_stage import (
    create_offer_record, validate_offer_selection,
)


def test_create_offer_record_output():
    record = TableRecord(
        test_name="smoke/test_bilibili_order_stage.py::test_create_offer_record_output",
        app_type="视频类", app_name="B站",
    )
    row = create_offer_record(record, operator="移动",
                              offer_id="cmcc_member_data_15gb")
    out = record.write_json(Path("test-results/table_records/smoke_order_stage.json"))

    # 断言字段真的填进去了
    assert row.fields["页面信息.业务信息展示.业务名称"] == "移动·哔哩哔哩会员流量包"
    assert row.metadata["offer_id"] == "cmcc_member_data_15gb"
    assert out.exists()