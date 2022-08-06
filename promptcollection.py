from collections import defaultdict
import dateutil
import dateutil.parser
import requests
import json
import prompts
import re
import utils


def get_auth_headers(discord_auth_token):
    return {'Authorization': f'{discord_auth_token}',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'Content-Type': 'application/json'}


def collect_prompts(max_age, discord_auth_token, limit_per_req=100, print_every=10000):
    all_dream_messages = {}
    successful_dream_ids = []
    successful_dreams = []
    successful_prompt_meta = {}

    last_message_id = None
    auth_headers = get_auth_headers(discord_auth_token)
    completed = 0
    last_date = utils.get_utc_now()
    while utils.get_utc_now() - last_date < max_age:
        try:
            if completed % print_every == 0:
                print(f"Completed {completed} finding {len(successful_dream_ids)} dreams latest at {last_date}")

            req = requests.get(_get_art_gen_url(last_message_id, limit=limit_per_req), headers=auth_headers, timeout=5)
            if req.status_code != 200:
                print("Unsuccessful req")
                break
            messages = json.loads(req.text)
            completed += len(messages)
            last_message_id = messages[-1]["id"]
            for message in messages:
                _parse_message(message, successful_dream_ids, all_dream_messages, successful_prompt_meta)

            last_date = dateutil.parser.parse(messages[-1]["timestamp"])
        except:
            # Shameful hack to avoid losing crawled data if something unexpected happens
            break

    successful_dream_ids = [msg_id for msg_id in successful_dream_ids if msg_id in all_dream_messages]

    # Remove duplicates
    successful_dream_messages = list({all_dream_messages[dream_id] for dream_id in successful_dream_ids})
    usr_dreams = defaultdict(list)
    for dream_id in successful_dream_ids:
        dream_metadata = successful_prompt_meta[dream_id]
        prompt, args = prompts.arg_prompt_split(all_dream_messages[dream_id])
        usr_dreams[dream_metadata["user"]].append(
            prompts.UserPrompt(prompt, args, dream_metadata["url"], dream_metadata["date"]))

    return successful_dream_messages, usr_dreams


def _get_art_gen_url(last_message_id, limit=100):
    url = f"https://discord.com/api/v9/channels/970175047891308544/messages?&limit={limit}"
    if last_message_id:
        url += f"&before={last_message_id}"
    return url


def _parse_message(message, successful_dream_ids, all_dream_messages, successful_prompt_meta):
    if message["content"].startswith('!dream'):
        all_dream_messages[message['id']] = re.sub("!dream ", "", message['content'])

    if message["content"].startswith('Dreamt of "'):
        if "message_reference" not in message:
            return None

        parent_id = message["message_reference"]["message_id"]
        if "mentions" in message:
            user = message["mentions"][0]["username"]
            url = message["attachments"][0]['proxy_url']
            date = dateutil.parser.parse(message["timestamp"])
            date_str = re.sub(r"0*\+00:00", "", str(date))
            successful_prompt_meta[parent_id] = {
                "user": user,
                "date": date_str,
                "url": url,
            }

        successful_dream_ids.append(parent_id)
