import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "configs/app_configs.yaml"

def load_app_configs():
    with open(CONFIG_PATH, encoding= "utf-8") as f:
        return yaml.safe_load(f)

APP_CONFIGS = load_app_configs()

def get_app_config(app_name):
    """按应用名称读取单个应用配置。

    :param app_name: configs/app_configs.yaml 中定义的应用名称（key）
    :return: 该应用对应的配置字典
    :raises ValueError: 配置中不存在该应用名称时抛出
    """
    if app_name not in APP_CONFIGS:
        available = ", ".join(APP_CONFIGS.keys())
        raise ValueError(f"配置中不存在应用 '{app_name}'，可用应用: {available}")
    return APP_CONFIGS[app_name]