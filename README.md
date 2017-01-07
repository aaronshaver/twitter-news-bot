[![Build Status](https://travis-ci.org/aaronshaver/twitter-news-bot.svg?branch=master)](https://travis-ci.org/aaronshaver/twitter-news-bot)

# twitter-news-bot

This is a Twitter bot that periodically retweets the most retweeted recent tweets for a search term. It has additional
features, such as being able to specify how many tweets you want to fetch and the maximum age for those tweets.

## Setup

1. Install Python 3.x
2. pip install tweepy
3. Edit the configuration.sample file and rename it to configuration.txt
4. python Bot/bot.py
5. Tip: if running on, e.g. an EC2 instance, make sure networking/security groups are sufficiently open for the OAuth
call to be made, and then run the script with 'nohup python Bot/bot.py &' to keep it running even when you close your
SSH client. You can then 'ps aux' to see the running process, and 'kill <pid>' to kill it.
