import sys
import datetime
from mysql.connector import connect, Error
import schedule
import time
import requests
import utils.read_config as rc

# MySQL数据库配置
host = rc.confParser().get("mysql", "HOST")
user = rc.confParser().get("mysql", "USER")
password = rc.confParser().get("mysql", "PASSWORD")
database = rc.confParser().get("mysql", "DATABASE")

DB_CONFIG = {
    'host': host,
    'user': user,
    'password': password,
    'database': database
}


# 创建表结构（如果不存在）
CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS user_bets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numbers VARCHAR(20),
    draw_date DATE,
    result ENUM('pending', 'win', 'lose') DEFAULT 'pending'
);
"""

# 插入用户投注信息
INSERT_BET_QUERY = """
INSERT INTO user_bets (numbers, draw_date)
VALUES (%s, %s)
"""

# 更新中奖结果
UPDATE_RESULT_QUERY = """
UPDATE user_bets SET result = %s WHERE id = %s
"""


# 获取下一次开奖日期
def get_next_draw_date():
    today = datetime.date.today()
    # 双色球开奖时间：周二、周四、周日
    days_of_week = [1, 3, 6]  # 星期一、三、六分别是0, 2, 5
    next_draw_day = None

    for day in days_of_week:
        delta_days = (day - today.weekday() + 7) % 7
        if delta_days == 0:
            delta_days = 7  # 如果今天开奖，则取下一周的相同日子
        next_draw_date = today + datetime.timedelta(days=delta_days)
        if not next_draw_day or next_draw_date < next_draw_day:
            next_draw_day = next_draw_date

    return next_draw_day


# 检查是否中奖（假设有一个API可以查询最新一期的中奖号码）
def check_if_win(bet_id, bet_numbers):
    # 这里应该调用真实的彩票查询API来获取最新的中奖号码
    # 假设我们已经有了这些数据
    latest_winning_numbers = "1 3 16 22 23 30 3"  # 示例数据

    if sorted(bet_numbers.split()) == sorted(latest_winning_numbers.split()):
        return True
    else:
        return False


# 安排每天检查是否开奖并更新结果
def job():
    try:
        connection = connect(**DB_CONFIG)
        cursor = connection.cursor()

        cursor.execute("SELECT id, numbers FROM user_bets WHERE result = 'pending'")
        bets = cursor.fetchall()

        for bet in bets:
            bet_id, bet_numbers = bet
            if check_if_win(bet_id, bet_numbers):
                update_result(cursor, 'win', bet_id)
            else:
                update_result(cursor, 'lose', bet_id)

        connection.commit()
    except Error as e:
        print(f"The error '{e}' occurred")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def update_result(cursor, result, bet_id):
    cursor.execute(UPDATE_RESULT_QUERY, (result, bet_id))


# 验证双色球号码是否合法
def validate_double_color_ball_numbers(numbers_str):
    try:
        numbers = list(map(int, numbers_str.split()))
        if len(numbers) != 7:
            return False, "必须输入7个数字"

        red_balls = sorted(numbers[:6])
        blue_ball = numbers[6]

        if len(set(red_balls)) != 6 or any(not (1 <= n <= 33) for n in red_balls):
            return False, "前6个数字（红球）应在1到33之间且互不相同"

        if not (1 <= blue_ball <= 16):
            return False, "第7个数字（蓝球）应在1到16之间"

        return True, "号码合法"
    except ValueError:
        return False, "输入包含非整数字符"

def main():
    if len(sys.argv) != 2:
        print("Usage: python lottery_checker.py '1 3 16 22 23 30 3'")
        return

    user_numbers = sys.argv[1]

    is_valid, message = validate_double_color_ball_numbers(user_numbers)
    if not is_valid:
        print(message)
        return

    try:
        connection = connect(**DB_CONFIG)
        cursor = connection.cursor()

        cursor.execute(CREATE_TABLE_QUERY)

        next_draw_date = get_next_draw_date()
        cursor.execute(INSERT_BET_QUERY, (user_numbers, next_draw_date))
        connection.commit()

        print(f"Your bet '{user_numbers}' has been recorded for the draw on {next_draw_date}.")

        # 设置每日检查任务
        schedule.every().day.at("18:00").do(job)  # 假设每天18:00检查

        while True:
            schedule.run_pending()
            time.sleep(60)

    except Error as e:
        print(f"The error '{e}' occurred")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    main()