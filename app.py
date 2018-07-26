#all the imports that we need
from flask import Flask, request
from fbmq import Page, Template
import json
import requests
from flask_sqlalchemy import SQLAlchemy
import os
#you need praw libarary to access reddit
import praw
import emoji


""" Must create database for this work
    from app import db
    """
#connects the postgesql to python
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

#this is the reddit developer acc
reddit = praw.Reddit(client_id = 'uEtRe1qjFz2Y8g', client_secret = 'NpQhElij2IbzBGEnm_DFZvhe98U', user_agent = 'my user agent')

#This needs to be filled with the PAGE ACCESS TOKEN

PAT= 'EAANn6QXoef8BAOuwvsWvRSQ6kUSHGyeAr7ORrc9AU7ChJDEZB3K74lYqFSIO823oAOozrbyzCIPLjQ9r5oagOdVp2KfaSfZBVfTO8GhcvJyHfaaj29z7mIGyye3ror62SBA1JDwbp6he9w1deS6eOZAjnNLJyUMFNxEfHiHrqWb78hays9l'
page = Page(PAT)

#this is the welcome screen before you get started
page.greeting("Hi! I'm Todd! If you want to laugh or just need someone to make you happy, I'm the right person to talk to!")


#this will show the get started button
page.show_starting_button("START_PAYLOAD")
@page.callback(['START_PAYLOAD'])
def start_callback(payload, event):
  print("Let's start!")

page.show_persistent_menu([Template.ButtonPostBack('HELP', 'MENU_PAYLOAD/1'),
                           Template.ButtonPostBack('HOTLINE', 'MENU_PAYLOAD/2')])

@page.callback(['MENU_PAYLOAD/(.+)'])
def click_persistent_menu(payload, event):
  click_menu = payload.split('/')[1]
  print("you clicked %s menu" % click_menu)



quick_replies_list = [{
                      "content_type":"text",
                      "title": emoji.emojize("Meme :thumbs_up:"),
                      "image_url": "https://emojipedia-us.s3.amazonaws.com/thumbs/144/facebook/65/grinning-face-with-smiling-eyes_1f601.png",
                      "payload": "meme",
                      },
                      {
                      "content_type":"text",
                      "title": emoji.emojize("Motivation :satisfied:", use_aliases=True),
                      "image_url": "https://emojipedia-us.s3.amazonaws.com/thumbs/240/facebook/138/thinking-face_1f914.png",
                      "payload": "motivation",
                      },
                      {
                      "content_type":"text",
                      "title": emoji.emojize("Shower Thought :confounded:", use_aliases=True),
                      "image_url": "https://emojipedia-us.s3.amazonaws.com/thumbs/144/facebook/65/astonished-face_1f632.png",
                      "payload": "Shower_Thought",
                      },
                      {
                      "content_type":"text",
                      "title": emoji.emojize("Joke :smirk:", use_aliases=True),
                      "image_url": "https://emojipedia-us.s3.amazonaws.com/thumbs/144/facebook/65/face-with-tears-of-joy_1f602.png",
                      "payload":"joke",
                      },
                      {
                      "content_type":"text",
                      "title": emoji.emojize("facepalm :bow:", use_aliases=True),
                      "image_url": "https://emojipedia-us.s3.amazonaws.com/thumbs/240/facebook/138/shocked-face-with-exploding-head_1f92f.png",
                      "payload":"facepalm",
                      }
                      ]



"""A decorator that is used to register a view function for a given URL rule. This does the same thing as add_url_rule() but is intended for decorator usage:"""
#requests is a python library
#GET requests are used for authentiation
@app.route('/', methods=['GET'])
def handle_verification():
    print "Handling Verification."
    if request.args.get('hub.verify_token') == 'im_sad':
        print "Verification successful!"
        return request.args.get('hub.challenge')
    else:
        print "Verification failed!"
        return 'Error, wrong validation token'

