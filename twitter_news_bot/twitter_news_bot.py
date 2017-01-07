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


class TwitterNewsBot:
    userBlacklist = []
    wordBlacklist = []

    @staticmethod
    def retrieve_save_point(last_id_file):
        try:
            with open(last_id_file, "r") as saved_file:
                return saved_file.read()
        except IOError:
            logging.info('No savepoint found. Trying to get as many results (tweets) as possible.')
            return ""

    def build_save_point(self):
        hashedsearch_term = hashlib.md5(self.search_term.encode('utf-8')).hexdigest()
        last_id_filename = "last_id_search_term_%s" % hashedsearch_term
        current_directory = os.path.dirname(os.path.abspath(__file__))
        last_id_file = os.path.join(current_directory, last_id_filename)
        return last_id_file

    def __init__(self):
        date_time_name = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename=date_time_name + '.log', level=logging.INFO)

        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(path, "configuration.txt"))
        self.sleep_time = int(self.config.get("settings", "time_between_retweets"))
        self.search_term = self.config.get("settings", "search_query")
        self.tweet_language = self.config.get("settings", "tweet_language")
        self.max_age_in_minutes = int(self.config.get("settings", "max_age_in_minutes"))

        self.last_id_file = self.build_save_point()
        self.savepoint = self.retrieve_save_point(self.last_id_file)

        auth = tweepy.OAuthHandler(self.config.get("twitter", "consumer_key"), self.config.
                                   get("twitter", "consumer_secret"))
        auth.set_access_token(self.config.get("twitter", "access_token"), self.config.
                              get("twitter", "access_token_secret"))
        self.api = tweepy.API(auth)

    def retweet(self):
        print("The Twitter retweet bot is now running. Please see the dated .log file for output.")

        while True:
            timeline_iterator = tweepy.Cursor(self.api.search, q=self.search_term, since_id=self.savepoint,
                                              lang=self.tweet_language, wait_on_rate_limit=True,
                                              wait_on_rate_limit_notify=True). \
                items(int(self.config.get("settings", "max_tweets_to_fetch")))

            timeline = []
            for status in timeline_iterator:
                timeline.append(status)
            if len(timeline) < 1:
                logging.error("Exiting program. Zero tweets. Something went wrong (OAuth or search had no results)")
                sys.exit()
            logging.info("Total tweets found: " + str(len(timeline)))

            timeline.sort(key=lambda x: x.retweet_count, reverse=True)  # put most-retweeted tweets first

            try:
                last_tweet_id = timeline[0].id
            except IndexError:
                last_tweet_id = self.savepoint

            timeline = [tweet for tweet in timeline if hasattr(tweet, "retweeted_status")]
            timeline = filter(lambda tweet: tweet.text[0] != "@", timeline)
            timeline = filter(lambda tweet: not any(word in tweet.text.split() for word in self.wordBlacklist),
                              timeline)
            timeline = filter(lambda tweet: tweet.author.screen_name not in self.userBlacklist, timeline)
            timeline = filter(lambda tweet: tweet.retweeted_status.created_at >
                                            (datetime.utcnow() - timedelta(minutes=self.max_age_in_minutes)), timeline)

            success = False
            while not success:
                for status in timeline:
                    try:
                        if self.config.get("settings", "retweeting_enabled") == "True":
                            self.api.retweet(status.id)
                            logging.info("Retweeting tweet id " + str(status.id) + " succeeded")
                            success = True
                            last_tweet_id = status.id
                            break
                        else:
                            logging.warning("retweeting_enabled is not True, so we do nothing instead of retweet")
                            success = True
                            break
                    except tweepy.error.TweepError as e:
                        logging.info("Tweepy error: " + e.reason)
                        continue

            with open(self.last_id_file, "w") as file:
                file.write(str(last_tweet_id))

            logging.info("Now time.sleep for %d seconds between retweets" % self.sleep_time)
            logging.info("------------------------------------------------------------------------------")
            time.sleep(self.sleep_time)

if __name__ == "twitter_news_bot":
    bot = TwitterNewsBot()
    bot.retweet()
