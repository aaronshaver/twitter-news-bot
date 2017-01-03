#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import hashlib
import inspect
import os
import sys
import time
from datetime import datetime, timedelta

import tweepy


class Bot:
    userBlacklist = []
    wordBlacklist = []

    @staticmethod
    def write_to_log(text):
        print(str(datetime.utcnow()))
        print(str(text) + "\n")

    @staticmethod
    def retrieve_save_point(self, last_id_file):
        try:
            with open(last_id_file, "r") as saved_file:
                self.savepoint = saved_file.read()
        except IOError:
            self.write_to_log("No savepoint found. Trying to get as many results as possible.")
            self.savepoint = ""

    @staticmethod
    def build_log_file():
        log_filename = "log.txt"
        current_directory = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_directory, log_filename)

    def build_save_point(self):
        hashedsearch_term = hashlib.md5(self.search_term.encode('utf-8')).hexdigest()
        last_id_filename = "last_id_search_term_%s" % hashedsearch_term
        current_directory = os.path.dirname(os.path.abspath(__file__))
        last_id_file = os.path.join(current_directory, last_id_filename)
        return last_id_file

    def __init__(self):
        self.log_filename = self.build_log_file()

        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(path, "configuration.txt"))
        self.search_term = self.config.get("settings", "search_query")
        self.tweet_language = self.config.get("settings", "tweet_language")
        self.last_id_file = self.build_save_point()
        self.retrieve_save_point(self, self.last_id_file)

        auth = tweepy.OAuthHandler(self.config.get("twitter", "consumer_key"), self.config.
                                   get("twitter", "consumer_secret"))
        auth.set_access_token(self.config.get("twitter", "access_token"), self.config.
                              get("twitter", "access_token_secret"))
        self.api = tweepy.API(auth)

    def execute(self):
        while True:
            self.write_to_log("Creating timeline iterator...")
            timeline_iterator = tweepy.Cursor(self.api.search, q=self.search_term, since_id=self.savepoint,
                                              lang=self.tweet_language, wait_on_rate_limit=True,
                                              wait_on_rate_limit_notify=True). \
                items(int(self.config.get("settings", "max_tweets_to_fetch")))

            self.write_to_log("Puting items from tweety.Cursor object into a list for easier sorting, filtering...")
            timeline = []
            for status in timeline_iterator:
                timeline.append(status)

            self.write_to_log("\nTotal tweets found: " + str(len(timeline)))

            timeline.sort(key=lambda x: x.retweet_count, reverse=True)  # put most-retweeted tweets at head of list

            try:
                last_tweet_id = timeline[0].id
                self.write_to_log("\nNEW last tweet id: " + str(last_tweet_id))
            except IndexError:
                last_tweet_id = self.savepoint
                self.write_to_log("\nRe-using old, savepoint tweet id: " + str(last_tweet_id))

            if len(timeline) < 1:
                self.write_to_log("Timeline had zero tweets; something probably went wrong, or search had no results")
                self.write_to_log("Exiting program so you can fix your configuration")
                sys.exit()

            timeline = [tweet for tweet in timeline if hasattr(tweet, "retweeted_status")]
            timeline = filter(lambda tweet: tweet.text[0] != "@", timeline)
            timeline = filter(lambda tweet: not any(word in tweet.text.split() for word in self.wordBlacklist),
                              timeline)
            timeline = filter(lambda tweet: tweet.author.screen_name not in self.userBlacklist, timeline)
            minutes_age = int(self.config.get("settings", "max_age_in_minutes"))
            timeline = filter(lambda tweet: tweet.retweeted_status.created_at >
                                            (datetime.utcnow() - timedelta(minutes=minutes_age)), timeline)

            self.write_to_log("Attempting to retweet the most-retweeted tweet...\n")
            success = False
            err_counter = 0
            while not success:
                for status in timeline:
                    try:
                        if self.config.get("settings", "retweeting_enabled") == "True":
                            self.api.retweet(status.id)
                            self.write_to_log("Retweeting " + str(status.id) + " succeeded\n")
                            success = True
                            last_tweet_id = status.id
                            break
                    except tweepy.error.TweepError as e:
                        self.write_to_log("Error: " + e.reason + "\n")
                        err_counter += 1
                        continue

            self.write_to_log("FINISHED. %d errors occured" % err_counter)

            with open(self.last_id_file, "w") as file:
                file.write(str(last_tweet_id))

            sleep_time = int(self.config.get("settings", "time_between_retweets"))
            self.write_to_log("\nSleeping for %d seconds between retweets..." % sleep_time)
            self.write_to_log(
                "\n-------------------------------------------------------------------------------------------------\n")
            time.sleep(sleep_time)


bot = Bot()
bot.execute()