#POST request send users the data
@app.route('/', methods=['POST'])
def handle_messages():
    print "Handling Messages"
    payload = request.get_data()
    print payload
    webhook_type = get_type_from_payload(payload)
    if webhook_type == 'postback':
        print "This is a postback"
        for sender_id, postback_payload in postback_events(payload):
            if  postback_payload == 'START_PAYLOAD':
                print "This is a get started postback"
                send_message(PAT, sender_id, "greeting")
            if postback_payload == 'MENU_PAYLOAD/1':
                print "This is the help postback"
                send_message(PAT, sender_id, "help")
            if postback_payload == 'MENU_PAYLOAD/2':
                print "This is the hotline postback"
                send_message(PAT, sender_id, "hotline")
    elif webhook_type == 'message':
        for sender, message in messaging_events(payload):
            print "Incoming from %s: %s" % (sender, message)
            print "This is the message " + message
            send_message(PAT, sender, message)
    return "ok"

def messaging_events(payload):
    """Generate tuples of (sender_id, message_text) from the
        provided payload.
        """
    data = json.loads(payload)
    messaging_events = data["entry"][0]["messaging"]
    for event in messaging_events:
        if "message" in event and "text" in event["message"]:
            yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')
        else:
            yield event["sender"]["id"], "I can't echo this"

def send_message(token, recipient, text):
    """send the message text to recipient with id recipient"""
    if "meme" in text.lower():
        subreddit_name = "memes"
    elif "shower" in text.lower():
        subreddit_name = "Showerthoughts"
    elif "joke" in text.lower():
        subreddit_name = "Jokes"
    elif "motivation" in text.lower():
        subreddit_name = "GetMotivated"
    elif "facepalm" in text.lower():
        subreddit_name = "facepalm"
    #elif "aww" in text.lower():
    #    subreddit_name = "Aww"
    elif "hotline" in text.lower():
        subreddit_name = "hotline"
    else:
        subreddit_name = ""
    
    page.typing_on(recipient)
    checkSubReddit(token, recipient, subreddit_name)
    page.typing_off(recipient)



# Get type of webhook
# Current support: message, postback
# Reference: https://developers.facebook.com/docs/messenger-platform/webhook-reference/message-received
def get_type_from_payload(payload):
    data = json.loads(payload)
    if "postback" in data["entry"][0]["messaging"][0]:
        return "postback"

    elif "message" in data["entry"][0]["messaging"][0]:
        return "message"


def postback_events(payload):
    data = json.loads(payload)

    postbacks = data["entry"][0]["messaging"]
    print(postbacks)
    for event in postbacks:
        sender_id = event["sender"]["id"]
        postback_payload = event["postback"]["payload"]
        yield sender_id, postback_payload

#this will check the subreddit the user choses
def checkSubReddit(token, recipient, subreddit_name):
    #checks if the user has been added to the database or it hasnt been added
    myUser = get_or_create(db.session, Users, name=recipient)
    if subreddit_name == "Showerthoughts":
        payload = "You can think of a showerthought by yourself, but this bot needs to have some time in the shower first"
        for submission in reddit.subreddit(subreddit_name).hot(limit=None):
            if (submission.is_self == True):
                query_result = Posts.query.filter(Posts.name == submission.id).first()
                if query_result is None:
                    myPost = Posts(submission.id, submission.title)
                    myUser.posts.append(myPost)
                    db.session.commit()
                    payload = submission.title
                    break
                elif myUser not in query_result.users:
                    myUser.posts.append(query_result)
                    db.session.commit()
                    payload = submission.title
                    break
                else:
                    continue
    
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params={"access_token": token},
                          data=json.dumps({
                                          "recipient": {"id": recipient},
                                          "message": {"text": payload,
                                          "quick_replies": quick_replies_list}
                                          }),
                          headers={'Content-type': 'application/json'})

