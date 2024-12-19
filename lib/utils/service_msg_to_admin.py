import requests
import json
import utils.read_config as rc
import utils.text_template as text_template

def send_msg(summary, msg):
    push_url = rc.confParser().get("wxpusher", "PUSH_URL")
    app_token = rc.confParser().get("admin", "APP_TOKEN")
    topic_ids_str = rc.confParser().get("admin", "TOPIC_IDS")
    topicids = json.loads(topic_ids_str)

    json_body = json.loads(text_template.TASK_EXCEPTION_WARNNING)
    json_body['appToken'] = app_token
    json_body['content'] = msg
    json_body['summary'] = summary
    json_body['topicIds'] = topicids
    requests.post(url=push_url, json=json_body, verify=False)