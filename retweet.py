#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import hashlib
import inspect
import os
import time

import tweepy

# read config
path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
config = configparser.ConfigParser()
config.read(os.path.join(path, "configuration.txt"))

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

while True:
    # retrieve last savepoint if available
    try:
        with open(last_id_file, "r") as file:
            savepoint = file.read()
    except IOError:
        savepoint = ""
        print("No savepoint found. Trying to get as many results as possible.")

    print("Creating timeline iterator...\n")
    timelineIterator = tweepy.Cursor(api.search, q=search_term, since_id=savepoint, lang=tweetLanguage,
                                     wait_on_rate_limit=True, wait_on_rate_limit_notify=True). \
        items(int(config.get("settings", "max_tweets_to_fetch")))

    print("Put items from tweety.Cursor object into a list for easier sorting, filtering...\n")
    timeline = []
    total = 0
    for status in timelineIterator:
        timeline.append(status)
        total += 1
    print("Total tweets found: " + str(total) + "\n")

    # print()
    # pprint(vars(timeline[0]))
    # print()

    timeline.sort(key=lambda x: x.retweet_count, reverse=True)

    try:
        last_tweet_id = timeline[0].id
    except IndexError:
        last_tweet_id = savepoint

    # filter @replies/blacklisted words & users out and reverse timeline
    timeline = filter(lambda status: status.text[0] != "@", timeline)
    timeline = filter(lambda status: not any(word in status.text.split() for word in wordBlacklist), timeline)
    timeline = filter(lambda status: status.author.screen_name not in userBlacklist, timeline)
    # timeline.reverse()

    err_counter = 0

    print("Attempting to retweet the most-retweeted tweet...\n")
    success = False

    while not success:
        for status in timeline:
            try:
                if config.get("settings", "retweeting_enabled") == "True":
                    api.retweet(status.id)
                    print("Retweeting " + str(status.id) + " succeeded\n")
                    success = True
                    break
            except tweepy.error.TweepError as e:
                print("Error: " + e.reason + "\n")
                err_counter += 1
                continue

    print("Finished attempting to retweet from that batch of tweets; %d errors occured" % err_counter)

    # write last retweeted tweet id to file
    with open(last_id_file, "w") as file:
        file.write(str(last_tweet_id))

    sleep_time = int(config.get("settings", "time_between_retweets"))
    print("\nSleeping for %d seconds between retweets..." % sleep_time)
    print("\n-------------------------------------------------------------------------------------------------------\n")
    time.sleep(sleep_time)