elif subreddit_name == "Jokes":
    payload = "Come back later!"
        payload_text = "I have no more jokes!"
        for submission in reddit.subreddit(subreddit_name).hot(limit=None):
            if ((submission.is_self == True) and (submission.link_flair_text is None)):
                query_result = Posts.query.filter(Posts.name == submission.id).first()
                if query_result is None:
                    myPost = Posts(submission.id, submission.title)
                    myUser.posts.append(myPost)
                    db.session.commit()
                    payload = submission.title
                    payload_text = submission.selftext
                    break
                elif myUser not in query_result.users:
                    myUser.posts.append(query_result)
                    db.session.commit()
                    payload = submission.title
                    payload_text = submission.selftext
                    break
                else:
                    continue

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                                      "recipient": {"id": recipient},
                                      "message": {"text": payload}
                                      }),
                      headers={'Content-type': 'application/json'})
        
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params={"access_token": token},
                          data=json.dumps({
                                          "recipient": {"id": recipient},
                                          "message": {"text": payload_text,
                                          "quick_replies": quick_replies_list}
                                          }),
                          headers={'Content-type': 'application/json'})

elif subreddit_name == "GetMotivated":
    payload = "https://i.kym-cdn.com/photos/images/original/001/047/847/73f.png"
        for submission in reddit.subreddit(subreddit_name).hot(limit=None):
            if (submission.link_flair_css_class == 'image') or (
                                                                (submission.is_self != True) and ((".jpg" in submission.url) or (".png" in submission.url))):
                query_result = Posts.query.filter(Posts.name == submission.id).first()
                if query_result is None:
                    myPost = Posts(submission.id, submission.url)
                    myUser.posts.append(myPost)
                    db.session.commit()
                    payload = submission.url
                    break
                elif myUser not in query_result.users:
                    myUser.posts.append(query_result)
                    db.session.commit()
                    payload = submission.url
                    break
                else:
                    continue

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                                      "recipient": {"id": recipient},
                                      "message": {"attachment": {
                                      "type": "image",
                                      "payload": {
                                      "url": payload
                                      }},
                                      "quick_replies": quick_replies_list}
                                      }),
                      headers={'Content-type': 'application/json'})

elif subreddit_name == "memes":
    payload = "https://i.kym-cdn.com/photos/images/original/001/047/847/73f.png"
        for submission in reddit.subreddit(subreddit_name).hot(limit=None):
            if (submission.link_flair_css_class == 'image') or (
                                                                (submission.is_self != True) and ((".jpg" in submission.url) or (".png" in submission.url))):
                query_result = Posts.query.filter(Posts.name == submission.id).first()
                if query_result is None:
                    myPost = Posts(submission.id, submission.url)
                    myUser.posts.append(myPost)
                    db.session.commit()
                    payload = submission.url
                    break
                elif myUser not in query_result.users:
                    myUser.posts.append(query_result)
                    db.session.commit()
                    payload = submission.url
                    break
                else:
                    continue

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                                      "recipient": {"id": recipient},
                                      "message": {"attachment": {
                                      "type": "image",
                                      "payload": {
                                      "url": payload
                                      }},
                                      "quick_replies": quick_replies_list}
                                      }),
                      headers={'Content-type': 'application/json'})

elif subreddit_name == "facepalm":
    payload = "https://i.kym-cdn.com/photos/images/original/001/047/847/73f.png"
        for submission in reddit.subreddit(subreddit_name).hot(limit=None):
            if (submission.link_flair_css_class == 'image') or (
                                                                (submission.is_self != True) and ((".jpg" in submission.url) or (".png" in submission.url))):
                query_result = Posts.query.filter(Posts.name == submission.id).first()
                if query_result is None:
                    myPost = Posts(submission.id, submission.url)
                    myUser.posts.append(myPost)
                    db.session.commit()
                    payload = submission.url
                    break
                elif myUser not in query_result.users:
                    myUser.posts.append(query_result)
                    db.session.commit()
                    payload = submission.url
                    break
                else:
                    continue

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                                      "recipient": {"id": recipient},
                                      "message": {"attachment": {
                                      "type": "image",
                                      "payload": {
                                      "url": payload
                                      }},
                                      "quick_replies": quick_replies_list}
                                      }),
                      headers={'Content-type': 'application/json'})

