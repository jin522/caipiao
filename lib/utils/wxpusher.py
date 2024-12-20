import requests
import json
import utils.read_config as rc
import utils.text_template as text_template

def send_msg(config_group, summary, content):
    push_url = rc.confParser().get("wxpusher", "PUSH_URL")
    app_token = rc.confParser().get(config_group, "APP_TOKEN")
    topic_ids_str = rc.confParser().get(config_group, "TOPIC_IDS")
    topicids = json.loads(topic_ids_str)

    json_body = json.loads(text_template.TASK_EXCEPTION_WARNNING)
    json_body['appToken'] = app_token
    json_body['content'] = content
    json_body['summary'] = summary
    json_body['topicIds'] = topicids
    requests.post(url=push_url, json=json_body, verify=False)