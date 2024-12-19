import os

import requests
import time
import json
import utils.fake_header as fake_header
import utils.read_config as rc
import utils.service_msg_to_admin as admin
from datetime import datetime
from utils.log_config import getLog
import utils.text_template as text_template

"""
    crontab定时任务命令：
    30 21 * * 0,2,4 sh /path/to/your/command
    每周二、四、日晚9：30触发脚本执行一次
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
    data_file = rc.confParser().get("shuangseqiu", "DATA_FILE_NAME")
    if not os.path.exists(data_file):
        open(data_file, 'w').close()
    with open(data_file, 'r', encoding='utf_8_sig') as rf:
        before_period = rf.read()
    # 日期比较
    date_format = "%Y-%m-%d"
    current_period_date = datetime.strptime(current_period, date_format)
    if "" == before_period:
        before_period = "1999-01-01"
    before_period_date = datetime.strptime(before_period.strip(), date_format)

    if before_period_date < current_period_date:
        with open(data_file, 'w', encoding='utf_8_sig') as wf:
            wf.write(current_period)
            LOG.info(f'双色球最新期号[{current_period}]已写入本地文件:{data_file}')
        return True
    else:
        LOG.info(f'本期未开奖，双色球上期号为[{before_period}]')
        return False


# 推送消息
def send_msg(code, msg):
    push_url = rc.confParser().get("wxpusher", "PUSH_URL")
    app_token = rc.confParser().get("shuangseqiu", "APP_TOKEN")
    topic_ids_str = rc.confParser().get("shuangseqiu", "TOPIC_IDS")
    topicids = json.loads(topic_ids_str)

    json_body = json.loads(text_template.WXPUSHER_POST_BODY_TEMPLATE)
    json_body['appToken'] = app_token
    json_body['content'] = msg
    json_body['summary'] = "[{}期]双色球已开奖".format(code)
    json_body['topicIds'] = topicids
    requests.post(url=push_url, json=json_body, verify=False)


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
    if check_latest_period(date):
        send_msg(code, info)


def main():
    counter = 0
    while counter < 10:
        print(counter)
        latest_period_info = get_latest_prize_info()
        code, date, info = analyze_result(latest_period_info)
        if check_latest_period(date):
            send_msg(code, info)
            return
        # 任务sleep 10分钟后再次执行
        time.sleep(60 * 10)
        counter += 1

    LOG.info(f'双色球最新数据爬取次数为：{counter}')
    # 同步失败告警
    admin.send_msg("双色球开奖信息抓取失败", "双色球今日开奖号码通知任务失败， 请检查服务是否正常")
