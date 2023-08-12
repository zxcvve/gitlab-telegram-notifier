import re
import os
from fastapi import FastAPI, Request
import requests

app = FastAPI()

TELEGRAM_API_TOKEN = os.environ["TELEGRAM_API_TOKEN"]
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']


def escape_markdown(text, version=2, entity_type=None):
    if int(version) == 1:
        escape_chars = r'_*`['
    elif int(version) == 2:
        if entity_type in ['pre', 'code']:
            escape_chars = r'\`'
        elif entity_type == 'text_link':
            escape_chars = r'\)'
        else:
            escape_chars = r'_*[]()~`>#+-=|{}.!'
    else:
        raise ValueError('Markdown version must be either 1 or 2!')

    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def send_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage"

    params = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': escape_markdown(message),
        'parse_mode': 'MarkdownV2'
    }
    response = requests.post(url, params=params)
    if response.status_code != 200:
        print("Failed to send Telegram notification.")


def merge_event_handler(data):
    author = data['user']['name']
    merge_request_title = data["object_attributes"]["title"]
    source_branch = data["object_attributes"]["source_branch"]
    target_branch = data["object_attributes"]["target_branch"]
    url = data["object_attributes"]['url']

    match data['object_attributes']['action']:
        case 'open':
            send_notification(f"Merge Request Created: {merge_request_title}\n"
                              f"Author: {author}\n"
                              f"URL: {url}\n"
                              f"Source Branch: {source_branch}\n"
                              f"Target Branch: {target_branch}")

        case 'merge':
            send_notification(f"Merge Request Accepted: {merge_request_title}\n"
                              f"URL: {url}\n"
                              f"Source Branch: {source_branch}\n"
                              f"Target Branch: {target_branch}")
        case 'close':
            send_notification(f"Merge Request Closed: {merge_request_title}\n"
                              f"URL: {url}")


def push_event_handler(data):
    branch_name = data["ref"].split("/")[-1]
    event_author = data['user_name']
    empty_commit_hash = "0000000000000000000000000000000000000000"

    if data['after'] == empty_commit_hash:
        send_notification(f"Branch Deleted\n"
                          f"Author: {event_author}\n"
                          f"Branch: {branch_name}")
        return

    if data['before'] == empty_commit_hash:
        send_notification(f"Branch Created\n"
                          f"Author: {event_author}\n"
                          f"Branch: {branch_name}")
        return


def pipeline_event_handler(data):
    pipeline_id = data["object_attributes"]["ref"]
    status = data["object_attributes"]["status"]
    send_notification(f"Pipeline '{pipeline_id}' status: {status}!")


@app.post("/")
async def gitlab_webhook(request: Request):
    event_json = await request.json()
    object_kind = event_json["object_kind"]
    match object_kind:
        case 'merge_request':
            merge_event_handler(event_json)
        case 'push':
            push_event_handler(event_json)
        case 'pipeline':
            pipeline_event_handler(event_json)
