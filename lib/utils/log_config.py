import logging as LOG


def getLog(log_file_name):
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
    fp = LOG.FileHandler(str(log_file_name), encoding='utf-8')
    LOG.basicConfig(level=LOG.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT, handlers=[fp])
    return LOG