elif subreddit_name == "Aww":
    payload = "https://i.kym-cdn.com/photos/images/original/001/047/847/73f.png"
        for submission in reddit.subreddit(subreddit_name).hot(limit=None):
            if (submission.link_flair_css_class == 'image') or (
                                                                (submission.is_self != True) and ((".jpg" in submission.url) or (".png" in submission.url))):
                query_result = Posts.query.filter(Posts.name == submission.id).first()
                if query_result is None:
                    myPost = Posts(submission.id, submission.url)
                    myUser.posts.append(myPost)
                    db.session.commit()
                    payload = submission.url
                    break
                elif myUser not in query_result.users:
                    myUser.posts.append(query_result)
                    db.session.commit()
                    payload = submission.url
                    break
                else:
                    continue

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                                      "recipient": {"id": recipient},
                                      "message": {"attachment": {
                                      "type": "image",
                                      "payload": {
                                      "url": payload
                                      }},
                                      "quick_replies": quick_replies_list}
                                      }),
                      headers={'Content-type': 'application/json'})

elif subreddit_name == "hotline":
    payload = "Hey, I know at this moment it may not mean much, but we at Todd care. Please take care of yourself. Here is a hotline you should call if you need help!";
        payload_text = "1-800-273-8255";
        
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params={"access_token": token},
                          data=json.dumps({
                                          "recipient": {"id": recipient},
                                          "message": {"text": payload}
                                          }),
                          headers={'Content-type': 'application/json'})
            
                          r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                                            params={"access_token": token},
                                            data=json.dumps({
                                                            "recipient": {"id": recipient},
                                                            "message": {"text": payload_text,
                                                            "quick_replies": quick_replies_list}
                                                            }),
                                            headers={'Content-type': 'application/json'})

else:
    payload = "I'm Todd! I can send a meme, joke, showerthought, or motivational thought!"
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params={"access_token": token},
                          data=json.dumps({
                                          "recipient": {"id": recipient},
                                          "message": {"text": payload,
                                          "quick_replies": quick_replies_list}
                                          }),
                          headers={'Content-type': 'application/json'})
    
    if r.status_code != requests.codes.ok:
        print r.text

#this is to handle the first time user and add them to the database
def handle_first_time_user(user, token):
    page.typing_on(user)
    
    user_profile = page.get_user_profile(user)
    
    hi = "Hi {}, nice to meet you :)".format(user_profile['first_name'])
    myUser = get_or_create(db.session, Users, name = user)
    
    payload = "I'm Todd! I can send a meme, joke, showerthought, or motivational thought! I'm here to make you smile! Try me out!"
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                                      "recipient": {"id": user},
                                      "message": {"text": hi,
                                      "quick_replies": quick_replies_list}
                                      }),
                      headers={'Content-type': 'application/json'})
        
                      r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                                        params={"access_token": token},
                                        data=json.dumps({
                                                        "recipient": {"id": user},
                                                        "message": {"text": payload,
                                                        "quick_replies": quick_replies_list}
                                                        }),
                                        headers={'Content-type': 'application/json'})
                      page.typing_off(user)
                      if r.status_code != requests.codes.ok:
                          print r.text


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


relationship_table = db.Table('relationship_table',
                              db.Column('user_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
                              db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), nullable=False),
                              db.PrimaryKeyConstraint('user_id', 'post_id'))


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    posts = db.relationship('Posts', secondary=relationship_table, backref='users')

    def __init__(self, name=None):
        self.name = name


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    url = db.Column(db.String, nullable=False)

    def __init__(self, name=None, url=None):
        self.name = name
        self.url = url


if __name__ == '__main__':
    app.run()
