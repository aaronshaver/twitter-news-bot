# twitter-news-bot

Python Twitter bot that periodically retweets the most retweeted recent tweets for a search term

Code inspired by : https://github.com/basti2342/retweet-bot

## Setup

1. Install Python 3.x
2. pip install tweepy
3. Edit the configuration.sample file and rename it to configuration.txt
4. Tip: if running on, e.g. an EC2 instance, make sure networking is sufficient for the OAuth call to be made, and then
run the script with 'sudo nohup python Bot.py' to keep it running, and 'sudo ps aux' to see the running process