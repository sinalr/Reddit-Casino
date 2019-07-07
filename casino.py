import praw
import config
import random
import sqlite3
import requests
import re
from datetime import date,timedelta
import time

connection= sqlite3.connect('casino.db')
c = connection.cursor()

# c.execute("""CREATE TABLE users (
#            username text,
#            balance integer
#            )""")
# #
# c.execute("""CREATE TABLE comments (
#             id text
#             )""")

connection.commit()

def bot_login():
    print ("Logging in...")
    global r
    r = praw.Reddit(username = config.username,
            password = config.password,
            client_id = config.client_id,
            client_secret = config.client_secret,
            user_agent = config.user_agent)
    print ("Logged in!")

def run():
    for i in range(len(config.terms)):
        print("Searching for new comments with term: {}".format(config.terms[i]))
        search(config.terms[i])
    time.sleep(30)

def search(term):
    request = requests.get('https://api.pushshift.io/reddit/search/comment/?q=!{}&subreddit={}&limit=10'.format(term,config.subreddits))
    json = request.json()
    comments = json["data"]
    for comment in comments:
        author = comment["author"].lower()
        body = comment["body"]
        id = comment["id"]
        c.execute("SELECT * FROM users WHERE username='{}'".format(author))
        if c.fetchone() == None:
            print("Found new user: {}! Adding them to the database".format(author))
            c.execute("INSERT INTO users VALUES ('{}', 1000)".format(author))
            connection.commit()
        check_comment(author,body,id)

def check_comment(author,body,id):
    global r
    c.execute("SELECT id FROM comments WHERE id='{}'".format(id))
    if c.fetchone() == None:
        c.execute("INSERT INTO comments VALUES ('{}')".format(id))
        connection.commit()
        c.execute("SELECT balance FROM users WHERE username='{}'".format(author))
        balance = c.fetchone()[0]
        comment = r.comment(id=id)
        if "!resetbalance" in body:
            print("Resetting {}'s balance'".format(author))
            balance = 1000
            comment.reply(config.resetbalance_text + config.footer_text)
        elif "!checkbalance" in body:
            if body == "!checkbalance":
                print("Checking {}'s balance".format(author))
                comment.reply(config.checkbalance_self.format(balance) + config.footer_text)
            else:
                try:
                    body = body.split(" ")
                    username = (body[1].replace("/u/","")).lower()
                    print("Checking {}'s balance'".format(username))
                    c.execute("SELECT balance FROM users WHERE username='{}'".format(username))
                    checkbalance = c.fetchone()[0]
                    comment.reply(config.checkbalance_text.format(username,checkbalance) + config.footer_text)
                except:
                    print("Tried to check {}'s balance, but they were not in the database".format(username))
                    comment.reply(config.checkbalance_error + config.footer_text)
        elif "!setbalance" in body and author in config.admin_list:
            #make sure to add log
            [empty,username,amount] = body.split(" ")
            username = (username.replace("/u/","")).lower()
            if author == username:
                balance = amount
            print("{} set {}'s balance to {}".format(author,username,amount))
            c.execute("UPDATE users SET balance={} WHERE username='{}'".format(amount,username))
            connection.commit()
            comment.reply(config.setbalance_text.format(username,amount) + config.footer_text)
        elif "!tipcredits" in body:
            [empty,username,amount] = body.split(" ")
            username = (username.replace("/u/","")).lower()
            amount = int(amount)
            if amount > balance:
                print("{} tried to tip {} but did not have enough credits".format(author,username))
                amount_needed = amount - balance
                comment.reply(config.insufficient_text.format(amount_needed) + config.footer_text)
            else:
                cakeday = (r.redditor(author)).created_utc
                cakeday = date.fromtimestamp(cakeday)
                today = date.today()
                minage = date.today() - timedelta(days=30)
                if ((cakeday.year < minage.year) or (cakeday.year == minage.year and cakeday.month < minage.month) or (cakeday.year == minage.year and cakeday.month == minage.month and cakeday.day < minage.day ) ):
                    c.execute("SELECT * FROM users WHERE username='{}'".format(username))
                    if c.fetchone() == None:
                        print("Found new user: {}! Adding them to the database".format(username))
                        c.execute("INSERT INTO users VALUES ('{}', 1000)".format(username))
                        connection.commit()
                    c.execute("SELECT balance FROM users WHERE username='{}'".format(username))
                    tippedbalance = c.fetchone()[0]
                    tippedbalance = tippedbalance + amount
                    balance = balance - amount
                    c.execute("UPDATE users SET balance={} WHERE username='{}'".format(tippedbalance,username))
                    comment.reply(config.tip_text.format(username,amount,balance) + config.footer_text)
                    connection.commit()
                else:
                    print("{} tried to tip but is not old enough".format(author))
                    comment.reply(config.tip_age + config.footer_text)
        elif "!coinflip" in body:
            try:
                [empty,bet,choice] = body.split(" ")
                choice = choice.lower()
                bet = int(bet)
                if bet <= balance:
                    print("{} is playing gamemode: Coinflip".format(author))
                    flip = random.choice(["Heads","Tails"])
                    if flip.lower() == choice:
                        balance = balance + bet
                        comment.reply(config.coinflip_win.format(flip,bet,balance) + config.footer_text)
                    else:
                        balance = balance - bet
                        comment.reply(config.coinflip_lose.format(flip,bet,balance) + config.footer_text)
                else:
                    print(config.insufficient_print.format(author,"!coinflip"))
                    amount_needed = bet - balance
                    comment.reply(config.insufficient_text.format(amount_needed) + config.footer_text)
            except:
                print(config.invalid_print.format("!coinflip",author))
                comment.reply(config.invalid_text.format("!coinflip") + config.footer_text)
        # elif "!slots" in body:











# def reply(id,message,vals):
#     global r
#     comment = r.comment(id=id)
#     try:
#         comment.reply(message.format(*vals))
#     except:
#         print("Error when trying to reply to comment {}".format(id))





























# def error_log(error):
#     # log errors to a text file with date
#     x = 1



bot_login()
run()
