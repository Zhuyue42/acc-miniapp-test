"""导出收件箱中最近 N 分钟收到的短信到文本文件，用于人工流程留档。"""

import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

from common.Logger import logger

ADB = ["adb"]  # 多设备改为 ["adb", "-s", "你的serial"]

_ROW_RE = re.compile(
    r"Row:\s+\d+\s+_id=(\d+),\s*address=([^,]*),\s*body=(.*?),\s*date=(\d+)"
    r"(?=\s*(?:Row:|\Z))",
    re.DOTALL,
)

def query_inbox(adb: list[str] | None = None) -> list[dict]:
    """查询全部可见短信（含端口推送类），按 date 倒序返回。

    使用 content://sms 根 URI 而非 content://sms/inbox：
    第三方端口推送的权益短信（如 10681457000000019208）不在 inbox 文件夹，
    但出现在根 URI 的受限视图里。
    """
    cmd = ("content query --uri content://sms "
           "--projection _id:address:body:date "
           "--sort 'date DESC'")
    r = subprocess.run([*(adb or ADB), "shell", cmd], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"adb 执行失败: {r.stderr.strip()}")

    result = []
    for m in _ROW_RE.finditer(r.stdout):
        _id, address, body, date_ms = m.groups()
        result.append({"id": int(_id), "address": address,
                       "body": body.strip(), "date": int(date_ms)})
    return result


def export_recent_sms(minutes: int = 5,
                      output_dir: str | Path = "test-results/sms_export",
                      name_prefix: str = "recent_sms") -> Path:
    """把最近 minutes 分钟内收到的短信写入文本文件，返回文件路径。"""
    cutoff_ms = int(time.time() * 1000) - minutes * 60 * 1000
    recent = [s for s in query_inbox() if s["date"] >= cutoff_ms]
    recent.sort(key=lambda s: s["date"])  # 按时间正序写入，方便阅读

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{name_prefix}_{timestamp}.txt"

    lines = [
        f"导出时间: {datetime.now().isoformat(timespec='seconds')}",
        f"时间窗口: 最近 {minutes} 分钟",
        f"短信条数: {len(recent)}",
        "=" * 60,
    ]
    for sms in recent:
        receive_time = datetime.fromtimestamp(sms["date"] / 1000)
        lines.append(f"[{receive_time:%Y-%m-%d %H:%M:%S}] 发件人: {sms['address']}")
        lines.append(sms["body"])
        lines.append("-" * 60)

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info(f"已导出最近 {minutes} 分钟短信 {len(recent)} 条 -> {out_path}")
    return out_path

def export_latest_sms(count: int = 10,
                      output_dir: str | Path = "test-results/sms_export",
                      name_prefix: str = "latest_sms") -> Path:
    """导出收件箱最新的 count 条短信到文本文件，返回文件路径。"""
    latest = query_inbox()[:count]          # query_inbox 已按 date 倒序
    latest.sort(key=lambda s: s["date"])    # 写入时改为正序，方便阅读

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{name_prefix}_{timestamp}.txt"

    lines = [
        f"导出时间: {datetime.now().isoformat(timespec='seconds')}",
        f"导出条数: 最新 {len(latest)} 条",
        "=" * 60,
    ]
    for sms in latest:
        receive_time = datetime.fromtimestamp(sms["date"] / 1000)
        lines.append(f"[{receive_time:%Y-%m-%d %H:%M:%S}] 发件人: {sms['address']}")
        lines.append(sms["body"])
        lines.append("-" * 60)

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info(f"已导出最新短信 {len(latest)} 条 -> {out_path}")
    return out_path


if __name__ == "__main__":
    path = export_latest_sms(count=5)
    print(path.read_text(encoding="utf-8"))