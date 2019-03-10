#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import hashlib
import inspect
import logging
import os
import sys
import time
from datetime import datetime, timedelta

import tweepy

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    date_time_name = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    handler = logging.FileHandler(date_time_name + '.log', mode='w')
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

class TwitterNewsBot:
    def retrieve_save_point(self):
        try:
            with open(self.last_id_file, "r") as saved_file:
                return saved_file.read()
        except IOError:
            self.logger.info('No savepoint found. Trying to get as many results (tweets) as possible ')
            return ""

    def build_save_point(self):
        hashedsearch_term = hashlib.md5(self.search_term.encode('utf-8')).hexdigest()
        last_id_filename = "last_id_search_term_%s" % hashedsearch_term
        current_directory = os.path.dirname(os.path.abspath(__file__))
        last_id_file = os.path.join(current_directory, last_id_filename)
        return last_id_file

    def __init__(self):
        self.logger = setup_custom_logger('myapp')
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(path, "configuration.txt"))
        self.sleep_time = int(self.config.get("settings", "time_between_retweets_in_seconds"))
        self.search_term = self.config.get("settings", "search_query")
        self.tweet_language = self.config.get("settings", "tweet_language")
        self.max_age_in_minutes = int(self.config.get("settings", "max_age_in_minutes"))

        self.last_id_file = self.build_save_point()
        self.savepoint = self.retrieve_save_point()

        auth = tweepy.OAuthHandler(self.config.get("twitter", "consumer_key"), self.config.
                                   get("twitter", "consumer_secret"))
        auth.set_access_token(self.config.get("twitter", "access_token"), self.config.
                              get("twitter", "access_token_secret"))
        self.api = tweepy.API(auth)

    def retweet(self):
        print("\n\n\nThe Twitter retweet bot is now running. Please see the dated .log file for output.")

        while True:
            self.logger.info("Doing the actual Twitter search...")
            timeline_iterator = tweepy.Cursor(self.api.search, q=self.search_term, since_id=self.savepoint,
                                              lang=self.tweet_language, wait_on_rate_limit=True,
                                              wait_on_rate_limit_notify=True). \
                items(int(self.config.get("settings", "max_tweets_to_fetch")))

            timeline = []
            self.logger.info("Appending statuses to timeline...")
            for status in timeline_iterator:
                timeline.append(status)
            if len(timeline) < 1:
                self.logger.error("Something went wrong (no tweets found).")
                self.logger.error("Make sure OAuth is working (correct keys, etc. and networking is open if using a cloud provider).")
                self.logger.error("It's also possible you're using search settings that are way too restrictive, like an unusual phrase or you're not fetching enough tweets.") 
                print("\n\nError. See latest .log file for details.\n\n")
                sys.exit()
            self.logger.info("Total tweets found: " + str(len(timeline)))

            self.logger.info("Sorting tweets by highest retweet count...")
            timeline.sort(key=lambda x: x.retweet_count, reverse=True)  # put most-retweeted tweets first

            try:
                self.logger.info("Trying to get last tweet id by most recent in the bot's timeline")
                last_tweet_id = timeline[0].id
            except IndexError:
                self.logger.info("There was an index error, so use the savepoint instead")
                last_tweet_id = self.savepoint

            self.logger.info("Filtering of tweets...")
            self.logger.info("Initial length of timeline: " + str(len(timeline)))
            timeline = [tweet for tweet in timeline if hasattr(tweet, "retweeted_status")]
            self.logger.info("Length after filtering out un-retweeted tweets: " + str(len(timeline)))
            timeline = [tweet for tweet in timeline if tweet.text[0] != "@"]  # prevents retweeting @ mention tweets
            self.logger.info("Length after filtering out @ mention tweets: " + str(len(timeline)))

            for tweet in timeline:
                self.logger.debug(tweet)
            no_older_than_this_time = datetime.utcnow() - timedelta(minutes=self.max_age_in_minutes)
            timeline = [tweet for tweet in timeline if tweet.retweeted_status.created_at > no_older_than_this_time]
            self.logger.info("Length after filtering out tweets that are older than our specified max age: " + str(len(timeline)))

            num_tweets_after_filtering = len(timeline)
            self.logger.info("Final length of timeline: " + str(num_tweets_after_filtering))

            if self.config.get("settings", "retweeting_enabled") == "True":
                if num_tweets_after_filtering > 0:
                    stop_trying_to_retweet = False
                    while not stop_trying_to_retweet:
                        for status in timeline:
                            self.logger.info("Going through statuses in timeline...")
                            try:
                                self.logger.info("Attempting to retweet " + str(status.id) + "...")
                                self.api.retweet(status.id)
                                self.logger.info("Retweeting tweet id " + str(status.id) + " succeeded!")
                                last_tweet_id = status.id
                                stop_trying_to_retweet = True
                                break
                            except tweepy.error.TweepError as e:
                                self.logger.info("Tweepy error: " + e.reason())
                                continue
                            except:
                                self.logger.error("Unexpected error: ", sys.exc_info()[0])
                                raise
                else:
                    self.logger.warning("There were no tweets left after filtering")
                    self.logger.warning("Hints: try increasing max_tweets_to_fetch, or increasing max_age_in_minutes, or use a different search phrase")
            else:
                self.logger.warning("retweeting_enabled is not True, so we do nothing instead of retweet")

            self.logger.info("Writing last id file...")
            with open(self.last_id_file, "w") as file:
                file.write(str(last_tweet_id))

            self.logger.info("Now sleeping for %d seconds between retweets" % self.sleep_time)
            self.logger.info("------------------------------------------------------------------------------")
            time.sleep(self.sleep_time)

if __name__ == "__main__":
    bot = TwitterNewsBot()
    bot.retweet()
