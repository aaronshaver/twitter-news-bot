#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import hashlib
import inspect
import os

import tweepy

path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# read config
config = configparser.ConfigParser()
config.read(os.path.join(path, "config"))

# your search query and tweet language (empty = all languages)
search_term = config.get("settings", "search_query")
tweetLanguage = config.get("settings", "tweet_language")

# blacklisted users and words
userBlacklist = []
wordBlacklist = []

# build savepoint path + file
hashedsearch_term = hashlib.md5(search_term.encode('utf-8')).hexdigest()
last_id_filename = "last_id_search_term_%s" % hashedsearch_term
rt_bot_path = os.path.dirname(os.path.abspath(__file__))
last_id_file = os.path.join(rt_bot_path, last_id_filename)

# create bot
auth = tweepy.OAuthHandler(config.get("twitter", "consumer_key"), config.get("twitter", "consumer_secret"))
auth.set_access_token(config.get("twitter", "access_token"), config.get("twitter", "access_token_secret"))
api = tweepy.API(auth)

# retrieve last savepoint if available
try:
    with open(last_id_file, "r") as file:
        savepoint = file.read()
except IOError:
    savepoint = ""
    print("No savepoint found. Trying to get as many results as possible.")

timelineIterator = tweepy.Cursor(api.search, q=search_term, since_id=savepoint, lang=tweetLanguage,
                                 wait_on_rate_limit=True, wait_on_rate_limit_notify=True).items()

# put everything into a list to be able to sort/filter
timeline = []
for status in timelineIterator:
    print('.', end="")
    timeline.append(status)

try:
    last_tweet_id = timeline[0].id
except IndexError:
    last_tweet_id = savepoint

# filter @replies/blacklisted words & users out and reverse timeline
timeline = filter(lambda status: status.text[0] != "@", timeline)
timeline = filter(lambda status: not any(word in status.text.split() for word in wordBlacklist), timeline)
timeline = filter(lambda status: status.author.screen_name not in userBlacklist, timeline)
# timeline.reverse()

tw_counter = 0
err_counter = 0

# iterate the timeline and retweet
for status in timeline:
    try:
        print("(%(date)s) %(name)s: %(message)s\n" % \
              {"date": status.created_at,
               "name": status.author.screen_name.encode('utf-8'),
               "message": status.text.encode('utf-8')})

        api.retweet(status.id)
        tw_counter += 1
    except tweepy.error.TweepError as e:
        # just in case tweet got deleted in the meantime or already retweeted
        err_counter += 1
        # print e
        continue

print("Finished. %d Tweets retweeted, %d errors occured." % (tw_counter, err_counter))

# write last retweeted tweet id to file
with open(last_id_file, "w") as file:
    file.write(str(last_tweet_id))
