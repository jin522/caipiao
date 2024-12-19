import configparser
from os.path import dirname, abspath

def confParser():
    root_dir = dirname(dirname(dirname(abspath(__file__))))
    cf = configparser.ConfigParser()
    cf.read(root_dir+"/conf/config.ini", encoding='utf-8')  # 拼接得到config.ini文件的路径，直接使用
    return cf