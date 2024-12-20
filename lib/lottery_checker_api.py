import sys
import datetime
from mysql.connector import connect, Error
import schedule
import time
from flask import Flask, request, jsonify
import utils.read_config as rc
import threading

app = Flask(__name__)

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
    result ENUM('pending', 'win', 'lose') DEFAULT 'pending',
    user_head_id VARCHAR(255)
);
"""

# 插入用户投注信息
INSERT_BET_QUERY = """
INSERT INTO user_bets (numbers, draw_date, user_head_id)
VALUES (%s, %s, %s)
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
        with connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:

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


@app.route('/submit_numbers', methods=['POST'])
def submit_numbers():
    try:
        # 从 Headers 中获取 user-head-id
        user_head_id = request.headers.get('user_head_id')
        if not user_head_id:
            return jsonify({"error": "缺少必要的 Header: user_head_id"}), 400

        # 从请求体中获取 JSON 数据
        data = request.get_json()
        if not data or 'numbers' not in data or not isinstance(data['numbers'], list):
            return jsonify({"error": "缺少必要的参数: numbers 或格式不正确"}), 400

        all_responses = []
        next_draw_date = get_next_draw_date()

        with connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:

                cursor.execute(CREATE_TABLE_QUERY)

                for number_set in data['numbers']:
                    is_valid, message = validate_double_color_ball_numbers(number_set)
                    if not is_valid:
                        all_responses.append({"error": message})
                        continue

                    cursor.execute(INSERT_BET_QUERY, (number_set, next_draw_date, user_head_id))
                    response_data = {
                        "message": f"您的号码 '{number_set}' 已记录，将在 {next_draw_date} 开奖时进行检查。",
                        "draw_date": str(next_draw_date),
                        "user_head_id": user_head_id
                    }
                    all_responses.append(response_data)

                connection.commit()

        if all_responses and all('error' not in resp for resp in all_responses):
            return jsonify(all_responses), 201
        else:
            return jsonify(all_responses), 400

    except Error as e:
        return jsonify({"error": f"数据库错误: {str(e)}"}), 500

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # 设置每日检查任务
    schedule.every().day.at("18:00").do(job)  # 假设每天18:00检查

    # 启动调度器线程
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.start()

    # 启动 Flask 应用，监听 5001 端口
    app.run(debug=True, port=5001, host='0.0.0.0', use_reloader=False)