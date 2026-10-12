import re
import subprocess
from common.Logger import logger

ADB = ["adb"]          # 多设备可换成 ["adb", "-s", "你的serial"]

def get_latest_sms() -> dict | None:
    cmd = (
        "content query --uri content://sms/inbox "
        "--projection _id:address:body:date "
        "--sort 'date DESC'"
        )
    r = subprocess.run(
        [*ADB, "shell", cmd],          # cmd 作为「一个参数」传给 adb，adb 再交给设备 sh
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=15,
        )
    if r.returncode != 0:
        raise RuntimeError(f"adb 执行失败: {r.stderr.strip()}")

    first = next((ln for ln in r.stdout.splitlines() if ln.startswith("Row: 0")), None)
    if not first:
        return None

    m = re.match(r"Row: 0 _id=(\d+), address=([^,]*), body=(.*), date=(\d+)\s*$", first)
    if not m:
        return None
    _id, address, body, date_ms = m.groups()
    sms_dic = {"id": int(_id), "address": address, "body": body, "date": int(date_ms)}
    logger.info(f"获取到最新短信: {sms_dic}")
    #print(f"获取到最新短信: {sms_dic}")
    return sms_dic


if __name__ == "__main__":
    sms = get_latest_sms()
    print(sms)