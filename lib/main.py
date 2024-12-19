# -*- coding: utf-8 -*-
import argparse
import shuangseqiu
from utils.log_config import getLog
from utils.read_config import confParser

LOG = getLog(confParser().get("base", "LOG_FILE_NAME"))

def exec_script(args):
    save_where = args.param1
    LOG.info(f'脚本操作输入参数命令为：{save_where}')
    if "shuangseqiu" == save_where:
        shuangseqiu.main()
    elif "daletou" == save_where:
        # initfile.main()
        print("大乐透功能暂未开发")
    elif "all" == save_where:
        shuangseqiu.main()
        # initfile.main()
    else:
        print("输入参数有误，选择如下参数：")
        print("shuangseqiu：双色球")
        print("daletou：大乐透")
        print("all：全部类型")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="get caipiao prize code from official website")
    parser.add_argument("param1", help="caipiao type: 1.shuangseqiu, 2.daletou, 3.all")
    args = parser.parse_args()
    exec_script(args)
