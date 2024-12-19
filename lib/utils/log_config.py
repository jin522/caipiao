import logging as LOG
from pathlib import Path

def getLog(log_file_name):
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
    file_path = Path(log_file_name)
    if not file_path.exists():
        # 文件不存在，则创建文件（包括目录）
        file_path.parent.mkdir(parents=True, exist_ok=True)  # 创建目录（如果不存在）
        file_path.touch()  # 创建空文件
    fp = LOG.FileHandler(str(log_file_name), encoding='utf-8')
    LOG.basicConfig(level=LOG.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT, handlers=[fp])
    return LOG