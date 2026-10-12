import subprocess
import time
from pathlib import Path
from common.Logger import logger

ADB = ["adb"]  # 多设备可换成 ["adb", "-s", "你的serial"]
DEVICE_DIR = "/sdcard/recordings"

class ScreenRecorder:
    def __init__(self, name: str, output_dir: str | Path = "recordings",
                 time_limit: int = 180):
        self.name = name
        self.output_dir = Path(output_dir)
        self.time_limit = time_limit
        self.device_path = f"{DEVICE_DIR}/{name}_{int(time.time())}.mp4"
        self._proc = None

    def start(self):
        subprocess.run([*ADB, "shell", f"mkdir -p {DEVICE_DIR}"], check=False)
        self._proc = subprocess.Popen(
            [*ADB, "shell", "screenrecord",
             "--time-limit", str(self.time_limit), self.device_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        logger.info(f"开始录屏: {self.device_path}")

    def stop(self) -> Path | None:
        if self._proc is None:
            return None
        # 发 SIGINT 让设备端 screenrecord 正常收尾，保证 mp4 索引完整
        subprocess.run([*ADB, "shell", "pkill", "-INT", "screenrecord"],
                       capture_output=True)
        try:
            self._proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._proc.kill()  # 兜底：只杀本地 adb 客户端
        self._proc = None

        self.output_dir.mkdir(parents=True, exist_ok=True)
        local_path = self.output_dir / Path(self.device_path).name
        r = subprocess.run([*ADB, "pull", self.device_path, str(local_path)],
                           capture_output=True, text=True, timeout=60)
        subprocess.run([*ADB, "shell", "rm", "-f", self.device_path])
        if r.returncode != 0:
            logger.error(f"录屏拉取失败: {r.stderr.strip()}")
            return None
        logger.info(f"录屏已保存: {local_path}")
        return local_path

# if __name__ == "__main__":
#     # 冒烟测试：录 10 秒，验证 start/stop/pull 全链路
#     recorder = ScreenRecorder(name="smoke_test", time_limit=60)
#     recorder.start()

#     # 模拟测试过程中的一些操作：让屏幕有画面变化，方便肉眼确认
#     subprocess.run([*ADB, "shell", "input", "keyevent", "KEYCODE_HOME"])
#     time.sleep(5)
#     subprocess.run([*ADB, "shell", "input", "keyevent", "KEYCODE_APP_SWITCH"])
#     time.sleep(5)

#     path = recorder.stop()
#     print(f"录屏文件: {path}")