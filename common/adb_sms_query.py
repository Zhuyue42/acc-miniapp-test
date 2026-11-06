"""按「指定日期 + 正文关键字」查询手机短信（基于 adb content query）。

设计要点：
- 日期区间交给设备端 ``--where "date>=... AND date<..."`` 过滤，
  条件里只有数字，不会遇到 adb shell 的引号转义问题；
- 关键字在 Python 侧匹配，避免中文关键字经由 adb -> sh 传递时的编码/引号坑；
- 默认查 ``content://sms`` 根 URI（含第三方端口推送短信），
  也可用 ``--uri content://sms/inbox`` 只查收件箱。

命令行用法：
    # 查今天、正文包含「验证码」的短信
    python -m common.adb_sms_query -k 验证码

    # 查 2026-10-22 当天、正文包含「验证码」的短信
    python -m common.adb_sms_query -d 2026-10-22 -k 验证码

    # 查 2026-10-22 14:00~15:00，正文同时包含「验证码」和「元」
    python -m common.adb_sms_query -d 2026-10-22 --start-time 14:00 --end-time 15:00 -k 验证码 -k 元

    # 不限日期，查包含任一关键字（验证码/校验码），输出前 5 条 JSON
    python -m common.adb_sms_query --all-days -k 验证码 -k 校验码 --match-any -n 5 --json

代码里调用：
    from common.adb_sms_query import query_sms_by_date_and_keyword

    rows = query_sms_by_date_and_keyword("验证码", date="2026-10-22")
    latest = rows[0] if rows else None
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from common.Logger import logger

ADB = ["adb"]  # 多设备改为 ["adb", "-s", "你的serial"]

DEFAULT_URI = "content://sms"

# content query 输出形如：
#   Row: 0 _id=3241, address=10690123, body=xxx, date=1758965321000
# 正文可能含换行，所以用 DOTALL + 前瞻定位下一条 Row。
_ROW_RE = re.compile(
    r"Row:\s+\d+\s+_id=(\d+),\s*address=([^,]*),\s*body=(.*?),\s*date=(\d+)"
    r"(?=\s*(?:Row:|\Z))",
    re.DOTALL,
)

_DAY_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d")


# ---------------------------------------------------------------- 时间解析


def _parse_day(day: str) -> datetime:
    """解析日期字符串为当天 00:00:00 的 datetime。"""
    text = day.strip()
    for fmt in _DAY_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"日期格式不支持: {day}（应形如 2026-10-22）")


def _parse_hhmm(text: str, base: datetime) -> datetime:
    """把 HH:MM[:SS] 落到 base 那一天的对应时刻。"""
    raw = text.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            t = datetime.strptime(raw, fmt)
            return base.replace(hour=t.hour, minute=t.minute,
                                second=t.second, microsecond=0)
        except ValueError:
            continue
    raise ValueError(f"时间格式不支持: {text}（应形如 14:00 或 14:00:30）")


def resolve_time_range(
    date: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> tuple[int, int]:
    """把「日期 + 起止时间」换算为毫秒时间戳区间 ``[start_ms, end_ms)``。

    - 不给 date 时按今天算；
    - 不给 end_time 时区间结束为次日 00:00:00；
    - end_time 小于 start_time 时视为跨天（如 23:00~01:00）。

    注意：这里按 **本机时区** 换算。若手机时区与本机不一致，
    请按手机当地日期传 date。
    """
    day = _parse_day(date) if date else datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0)

    start = _parse_hhmm(start_time, day) if start_time else day
    end = _parse_hhmm(end_time, day) if end_time else day + timedelta(days=1)
    if end <= start:
        end += timedelta(days=1)

    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


# ---------------------------------------------------------------- 查询


def _normalize_keywords(keyword: str | list[str] | None) -> list[str]:
    if not keyword:
        return []
    items = [keyword] if isinstance(keyword, str) else list(keyword)
    return [k for k in (str(item).strip() for item in items) if k]


def query_sms(
    keyword: str | list[str] | None = None,
    start_ms: int | None = None,
    end_ms: int | None = None,
    uri: str = DEFAULT_URI,
    match_any: bool = False,
    ignore_case: bool = True,
    adb: list[str] | None = None,
    timeout: int = 20,
) -> list[dict]:
    """查询短信，返回按 date 倒序（新->旧）的字典列表。

    :param keyword: 正文关键字；传入列表时默认要求全部命中
    :param start_ms: 起始时间（毫秒，含）
    :param end_ms: 结束时间（毫秒，不含）
    :param uri: content URI，默认 content://sms
    :param match_any: 多个关键字命中任一即可
    :param ignore_case: 关键字匹配是否忽略大小写
    """
    where: list[str] = []
    if start_ms is not None:
        where.append(f"date>={start_ms}")
    if end_ms is not None:
        where.append(f"date<{end_ms}")

    cmd = (
        f"content query --uri {uri} "
        "--projection _id:address:body:date "
    )
    if where:
        # 条件内容只有数字与 AND，用单引号包住交给设备端 sh 是安全的
        cmd += f"--where '{' AND '.join(where)}' "
    cmd += "--sort 'date DESC'"

    r = subprocess.run(
        [*(adb or ADB), "shell", cmd],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError(f"adb 执行失败: {r.stderr.strip()}")

    rows: list[dict] = []
    for m in _ROW_RE.finditer(r.stdout):
        _id, address, body, date_ms = m.groups()
        ms = int(date_ms)
        rows.append({
            "id": int(_id),
            "address": address.strip(),
            "body": body.strip(),
            "date": ms,
            "time": datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M:%S"),
        })

    keywords = _normalize_keywords(keyword)
    if keywords:
        needles = [k.casefold() for k in keywords] if ignore_case else keywords

        def hit(body: str) -> bool:
            text = body.casefold() if ignore_case else body
            checks = [n in text for n in needles]
            return any(checks) if match_any else all(checks)

        rows = [row for row in rows if hit(row["body"])]

    logger.info(
        "短信查询完成: 关键字=%s 区间=[%s, %s) 命中 %d 条",
        keywords or "-",
        _ms_to_text(start_ms),
        _ms_to_text(end_ms),
        len(rows),
    )
    return rows


def _ms_to_text(ms: int | None) -> str:
    if ms is None:
        return "-"
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def query_sms_by_date_and_keyword(
    keyword: str | list[str] | None = None,
    date: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    all_days: bool = False,
    uri: str = DEFAULT_URI,
    match_any: bool = False,
    ignore_case: bool = True,
    serial: str | None = None,
    **kwargs,
) -> list[dict]:
    """按日期（可再到时分）+ 关键字查询短信的便捷入口。

    :param keyword: 正文关键字，可为单个字符串或列表
    :param date: 日期，形如 "2026-10-22"；不传默认今天
    :param start_time: 开始时间 "14:00"（含）
    :param end_time: 结束时间 "15:00"（不含），小于开始时间视为跨天
    :param all_days: True 时不限制日期，全量查询
    :param serial: 多设备时的 adb serial
    """
    start_ms = end_ms = None
    if not all_days:
        start_ms, end_ms = resolve_time_range(date, start_time, end_time)

    adb = ["adb", "-s", serial] if serial else None
    return query_sms(
        keyword=keyword,
        start_ms=start_ms,
        end_ms=end_ms,
        uri=uri,
        match_any=match_any,
        ignore_case=ignore_case,
        adb=adb,
        **kwargs,
    )


# ---------------------------------------------------------------- 输出


def format_sms_list(rows: list[dict]) -> str:
    if not rows:
        return "未找到匹配的短信"
    lines = [f"共匹配 {len(rows)} 条短信（按时间倒序）：", "=" * 60]
    for row in rows:
        lines.append(f"[{row['time']}] 发件人: {row['address']}  (id={row['id']})")
        lines.append(row["body"])
        lines.append("-" * 60)
    return "\n".join(lines)


def save_sms(rows: list[dict],
             output_dir: str | Path = "test-results/sms_export",
             name_prefix: str = "query_sms") -> Path:
    """把查询结果写入文本文件（时间正序，方便阅读），返回文件路径。"""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name_prefix}_{datetime.now():%Y%m%d_%H%M%S}.txt"

    lines = [
        f"导出时间: {datetime.now().isoformat(timespec='seconds')}",
        f"短信条数: {len(rows)}",
        "=" * 60,
    ]
    for row in sorted(rows, key=lambda item: item["date"]):
        lines.append(f"[{row['time']}] 发件人: {row['address']}")
        lines.append(row["body"])
        lines.append("-" * 60)

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("已写入查询结果 %d 条 -> %s", len(rows), out_path)
    return out_path


# ---------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="按指定日期 + 正文关键字查询手机短信（adb content query）")
    parser.add_argument("-d", "--date",
                        help="日期，形如 2026-10-22；不填默认今天")
    parser.add_argument("--start-time", help="开始时间 HH:MM（含）")
    parser.add_argument("--end-time", help="结束时间 HH:MM（不含），小于开始时间视为跨天")
    parser.add_argument("--all-days", action="store_true", help="不限制日期，全量查询")
    parser.add_argument("-k", "--keyword", action="append",
                        help="正文关键字，可重复；不加 --match-any 时要求全部命中")
    parser.add_argument("--match-any", action="store_true", help="多个关键字命中任一即可")
    parser.add_argument("-c", "--case-sensitive", action="store_true",
                        help="关键字区分大小写（默认忽略）")
    parser.add_argument("-u", "--uri", default=DEFAULT_URI,
                        help=f"content URI，默认 {DEFAULT_URI}；可用 content://sms/inbox")
    parser.add_argument("-s", "--serial", help="adb 设备序列号（多设备时必填）")
    parser.add_argument("-n", "--limit", type=int, default=0,
                        help="最多输出条数，0 表示不限")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    parser.add_argument("--save", action="store_true",
                        help="同时写入 test-results/sms_export")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    rows = query_sms_by_date_and_keyword(
        keyword=args.keyword,
        date=args.date,
        start_time=args.start_time,
        end_time=args.end_time,
        all_days=args.all_days,
        uri=args.uri,
        match_any=args.match_any,
        ignore_case=not args.case_sensitive,
        serial=args.serial,
    )
    if args.limit > 0:
        rows = rows[:args.limit]

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(format_sms_list(rows))

    if args.save:
        print(f"\n已保存: {save_sms(rows)}")

    return 0 if rows else 1


if __name__ == "__main__":
    # Windows 控制台默认 GBK，避免中文正文/关键字输出报错
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
