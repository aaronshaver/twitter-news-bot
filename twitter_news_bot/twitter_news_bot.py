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
            logging.info('No savepoint found. Trying to get as many results (tweets) as possible ' + get_current_time_string())
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
        self.sleep_time = int(self.config.get("settings", "time_between_retweets_in_seconds"))
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
        print("\n\n\nThe Twitter retweet bot is now running. Please see the dated .log file for output." + get_current_time_string())

        while True:
            logging.info("Doing the actual Twitter search..." + get_current_time_string())
            timeline_iterator = tweepy.Cursor(self.api.search, q=self.search_term, since_id=self.savepoint,
                                              lang=self.tweet_language, wait_on_rate_limit=True,
                                              wait_on_rate_limit_notify=True). \
                items(int(self.config.get("settings", "max_tweets_to_fetch")))

            timeline = []
            logging.info("appending statuses to timeline..." + get_current_time_string())
            for status in timeline_iterator:
                timeline.append(status)
            if len(timeline) < 1:
                logging.error("Exiting program. Zero tweets. Something went wrong (OAuth or search had no results)" + get_current_time_string())
                sys.exit()
            logging.info("Total tweets found: " + str(len(timeline)) + get_current_time_string())

            logging.info("Sorting tweets by highest retweet count...")
            timeline.sort(key=lambda x: x.retweet_count, reverse=True)  # put most-retweeted tweets first

            try:
                logging.info("trying to get last tweet id by most recent in the bot's timeline" + get_current_time_string())
                last_tweet_id = timeline[0].id
            except IndexError:
                logging.info("there was an index error, so use the savepoint instead" + get_current_time_string())
                last_tweet_id = self.savepoint

            logging.info("Doing filtering of tweets..." + get_current_time_string())
            timeline = [tweet for tweet in timeline if hasattr(tweet, "retweeted_status")]
            timeline = filter(lambda tweet: tweet.text[0] != "@", timeline)
            timeline = filter(lambda tweet: not any(word in tweet.text.split() for word in self.wordBlacklist),
                              timeline)
            timeline = filter(lambda tweet: tweet.author.screen_name not in self.userBlacklist, timeline)
            timeline = filter(lambda tweet: tweet.retweeted_status.created_at >
                                            (datetime.utcnow() - timedelta(minutes=self.max_age_in_minutes)), timeline)

            logging.info("Filtering done." + get_current_time_string())

            logging.info("Going through statuses in timeline..." + get_current_time_string())
            success = False
            for status in timeline:
                try:
                    if self.config.get("settings", "retweeting_enabled") == "True":
                        logging.info("Attempting to retweet " + str(status.id) + "..." + get_current_time_string())
                        self.api.retweet(status.id)
                        logging.info("Retweeting tweet id " + str(status.id) + " succeeded!" + get_current_time_string())
                        last_tweet_id = status.id
                        success = True
                        break
                    else:
                        logging.warning("retweeting_enabled is not True, so we do nothing instead of retweet" + get_current_time_string())
                        break
                except tweepy.error.TweepError as e:
                    logging.info("Tweepy error: " + e.reason + get_current_time_string())
                    continue
            
            if success == False:
                logging.info("If retweeting continues to fail, try increasing max_tweets_to_fetch in the config file or using a different search phrase")

            logging.info("Writing last id file..." + get_current_time_string())
            with open(self.last_id_file, "w") as file:
                file.write(str(last_tweet_id))

            logging.info("Now sleeping for %d seconds between retweets" % self.sleep_time)
            logging.info("It is now" + get_current_time_string())
            logging.info("------------------------------------------------------------------------------")
            time.sleep(self.sleep_time)

def get_current_time_string():
    return " [" + datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S") + "]"

if __name__ == "__main__":
    bot = TwitterNewsBot()
    bot.retweet()
