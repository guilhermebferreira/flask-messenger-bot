import os
import random
import sys
import json

import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():
    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]  # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    greetings = check_for_greeting(message_text)
                    if(greetings):
                        send_message(sender_id, greetings)

                    if message_text == "seen":
                        action_mark_seen(sender_id)
                    elif message_text == "type":
                        action_typing_on(sender_id)
                    elif message_text == "button":
                        send_buttons(sender_id)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200

def send(data):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    send(data);


def action_typing_on(recipient_id):
    send_action(recipient_id, "typing_on")


def action_typing_off(recipient_id):
    send_action(recipient_id, "typing_off")


def action_mark_seen(recipient_id):
    send_action(recipient_id, "mark_seen")


def send_action(recipient_id, action):
    # actions:
    #   mark_seen
    #   typing_on
    #   typing_off

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action": action
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_buttons(recipient_id):
    buttons = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": "What do you want to do next?",
                    "buttons": [
                        {
                            "type": "web_url",
                            "url": "https://www.messenger.com",
                            "title": "Visit Messenger"
                        }
                    ]
                }
            }
        }
    })
    send(buttons)

def check_for_greeting(user_input):
    GREETING_KEYWORDS = ("hello", "hi", "oi", "ola", "olá", "bom dia", "bom noite", "bom tarde",)

    GREETING_RESPONSES = ["Oi", "Olá :)", "Hey", "Oi!"]

    for words in GREETING_KEYWORDS:
        if words in user_input.lower():
            # if inp.lower().find(words) == 0:
            return random.choice(GREETING_RESPONSES)

    return 0



def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
