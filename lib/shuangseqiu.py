import requests
import json
import utils.fake_header as fake_header
import utils.read_config as rc
import utils.wxpusher as wxpusher
from datetime import datetime
from utils.log_config import getLog
import utils.text_template as text_template

"""
    crontab定时任务命令：
    30 21 * * * sh /path/to/your/command
    每晚9：30触发脚本执行一次
"""

LOG = getLog(rc.confParser().get("base", "LOG_FILE_NAME"))


# 获取最新一期开奖结果
def get_latest_prize_info():
    url = rc.confParser().get("shuangseqiu", "WEB")
    json_str = requests.get(url, headers=fake_header.get_random_header()).text
    json_obj = json.loads(json_str)

    state_code = json_obj['state']
    if 0 == state_code:
        # 最新一期号码
        latest_period_info = json_obj['result'][0]
        return latest_period_info


# 检查最新一期是否已经开奖
def check_latest_period(current_period):
    # 日期比较
    date_format = "%Y-%m-%d"
    current_period_date = datetime.strptime(current_period, date_format).date()

    today_date = datetime.now().date()

    if today_date < current_period_date:
        return True
    else:
        LOG.info(f'本期未开奖，双色球上期号为[{current_period}]')
        return False


# 解析双色球消息体并拼装自定义消息体
def analyze_result(latest_period_info):
    name = rc.confParser().get("shuangseqiu", "NAME")
    code = latest_period_info['code']
    date = latest_period_info['date'][:-3]
    week = latest_period_info['week']
    red = latest_period_info['red']
    blue = latest_period_info['blue']
    nums = "<b><font color=\"green\">{}</font>,<font color=\"red\">{}</font></b>".format(red, blue)

    info = text_template.SHUANGSEQIU_MSG_TEMPLATE.format(name, code, date, week, nums)
    return code, date, info


def main():
    counter = 0
    while counter < 6:
        latest_period_info = get_latest_prize_info()
        code, date, info = analyze_result(latest_period_info)
        if check_latest_period(date):
            wxpusher.send_msg(code, info)
            return
        # 任务sleep 10分钟后再次执行
        # time.sleep(60 * 10)
        counter += 1

    LOG.info(f'双色球最新数据爬取次数为：{counter}')
    # 同步失败告警
    wxpusher.send_msg("admin", "双色球开奖信息抓取失败", "双色球今日开奖号码通知任务失败， 请检查服务是否正常")
